"""Formal tests of predictive effectiveness in series.

  * Pesaran-Timmermann (1992) directional test, non-overlapping subsamples for h>1
  * Diebold-Mariano style test of the Brier score against the constant p=0.5
    forecast with Newey-West (Bartlett, lag h) long-run variance
  * Sequential log-score (cumulative log Bayes factor vs. a fair coin) and the
    even-odds Kelly growth of betting fraction 2p-1 each session
All three are computed for every horizon, and for h=1 split into calm vs shock
sessions and quiet vs headline-spike days.
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

CLIP = 0.02


def pesaran_timmermann(y: np.ndarray, x: np.ndarray) -> dict:
    n = len(y)
    if n < 20:
        return {"n": int(n)}
    p_hat = float(np.mean(y == x))
    py, px = float(y.mean()), float(x.mean())
    p_star = py * px + (1 - py) * (1 - px)
    v_hat = p_star * (1 - p_star) / n
    v_star = ((2 * py - 1) ** 2 * px * (1 - px) / n
              + (2 * px - 1) ** 2 * py * (1 - py) / n
              + 4 * py * px * (1 - py) * (1 - px) / n ** 2)
    denom = v_hat - v_star
    if denom <= 0:
        return {"n": int(n), "p_hat": round(p_hat, 4), "p_star": round(p_star, 4), "statistic": None}
    s = (p_hat - p_star) / np.sqrt(denom)
    return {"n": int(n), "p_hat": round(p_hat, 4), "p_star_independence": round(p_star, 4),
            "statistic": round(float(s), 3), "p_one_sided_skill": round(float(1 - stats.norm.cdf(s)), 4)}


def newey_west_mean_test(d: np.ndarray, lag: int) -> dict:
    n = len(d)
    d = d - d.mean() + d.mean()  # no-op for clarity
    mean = float(d.mean())
    centred = d - mean
    var = float(np.dot(centred, centred) / n)
    for k in range(1, lag + 1):
        w = 1 - k / (lag + 1)
        var += 2 * w * float(np.dot(centred[k:], centred[:-k]) / n)
    se = np.sqrt(max(var, 1e-12) / n)
    t = mean / se
    return {"n": int(n), "mean_diff": round(mean, 5), "hac_se": round(float(se), 5), "lag": lag,
            "t_stat": round(float(t), 3), "p_two_sided": round(float(2 * (1 - stats.norm.cdf(abs(t)))), 4)}


def sequential_scores(p: np.ndarray, y: np.ndarray) -> dict:
    p = np.clip(p, CLIP, 1 - CLIP)
    ll = y * np.log(p) + (1 - y) * np.log(1 - p) + np.log(2.0)   # log Bayes factor vs fair coin, per step
    cum = np.cumsum(ll)
    f = 2 * p - 1                                                  # Kelly fraction on "up" at even odds
    growth = np.log1p(f * (2 * y - 1))
    return {
        "n": int(len(p)),
        "cum_log_bayes_factor_vs_coin": round(float(cum[-1]), 3),
        "bits_per_forecast": round(float(cum[-1] / len(p) / np.log(2)), 5),
        "running_max": round(float(cum.max()), 3), "running_min": round(float(cum.min()), 3),
        "share_of_time_below_zero": round(float((cum < 0).mean()), 3),
        "kelly_total_log_growth": round(float(growth.sum()), 4),
        "kelly_growth_per_session_bps": round(float(growth.mean() * 1e4), 3),
    }


def run(key: str) -> dict:
    fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{key}.csv", parse_dates=["origin"]).sort_values(["horizon", "pos"])
    out: dict = {"by_horizon": []}
    for h, g in fc.groupby("horizon"):
        y = g["actual_up"].to_numpy(int); x = g["pred_up"].to_numpy(int); p = g["prob_up"].to_numpy(float)
        pt_all = pesaran_timmermann(y, x)
        # non-overlapping subsamples for h>1: every h-th origin, each offset
        subs = [pesaran_timmermann(y[o::h], x[o::h]) for o in range(h)] if h > 1 else [pt_all]
        stats_sub = [s["statistic"] for s in subs if s.get("statistic") is not None]
        d = (p - y) ** 2 - 0.25
        out["by_horizon"].append({
            "horizon": int(h),
            "pesaran_timmermann_all_origins": pt_all,
            "pesaran_timmermann_nonoverlapping": {"offsets": h, "mean_statistic": round(float(np.mean(stats_sub)), 3),
                                                  "min": round(float(np.min(stats_sub)), 3), "max": round(float(np.max(stats_sub)), 3),
                                                  "any_offset_significant_5pct_one_sided": bool(np.max(stats_sub) > 1.645)},
            "brier_vs_constant_0.5_newey_west": newey_west_mean_test(d, lag=int(h)),
            "sequential": sequential_scores(p, y),
        })
    h1 = fc[fc["horizon"] == 1]
    splits = {
        "calm_sessions": h1[~h1["window_has_shock"]],
        "shock_sessions_abs_z_ge_2.5": h1[h1["window_has_shock"]],
        "quiet_news_days": h1[h1["target_news_ratio"].notna() & (h1["target_news_ratio"] < 2)],
        "headline_spike_days": h1[h1["target_news_ratio"] >= 2],
        "live_2026": h1[h1["origin"] >= "2026-01-01"],
    }
    out["h1_conditional"] = {}
    for name, g in splits.items():
        y = g["actual_up"].to_numpy(int); x = g["pred_up"].to_numpy(int); p = g["prob_up"].to_numpy(float)
        out["h1_conditional"][name] = {
            "pesaran_timmermann": pesaran_timmermann(y, x),
            "brier_vs_constant_newey_west": newey_west_mean_test((p - y) ** 2 - 0.25, lag=1),
            "sequential": sequential_scores(p, y),
        }
    return out


def main() -> None:
    keys = sys.argv[1:] or sorted(p.stem.replace("forecasts_", "") for p in OUTPUT_DIR.glob("forecasts_*.csv"))
    path = OUTPUT_DIR / "effectiveness.json"
    result = json.loads(path.read_text()) if path.exists() else {}
    result.update({k: run(k) for k in keys})
    path.write_text(json.dumps(result, indent=2))
    result = {k: result[k] for k in keys}
    for k, r in result.items():
        print(f"\n===== {k} =====")
        for row in r["by_horizon"]:
            pt = row["pesaran_timmermann_all_origins"]; no = row["pesaran_timmermann_nonoverlapping"]
            nw = row["brier_vs_constant_0.5_newey_west"]; sq = row["sequential"]
            print(f" h={row['horizon']} PT_all={pt['statistic']} (p={pt.get('p_one_sided_skill')}) PT_nonoverlap mean={no['mean_statistic']} [{no['min']},{no['max']}] "
                  f"| Brier-0.25 mean={nw['mean_diff']:+.4f} t={nw['t_stat']} p={nw['p_two_sided']} "
                  f"| logBF={sq['cum_log_bayes_factor_vs_coin']} bits/fc={sq['bits_per_forecast']} below0={sq['share_of_time_below_zero']} kelly_bps={sq['kelly_growth_per_session_bps']}")
        print(" h=1 conditional:")
        for name, v in r["h1_conditional"].items():
            pt = v["pesaran_timmermann"]; nw = v["brier_vs_constant_newey_west"]; sq = v["sequential"]
            print(f"  {name:30s} n={pt.get('n')} PT={pt.get('statistic')} p={pt.get('p_one_sided_skill')} | Brier-0.25 t={nw['t_stat']} p={nw['p_two_sided']} | logBF={sq['cum_log_bayes_factor_vs_coin']} kelly_bps={sq['kelly_growth_per_session_bps']}")


if __name__ == "__main__":
    main()
