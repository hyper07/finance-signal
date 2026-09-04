"""Shared data loading for the news-shock event study.

Everything here is offline and reproducible: prices come from the Alpaca
archive in ``data/alpaca`` and the frozen live signals come from the public
dataset export cached in ``research/output``.  The production signal engine
(``model/strategy.run_simulation``) and forecast engine
(``model/forecast.build_forecast``) are imported unchanged so the study
evaluates exactly the code that runs on signal.dotori.ai.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO / "model"
ALPACA_DIR = REPO / "data" / "alpaca"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
PUBLIC_BASE = "https://signal.dotori.ai"

if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

PRED_TO_SIGNAL = {"long": 1, "short": -1, "hold": 0}


def _dedupe_alpaca(frame: pd.DataFrame, keep: str) -> pd.DataFrame:
    """Alpaca CSVs hold two pulls per (symbol, day): an IEX and a SIP feed.

    Equity rows: keep the higher-volume (SIP, consolidated) print.
    Crypto rows: both pulls are identical except the still-open last bar, so
    keep the later pull.
    """
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["t"], utc=True).dt.tz_convert(None).dt.normalize()
    if keep == "max_volume":
        frame = frame.sort_values(["symbol", "date", "v"])
    else:
        frame["_order"] = np.arange(len(frame))
        frame = frame.sort_values(["symbol", "date", "_order"])
    frame = frame.drop_duplicates(["symbol", "date"], keep="last")
    return frame.drop(columns=[c for c in ("_order",) if c in frame])


def load_equity_daily(adjusted: bool = True) -> pd.DataFrame:
    name = "underlying_daily.csv" if adjusted else "underlying_daily_raw.csv"
    raw = pd.read_csv(ALPACA_DIR / name)
    return _dedupe_alpaca(raw, keep="max_volume")


def load_btc_daily() -> pd.DataFrame:
    raw = pd.read_csv(ALPACA_DIR / "crypto_daily.csv")
    frame = _dedupe_alpaca(raw, keep="last_pull")
    return frame.loc[frame["symbol"] == "BTC/USD"].sort_values("date")


STOCK_SNAPSHOT = OUTPUT_DIR / "stocks_yf_snapshot.csv"


def load_stock_snapshot() -> pd.DataFrame:
    """Offline copy of the core stocks' adjusted daily history (Yahoo, 2010 →).

    Saved once by the study so that the single-stock extension does not depend
    on a live Yahoo pull.  Columns: symbol, date, h, l, c, split.
    """
    frame = pd.read_csv(STOCK_SNAPSHOT, parse_dates=["date"])
    frame["v"] = 0.0
    return frame


def production_ohlc(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Shape one symbol like ``strategy.fetch_ohlc`` output.

    Production feeds high/low/close only (open is back-filled from close by
    run_simulation), so the open column is deliberately left out to keep the
    indicator set identical to the deployed model.  A ``split`` column, when
    present, feeds the post-split attention layer used for cash-mode stocks.
    """
    sub = frame.loc[frame["symbol"] == symbol].sort_values("date")
    out = pd.DataFrame(
        {
            "date": sub["date"].to_numpy(),
            "high": sub["h"].to_numpy(dtype=float),
            "low": sub["l"].to_numpy(dtype=float),
            "close": sub["c"].to_numpy(dtype=float),
            "stock_split": (
                sub["split"].fillna(0.0).to_numpy(dtype=float) if "split" in sub else 0.0
            ),
        }
    )
    out[["high", "low", "close"]] = out[["high", "low", "close"]].ffill()
    return out.reset_index(drop=True)


def inverse_pair_ohlc(long_symbol: str, short_symbol: str) -> pd.DataFrame:
    """Long-leg OHLC merged with the inverse leg close (``prepare_data`` shape)."""
    equity = load_equity_daily(adjusted=True)
    data = production_ohlc(equity, long_symbol)
    short = production_ohlc(equity, short_symbol)[["date", "close"]].rename(
        columns={"close": "close_short"}
    )
    data = pd.merge(data, short, on="date", how="left")
    data["close_short"] = data["close_short"].ffill()
    return data


def fetch_public_records(dataset: str, refresh: bool = False) -> list[dict]:
    """Download (once) the public dataset rows: the frozen live signal record."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cache = OUTPUT_DIR / f"public_{dataset}.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())
    import requests

    response = requests.get(
        f"{PUBLIC_BASE}/api/public/datasets/{dataset}", timeout=60
    )
    response.raise_for_status()
    records = response.json()["records"]
    cache.write_text(json.dumps(records))
    return records


def public_frame(dataset: str) -> pd.DataFrame:
    rows = fetch_public_records(dataset)
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.set_index("date").sort_index()
    frame["signal"] = (
        frame["prediction"]
        .astype(str)
        .str.replace(r"[^\w\s]", "", regex=True)
        .str.strip()
        .str.lower()
        .map(PRED_TO_SIGNAL)
        .fillna(0)
        .astype(int)
    )
    return frame


def write_signal_cache(dataset: str, cache_dir: Path) -> Path:
    """Materialize the published predictions as a strategy-engine cache CSV.

    ``run_simulation`` freezes any date present in this file (on/after the live
    start), so the reproduced history carries exactly the signals that were
    published live rather than a re-derived approximation.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    frame = public_frame(dataset)
    table = pd.DataFrame(
        {
            "Date(T)": frame.index.strftime("%Y-%m-%d"),
            "Prediction": frame["prediction"].to_numpy(),
            "Actual_Ret": frame["actual_ret"].to_numpy(),
            "Strategy_Ret": frame["strategy_ret"].to_numpy(),
        }
    )
    path = cache_dir / f"{dataset}.csv"
    table.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def reproduce_detailed_frame(
    dataset: str,
    ohlc: pd.DataFrame,
    short_mode: str,
    cache_dir: Path,
    live_signal_start: str = "2026-01-01",
    use_published_cache: bool = True,
) -> pd.DataFrame:
    """Run the deployed walk-forward signal engine on the archived prices."""
    from strategy import run_simulation  # noqa: WPS433 (model import)

    cache_dir.mkdir(parents=True, exist_ok=True)
    if use_published_cache:
        write_signal_cache(dataset, cache_dir)
    cache_csv = cache_dir / f"{dataset}.csv"
    if not use_published_cache and cache_csv.exists():
        cache_csv.unlink()
    _, detailed, _, _ = run_simulation(
        ohlc,
        str(cache_csv),
        short_mode,
        rotation_series=None,
        live_signal_start=live_signal_start,
        dataset=dataset,
    )
    return detailed
