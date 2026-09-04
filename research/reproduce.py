"""Rebuild the deployed model's detailed frames offline and check fidelity.

Jobs (research/output/detailed_<name>.pkl):
  b04_prediction_us_coin   BITO/BITI, published 2026 signals frozen (+ unfrozen twin)
  btc_spot                 BTC/USD spot, cash mode, walk-forward
  b01_prediction_us_snp    SPXL/SPXS, published 2026 signals frozen (+ unfrozen twin)
  spy_spot                 SPY, cash mode, walk-forward
  s01..s04 (aapl, msft, tsla, nvda)  cash mode, published signals frozen from the
                           production stock live-start 2026-07-30 (+ unfrozen twin)
reproduction_fidelity.json  agreement of each unfrozen twin with the published record
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    OUTPUT_DIR,
    inverse_pair_ohlc,
    load_btc_daily,
    load_equity_daily,
    load_stock_snapshot,
    production_ohlc,
    public_frame,
    reproduce_detailed_frame,
)

CACHE_DIR = OUTPUT_DIR / "cache"
STOCK_LIVE_START = "2026-07-30"   # instruments.DEFAULT_STOCK_LIVE_START
ETF_LIVE_START = "2026-01-01"


def jobs() -> list[dict]:
    equity = load_equity_daily(adjusted=True)
    stocks = load_stock_snapshot()
    out = [
        dict(name="b04_prediction_us_coin", dataset="b04_prediction_us_coin", short_mode="inverse_etf",
             ohlc=inverse_pair_ohlc("BITO", "BITI"), cache=True, live=ETF_LIVE_START, unfrozen_name="b04_unfrozen"),
        dict(name="btc_spot", dataset="crypto_btc_spot", short_mode="cash",
             ohlc=production_ohlc(load_btc_daily(), "BTC/USD"), cache=False, live="2099-01-01"),
        dict(name="b01_prediction_us_snp", dataset="b01_prediction_us_snp", short_mode="inverse_etf",
             ohlc=inverse_pair_ohlc("SPXL", "SPXS"), cache=True, live=ETF_LIVE_START, unfrozen_name="b01_unfrozen"),
        dict(name="spy_spot", dataset="index_spy_spot", short_mode="cash",
             ohlc=production_ohlc(equity, "SPY"), cache=False, live="2099-01-01"),
    ]
    for i, ticker in enumerate(("AAPL", "MSFT", "TSLA", "NVDA"), start=1):
        dataset = f"s{i:02d}_prediction_us_{ticker.lower()}"
        out.append(dict(name=dataset, dataset=dataset, short_mode="cash",
                        ohlc=production_ohlc(stocks, ticker), cache=True, live=STOCK_LIVE_START,
                        unfrozen_name=f"{dataset}_unfrozen"))
    return out


def fidelity(dataset: str, unfrozen: pd.DataFrame, live_start: str) -> dict:
    published = public_frame(dataset)
    joined = published[["signal", "adjusted_close", "actual_ret"]].join(
        unfrozen[["strategy_signal", "close", "daily_ret"]], how="inner"
    )
    live = joined[joined.index >= live_start]
    agree = (joined["signal"] == joined["strategy_signal"]).mean()
    close_gap = (joined["close"] / joined["adjusted_close"] - 1.0).abs()
    by_month = (joined["signal"] == joined["strategy_signal"]).groupby(joined.index.to_period("M")).mean().round(3)
    return {
        "overlap_days": int(len(joined)),
        "signal_agreement": round(float(agree), 4),
        "signal_agreement_live_rows": (round(float((live["signal"] == live["strategy_signal"]).mean()), 4) if len(live) else None),
        "live_rows": int(len(live)),
        "signal_agreement_by_month": {str(k): float(v) for k, v in by_month.items()},
        "max_abs_close_gap_pct": round(float(close_gap.max() * 100.0), 4),
        "median_abs_close_gap_pct": round(float(close_gap.median() * 100.0), 4),
        "published_signal_counts": {int(k): int(v) for k, v in published["signal"].value_counts().items()},
        "unfrozen_signal_counts": {int(k): int(v) for k, v in joined["strategy_signal"].value_counts().items()},
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    wanted = set(sys.argv[1:])
    report: dict = {}
    for job in jobs():
        if wanted and job["name"] not in wanted:
            continue
        ohlc = job["ohlc"]
        print(f"[{job['name']}] rows={len(ohlc)} {ohlc['date'].min().date()} -> {ohlc['date'].max().date()}")
        frozen = reproduce_detailed_frame(job["dataset"], ohlc, job["short_mode"], CACHE_DIR / job["name"],
                                          live_signal_start=job["live"], use_published_cache=job["cache"])
        frozen.to_pickle(OUTPUT_DIR / f"detailed_{job['name']}.pkl")
        print(f"[{job['name']}] signal counts:", frozen["strategy_signal"].value_counts().to_dict())
        if job["cache"]:
            unfrozen = reproduce_detailed_frame(job["dataset"], ohlc, job["short_mode"], CACHE_DIR / f"{job['name']}_unfrozen",
                                                live_signal_start=job["live"], use_published_cache=False)
            unfrozen.to_pickle(OUTPUT_DIR / f"detailed_{job['unfrozen_name']}.pkl")
            report[job["dataset"]] = fidelity(job["dataset"], unfrozen, job["live"])
            print(f"[{job['name']}] fidelity:", {k: v for k, v in report[job['dataset']].items() if k != "signal_agreement_by_month"})
    path = OUTPUT_DIR / "reproduction_fidelity.json"
    existing = json.loads(path.read_text()) if path.exists() and wanted else {}
    if existing and "overlap_days" in existing:      # legacy single-dataset layout
        existing = {"b04_prediction_us_coin": existing}
    existing.update(report)
    path.write_text(json.dumps(existing, indent=2, default=int))


if __name__ == "__main__":
    main()
