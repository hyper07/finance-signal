"""Robustness checks: the 50-origin sampling illusion, the 3-day signal's own
hit rate, and sensitivity of the shock split to the z threshold."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR, public_frame  # noqa: E402


def sampled_evaluator(fc: pd.DataFrame, horizon: int, max_origins: int = 50, step: int = 5, draws: int = 2000, seed: int = 3) -> dict:
    """Mimic evaluate_forecast's default (50 origins, step 5) with random anchors."""
    sub = fc[fc["horizon"] == horizon].sort_values("pos")
    hits = sub["hit"].to_numpy(float)
    rng = np.random.default_rng(seed)
    samples = []
    span = max_origins * step
    for _ in range(draws):
        start = rng.integers(0, len(hits) - span)
        samples.append(hits[start:start + span:step].mean())
    samples = np.array(samples)
    return {
        "max_origins": max_origins, "step": step, "draws": draws,
        "mean": round(float(samples.mean()), 4), "sd": round(float(samples.std()), 4),
        "share_at_or_above_0.60": round(float((samples >= 0.60).mean()), 4),
        "share_at_or_above_0.65": round(float((samples >= 0.65).mean()), 4),
        "max": round(float(samples.max()), 4),
        "samples": [round(float(x), 4) for x in samples],
    }


def three_day_signal_hit(dataset: str) -> dict:
    pub = public_frame(dataset)
    ret = pub["actual_ret"].astype(float)
    prev = pub["signal"].shift(1)
    active = prev.isin([1, -1]) & ret.notna()
    hit = (np.sign(ret[active]) == prev[active]).astype(int)
    k, n = int(hit.sum()), int(len(hit))
    by_month = hit.groupby(hit.index.to_period("M")).agg(["mean", "size"])
    return {
        "dataset": dataset, "active_days": n, "hit_rate": round(k / n, 4),
        "binomial_p_vs_0.5": round(float(stats.binomtest(k, n, 0.5).pvalue), 4),
        "by_month": {str(i): [round(float(r["mean"]), 3), int(r["size"])] for i, r in by_month.iterrows()},
        "strategy_cum_ret_pct_last": float(pub["strategy_cum_ret"].iloc[-1]),
        "buy_hold_cum_ret_pct_last": float(pub["actual_cum_ret"].iloc[-1]),
    }


def z_sensitivity(fc: pd.DataFrame, day: pd.DataFrame) -> list[dict]:
    out = []
    z = day["z"].to_numpy(float)
    for thr in (2.0, 2.5, 3.0, 3.5):
        shock_pos = np.flatnonzero(np.abs(z) >= thr)
        flag = np.array([bool(((shock_pos > p) & (shock_pos <= p + h)).any()) for p, h in zip(fc["pos"], fc["horizon"])])
        s, c = fc[flag], fc[~flag]
        pre = fc[(fc["horizon"] == 1) & np.isin(fc["target_pos"], shock_pos)]
        out.append({
            "z_threshold": thr, "shock_days": int(len(shock_pos)),
            "shock_window_hit": round(float(s["hit"].mean()), 4), "shock_window_n": int(len(s)),
            "calm_window_hit": round(float(c["hit"].mean()), 4), "calm_window_n": int(len(c)),
            "shock_window_coverage": round(float(s["covered"].mean()), 4),
            "calm_window_coverage": round(float(c["covered"].mean()), 4),
            "pre_event_h1_hit": round(float(pre["hit"].mean()), 4), "pre_event_h1_n": int(len(pre)),
            "pre_event_h1_coverage": round(float(pre["covered"].mean()), 4),
        })
    return out


def main() -> None:
    result = {}
    for key in ("bito", "btc"):
        fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{key}.csv")
        day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
        result[key] = {
            "sampled_evaluator_accuracy_h1": sampled_evaluator(fc, 1),
            "sampled_evaluator_accuracy_h7": {k: v for k, v in sampled_evaluator(fc, 7).items() if k != "samples"},
            "z_threshold_sensitivity": z_sensitivity(fc, day),
        }
    result["three_day_signal_published"] = {
        "b04_prediction_us_coin": three_day_signal_hit("b04_prediction_us_coin"),
    }
    (OUTPUT_DIR / "robustness.json").write_text(json.dumps(result, indent=2))
    for key in ("bito", "btc"):
        r = result[key]
        s1 = {k: v for k, v in r["sampled_evaluator_accuracy_h1"].items() if k != "samples"}
        print(key, "sampled h1:", s1)
        print(key, "sampled h7:", r["sampled_evaluator_accuracy_h7"])
        for row in r["z_threshold_sensitivity"]:
            print(key, row)
    t = result["three_day_signal_published"]["b04_prediction_us_coin"]
    print("3-day published signal b04:", {k: v for k, v in t.items() if k != "by_month"})
    print("  by month:", t["by_month"])


if __name__ == "__main__":
    main()
