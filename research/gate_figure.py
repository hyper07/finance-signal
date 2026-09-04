"""Fig. 13: event-conditional gate effect by gate type, per instrument and pooled over stocks."""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR
g = json.load(open(OUTPUT_DIR / "gate_experiment.json")); u = json.load(open(OUTPUT_DIR / "gate_experiment_universe.json"))
COLOR = {"crypto": "#B7791F", "index": "#1F5F8B", "stock": "#B23A34"}
labels, vals, cols, errs = [], [], [], []
for key, name, typ in (("btc", "BTC", "crypto"), ("bito", "BITO", "crypto"), ("spy", "SPY", "index"), ("spxl", "SPXL", "index")):
    for gate in ("shock", "headline", "calendar"):
        e = g[key]["windows"]["full"]["by_gate_type"].get(gate)
        if not e: continue
        wm = e["model"]["winkler"]; d = e["winkler_event_conditional_minus_model"]
        labels.append(f"{name} · {gate}"); vals.append(e["winkler_improvement_pct"]); cols.append(COLOR[typ])
        errs.append([100 * -d["ci95"][1] / wm, 100 * -d["ci95"][0] / wm])
for gate in ("calendar", "headline", "shock"):
    e = u["pooled_full_sample"][gate]; wm = e["winkler_model"]; d = e["winkler_diff_bootstrap"]
    labels.append(f"50 stocks pooled · {gate}" + (" (earnings)" if gate == "calendar" else "")); vals.append(e["winkler_improvement_pct"]); cols.append(COLOR["stock"])
    errs.append([100 * -d["ci95"][1] / wm, 100 * -d["ci95"][0] / wm])
vals = np.array(vals); lo = vals - np.array([a for a, b in errs]); hi = np.array([b for a, b in errs]) - vals
fig, ax = plt.subplots(figsize=(9, 5.2))
y = np.arange(len(labels))
ax.barh(y, vals, color=cols, alpha=0.85)
ax.errorbar(vals, y, xerr=[np.abs(vals - np.array([a for a, b in errs])), np.abs(np.array([b for a, b in errs]) - vals)], fmt="none", ecolor="black", elinewidth=1, capsize=3)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9); ax.invert_yaxis(); ax.axvline(0, color="grey", lw=1)
ax.set_xlabel("improvement in Winkler interval score on gated forecasts, % (event-conditional replacement vs deployed model; 95% block-bootstrap CI)")
ax.set_title("Where a causal, type-specific gate helps — and where it hurts", fontsize=11)
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in COLOR.values()]; ax.legend(handles, list(COLOR.keys()), fontsize=8, loc="lower right")
fig.tight_layout(); fig.savefig(OUTPUT_DIR / "figures" / "fig13_gate_effects.png", dpi=160); print("fig13 saved")
