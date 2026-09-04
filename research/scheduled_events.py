"""Fully exogenous scheduled-event test.

Event days are fixed by public calendars, never by returns or headlines:

  fomc      FOMC decision days (second day of each scheduled meeting; the two
            2020 emergency actions are included as decision days), 2016-2026.
            Source: Federal Reserve FOMC calendars.
  payrolls  BLS Employment Situation release: first Friday of the month, moved
            to Thursday when that Friday is 1 January or 4 July (approximation of
            the BLS schedule; occasional government-shutdown delays are ignored).
  earnings  first trading session after each quarterly report (reports after the
            close react next session), from research/output/earnings_dates.csv.

For each instrument and event set we compare the h=1 forecast issued the day
before an event day with forecasts for all other days, and report post-event
continuation.  Crypto instruments are included for the macro sets as a spillover
check: they have no scheduled events of their own.
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
from event_study import DATASETS, block_bootstrap_diff, hit_summary  # noqa: E402

FOMC_DECISION_DAYS = [
    # 2016-2019
    "2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15", "2016-07-27", "2016-09-21", "2016-11-02", "2016-12-14",
    "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14", "2017-07-26", "2017-09-20", "2017-11-01", "2017-12-13",
    "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13", "2018-08-01", "2018-09-26", "2018-11-08", "2018-12-19",
    "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19", "2019-07-31", "2019-09-18", "2019-10-30", "2019-12-11",
    # 2020 (incl. emergency cuts 3 Mar and Sun 15 Mar -> first session Mon 16 Mar)
    "2020-01-29", "2020-03-03", "2020-03-16", "2020-04-29", "2020-06-10", "2020-07-29", "2020-09-16", "2020-11-05", "2020-12-16",
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16", "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15", "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29",
]


def payroll_days(start: str, end: str) -> list[pd.Timestamp]:
    out = []
    for month in pd.period_range(start, end, freq="M"):
        first = month.to_timestamp()
        friday = first + pd.Timedelta(int((4 - first.weekday()) % 7), unit="D")
        if (friday.month, friday.day) in {(1, 1), (7, 4)}:
            friday -= pd.Timedelta(1, unit="D")
        out.append(friday)
    return out


def earnings_reaction_days(symbol: str, index: pd.DatetimeIndex) -> list[pd.Timestamp]:
    table = pd.read_csv(OUTPUT_DIR / "earnings_dates.csv")
    sub = table[table["symbol"] == symbol]
    days = []
    for _, row in sub.iterrows():
        ts = pd.Timestamp(row["report_datetime_ny"]).normalize()
        pos = index.searchsorted(ts, side="right" if row["after_close"] else "left")
        if pos < len(index):
            days.append(index[pos])
    return sorted(set(days))


def to_sessions(days: list, index: pd.DatetimeIndex) -> np.ndarray:
    """Map calendar days to the first session on/after each day (positions)."""
    pos = index.searchsorted(pd.DatetimeIndex(days), side="left")
    pos = pos[pos < len(index)]
    return np.unique(pos)


def evaluate(key: str, event_sets: dict[str, np.ndarray]) -> dict:
    fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{key}.csv", parse_dates=["origin", "target_date"])
    day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
    org = pd.read_csv(OUTPUT_DIR / f"origins_{key}.csv", parse_dates=["origin"]).set_index("origin")
    closes = day["close"].to_numpy(float)
    ret = day["ret"].to_numpy(float)
    h1 = fc[fc["horizon"] == 1].copy()
    result = {"dataset": DATASETS[key]["label"], "asset_type": DATASETS[key]["asset_type"], "event_sets": {}}
    for name, positions in event_sets.items():
        positions = positions[(positions >= h1["target_pos"].min()) & (positions <= h1["target_pos"].max())]
        is_event = h1["target_pos"].isin(positions)
        ev, other = h1[is_event], h1[~is_event]
        if len(ev) < 8:
            continue
        block = {
            "event_days": {**hit_summary(ev["hit"]), "coverage": round(float(ev["covered"].mean()), 4),
                           "brier": round(float(ev["brier"].mean()), 4),
                           "mean_abs_surprise_z": round(float(ev["surprise_z"].abs().mean()), 3),
                           "median_abs_surprise_z": round(float(ev["surprise_z"].abs().median()), 3),
                           "mean_abs_ret_pct": round(float(ev["realized"].abs().mean() * 100), 3),
                           "shock_share_pct": round(float((ev["target_abs_z"] >= 2.5).mean() * 100), 1),
                           "always_up_rate": round(float(ev["actual_up"].mean()), 3)},
            "other_days": {**hit_summary(other["hit"]), "coverage": round(float(other["covered"].mean()), 4),
                           "brier": round(float(other["brier"].mean()), 4),
                           "mean_abs_surprise_z": round(float(other["surprise_z"].abs().mean()), 3),
                           "median_abs_surprise_z": round(float(other["surprise_z"].abs().median()), 3),
                           "mean_abs_ret_pct": round(float(other["realized"].abs().mean() * 100), 3),
                           "shock_share_pct": round(float((other["target_abs_z"] >= 2.5).mean() * 100), 1),
                           "always_up_rate": round(float(other["actual_up"].mean()), 3)},
            "tests": {
                "hit_binomial_p_vs_0.5": hit_summary(ev["hit"])["binomial_p_vs_0.5"],
                "hit_diff_event_minus_other": block_bootstrap_diff(ev["hit"].to_numpy(float), other["hit"].to_numpy(float)),
                "coverage_diff_event_minus_other": block_bootstrap_diff(ev["covered"].to_numpy(float), other["covered"].to_numpy(float)),
                "abs_surprise_mannwhitney_p": round(float(stats.mannwhitneyu(ev["surprise_z"].abs(), other["surprise_z"].abs(), alternative="greater").pvalue), 5),
                "abs_return_mannwhitney_p": round(float(stats.mannwhitneyu(ev["realized"].abs(), other["realized"].abs(), alternative="greater").pvalue), 5),
            },
        }
        # 7-session path issued the day before the event
        path = fc[fc["pos"].isin(positions - 1)]
        block["path_1to7_issued_day_before"] = {"n": int(len(path)), "hit_rate": round(float(path["hit"].mean()), 4),
                                                "coverage": round(float(path["covered"].mean()), 4)}
        # consensus alignment with the event-day move, and post-event continuation
        aligned = []
        cont = {k: [] for k in (1, 3, 7)}
        for p in positions:
            direction = np.sign(ret[p])
            if direction == 0:
                continue
            origin = day.index[p - 1]
            if origin in org.index:
                want = "Buy" if direction > 0 else "Sell"
                aligned.append(org.loc[origin, "consensus_direction"] == want)
            for k in cont:
                if p + k < len(closes):
                    cont[k].append(direction * (closes[p + k] / closes[p] - 1) * 100)
        block["consensus_aligned_with_event_move_pct"] = round(float(np.mean(aligned)) * 100, 1) if aligned else None
        block["post_event_continuation"] = {}
        for k, vals in cont.items():
            vals = np.asarray(vals)
            if len(vals) > 5:
                t, p = stats.ttest_1samp(vals, 0.0)
                block["post_event_continuation"][f"{k}d"] = {"n": int(len(vals)), "mean_pct": round(float(vals.mean()), 3),
                                                             "share_positive": round(float((vals > 0).mean()), 3),
                                                             "t": round(float(t), 2), "p": round(float(p), 4)}
        result["event_sets"][name] = block
    return result


def main() -> None:
    out = {}
    for key in ("spxl", "spy", "bito", "btc", "aapl", "msft", "tsla", "nvda"):
        if not (OUTPUT_DIR / f"forecasts_{key}.csv").exists():
            continue
        day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
        index = day.index
        sets: dict[str, np.ndarray] = {}
        spec = DATASETS[key]
        if spec["asset_type"] in ("index", "crypto"):
            fomc = to_sessions(pd.to_datetime(FOMC_DECISION_DAYS), index)
            pay = to_sessions(payroll_days(str(index.min().date()), str(index.max().date())), index)
            sets["fomc"] = fomc
            sets["payrolls"] = pay
            sets["fomc_or_payrolls"] = np.unique(np.r_[fomc, pay])
        if spec["asset_type"] == "stock":
            sets["earnings"] = to_sessions(earnings_reaction_days(spec["symbol"], index), index)
        out[key] = evaluate(key, sets)
    (OUTPUT_DIR / "scheduled_events.json").write_text(json.dumps(out, indent=2, default=float))
    for key, r in out.items():
        print(f"\n== {key} ({r['asset_type']})")
        for name, b in r["event_sets"].items():
            e, o, t = b["event_days"], b["other_days"], b["tests"]
            print(f"  {name:18s} n={e['n']:4d} hit={e['hit_rate']:.3f} (CI {e['wilson95']}) vs other {o['hit_rate']:.3f} | up-rate {e['always_up_rate']:.2f} vs {o['always_up_rate']:.2f} "
                  f"| cov {e['coverage']:.3f} vs {o['coverage']:.3f} | |s| {e['mean_abs_surprise_z']:.2f} vs {o['mean_abs_surprise_z']:.2f} (MWU p={t['abs_surprise_mannwhitney_p']}) "
                  f"| |r| {e['mean_abs_ret_pct']:.2f}% vs {o['mean_abs_ret_pct']:.2f}% (p={t['abs_return_mannwhitney_p']}) | shock share {e['shock_share_pct']}% vs {o['shock_share_pct']}%")
            print(f"  {'':18s} hit diff {t['hit_diff_event_minus_other']} | path hit/cov {b['path_1to7_issued_day_before']['hit_rate']:.3f}/{b['path_1to7_issued_day_before']['coverage']:.3f} "
                  f"| consensus aligned {b['consensus_aligned_with_event_move_pct']}% | continuation {b['post_event_continuation']}")


if __name__ == "__main__":
    main()
