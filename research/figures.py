"""Figures for the news-shock event study (reads research/output CSV/JSON)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR  # noqa: E402

FIG = OUTPUT_DIR / "figures"
FIG.mkdir(parents=True, exist_ok=True)
LABEL = {"bito": "BITO (deployed b04)", "btc": "BTC/USD spot"}
COLOR = {"bito": "#1f77b4", "btc": "#d62728"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return c - h, c + h


def load(key):
    fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{key}.csv", parse_dates=["origin", "target_date"])
    org = pd.read_csv(OUTPUT_DIR / f"origins_{key}.csv", parse_dates=["origin"]).set_index("origin")
    day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
    ev = pd.read_csv(OUTPUT_DIR / f"events_{key}.csv", parse_dates=["event_date"])
    return fc, org, day, ev


def fig_fan_chart():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, key in zip(axes, ("bito", "btc")):
        fc, org, day, _ = load(key)
        as_of = pd.Timestamp("2026-08-18")
        sub = fc[fc["origin"] == as_of].sort_values("horizon")
        c0 = float(org.loc[as_of, "close"])
        hist = day.loc["2026-08-10":"2026-08-28", "close"]
        pos0 = int(day.index.get_loc(as_of))
        realized = day["close"].iloc[pos0: pos0 + 8]
        x_h = np.arange(0, 8)
        p10 = np.r_[c0, c0 * (1 + sub["p10"].to_numpy())]
        p50 = np.r_[c0, c0 * (1 + sub["p50"].to_numpy())]
        p90 = np.r_[c0, c0 * (1 + sub["p90"].to_numpy())]
        ax.fill_between(x_h, p10, p90, color=COLOR[key], alpha=0.18, label="forecast P10–P90 (as of Aug 18)")
        ax.plot(x_h, p50, color=COLOR[key], lw=1.5, ls="--", label="forecast median")
        ax.plot(x_h[: len(realized)], realized.to_numpy(), color="black", lw=2, marker="o", ms=4, label="realized close")
        pre_x = np.arange(-(pos0 - day.index.get_loc(hist.index[0])), 1)
        ax.plot(pre_x, day["close"].iloc[pos0 + pre_x[0]: pos0 + 1].to_numpy(), color="grey", lw=1.5)
        ax.axvline(0, color="grey", ls=":", lw=1)
        ax.axvline(1, color="orange", ls="-.", lw=1)
        ax.text(1.05, ax.get_ylim()[0] if False else p10.min(), "Aug 19\nWhite House\ncrypto summit", fontsize=8, color="orange", va="bottom")
        ax.set_title(f"{LABEL[key]} — point-in-time forecast made 2026-08-18")
        ax.set_xlabel("sessions after origin (0 = Aug 18 close)")
        ax.set_ylabel("price")
        ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "fig1_august_fan_chart.png", dpi=160)
    plt.close(fig)


def fig_rolling_event_view():
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), sharex="col")
    for col, key in enumerate(("bito", "btc")):
        fc, org, day, _ = load(key)
        win = org.loc["2026-08-05":"2026-08-28"]
        h1 = fc[(fc["horizon"] == 1) & fc["origin"].isin(win.index)].set_index("origin")
        ax = axes[0, col]
        ax.plot(win.index, win["close"], color="black", marker="o", ms=3)
        ax.set_title(f"{LABEL[key]}: price")
        ax.axvspan(pd.Timestamp("2026-08-18 12:00"), pd.Timestamp("2026-08-21 12:00"), color="orange", alpha=0.15)
        ax2 = axes[1, col]
        ax2.bar(win.index, win["consensus_votes_buy"], color="#2ca02c", alpha=0.7, label="Buy votes", width=0.8)
        ax2.bar(win.index, -win["consensus_votes_sell"], color="#d62728", alpha=0.7, label="Sell votes", width=0.8)
        ax2.axhline(0, color="grey", lw=0.8)
        ax2.set_ylim(-7.5, 7.5)
        ax2.set_ylabel("7-session consensus votes")
        ax3 = ax2.twinx()
        ax3.plot(h1.index, h1["prob_up"], color="purple", marker="s", ms=3, lw=1, label="P(up) next session")
        ax3.step(win.index, win["strategy_signal"] * 0.5 + 0.5, where="mid", color="grey", ls="--", lw=1, label="3-day signal (1=Long, 0=Short or Cash)")
        ax3.set_ylim(-0.05, 1.05)
        ax3.axhline(0.5, color="purple", lw=0.5, ls=":")
        ax2.axvspan(pd.Timestamp("2026-08-18 12:00"), pd.Timestamp("2026-08-21 12:00"), color="orange", alpha=0.15)
        ax2.set_title("model state day by day (as-of each close)")
        h_a, l_a = ax2.get_legend_handles_labels(); h_b, l_b = ax3.get_legend_handles_labels()
        ax2.legend(h_a + h_b, l_a + l_b, fontsize=7, loc="lower left")
        for a in (ax, ax2):
            a.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(FIG / "fig2_august_daily_model_state.png", dpi=160)
    plt.close(fig)


def fig_calibration_by_horizon():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for key in ("bito", "btc"):
        s = json.load(open(OUTPUT_DIR / f"summary_{key}.json"))
        rows = s["calibration_all"]
        h = [r["horizon"] for r in rows]
        hit = np.array([r["hit_rate"] for r in rows])
        lo = np.array([r["wilson95"][0] for r in rows]); hi = np.array([r["wilson95"][1] for r in rows])
        axes[0].errorbar(np.array(h) + (0.1 if key == "btc" else -0.1), hit, yerr=[hit - lo, hi - hit], fmt="o-", color=COLOR[key], capsize=3, label=LABEL[key])
        cov = [r["p10_p90_coverage"] for r in rows]
        axes[1].plot(h, cov, "o-", color=COLOR[key], label=LABEL[key])
    axes[0].axhline(0.5, color="grey", ls="--", lw=1)
    axes[0].set_ylim(0.35, 0.70); axes[0].set_xlabel("horizon (sessions)"); axes[0].set_ylabel("directional accuracy (95% Wilson CI)")
    axes[0].set_title("Direction: all origins 2021/22–2026")
    axes[1].axhline(0.8, color="grey", ls="--", lw=1, label="nominal 80%")
    axes[1].set_ylim(0.5, 1.0); axes[1].set_xlabel("horizon (sessions)"); axes[1].set_ylabel("P10–P90 empirical coverage")
    axes[1].set_title("Interval calibration")
    for a in axes: a.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig3_calibration_by_horizon.png", dpi=160); plt.close(fig)


def fig_conditional_bins():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for key in ("bito", "btc"):
        s = json.load(open(OUTPUT_DIR / f"summary_{key}.json"))
        zb = s["h1_hit_by_target_abs_z"]
        x = np.arange(len(zb)); off = 0.18 if key == "btc" else -0.18
        hit = np.array([b["hit_rate"] for b in zb]); lo = np.array([b["wilson95"][0] for b in zb]); hi = np.array([b["wilson95"][1] for b in zb])
        axes[0].errorbar(x + off, hit, yerr=[hit - lo, hi - hit], fmt="o", color=COLOR[key], capsize=3, label=f"{LABEL[key]} direction")
        axes[0].plot(x + off, [b["coverage"] for b in zb], "s--", color=COLOR[key], alpha=0.6, label=f"{LABEL[key]} coverage")
        axes[0].set_xticks(x); axes[0].set_xticklabels([b["bin"] for b in zb])
        nb = s["h1_hit_by_target_news_ratio"]
        x = np.arange(len(nb))
        hit = np.array([b["hit_rate"] for b in nb]); lo = np.array([b["wilson95"][0] for b in nb]); hi = np.array([b["wilson95"][1] for b in nb])
        axes[1].errorbar(x + off, hit, yerr=[hit - lo, hi - hit], fmt="o", color=COLOR[key], capsize=3, label=f"{LABEL[key]} direction")
        axes[1].plot(x + off, [b["coverage"] for b in nb], "s--", color=COLOR[key], alpha=0.6, label=f"{LABEL[key]} coverage")
        axes[1].set_xticks(x); axes[1].set_xticklabels([b["bin"] for b in nb])
    for a in axes:
        a.axhline(0.5, color="grey", ls=":", lw=1); a.set_ylim(0, 1.05); a.legend(fontsize=7)
    axes[0].set_xlabel("|z| of the target session's return (realized / trailing σ20)"); axes[0].set_title("Next-session forecast vs size of the realized move")
    axes[1].set_xlabel("crypto headline count / trailing 30-day median (target day)"); axes[1].set_title("Next-session forecast vs news intensity (2024-02 →)")
    fig.tight_layout(); fig.savefig(FIG / "fig4_conditional_accuracy_bins.png", dpi=160); plt.close(fig)


def fig_surprise_distribution():
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for ax, key in zip(axes, ("bito", "btc")):
        fc, _, _, _ = load(key)
        s = fc[fc["horizon"] == 1]
        calm = s.loc[~s["window_has_shock"], "surprise_z"].clip(-10, 10)
        shock = s.loc[s["window_has_shock"], "surprise_z"].clip(-10, 10)
        bins = np.linspace(-10, 10, 61)
        ax.hist(calm, bins=bins, density=True, alpha=0.55, color="grey", label=f"calm sessions (n={len(calm)})")
        ax.hist(shock, bins=bins, density=True, alpha=0.55, color=COLOR[key], label=f"shock sessions |z|≥2.5 (n={len(shock)})")
        ax.axvline(-1.28, color="k", ls=":", lw=0.8); ax.axvline(1.28, color="k", ls=":", lw=0.8)
        ax.set_title(f"{LABEL[key]}: standardized surprise (realized − P50)/σ_band, h=1")
        ax.set_xlabel("surprise in forecast-band σ units (dotted = P10/P90)"); ax.legend(fontsize=8)
    axes[0].set_ylabel("density")
    fig.tight_layout(); fig.savefig(FIG / "fig5_surprise_distribution.png", dpi=160); plt.close(fig)


def fig_post_shock_drift():
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ks = [1, 2, 3, 5, 7]
    for key in ("bito", "btc"):
        _, _, _, ev = load(key)
        means, ses = [], []
        for k in ks:
            col = ev[f"continuation_{k}d_pct"].dropna()
            means.append(col.mean()); ses.append(col.std(ddof=1) / np.sqrt(len(col)))
        means = np.array(means); ses = np.array(ses)
        ax.errorbar(ks, means, yerr=1.96 * ses, fmt="o-", color=COLOR[key], capsize=3, label=f"{LABEL[key]} (n={len(ev)} shocks)")
    ax.axhline(0, color="grey", lw=1)
    ax.set_xlabel("sessions after the shock close (position opened at the shock close)")
    ax.set_ylabel("sign-adjusted return, % (mean ± 95% CI)")
    ax.set_title("Post-shock continuation: 'chase the news' at the close of the shock day")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig6_post_shock_continuation.png", dpi=160); plt.close(fig)


def fig_latency():
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    for ax, key in zip(axes, ("bito", "btc")):
        _, _, _, ev = load(key)
        sig = ev["signal_latency_sessions"]; cons = ev["consensus_latency_sessions"]
        bins = np.arange(-0.5, 15.5, 1)
        ax.hist(sig.dropna(), bins=bins, alpha=0.6, color="grey", label=f"3-day signal (already aligned: {int(ev['signal_already_aligned'].sum())}, never within 15: {int(sig.isna().sum() - ev['signal_already_aligned'].sum())})")
        ax.hist(cons.dropna(), bins=bins, alpha=0.6, color=COLOR[key], label=f"7-session consensus (already aligned: {int(ev['consensus_already_aligned'].sum())}, never within 15: {int(cons.isna().sum() - ev['consensus_already_aligned'].sum())})")
        ax.set_title(f"{LABEL[key]}: sessions until the model agrees with the shock direction")
        ax.set_xlabel("sessions after shock day T (0 = at T's close)"); ax.set_ylabel("events"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "fig7_adaptation_latency.png", dpi=160); plt.close(fig)


def fig_sixty_five():
    path = OUTPUT_DIR / "robustness.json"
    if not path.exists():
        return
    r = json.load(open(path))
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for key in ("bito", "btc"):
        d = r[key]["sampled_evaluator_accuracy_h1"]
        ax.hist(d["samples"], bins=np.linspace(0.3, 0.75, 46), alpha=0.55, color=COLOR[key], label=f"{LABEL[key]}: 50-origin samples (mean {d['mean']:.3f})")
    ax.axvline(0.65, color="k", ls="--", lw=1.2, label="0.65 (a figure seen on the dashboard)")
    ax.axvline(0.5, color="grey", ls=":", lw=1)
    ax.set_xlabel("directional accuracy (h=1) from a sample of 50 origins, step 5")
    ax.set_ylabel("count of resampled evaluations"); ax.set_title("Why a 50-origin evaluation can print 65% when the true rate is ≈50%")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig8_sampled_accuracy_illusion.png", dpi=160); plt.close(fig)


if __name__ == "__main__":
    fig_fan_chart(); fig_rolling_event_view(); fig_calibration_by_horizon(); fig_conditional_bins()
    fig_surprise_distribution(); fig_post_shock_drift(); fig_latency(); fig_sixty_five()
    print("figures:", sorted(p.name for p in FIG.glob("*.png")))
