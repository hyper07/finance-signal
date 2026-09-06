"""Is the model's P10-P90 area a useful prediction? Coverage of the model band versus
a naive trailing-volatility band (±1.2816·σ20·√h around the origin close) at 1 and 7
sessions, Winkler interval scores for both, where the misses fall (shock and
headline-spike sessions), and a ribbon figure of the day-before band against the
realized close over the last fifteen months. Output: output/band_vs_naive.json,
output/figures/fig19_band_ribbon.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent; OUT = HERE / "output"; FIG = OUT / "figures"
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BAND, NAIVE, MISS = "#d62728", "#2a78d6", "#0b0b0b"
Z80 = 1.2816


def winkler(lo, hi, y, alpha=0.2):
    w = hi - lo
    return w + (2 / alpha) * np.where(y < lo, lo - y, 0) + (2 / alpha) * np.where(y > hi, y - hi, 0)


def main() -> None:
    days = pd.read_csv(OUT / "days_btc.csv", parse_dates=["date"]).set_index("date")
    fc = pd.read_csv(OUT / "forecasts_btc.csv", parse_dates=["origin", "target_date"])
    ret = days["close"].pct_change(); sig20 = ret.rolling(20).std()
    fc["sig20"] = sig20.reindex(fc["origin"]).to_numpy()
    fc["naive_lo"] = -Z80 * fc["sig20"] * np.sqrt(fc["horizon"]); fc["naive_hi"] = -fc["naive_lo"]
    fc["naive_covered"] = (fc["realized"] >= fc["naive_lo"]) & (fc["realized"] <= fc["naive_hi"])
    fc["model_covered"] = (fc["realized"] >= fc["p10"]) & (fc["realized"] <= fc["p90"])
    fc["w_model"] = winkler(fc["p10"], fc["p90"], fc["realized"]); fc["w_naive"] = winkler(fc["naive_lo"], fc["naive_hi"], fc["realized"])
    fc["target_shock"] = fc["target_abs_z"] >= 2.5
    res = {}
    for h in (1, 3, 7):
        f = fc[(fc.horizon == h) & fc.sig20.notna()]
        calm = f[~f["window_has_shock"].astype(bool)]; shock = f[f["window_has_shock"].astype(bool)]
        spike = f[f["target_news_spike"].fillna(False).astype(bool)]
        res[f"h={h}"] = {"n": int(len(f)), "model_coverage": round(f.model_covered.mean(), 3), "naive_coverage": round(f.naive_covered.mean(), 3),
                         "model_coverage_calm": round(calm.model_covered.mean(), 3), "naive_coverage_calm": round(calm.naive_covered.mean(), 3),
                         "model_coverage_shock_window": round(shock.model_covered.mean(), 3), "naive_coverage_shock_window": round(shock.naive_covered.mean(), 3),
                         "model_coverage_headline_spike_target": round(spike.model_covered.mean(), 3) if len(spike) else None,
                         "model_width_pct": round(float((f.p90 - f.p10).mean() * 100), 2), "naive_width_pct": round(float((f.naive_hi - f.naive_lo).mean() * 100), 2),
                         "winkler_model": round(float(f.w_model.mean() * 100), 3), "winkler_naive": round(float(f.w_naive.mean() * 100), 3),
                         "misses_below_share": round(float(((f.realized < f.p10).sum()) / max(1, (~f.model_covered).sum())), 3),
                         "share_of_misses_on_shock_windows": round(float((~f.model_covered & f["window_has_shock"].astype(bool)).sum() / max(1, (~f.model_covered).sum())), 3),
                         "share_of_days_that_are_shock_windows": round(float(f["window_has_shock"].astype(bool).mean()), 3)}
    # clustering of misses: runs of consecutive misses at h=1
    f1 = fc[fc.horizon == 1].set_index("target_date").sort_index(); m = ~f1.model_covered
    runs = (m != m.shift()).cumsum(); run_len = m.groupby(runs).transform("size")[m]
    res["h=1 miss clustering"] = {"misses": int(m.sum()), "share_in_runs_of_2_or_more": round(float((run_len >= 2).sum() / max(1, m.sum())), 3), "expected_if_independent": round(float(1 - (1 - m.mean()) ** 2), 3)}
    (OUT / "band_vs_naive.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))

    # ---- figure: ribbon of the day-before band vs realized close, last 15 months ----
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    start, end = pd.Timestamp("2025-06-01"), days.index.max()
    fig, axes = plt.subplots(2, 1, figsize=(13.5, 8.2), sharex=True)
    for ax, h in zip(axes, (1, 7)):
        f = fc[(fc.horizon == h)].set_index("target_date").sort_index(); f = f.loc[start:end]
        c0 = days["close"].reindex(f["origin"]).to_numpy()
        lo, hi = c0 * (1 + f["p10"].to_numpy()), c0 * (1 + f["p90"].to_numpy()); nlo, nhi = c0 * (1 + f["naive_lo"].to_numpy()), c0 * (1 + f["naive_hi"].to_numpy())
        ax.fill_between(f.index, lo, hi, color=BAND, alpha=0.18, lw=0, zorder=1)
        ax.plot(f.index, nlo, color=NAIVE, lw=1, ls=":", zorder=2); ax.plot(f.index, nhi, color=NAIVE, lw=1, ls=":", zorder=2)
        real = days["close"].loc[start:end]; ax.plot(real.index, real, color=INK, lw=1.6, zorder=3)
        miss = f[~f.model_covered]; ax.scatter(miss.index, days["close"].reindex(miss.index), s=22, color=MISS, edgecolor=SURF, lw=0.8, zorder=4)
        spikes = days.loc[start:end]; spikes = spikes[spikes["news_spike"].fillna(False).astype(bool)]
        for d in spikes.index: ax.axvline(d, color=MUTED, lw=0.6, alpha=0.5, zorder=0)
        cov = f.model_covered.mean(); ncov = f.naive_covered.mean()
        ax.set_title(f"{h}-session-ahead band issued at each origin, drawn at its target date — in this window the close sat inside the model band on {cov:.0%} of sessions (naive volatility band: {ncov:.0%})", loc="left", fontsize=9.5)
        ax.set_ylabel("BTC/USD"); ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k")); ax.tick_params(length=0)
        for y in ax.get_yticks(): ax.axhline(y, color=GRID, lw=0.6, zorder=0)
    handles = [Patch(color=BAND, alpha=0.18, label="model P10–P90 area"), Line2D([], [], color=NAIVE, ls=":", lw=1, label="naive band: ±1.28 × 20-day σ × √h"), Line2D([], [], color=INK, lw=1.6, label="realized close"),
               Line2D([], [], marker="o", ls="", color=MISS, label="close outside the model area"), Line2D([], [], color=MUTED, lw=0.6, alpha=0.7, label="headline-spike session")]
    fig.legend(handles=handles, loc="upper center", ncol=5, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.985))
    fig.suptitle("The area is right about four sessions in five — and so is a volatility formula; the misses cluster on news", fontsize=11, y=0.998, x=0.5)
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(FIG / "fig19_band_ribbon.png", dpi=160, facecolor=SURF)


if __name__ == "__main__":
    main()
