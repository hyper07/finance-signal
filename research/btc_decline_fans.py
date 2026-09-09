"""Figure: the seven-session forecast issued the session before each major Bitcoin
decline, against the realized path (BTC/USD, % from the origin close). Twelve
panels: the ten largest single-session declines with a forecast on record and the
two largest liquidation events of the headline-archive period. Same conventions as
Figure 1 (fig1_august_fan_chart.png). Written as PNG (full paper) and as a vector
PDF (Figure 3 of the arXiv preprint, set on a landscape page)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"; FIG = OUT / "figures"
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BAND = "#d62728"                                   # BTC colour used throughout the paper
EVENTS = [  # first shock session -> short label
    ("2021-05-12", "Tesla stops BTC payments; hot CPI"), ("2021-05-19", "China bans crypto services"),
    ("2021-09-07", "El Salvador launch flash crash"), ("2022-01-21", "Fed tightening; Russia ban plan"),
    ("2022-05-09", "Terra/LUNA collapse"), ("2022-06-13", "Celsius freeze; hot CPI"),
    ("2022-08-19", "Liquidation cascade; hawkish Fed"), ("2022-09-13", "Hot CPI; S&P 500 −4.3%"),
    ("2022-11-08", "FTX collapse"), ("2024-08-05", "Yen carry-trade unwind"),
    ("2025-10-10", "100% China tariffs announced"), ("2026-02-05", "Cross-asset deleveraging"),
]
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
                     "pdf.fonttype": 42})                     # embed TrueType, not Type 3, in the vector export


def main() -> None:
    days = pd.read_csv(OUT / "days_btc.csv", parse_dates=["date"]).set_index("date")
    fc = pd.read_csv(OUT / "forecasts_btc.csv", parse_dates=["origin"])
    ev = pd.read_csv(OUT / "events_btc.csv", parse_dates=["event_date"]).set_index("event_date")
    fig, axes = plt.subplots(3, 4, figsize=(13.5, 9.2), sharex=True, sharey=True)
    stats = []
    for ax, (day, label) in zip(axes.ravel(), EVENTS):
        d = pd.Timestamp(day); pos = days.index.get_loc(d); origin = days.index[pos - 1]
        c0 = float(days["close"].iloc[pos - 1])
        sub = fc[fc["origin"] == origin].sort_values("horizon")
        x = np.arange(0, 8)
        p10 = np.r_[0, sub["p10"].to_numpy() * 100]; p50 = np.r_[0, sub["p50"].to_numpy() * 100]; p90 = np.r_[0, sub["p90"].to_numpy() * 100]
        real = (days["close"].iloc[pos - 1: pos + 7].to_numpy() / c0 - 1) * 100
        pre = (days["close"].iloc[pos - 4: pos].to_numpy() / c0 - 1) * 100
        for y in (-20, -10, 10): ax.axhline(y, color=GRID, lw=0.8, zorder=0)
        ax.axhline(0, color=AXIS, lw=0.8, zorder=0)
        ax.fill_between(x, p10, p90, color=BAND, alpha=0.15, lw=0, zorder=1)
        ax.plot(x, p50, color=BAND, lw=1.6, ls="--", zorder=2)
        ax.plot(np.arange(-3, 1), pre, color=MUTED, lw=1.6, zorder=2)
        ax.plot(x[: len(real)], real, color=INK, lw=2, marker="o", ms=4.5, mec="#fcfcfb", mew=1, zorder=3)
        ax.axvline(1, color=MUTED, ls=":", lw=1, zorder=1)
        e = ev.loc[d]
        ax.set_title(f"{day} · {label}", fontsize=9, color=INK, loc="left", pad=4)
        ax.text(0.03, 0.04, f"P(up) {float(e['pre_h1_prob_up']):.2f}\nconsensus {e['pre_consensus']}", transform=ax.transAxes, fontsize=7.5, color=INK2, va="bottom", linespacing=1.3)
        ax.text(7.15, real[-1], f"{real[-1]:+.0f}%", fontsize=7.5, color=INK, va="center")
        ax.set_xlim(-3.4, 8.4); ax.set_ylim(-32, 22); ax.set_xticks([-3, 0, 1, 3, 5, 7])
        ax.tick_params(length=0)
        stats.append({"event": day, "label": label, "origin": str(origin.date()), "prob_up_h1": round(float(e["pre_h1_prob_up"]), 3), "consensus": e["pre_consensus"],
                      "p10_h1_pct": round(p10[1], 2), "p50_h1_pct": round(p50[1], 2), "p90_h1_pct": round(p90[1], 2),
                      "realized_h1_pct": round(real[1], 2), "realized_h7_pct": round(real[-1], 2),
                      "p10_h7_pct": round(p10[-1], 2), "p50_h7_pct": round(p50[-1], 2), "p90_h7_pct": round(p90[-1], 2),
                      "inside_band_h1": bool(p10[1] <= real[1] <= p90[1]), "inside_band_h7": bool(p10[-1] <= real[-1] <= p90[-1])})
    fig.supxlabel("sessions after the origin (0 = the close before the shock; 1 = the shock session)", fontsize=8.5, color=INK2, y=0.012)
    for ax in axes[:, 0]: ax.set_ylabel("% from origin close", fontsize=8)
    handles = [Patch(facecolor=BAND, alpha=0.15, label="forecast P10–P90 band, issued at the origin close"),
               Line2D([], [], color=BAND, ls="--", lw=1.6, label="forecast median"),
               Line2D([], [], color=INK, lw=2, marker="o", ms=4.5, label="realized close"),
               Line2D([], [], color=MUTED, lw=1.6, label="three sessions before the origin"),
               Line2D([], [], color=MUTED, ls=":", lw=1, label="first shock session")]
    fig.legend(handles=handles, loc="upper center", ncol=5, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.985))
    fig.suptitle("Seven-session forecast issued the session before each major Bitcoin decline, versus what happened (BTC/USD)", fontsize=11, color=INK, y=0.995, x=0.5, ha="center")
    fig.tight_layout(rect=(0, 0.025, 1, 0.955))
    fig.savefig(FIG / "fig15_btc_declines_fan.png", dpi=160, facecolor="#fcfcfb")
    fig.savefig(FIG / "fig15_btc_declines_fan.pdf", facecolor="#fcfcfb")
    (OUT / "btc_declines_fan_stats.json").write_text(json.dumps(stats, indent=1))
    df = pd.DataFrame(stats)
    print(df[["event", "origin", "prob_up_h1", "consensus", "realized_h1_pct", "p10_h1_pct", "realized_h7_pct", "inside_band_h1", "inside_band_h7"]].to_string(index=False))
    print(f"\nmean P(up) before: {df.prob_up_h1.mean():.2f} | consensus Sell: {(df.consensus=='Sell').sum()}/12 | inside band at h=1: {df.inside_band_h1.sum()}/12 | inside band at h=7: {df.inside_band_h7.sum()}/12 | mean realized h7: {df.realized_h7_pct.mean():+.1f}%")


if __name__ == "__main__":
    main()
