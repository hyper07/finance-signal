"""Exogenous event test: headline-count spikes (independent of returns).

A news-spike day is any session where the crypto-tagged headline count is at
least NEWS_RATIO times its trailing 30-day median.  Unlike the |z| rule this
does not condition on the realized return, so the coverage result cannot be
tautological.  Also recomputes the dashboard's sampled evaluator (50 origins,
step 5) as it would have appeared on each day of 2026 to explain remembered
figures such as 'h=5 was 61-63%'.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR  # noqa: E402
from event_study import (  # noqa: E402
    NEWS_RATIO,
    block_bootstrap_group_diff,
    hit_summary,
)


def news_spike_events(fc: pd.DataFrame, day: pd.DataFrame) -> dict:
    h1 = fc[(fc["horizon"] == 1) & fc["target_news_ratio"].notna()].copy()
    is_spike = h1["target_news_ratio"].to_numpy(float) >= NEWS_RATIO
    spike = h1[is_spike]
    quiet = h1[~is_spike]
    out = {
        "rule": f"headline count >= {NEWS_RATIO} x trailing 30-day median (2024-02 onward)",
        "spike_days": int(len(spike)), "quiet_days": int(len(quiet)),
        "spike": {**hit_summary(spike["hit"]),
                  "coverage": round(float(spike["covered"].mean()), 4),
                  "brier": round(float(spike["brier"].mean()), 4),
                  "mean_abs_surprise_z": round(float(spike["surprise_z"].abs().mean()), 3),
                  "median_abs_surprise_z": round(float(spike["surprise_z"].abs().median()), 3),
                  "mean_abs_realized_pct": round(float((spike["realized"].abs() * 100).mean()), 3),
                  "share_abs_z_ge_2.5": round(float((spike["target_abs_z"] >= 2.5).mean()), 4)},
        "quiet": {**hit_summary(quiet["hit"]),
                  "coverage": round(float(quiet["covered"].mean()), 4),
                  "brier": round(float(quiet["brier"].mean()), 4),
                  "mean_abs_surprise_z": round(float(quiet["surprise_z"].abs().mean()), 3),
                  "median_abs_surprise_z": round(float(quiet["surprise_z"].abs().median()), 3),
                  "mean_abs_realized_pct": round(float((quiet["realized"].abs() * 100).mean()), 3),
                  "share_abs_z_ge_2.5": round(float((quiet["target_abs_z"] >= 2.5).mean()), 4)},
        "hit_diff_spike_minus_quiet": block_bootstrap_group_diff(
            h1["hit"].to_numpy(float), is_spike
        ),
        "coverage_diff_spike_minus_quiet": block_bootstrap_group_diff(
            h1["covered"].to_numpy(float), is_spike
        ),
        "abs_surprise_mannwhitney_p": round(float(stats.mannwhitneyu(spike["surprise_z"].abs(), quiet["surprise_z"].abs(), alternative="greater").pvalue), 5),
        "abs_return_mannwhitney_p": round(float(stats.mannwhitneyu(spike["realized"].abs(), quiet["realized"].abs(), alternative="greater").pvalue), 5),
    }
    # path view: forecasts issued the day before a spike, horizons 1..7
    spike_pos = set(spike["target_pos"].to_numpy() - 1)
    path = fc[fc["pos"].isin(spike_pos)]
    calm_path = fc[(fc["origin"] >= "2024-02-01") & ~fc["pos"].isin(spike_pos)]
    out["path_1to7_issued_day_before_spike"] = {
        "n_forecasts": int(len(path)),
        "hit_rate": round(float(path["hit"].mean()), 4),
        "coverage": round(float(path["covered"].mean()), 4),
        "mean_abs_surprise_z": round(float(path["surprise_z"].abs().mean()), 3),
        "calm_hit_rate": round(float(calm_path["hit"].mean()), 4),
        "calm_coverage": round(float(calm_path["covered"].mean()), 4),
    }
    return out


def dashboard_as_displayed(fc: pd.DataFrame, max_origins: int = 50, step: int = 5) -> dict:
    """Replicate evaluate_forecast's default origin sampling ending on each 2026 date."""
    result = {}
    origins = np.sort(fc["pos"].unique())
    dates = fc.drop_duplicates("pos").set_index("pos")["origin"]
    series = {h: {} for h in range(1, 8)}
    for end_pos in origins:
        if dates[end_pos] < pd.Timestamp("2026-01-01"):
            continue
        # evaluator: last origin = len-8 -> horizons all observable; sample every `step`, keep last 50
        sample = np.arange(end_pos, -1, -step)[:max_origins]
        sub = fc[fc["pos"].isin(sample)]
        if sub["realized"].isna().any():
            continue
        for h, g in sub.groupby("horizon"):
            if len(g) == max_origins:
                series[h][str(dates[end_pos].date())] = round(float(g["hit"].mean()), 3)
    for h in range(1, 8):
        vals = np.array(list(series[h].values()))
        if len(vals) == 0:
            continue
        result[f"h{h}"] = {
            "days_evaluated_2026": int(len(vals)),
            "min": round(float(vals.min()), 3), "median": round(float(np.median(vals)), 3), "max": round(float(vals.max()), 3),
            "share_days_ge_0.60": round(float((vals >= 0.60).mean()), 3),
            "share_days_ge_0.61": round(float((vals >= 0.61).mean()), 3),
            "share_days_ge_0.63": round(float((vals >= 0.63).mean()), 3),
            "argmax_date": max(series[h], key=series[h].get),
        }
    # any-horizon view: on how many days did at least one horizon show >= 0.60?
    frame = pd.DataFrame(series)
    if not frame.empty:
        result["any_horizon_ge_0.60_share_of_days"] = round(float((frame.max(axis=1) >= 0.60).mean()), 3)
        result["any_horizon_ge_0.63_share_of_days"] = round(float((frame.max(axis=1) >= 0.63).mean()), 3)
        result["best_single_display"] = {"value": float(frame.max().max()), "horizon": str(frame.max().idxmax()),
                                         "date": str(frame[frame.max().idxmax()].idxmax())}
        frame.to_csv(OUTPUT_DIR / "dashboard_as_displayed_2026.csv")
    return result


def main() -> None:
    out = {}
    for key in ("bito", "btc"):
        fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{key}.csv", parse_dates=["origin", "target_date"])
        day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
        out[key] = {"news_spike_events": news_spike_events(fc, day)}
        if key == "bito":
            out[key]["dashboard_as_displayed_2026"] = dashboard_as_displayed(fc)
    (OUTPUT_DIR / "news_events.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
