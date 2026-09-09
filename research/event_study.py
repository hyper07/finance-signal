"""News-shock event study for the seven-session historical-analog forecast.

For every origin t the deployed ``build_forecast`` is called on the frame
truncated at t (no look-ahead) and the seven-horizon distribution is scored
against the realized path.  Shock days are defined mechanically before any
scoring:

  z-shock   : |r_T| / sigma_20(T-1) >= Z_SHOCK   (trailing vol known at T-1)
  news spike: crypto-tagged Benzinga headline count on T at least
              NEWS_RATIO x the trailing 30-day median (coverage from 2024-02)
  3d episode: |close_T / close_{T-3} - 1| >= BIG3_PCT

Outputs per dataset (research/output):
  forecasts_<key>.csv   one row per (origin, horizon) with forecast + realized
  origins_<key>.csv     one row per origin (consensus, flags, next-day target)
  events_<key>.csv      one row per shock day with pre-event forecast scores,
                        post-shock continuation returns and adaptation latency
  summary_<key>.json    aggregate statistics and tests
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ALPACA_DIR, OUTPUT_DIR  # noqa: E402
from forecast import build_forecast  # noqa: E402  (model/ on sys.path via common)

Z_SHOCK = 2.5
NEWS_RATIO = 2.0
BIG3_PCT = 10.0
HORIZONS = range(1, 8)
CRYPTO_SYMBOLS = {"BTCUSD", "BTC", "BITO", "IBIT", "BITI", "MSTR", "COIN"}
CRYPTO_WORDS = re.compile(r"bitcoin|crypto|btc|stablecoin|digital asset")
NEWS_COVERAGE_START = pd.Timestamp("2024-02-01")
NORMAL_P10_P90_WIDTH = 2.5631  # sigma units spanned by the 10-90 band

DATASETS = {
    "bito": dict(pickle="detailed_b04_prediction_us_coin.pkl", dataset="b04_prediction_us_coin", symbol="BITO",
                 short_mode="inverse_etf", news="crypto", asset_type="crypto",
                 label="BITO / BITI (deployed b04 dataset, published 2026 signals frozen)"),
    "btc": dict(pickle="detailed_btc_spot.pkl", dataset="crypto_btc_spot", symbol="BTC-USD",
                short_mode="cash", news="crypto", asset_type="crypto",
                label="BTC/USD spot (Alpaca, 24/7 calendar days)"),
    "spxl": dict(pickle="detailed_b01_prediction_us_snp.pkl", dataset="b01_prediction_us_snp", symbol="SPXL",
                 short_mode="inverse_etf", news="index", asset_type="index",
                 label="SPXL / SPXS (deployed b01 dataset, published 2026 signals frozen)"),
    "spy": dict(pickle="detailed_spy_spot.pkl", dataset="index_spy_spot", symbol="SPY",
                short_mode="cash", news="index", asset_type="index",
                label="SPY spot (S&P 500 ETF, cash mode)"),
    "aapl": dict(pickle="detailed_s01_prediction_us_aapl.pkl", dataset="s01_prediction_us_aapl", symbol="AAPL",
                 short_mode="cash", news="stock:AAPL", asset_type="stock",
                 label="AAPL (deployed s01 dataset, live signals frozen from 2026-07-30)"),
    "msft": dict(pickle="detailed_s02_prediction_us_msft.pkl", dataset="s02_prediction_us_msft", symbol="MSFT",
                 short_mode="cash", news="stock:MSFT", asset_type="stock",
                 label="MSFT (deployed s02 dataset)"),
    "tsla": dict(pickle="detailed_s03_prediction_us_tsla.pkl", dataset="s03_prediction_us_tsla", symbol="TSLA",
                 short_mode="cash", news="stock:TSLA", asset_type="stock",
                 label="TSLA (deployed s03 dataset)"),
    "nvda": dict(pickle="detailed_s04_prediction_us_nvda.pkl", dataset="s04_prediction_us_nvda", symbol="NVDA",
                 short_mode="cash", news="stock:NVDA", asset_type="stock",
                 label="NVDA (deployed s04 dataset)"),
    "bito_unfrozen": dict(pickle="detailed_b04_unfrozen.pkl", dataset="b04_prediction_us_coin", symbol="BITO",
                          short_mode="inverse_etf", news="crypto", asset_type="crypto",
                          label="BITO / BITI, unfrozen engine (robustness: no published signals used)"),
    "spxl_unfrozen": dict(pickle="detailed_b01_unfrozen.pkl", dataset="b01_prediction_us_snp", symbol="SPXL",
                          short_mode="inverse_etf", news="index", asset_type="index",
                          label="SPXL / SPXS, unfrozen engine (robustness)"),
}

INDEX_SYMBOLS = {"SPY", "QQQ", "DIA", "IWM", "VOO"}
MACRO_WORDS = re.compile(
    r"\bfed\b|fomc|powell|rate (hike|cut)|interest rate|\bcpi\b|inflation|jobs report|payroll|tariff|recession|treasury yield|\bgdp\b"
)


# --------------------------------------------------------------------------- #
# News intensity
# --------------------------------------------------------------------------- #
def news_counts(profile: str) -> pd.Series:
    """Daily headline counts for one asset type.

    crypto        crypto-tagged symbols or crypto words
    index         broad-market ETF tags or macro words (Fed, CPI, tariffs, ...)
    stock:TICKER  items tagged with that ticker
    """
    ticker = profile.split(":", 1)[1] if profile.startswith("stock:") else None
    counts: dict[str, int] = {}
    with open(ALPACA_DIR / "news.jsonl") as handle:
        for line in handle:
            item = json.loads(line)
            symbols = set(item.get("symbols", []))
            text = f"{item.get('headline', '')} {item.get('summary', '')}".lower()
            if profile == "crypto":
                hit = bool(symbols & CRYPTO_SYMBOLS) or bool(CRYPTO_WORDS.search(text))
            elif profile == "index":
                hit = bool(symbols & INDEX_SYMBOLS) or bool(MACRO_WORDS.search(text))
            else:
                hit = ticker in symbols
            if hit:
                day = item["created_at"][:10]
                counts[day] = counts.get(day, 0) + 1
    series = pd.Series(counts, dtype=float)
    series.index = pd.to_datetime(series.index)
    return series.sort_index()


def crypto_news_counts() -> pd.Series:
    return news_counts("crypto")


def align_news(counts: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    """Attribute every headline to the first index date on/after it.

    On a trading-day index this rolls weekend/holiday headlines into the next
    session, which is when their price impact can first be printed.
    """
    full = counts.reindex(
        pd.date_range(min(counts.index.min(), index.min()), index.max(), freq="D")
    ).fillna(0.0)
    positions = np.searchsorted(index.to_numpy(), full.index.to_numpy(), side="left")
    keep = positions < len(index)
    aligned = pd.Series(0.0, index=index)
    np.add.at(aligned.to_numpy(), positions[keep], full.to_numpy()[keep])
    return aligned


# --------------------------------------------------------------------------- #
# Rolling-origin forecasts
# --------------------------------------------------------------------------- #
def rolling_forecasts(frame: pd.DataFrame, spec: dict, min_history: int = 60):
    close = frame["close"].to_numpy(dtype=float)
    n = len(frame)
    rows: list[dict] = []
    origins: list[dict] = []
    for pos in range(min_history - 1, n - 1):
        observed = frame.iloc[: pos + 1]
        payload = build_forecast(
            observed, spec["dataset"], spec["symbol"], spec["short_mode"],
            as_of_date=observed.index[-1],
        )
        origin = frame.index[pos]
        consensus = payload["consensus"]
        origins.append(
            {
                "origin": origin,
                "pos": pos,
                "close": close[pos],
                "strategy_signal": int(frame["strategy_signal"].iloc[pos]),
                "consensus_direction": consensus["direction"],
                "consensus_status": consensus["status"],
                "consensus_votes_buy": consensus["vote_counts"]["Buy"],
                "consensus_votes_sell": consensus["vote_counts"]["Sell"],
                "consensus_target_pct": consensus["target_tactical_pct"],
                "current_tactical_pct": consensus["current_tactical_pct"],
                "next_target_pct": payload["rows"][0]["target_tactical_pct"],
                "trailing_vol_annual": payload["trailing_volatility"],
                "fallback": bool(payload["validation"]["fallback_horizons"]),
            }
        )
        for row in payload["rows"]:
            h = int(row["horizon"])
            if pos + h >= n:
                realized = np.nan
                session = np.nan
            else:
                realized = close[pos + h] / close[pos] - 1.0
                session = close[pos + h] / close[pos + h - 1] - 1.0
            rows.append(
                {
                    "origin": origin,
                    "pos": pos,
                    "horizon": h,
                    "target_pos": pos + h,
                    "prob_up": row["prob_up"],
                    "p10": row["p10_return_pct"] / 100.0,
                    "p50": row["p50_return_pct"] / 100.0,
                    "p90": row["p90_return_pct"] / 100.0,
                    "session_p50": row["session_p50_return_pct"] / 100.0,
                    "session_prob_up": row["session_prob_up"],
                    "vote": row["consensus_vote"],
                    "target_pct": row["target_tactical_pct"],
                    "realized": realized,
                    "session_realized": session,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(origins)


# --------------------------------------------------------------------------- #
# Scoring helpers
# --------------------------------------------------------------------------- #
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (centre - half, centre + half)


def hit_summary(hits: pd.Series) -> dict:
    hits = hits.dropna().astype(int)
    n = int(len(hits))
    k = int(hits.sum())
    if n == 0:
        return {"n": 0}
    low, high = wilson(k, n)
    p_value = float(stats.binomtest(k, n, 0.5).pvalue)
    return {
        "n": n,
        "hit_rate": round(k / n, 4),
        "wilson95": [round(low, 4), round(high, 4)],
        "binomial_p_vs_0.5": round(p_value, 6),
    }


def _moving_block_indices(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """Sample circular moving blocks while preserving local row order."""
    if n < 1:
        raise ValueError("cannot resample an empty array")
    width = min(max(int(block), 1), n)
    starts = rng.integers(0, n, int(np.ceil(n / width)))
    return ((starts[:, None] + np.arange(width)[None, :]) % n).ravel()[:n]


def _bootstrap_result(observed: float, estimates: list[float],
                      null_estimates: list[float], method: str) -> dict:
    boot = np.asarray(estimates, dtype=float)
    null = np.asarray(null_estimates, dtype=float)
    if len(boot) == 0 or len(null) == 0:
        raise ValueError("bootstrap produced no valid resamples")
    p_value = (np.count_nonzero(np.abs(null) >= abs(observed) - 1e-15) + 1) / (len(null) + 1)
    return {
        "difference": round(float(observed), 4),
        "ci95": [
            round(float(np.quantile(boot, 0.025)), 4),
            round(float(np.quantile(boot, 0.975)), 4),
        ],
        "p_two_sided": round(float(min(p_value, 1.0)), 6),
        "method": method,
    }


def block_bootstrap_diff(a: np.ndarray, b: np.ndarray, block: int = 7,
                         draws: int = 4000, seed: int = 11,
                         paired: bool = False) -> dict:
    """Moving-block CI and null-centered test for ``mean(a) - mean(b)``.

    Set ``paired=True`` when both losses were evaluated on the same forecasts.
    Common block indices are then sampled from the paired difference. For
    independent samples, each ordered series is resampled separately.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if paired:
        if len(a) != len(b):
            raise ValueError("paired samples must have equal lengths")
        valid = np.isfinite(a) & np.isfinite(b)
        diff = a[valid] - b[valid]
        if len(diff) == 0:
            raise ValueError("paired samples contain no finite observations")
        observed = float(diff.mean())
        centred = diff - observed
        rng = np.random.default_rng(seed)
        indices = [_moving_block_indices(len(diff), block, rng) for _ in range(draws)]
        estimates = [float(diff[idx].mean()) for idx in indices]
        null_estimates = [float(centred[idx].mean()) for idx in indices]
        return _bootstrap_result(
            observed, estimates, null_estimates,
            f"paired circular moving-block bootstrap (block={min(block, len(diff))})",
        )

    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) == 0 or len(b) == 0:
        raise ValueError("samples must each contain a finite observation")
    observed = float(a.mean() - b.mean())
    centred_a = a - a.mean()
    centred_b = b - b.mean()
    rng = np.random.default_rng(seed)
    estimates: list[float] = []
    null_estimates: list[float] = []
    for _ in range(draws):
        ia = _moving_block_indices(len(a), block, rng)
        ib = _moving_block_indices(len(b), block, rng)
        estimates.append(float(a[ia].mean() - b[ib].mean()))
        null_estimates.append(float(centred_a[ia].mean() - centred_b[ib].mean()))
    return _bootstrap_result(
        observed, estimates, null_estimates,
        f"independent circular moving-block bootstrap (block={block})",
    )


def block_bootstrap_group_diff(values: np.ndarray, group: np.ndarray, block: int = 7,
                               draws: int = 4000, seed: int = 11) -> dict:
    """Bootstrap a conditional-mean difference without discarding time order.

    ``group=True`` identifies the event observations. Blocks are sampled from
    the complete ordered sequence so clustered events and adjacent quiet
    observations remain together.
    """
    values = np.asarray(values, dtype=float)
    group = np.asarray(group, dtype=bool)
    if len(values) != len(group):
        raise ValueError("values and group must have equal lengths")
    valid = np.isfinite(values)
    values = values[valid]
    group = group[valid]
    if not group.any() or group.all():
        raise ValueError("both event and comparison observations are required")
    event_mean = float(values[group].mean())
    comparison_mean = float(values[~group].mean())
    observed = event_mean - comparison_mean
    pooled_mean = float(values.mean())
    centred = values.copy()
    centred[group] -= event_mean - pooled_mean
    centred[~group] -= comparison_mean - pooled_mean

    rng = np.random.default_rng(seed)
    estimates: list[float] = []
    null_estimates: list[float] = []
    event_estimates: list[float] = []
    comparison_estimates: list[float] = []
    attempts = 0
    while len(estimates) < draws and attempts < draws * 10:
        attempts += 1
        idx = _moving_block_indices(len(values), block, rng)
        sampled_group = group[idx]
        if not sampled_group.any() or sampled_group.all():
            continue
        sampled_event_mean = float(values[idx][sampled_group].mean())
        sampled_comparison_mean = float(values[idx][~sampled_group].mean())
        event_estimates.append(sampled_event_mean)
        comparison_estimates.append(sampled_comparison_mean)
        estimates.append(sampled_event_mean - sampled_comparison_mean)
        null_estimates.append(float(centred[idx][sampled_group].mean()
                                    - centred[idx][~sampled_group].mean()))
    result = _bootstrap_result(
        observed, estimates, null_estimates,
        f"group-preserving circular moving-block bootstrap (block={block})",
    )
    result["n_event"] = int(group.sum())
    result["n_comparison"] = int((~group).sum())
    result["event_mean"] = round(event_mean, 4)
    result["event_mean_ci95"] = [
        round(float(np.quantile(event_estimates, 0.025)), 4),
        round(float(np.quantile(event_estimates, 0.975)), 4),
    ]
    result["comparison_mean"] = round(comparison_mean, 4)
    result["comparison_mean_ci95"] = [
        round(float(np.quantile(comparison_estimates, 0.025)), 4),
        round(float(np.quantile(comparison_estimates, 0.975)), 4),
    ]
    return result


def block_bootstrap_mean(values: np.ndarray, block: int = 7, draws: int = 4000,
                         seed: int = 11, null: float | None = None) -> dict:
    """Moving-block interval for an ordered mean, with an optional null test."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        raise ValueError("values must contain a finite observation")
    observed = float(values.mean())
    centred = values - observed + (observed if null is None else null)
    rng = np.random.default_rng(seed)
    indices = [_moving_block_indices(len(values), block, rng) for _ in range(draws)]
    estimates = np.asarray([values[idx].mean() for idx in indices], dtype=float)
    out = {
        "n": int(len(values)),
        "mean": round(observed, 4),
        "ci95": [
            round(float(np.quantile(estimates, 0.025)), 4),
            round(float(np.quantile(estimates, 0.975)), 4),
        ],
        "method": f"circular moving-block bootstrap (block={min(block, len(values))})",
    }
    if null is not None:
        null_estimates = np.asarray([centred[idx].mean() for idx in indices], dtype=float)
        p_value = (
            np.count_nonzero(np.abs(null_estimates - null)
                             >= abs(observed - null) - 1e-15) + 1
        ) / (len(null_estimates) + 1)
        out["null"] = null
        out["p_two_sided"] = round(float(min(p_value, 1.0)), 6)
    return out


def score_table(fc: pd.DataFrame) -> pd.DataFrame:
    fc = fc.dropna(subset=["realized"]).copy()
    fc["actual_up"] = (fc["realized"] > 0).astype(int)
    fc["pred_up"] = (fc["prob_up"] >= 0.5).astype(int)
    fc["hit"] = (fc["pred_up"] == fc["actual_up"]).astype(int)
    fc["brier"] = (fc["prob_up"] - fc["actual_up"]) ** 2
    fc["covered"] = ((fc["realized"] >= fc["p10"]) & (fc["realized"] <= fc["p90"])).astype(int)
    width = (fc["p90"] - fc["p10"]).replace(0.0, np.nan)
    fc["surprise_z"] = (fc["realized"] - fc["p50"]) / (width / NORMAL_P10_P90_WIDTH)
    fc["session_up"] = (fc["session_realized"] > 0).astype(int)
    fc["session_hit"] = ((fc["session_prob_up"] >= 0.5).astype(int) == fc["session_up"]).astype(int)
    vote_dir = fc["vote"].map({"Buy": 1, "Sell": 0})
    fc["vote_hit"] = np.where(vote_dir.notna(), (vote_dir == fc["session_up"]).astype(float), np.nan)
    fc["always_up_hit"] = fc["actual_up"]
    return fc


# --------------------------------------------------------------------------- #
# Main analysis per dataset
# --------------------------------------------------------------------------- #
def analyse(key: str, spec: dict, counts: pd.Series) -> dict:
    frame = pd.read_pickle(OUTPUT_DIR / spec["pickle"])
    frame = frame.loc[:, ["close", "strategy_signal", "rotation_score", "daily_ret"]].copy()
    frame.index = pd.to_datetime(frame.index).normalize()
    close = frame["close"]
    ret = close.pct_change()
    vol20 = ret.rolling(20).std(ddof=0).shift(1)
    z = ret / vol20
    news = align_news(counts, frame.index)
    news_base = news.rolling(30, min_periods=10).median().shift(1)
    news_ratio = (news + 1.0) / (news_base + 1.0)
    news_ratio[frame.index < NEWS_COVERAGE_START] = np.nan
    move3 = (close / close.shift(3) - 1.0) * 100.0

    day = pd.DataFrame(
        {
            "close": close, "ret": ret, "z": z, "news": news, "news_ratio": news_ratio,
            "move3_pct": move3,
            "shock_z": z.abs() >= Z_SHOCK,
            "news_spike": news_ratio >= NEWS_RATIO,
            "big3": move3.abs() >= BIG3_PCT,
            "strategy_signal": frame["strategy_signal"],
        }
    )
    day["shock_any"] = day["shock_z"] | day["big3"]
    day["pos"] = np.arange(len(day))

    print(f"[{key}] rolling forecasts over {len(frame)} rows ...")
    fc, origins = rolling_forecasts(frame, spec)
    fc = score_table(fc)
    # target-day attributes
    tgt = day.iloc[fc["target_pos"].to_numpy()]
    for column in ("z", "news", "news_ratio", "shock_z", "news_spike", "big3", "shock_any"):
        fc[f"target_{column}"] = tgt[column].to_numpy()
    fc["target_date"] = tgt.index.to_numpy()
    fc["target_abs_z"] = fc["target_z"].abs()
    # window-level: does any session in (t, t+h] contain a z-shock?
    shock_pos = np.flatnonzero(day["shock_z"].to_numpy())
    fc["window_has_shock"] = [
        bool(((shock_pos > p) & (shock_pos <= p + h)).any())
        for p, h in zip(fc["pos"], fc["horizon"])
    ]
    origins = origins.set_index("origin")
    origins["next_shock_z"] = day["shock_z"].shift(-1).reindex(origins.index).fillna(False).astype(bool)
    origins["window7_has_shock"] = [
        bool(((shock_pos > p) & (shock_pos <= p + 7)).any()) for p in origins["pos"]
    ]

    fc.to_csv(OUTPUT_DIR / f"forecasts_{key}.csv", index=False)
    origins.to_csv(OUTPUT_DIR / f"origins_{key}.csv")
    day.to_csv(OUTPUT_DIR / f"days_{key}.csv")

    summary: dict = {"dataset": spec["label"], "asset_type": spec["asset_type"], "news_profile": spec["news"],
                     "rows": int(len(frame)),
                     "origins": int(len(origins)),
                     "first_origin": str(origins.index.min().date()),
                     "last_origin": str(origins.index.max().date()),
                     "rules": {"z_shock": Z_SHOCK, "news_ratio": NEWS_RATIO, "big3_pct": BIG3_PCT}}

    # ---- 1. unconditional calibration by horizon (whole sample and 2026) ----
    def by_horizon(sub: pd.DataFrame) -> list[dict]:
        out = []
        for h, g in sub.groupby("horizon"):
            hs = hit_summary(g["hit"])
            out.append(
                {
                    "horizon": int(h), **hs,
                    "always_up_rate": round(float(g["actual_up"].mean()), 4),
                    "brier": round(float(g["brier"].mean()), 4),
                    "p10_p90_coverage": round(float(g["covered"].mean()), 4),
                    "session_hit_rate": round(float(g["session_hit"].mean()), 4),
                    "vote_hit_rate": (round(float(g["vote_hit"].mean()), 4)
                                      if g["vote_hit"].notna().any() else None),
                    "vote_count": int(g["vote_hit"].notna().sum()),
                    "mean_abs_surprise_z": round(float(g["surprise_z"].abs().mean()), 4),
                }
            )
        return out

    summary["calibration_all"] = by_horizon(fc)
    summary["calibration_2026"] = by_horizon(fc[fc["origin"] >= "2026-01-01"])
    summary["calibration_since_news_coverage"] = by_horizon(fc[fc["origin"] >= NEWS_COVERAGE_START])

    # ---- 2. shock windows vs calm windows ----
    shock_w = fc[fc["window_has_shock"]]
    calm_w = fc[~fc["window_has_shock"]]
    summary["window_split"] = {
        "shock_windows": {"n": int(len(shock_w)), **{k: v for k, v in hit_summary(shock_w["hit"]).items() if k != "n"},
                          "coverage": round(float(shock_w["covered"].mean()), 4),
                          "brier": round(float(shock_w["brier"].mean()), 4),
                          "mean_abs_surprise_z": round(float(shock_w["surprise_z"].abs().mean()), 4)},
        "calm_windows": {"n": int(len(calm_w)), **{k: v for k, v in hit_summary(calm_w["hit"]).items() if k != "n"},
                         "coverage": round(float(calm_w["covered"].mean()), 4),
                         "brier": round(float(calm_w["brier"].mean()), 4),
                         "mean_abs_surprise_z": round(float(calm_w["surprise_z"].abs().mean()), 4)},
        "hit_rate_difference_shock_minus_calm": block_bootstrap_group_diff(
            fc["hit"].to_numpy(float), fc["window_has_shock"].to_numpy(bool),
            block=49,
        ),
        "coverage_difference_shock_minus_calm": block_bootstrap_group_diff(
            fc["covered"].to_numpy(float), fc["window_has_shock"].to_numpy(bool),
            block=49,
        ),
    }

    # ---- 3. target-day |z| bins and news-intensity bins (h=1 session view) ----
    h1 = fc[fc["horizon"] == 1].copy()
    z_bins = pd.cut(h1["target_abs_z"], [0, 0.5, 1.0, 1.5, 2.5, np.inf],
                    labels=["0-0.5", "0.5-1", "1-1.5", "1.5-2.5", ">=2.5"], include_lowest=True)
    summary["h1_hit_by_target_abs_z"] = [
        {"bin": str(b), **hit_summary(g["hit"]), "coverage": round(float(g["covered"].mean()), 4)}
        for b, g in h1.groupby(z_bins, observed=True)
    ]
    covered_news = h1.dropna(subset=["target_news_ratio"])
    n_bins = pd.cut(covered_news["target_news_ratio"], [0, 0.75, 1.25, 2.0, np.inf],
                    labels=["<0.75", "0.75-1.25", "1.25-2", ">=2"], include_lowest=True)
    summary["h1_hit_by_target_news_ratio"] = [
        {"bin": str(b), **hit_summary(g["hit"]), "coverage": round(float(g["covered"].mean()), 4),
         "mean_abs_ret_pct": round(float((g["realized"].abs() * 100).mean()), 3)}
        for b, g in covered_news.groupby(n_bins, observed=True)
    ]
    if len(covered_news) > 30:
        rho, p = stats.spearmanr(covered_news["target_news_ratio"], covered_news["hit"])
        rho_c, p_c = stats.spearmanr(covered_news["target_news_ratio"], covered_news["covered"])
        rho_s, p_s = stats.spearmanr(covered_news["target_news_ratio"], covered_news["surprise_z"].abs())
        summary["h1_news_intensity_correlations"] = {
            "spearman_news_ratio_vs_hit": [round(float(rho), 4), round(float(p), 4)],
            "spearman_news_ratio_vs_covered": [round(float(rho_c), 4), round(float(p_c), 4)],
            "spearman_news_ratio_vs_abs_surprise": [round(float(rho_s), 4), round(float(p_s), 4)],
        }

    # ---- 4. per-event table: forecast made at T-1, path after T ----
    events = []
    shock_days = day[day["shock_z"] & (day["pos"] >= origins["pos"].min() + 1)]
    closes = close.to_numpy(float)
    sig = frame["strategy_signal"].to_numpy(int)
    cons_dir = origins["consensus_direction"]
    for date, drow in shock_days.iterrows():
        T = int(drow["pos"])
        direction = int(np.sign(drow["ret"]))
        pre = fc[fc["pos"] == T - 1]
        if pre.empty:
            continue
        pre = pre.set_index("horizon")
        o = origins.iloc[T - 1 - origins["pos"].min()] if (T - 1) in set(origins["pos"]) else None
        h1r = pre.loc[1]
        rec = {
            "event_date": date.date().isoformat(),
            "ret_pct": round(drow["ret"] * 100, 3),
            "z": round(float(drow["z"]), 2),
            "direction": "up" if direction > 0 else "down",
            "news_count": float(drow["news"]),
            "news_ratio": (round(float(drow["news_ratio"]), 2) if pd.notna(drow["news_ratio"]) else None),
            "news_spike": bool(drow["news_spike"]) if pd.notna(drow["news_ratio"]) else None,
            "move3_pct": round(float(drow["move3_pct"]), 2),
            "pre_signal_3day": int(sig[T - 1]),
            "pre_consensus": None if o is None else o["consensus_direction"],
            "pre_consensus_status": None if o is None else o["consensus_status"],
            "pre_next_target_pct": None if o is None else float(o["next_target_pct"]),
            "pre_h1_prob_up": round(float(h1r["prob_up"]), 3),
            "pre_h1_p10_pct": round(float(h1r["p10"] * 100), 3),
            "pre_h1_p50_pct": round(float(h1r["p50"] * 100), 3),
            "pre_h1_p90_pct": round(float(h1r["p90"] * 100), 3),
            "pre_h1_hit": int(h1r["hit"]),
            "pre_h1_covered": int(h1r["covered"]),
            "pre_h1_surprise_z": round(float(h1r["surprise_z"]), 2),
            "pre_h3_hit": int(pre.loc[3, "hit"]) if 3 in pre.index else None,
            "pre_h7_hit": int(pre.loc[7, "hit"]) if 7 in pre.index else None,
            "pre_path_coverage_1to7": round(float(pre["covered"].mean()), 3),
            "pre_path_hits_1to7": int(pre["hit"].sum()),
        }
        # post-shock continuation: buy/sell at the close of T in the shock direction
        for k in (1, 2, 3, 5, 7):
            if T + k < len(closes):
                rec[f"post_ret_{k}d_pct"] = round((closes[T + k] / closes[T] - 1) * 100, 3)
                rec[f"continuation_{k}d_pct"] = round(direction * (closes[T + k] / closes[T] - 1) * 100, 3)
            else:
                rec[f"post_ret_{k}d_pct"] = None
                rec[f"continuation_{k}d_pct"] = None
        # adaptation latency of the 3-day signal and 7-day consensus
        want = 1 if direction > 0 else -1
        want_dir = "Buy" if direction > 0 else "Sell"
        lat_sig = None
        if sig[T - 1] != want:
            for j in range(T, min(T + 15, len(sig))):
                if sig[j] == want:
                    lat_sig = j - T
                    break
        lat_cons = None
        if o is not None and o["consensus_direction"] != want_dir:
            for j in range(T, min(T + 15, len(sig))):
                if j in origins["pos"].values and cons_dir.iloc[j - origins["pos"].min()] == want_dir:
                    lat_cons = j - T
                    break
        rec["signal_already_aligned"] = bool(sig[T - 1] == want)
        rec["signal_latency_sessions"] = lat_sig
        rec["consensus_already_aligned"] = bool(o is not None and o["consensus_direction"] == want_dir)
        rec["consensus_latency_sessions"] = lat_cons
        events.append(rec)
    events_df = pd.DataFrame(events)
    events_df.to_csv(OUTPUT_DIR / f"events_{key}.csv", index=False)

    pre_h1 = events_df["pre_h1_hit"]
    summary["events"] = {
        "count": int(len(events_df)),
        "up": int((events_df["direction"] == "up").sum()),
        "down": int((events_df["direction"] == "down").sum()),
        "pre_event_h1_direction": hit_summary(pre_h1),
        "pre_event_h1_coverage": round(float(events_df["pre_h1_covered"].mean()), 4),
        "pre_event_mean_abs_surprise_z": round(float(events_df["pre_h1_surprise_z"].abs().mean()), 3),
        "pre_event_path_coverage_1to7": round(float(events_df["pre_path_coverage_1to7"].mean()), 4),
        "pre_event_path_hits_1to7_mean": round(float(events_df["pre_path_hits_1to7"].mean()), 3),
        "signal_aligned_before_shock": round(float(events_df["signal_already_aligned"].mean()), 4),
        "consensus_aligned_before_shock": round(float(events_df["consensus_already_aligned"].mean()), 4),
        "signal_latency_sessions_median": (float(events_df["signal_latency_sessions"].dropna().median())
                                           if events_df["signal_latency_sessions"].notna().any() else None),
        "signal_never_aligned_within_15": int(events_df["signal_latency_sessions"].isna().sum()
                                              - events_df["signal_already_aligned"].sum()),
        "consensus_latency_sessions_median": (float(events_df["consensus_latency_sessions"].dropna().median())
                                              if events_df["consensus_latency_sessions"].notna().any() else None),
    }
    cont = {}
    for k in (1, 2, 3, 5, 7):
        col = events_df[f"continuation_{k}d_pct"].dropna()
        if len(col) >= 5:
            t, p = stats.ttest_1samp(col, 0.0)
            cont[f"{k}d"] = {"n": int(len(col)), "mean_pct": round(float(col.mean()), 3),
                             "median_pct": round(float(col.median()), 3),
                             "share_positive": round(float((col > 0).mean()), 3),
                             "t_stat": round(float(t), 2), "p_value": round(float(p), 4)}
    summary["post_shock_continuation_sign_adjusted"] = cont
    for label, mask in (("up", events_df["direction"] == "up"), ("down", events_df["direction"] == "down")):
        sub = events_df[mask]
        summary[f"post_shock_raw_{label}"] = {
            f"{k}d": {"n": int(sub[f'post_ret_{k}d_pct'].notna().sum()),
                      "mean_pct": round(float(sub[f"post_ret_{k}d_pct"].mean()), 3)}
            for k in (1, 3, 5, 7) if sub[f"post_ret_{k}d_pct"].notna().any()
        }

    # ---- 5. the August 2026 event in detail ----
    focus_dates = pd.to_datetime(["2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-24"])
    focus = []
    for d in focus_dates:
        if d not in origins.index:
            continue
        sub = fc[fc["origin"] == d].sort_values("horizon")
        o = origins.loc[d]
        focus.append(
            {
                "as_of": d.date().isoformat(),
                "close": round(float(o["close"]), 4),
                "signal_3day": int(o["strategy_signal"]),
                "consensus": f"{o['consensus_direction']}/{o['consensus_status']}",
                "votes_buy_sell": [int(o["consensus_votes_buy"]), int(o["consensus_votes_sell"])],
                "next_target_pct": float(o["next_target_pct"]),
                "rows": [
                    {
                        "h": int(r.horizon),
                        "target_date": pd.Timestamp(r.target_date).date().isoformat(),
                        "prob_up": round(float(r.prob_up), 3),
                        "p10_pct": round(float(r.p10 * 100), 2),
                        "p50_pct": round(float(r.p50 * 100), 2),
                        "p90_pct": round(float(r.p90 * 100), 2),
                        "realized_pct": round(float(r.realized * 100), 2) if pd.notna(r.realized) else None,
                        "covered": (int(r.covered) if pd.notna(r.realized) else None),
                        "hit": (int(r.hit) if pd.notna(r.realized) else None),
                        "surprise_z": (round(float(r.surprise_z), 2) if pd.notna(r.realized) else None),
                        "vote": r.vote,
                    }
                    for r in sub.itertuples()
                ],
            }
        )
    summary["august_2026_event"] = focus
    aug = events_df[events_df["event_date"].between("2026-08-15", "2026-08-25")]
    summary["august_2026_event_rows"] = aug.to_dict(orient="records")

    (OUTPUT_DIR / f"summary_{key}.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    keys = sys.argv[1:] or list(DATASETS)
    cache: dict[str, pd.Series] = {}
    for key in keys:
        profile = DATASETS[key]["news"]
        if profile not in cache:
            cache[profile] = news_counts(profile)
        summary = analyse(key, DATASETS[key], cache[profile])
        print(f"\n===== {key}: {summary['dataset']} =====")
        print("origins:", summary["origins"], summary["first_origin"], "->", summary["last_origin"])
        print("calibration (all):")
        for row in summary["calibration_all"]:
            print(f"  h={row['horizon']} hit={row['hit_rate']:.3f} CI={row['wilson95']} always_up={row['always_up_rate']:.3f} "
                  f"brier={row['brier']:.3f} cov={row['p10_p90_coverage']:.3f} session_hit={row['session_hit_rate']:.3f} "
                  f"vote_hit={row['vote_hit_rate']} (n_votes={row['vote_count']})")
        print("calibration (2026):")
        for row in summary["calibration_2026"]:
            print(f"  h={row['horizon']} hit={row['hit_rate']:.3f} CI={row['wilson95']} always_up={row['always_up_rate']:.3f} cov={row['p10_p90_coverage']:.3f}")
        print("window split:", json.dumps(summary["window_split"], indent=1))
        print("h1 by |z| bin:", json.dumps(summary["h1_hit_by_target_abs_z"]))
        print("h1 by news ratio:", json.dumps(summary["h1_hit_by_target_news_ratio"]))
        print("news correlations:", summary.get("h1_news_intensity_correlations"))
        print("events:", json.dumps(summary["events"], indent=1))
        print("continuation:", json.dumps(summary["post_shock_continuation_sign_adjusted"], indent=1))
        print("raw up:", summary["post_shock_raw_up"]); print("raw down:", summary["post_shock_raw_down"])
        print("AUGUST 2026:")
        for f in summary["august_2026_event"]:
            print(f" as_of {f['as_of']} close={f['close']} sig={f['signal_3day']} cons={f['consensus']} votes={f['votes_buy_sell']} next_target={f['next_target_pct']}")
            for r in f["rows"]:
                print(f"    h{r['h']} {r['target_date']} p_up={r['prob_up']:.2f} band=[{r['p10_pct']:+.2f},{r['p50_pct']:+.2f},{r['p90_pct']:+.2f}]% real={r['realized_pct']} cov={r['covered']} hit={r['hit']} z={r['surprise_z']} vote={r['vote']}")


if __name__ == "__main__":
    main()
