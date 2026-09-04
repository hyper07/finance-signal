"""Multiplicity control: Benjamini-Hochberg FDR across the paper's key tests.

Collects the p-values behind Tables 1, 1b, 1c, 3, 4, 5, 7 and the scheduled-event
test (when present), applies BH within each pre-specified family and across all
families, and reports which findings survive at q = 0.05 and q = 0.10.
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

KEYS = ["bito", "btc", "spxl", "spy", "aapl", "msft", "tsla", "nvda"]


def bh(pvals: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (q-values)."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(q, 1.0)
    return out


def collect() -> pd.DataFrame:
    rows = []
    for key in KEYS:
        s = json.load(open(OUTPUT_DIR / f"summary_{key}.json"))
        e = json.load(open(OUTPUT_DIR / "effectiveness.json"))[key]
        # Family A: directional accuracy vs 0.5 per horizon (two-sided binomial)
        for r in s["calibration_all"]:
            rows.append(dict(family="A_direction_vs_half", instrument=key, test=f"h={r['horizon']} hit={r['hit_rate']}",
                             p=r["binomial_p_vs_0.5"], direction="below" if r["hit_rate"] < 0.5 else "above"))
        # Family B: Pesaran-Timmermann skill (one-sided, all origins) per horizon
        for r in e["by_horizon"]:
            # h>1 outcomes overlap, so use the mean statistic over the h non-overlapping subsequences
            pt = r["pesaran_timmermann_all_origins"]
            stat = pt.get("statistic") if r["horizon"] == 1 else r["pesaran_timmermann_nonoverlapping"]["mean_statistic"]
            if stat is not None:
                rows.append(dict(family="B_pesaran_timmermann_skill", instrument=key, test=f"h={r['horizon']} PT={stat}",
                                 p=float(1 - stats.norm.cdf(stat)), direction="skill"))
            nw = r["brier_vs_constant_0.5_newey_west"]
            rows.append(dict(family="C_brier_worse_than_coin", instrument=key, test=f"h={r['horizon']} t={nw['t_stat']}",
                             p=nw["p_two_sided"], direction="worse" if nw["mean_diff"] > 0 else "better"))
        # Family D: shock-window vs calm hit difference (block bootstrap, two-sided)
        d = s["window_split"]["hit_rate_difference_shock_minus_calm"]
        rows.append(dict(family="D_shock_vs_calm_hit", instrument=key, test=f"diff={d['difference']}", p=max(d["p_two_sided"], 1 / 4000),
                         direction="shock worse" if d["difference"] < 0 else "shock better"))
        # Family E: pre-event h=1 accuracy vs 0.5
        pe = s["events"]["pre_event_h1_direction"]
        rows.append(dict(family="E_pre_event_direction", instrument=key, test=f"hit={pe['hit_rate']} n={pe['n']}", p=pe["binomial_p_vs_0.5"],
                         direction="below" if pe["hit_rate"] < 0.5 else "above"))
        # Family F: post-shock continuation at 7 sessions (one-sample t, two-sided)
        c = s["post_shock_continuation_sign_adjusted"].get("7d")
        if c:
            rows.append(dict(family="F_continuation_7d", instrument=key, test=f"mean={c['mean_pct']}% n={c['n']}", p=c["p_value"],
                             direction="continuation" if c["mean_pct"] > 0 else "reversal"))
        # Family G: headline-spike day accuracy vs 0.5 and coverage difference
        ne_path = OUTPUT_DIR / "news_events.json"
        if ne_path.exists():
            ne = json.load(open(ne_path))
            if key in ne:
                sp = ne[key]["news_spike_events"]
                rows.append(dict(family="G_headline_spike_direction", instrument=key, test=f"hit={sp['spike']['hit_rate']} n={sp['spike']['n']}",
                                 p=sp["spike"]["binomial_p_vs_0.5"], direction="below" if sp["spike"]["hit_rate"] < 0.5 else "above"))
                rows.append(dict(family="H_headline_spike_surprise", instrument=key, test="MWU |s| spike > quiet",
                                 p=sp["abs_surprise_mannwhitney_p"], direction="larger surprise"))
    # Family I: scheduled-event test, when available
    se_path = OUTPUT_DIR / "scheduled_events.json"
    if se_path.exists():
        se = json.load(open(se_path))
        for key, r in se.items():
            for name, block in r.get("event_sets", {}).items():
                t = block.get("tests", {})
                if "hit_binomial_p_vs_0.5" in t:
                    rows.append(dict(family="I_scheduled_event_direction", instrument=key, test=f"{name} hit={block['event_days']['hit_rate']} n={block['event_days']['n']}",
                                     p=t["hit_binomial_p_vs_0.5"], direction="below" if block["event_days"]["hit_rate"] < 0.5 else "above"))
                if "abs_surprise_mannwhitney_p" in t:
                    rows.append(dict(family="J_scheduled_event_surprise", instrument=key, test=f"{name} MWU |s|", p=t["abs_surprise_mannwhitney_p"],
                                     direction="larger surprise"))
    frame = pd.DataFrame(rows)
    frame["p"] = frame["p"].clip(lower=1e-6, upper=1.0)
    frame["q_within_family"] = np.nan
    for fam, g in frame.groupby("family"):
        frame.loc[g.index, "q_within_family"] = bh(g["p"].to_numpy())
    frame["q_all_tests"] = bh(frame["p"].to_numpy())
    return frame


def main() -> None:
    frame = collect()
    frame.to_csv(OUTPUT_DIR / "multiplicity.csv", index=False)
    summary = {
        "total_tests": int(len(frame)),
        "families": {fam: {"tests": int(len(g)), "survive_q05_within": int((g["q_within_family"] <= 0.05).sum()),
                           "survive_q10_within": int((g["q_within_family"] <= 0.10).sum()),
                           "survive_q05_all": int((g["q_all_tests"] <= 0.05).sum())}
                     for fam, g in frame.groupby("family")},
        "survivors_q05_all_tests": frame[frame["q_all_tests"] <= 0.05][["family", "instrument", "test", "direction", "p", "q_all_tests"]]
                                      .sort_values("q_all_tests").to_dict(orient="records"),
        "survivors_q10_all_tests_count": int((frame["q_all_tests"] <= 0.10).sum()),
    }
    (OUTPUT_DIR / "multiplicity.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps(summary["families"], indent=1))
    print(f"\n{summary['total_tests']} tests; {len(summary['survivors_q05_all_tests'])} survive BH q<=0.05 across ALL families; {summary['survivors_q10_all_tests_count']} at q<=0.10")
    for r in summary["survivors_q05_all_tests"]:
        print(f"  {r['family']:30s} {r['instrument']:5s} {r['test']:40s} {r['direction']:16s} p={r['p']:.2e} q={r['q_all_tests']:.3f}")


if __name__ == "__main__":
    main()
