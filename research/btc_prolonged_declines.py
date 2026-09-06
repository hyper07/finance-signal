"""Prolonged Bitcoin declines: weeks-to-months legs, calendar quarters and half-years.

A 15% zig-zag segments BTC/USD closes into swings; every peak-to-trough leg of 20% or
more is a decline leg. For each leg: depth, length, how much of the fall came on
z<=-2.5 sessions versus ordinary sessions, the S&P 500 move over the same window,
the model's state across the leg (P(up) at 1 and 7 sessions, consensus, 3-day
signal, tactical exposure and the exposure-weighted return), the single-day
catalogue events inside it, headline themes from the archive (2024-02 onward) and a
hand-written regime narrative (btc_decline_regimes.json). Calendar quarters and
half-years get the same model statistics. A slow trend filter (100/200-day moving
average, cash when below) is benchmarked against the 7-session model across the
legs and the full sample, as the simplest 'quarterly layer'.

Outputs: output/btc_decline_legs.csv/.json, output/btc_decline_calendar.csv,
output/btc_trend_filter_benchmark.json, output/figures/fig16_btc_prolonged_declines.png
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import load_equity_daily  # noqa: E402
from btc_decline_catalogue import crypto_headlines, DECLINE_WORDS  # noqa: E402

OUT = HERE / "output"; FIG = OUT / "figures"
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
BTC_RED, BLUE = "#d62728", "#2a78d6"
THEMES = {"tariffs": r"tariff", "Fed / rates": r"\bfed\b|fomc|powell|rate[- ]hike|rate cut|yields|treasur", "ETF flows": r"etf", "hack / exchange": r"hack|exploit|bybit|exchange|ftx|binance",
          "liquidations": r"liquidat", "regulation": r"\bsec\b|regulat|lawsuit|ban\b", "macro sell-off": r"sell-?off|recession|carry|plunge|crash|rout|bloodbath", "geopolitics": r"iran|war|strike|china|greenland|russia"}


def zigzag_legs(c: pd.Series, rev: float = 0.15, depth: float = 0.20):
    swings, mode, ext = [], None, 0
    for i in range(1, len(c)):
        if mode is None:
            if c.iloc[i] >= c.iloc[ext] * (1 + rev): mode, ext = "up", i
            elif c.iloc[i] <= c.iloc[ext] * (1 - rev): mode, ext = "down", i
            continue
        if mode == "up":
            if c.iloc[i] > c.iloc[ext]: ext = i
            elif c.iloc[i] <= c.iloc[ext] * (1 - rev): swings.append(("peak", ext)); mode, ext = "down", i
        else:
            if c.iloc[i] < c.iloc[ext]: ext = i
            elif c.iloc[i] >= c.iloc[ext] * (1 + rev): swings.append(("trough", ext)); mode, ext = "up", i
    swings.append(("peak" if mode == "up" else "trough", ext))
    return [(c.index[i1], c.index[i2]) for (k1, i1), (k2, i2) in zip(swings, swings[1:]) if k1 == "peak" and k2 == "trough" and c.iloc[i2] / c.iloc[i1] - 1 <= -depth]


def model_state(org, h1, h7, seg_close, a, b) -> dict:
    o = org.loc[a:b]
    if not len(o): return {}
    f1, f7 = h1.loc[a:b], h7.loc[a:b]
    sig = o["strategy_signal"]; expo = o["current_tactical_pct"].fillna(0) / 100
    nxt = seg_close.pct_change().shift(-1).reindex(o.index)
    return {"origins": int(len(o)), "prob_up_h1": round(f1["prob_up"].mean(), 3), "prob_up_h7": round(f7["prob_up"].mean(), 3), "share_p50_h7_negative": round(float((f7["p50"] < 0).mean()), 3),
            "hit_h7": round(f7["hit"].mean(), 3), "share_consensus_sell": round(float((o["consensus_direction"] == "Sell").mean()), 3), "share_consensus_buy": round(float((o["consensus_direction"] == "Buy").mean()), 3),
            "share_signal_long": round(float((sig > 0).mean()), 3), "share_signal_short": round(float((sig < 0).mean()), 3), "mean_exposure_pct": round(float(expo.mean() * 100), 1),
            "exposure_weighted_ret_pct": round(float((np.prod(1 + (expo * nxt).dropna()) - 1) * 100), 1)}


def main() -> None:
    days = pd.read_csv(OUT / "days_btc.csv", parse_dates=["date"]).set_index("date"); c = days["close"]
    org = pd.read_csv(OUT / "origins_btc.csv", parse_dates=["origin"]).set_index("origin")
    fc = pd.read_csv(OUT / "forecasts_btc.csv", parse_dates=["origin"]); h1 = fc[fc.horizon == 1].set_index("origin"); h7 = fc[fc.horizon == 7].set_index("origin")
    eq = load_equity_daily(); eq["date"] = pd.to_datetime(eq["date"]); px = eq.pivot_table(index="date", columns="symbol", values="c")
    cat = pd.read_csv(OUT / "btc_declines_catalogue.csv", parse_dates=["date"])
    regimes = json.loads((HERE / "btc_decline_regimes.json").read_text())
    news = crypto_headlines()

    # ---- legs ----
    legs = []
    for a, b in zigzag_legs(c):
        seg = c.loc[a:b]; lr = np.log(seg).diff().dropna(); depth = seg.iloc[-1] / seg.iloc[0] - 1
        shocks = days.loc[a:b]; shocks = shocks[shocks["z"] <= -2.5]
        inside = cat[(cat.date >= a) & (cat.date <= b)]
        win = news[(news.ts >= a) & (news.ts <= b + pd.Timedelta(1, unit="D"))]; win = win[win.headline.str.contains(DECLINE_WORDS)]
        themes = {k: int(win.headline.str.contains(v, case=False, regex=True).sum()) for k, v in THEMES.items()} if len(win) else {}
        reg = regimes.get(str(a.date()), {})
        legs.append({"peak": str(a.date()), "trough": str(b.date()), "days": int((b - a).days), "depth_pct": round(depth * 100, 1), "peak_close": round(float(seg.iloc[0])), "trough_close": round(float(seg.iloc[-1])),
                     "shock_sessions": int(len(shocks)), "shock_share_of_fall": round(float(np.log1p(shocks["ret"]).sum() / lr.sum()), 2) if lr.sum() else None,
                     "spy_pct": round(float((px["SPY"].asof(b) / px["SPY"].asof(a) - 1) * 100), 1), "tlt_pct": round(float((px["TLT"].asof(b) / px["TLT"].asof(a) - 1) * 100), 1),
                     "catalogue_events": [f"{d.date()} {r:+.1f}% {cz[:60]}" for d, r, cz in zip(inside.date, inside.ret_pct, inside.cause)],
                     "headline_themes": dict(sorted(themes.items(), key=lambda kv: -kv[1])[:4]) if themes else None, "decline_headlines": int(len(win)) if len(win) else None,
                     "narrative": reg.get("narrative", ""), "narrative_confidence": reg.get("confidence", ""), **model_state(org, h1, h7, seg, a, b)})
    pd.DataFrame(legs).to_csv(OUT / "btc_decline_legs.csv", index=False); (OUT / "btc_decline_legs.json").write_text(json.dumps(legs, indent=1))

    # ---- calendar quarters and half-years ----
    rows = []
    for label, freq in (("quarter", "Q"), ("half-year", "2Q")):
        for period, seg in c.groupby(c.index.to_period(freq) if freq == "Q" else ((c.index.year.astype(str) + "H" + ((c.index.month > 6) + 1).astype(str)))):
            a, b = seg.index[0], seg.index[-1]; prev = c.loc[:a].iloc[-2] if len(c.loc[:a]) > 1 else seg.iloc[0]
            st = model_state(org, h1, h7, seg, a, b)
            rows.append({"period_type": label, "period": str(period), "ret_pct": round((seg.iloc[-1] / prev - 1) * 100, 1), "max_drawdown_pct": round(((seg / seg.cummax()) - 1).min() * 100, 1),
                         "shock_sessions": int((days.loc[a:b, "z"] <= -2.5).sum()), "spy_pct": round(float((px["SPY"].asof(b) / px["SPY"].asof(a) - 1) * 100), 1),
                         "prob_up_h7": st.get("prob_up_h7"), "share_signal_long": st.get("share_signal_long"), "exposure_weighted_ret_pct": st.get("exposure_weighted_ret_pct")})
    cal = pd.DataFrame(rows); cal.to_csv(OUT / "btc_decline_calendar.csv", index=False)

    # ---- slow regime layer benchmark: trend filters vs the 7-session model's exposure ----
    ret = c.pct_change(); start = org.index.min()
    bench = {}
    for n in (50, 100, 200):
        ma = c.rolling(n).mean(); expo = (c.shift(1) > ma.shift(1)).astype(float)
        r = (expo * ret).loc[start:]; nav = (1 + r).cumprod()
        per_leg = {l["peak"]: round(float((1 + (expo * ret).loc[l["peak"]:l["trough"]]).prod() * 100 - 100), 1) for l in legs if pd.Timestamp(l["peak"]) >= start}
        bench[f"MA{n} filter (cash below)"] = {"cagr_pct": round(float(nav.iloc[-1] ** (365 / len(nav)) * 100 - 100), 1), "max_drawdown_pct": round(float(((nav / nav.cummax()) - 1).min() * 100), 1),
                                              "time_in_market": round(float(expo.loc[start:].mean()), 2), "switches": int((expo.diff().abs() > 0).loc[start:].sum()), "return_in_each_leg_pct": per_leg}
    expo_m = (org["current_tactical_pct"].fillna(0) / 100).reindex(c.index).ffill().shift(1).fillna(0)
    r = (expo_m * ret).loc[start:]; nav = (1 + r).cumprod(); bh = (1 + ret.loc[start:]).cumprod()
    bench["7-session model exposure"] = {"cagr_pct": round(float(nav.iloc[-1] ** (365 / len(nav)) * 100 - 100), 1), "max_drawdown_pct": round(float(((nav / nav.cummax()) - 1).min() * 100), 1), "time_in_market": round(float(expo_m.loc[start:].mean()), 2),
                                         "return_in_each_leg_pct": {l["peak"]: l.get("exposure_weighted_ret_pct") for l in legs if pd.Timestamp(l["peak"]) >= start}}
    bench["buy and hold"] = {"cagr_pct": round(float(bh.iloc[-1] ** (365 / len(bh)) * 100 - 100), 1), "max_drawdown_pct": round(float(((bh / bh.cummax()) - 1).min() * 100), 1), "time_in_market": 1.0,
                             "return_in_each_leg_pct": {l["peak"]: l["depth_pct"] for l in legs if pd.Timestamp(l["peak"]) >= start}}
    (OUT / "btc_trend_filter_benchmark.json").write_text(json.dumps(bench, indent=1))

    # ---- figure ----
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    fig, axes = plt.subplots(3, 1, figsize=(13.5, 9.6), sharex=True, gridspec_kw={"height_ratios": [2.4, 1.2, 1.0]})
    ax = axes[0]; ax.set_yscale("log"); ax.plot(c.index, c, color=INK, lw=1.4, zorder=3)
    for l in legs:
        a, b = pd.Timestamp(l["peak"]), pd.Timestamp(l["trough"])
        ax.axvspan(a, b, color=BTC_RED, alpha=0.13, lw=0, zorder=1)
        if l["depth_pct"] <= -25 or l["days"] >= 60:
            ax.text(a + (b - a) / 2, l["peak_close"] * 1.07, f"{l['depth_pct']:+.0f}%\n{l['days']} d", ha="center", va="bottom", fontsize=7.5, color=INK2)
    for y in (20000, 50000, 100000): ax.axhline(y, color=GRID, lw=0.8, zorder=0)
    ax.set_ylim(13000, 190000); ax.set_yticks([20000, 30000, 50000, 70000, 100000, 150000]); ax.set_yticklabels(["20k", "30k", "50k", "70k", "100k", "150k"])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); ax.set_ylabel("BTC/USD close (log)")
    ax.set_title("Bitcoin decline legs of 20% or more (shaded), what the model believed during them, and calendar-quarter returns", loc="left", fontsize=10.5, pad=8)
    ax.text(0.995, 0.03, "shading: peak-to-trough legs from a 15% swing filter; labels for legs deeper than 25% or longer than 60 days", transform=ax.transAxes, ha="right", fontsize=7.5, color=MUTED)
    ax2 = axes[1]
    pu = h7["prob_up"].rolling(20, min_periods=10).mean(); lg = (org["strategy_signal"] > 0).astype(float).rolling(20, min_periods=10).mean()
    for l in legs: ax2.axvspan(pd.Timestamp(l["peak"]), pd.Timestamp(l["trough"]), color=BTC_RED, alpha=0.13, lw=0, zorder=1)
    ax2.axhline(0.5, color=AXIS, lw=0.8, zorder=0)
    ax2.plot(pu.index, pu, color=BLUE, lw=1.8, zorder=3, label="P(up) at seven sessions, 20-day mean")
    ax2.plot(lg.index, lg, color=INK, lw=1.4, zorder=2, label="share of sessions the 3-day signal was Long, 20-day mean")
    ax2.set_ylim(0, 1.3); ax2.set_yticks([0, 0.5, 1]); ax2.set_ylabel("model state"); ax2.legend(loc="upper left", fontsize=7.5, frameon=False, ncol=2, bbox_to_anchor=(0, 1.02))
    ax3 = axes[2]
    q = c.resample("QE").last(); qr = (q / q.shift(1) - 1).dropna() * 100
    colors = [BTC_RED if v <= -20 else ("#e8a5a5" if v < 0 else "#9ec5f4") for v in qr]
    ax3.bar(qr.index - pd.Timedelta(45, unit="D"), qr.values, width=80, color=colors, zorder=2)
    ax3.axhline(0, color=AXIS, lw=0.8, zorder=0)
    for d, v in qr.items():
        if v <= -20: ax3.text(d - pd.Timedelta(45, unit="D"), v - 3, f"{v:+.0f}%", ha="center", va="top", fontsize=7.5, color=INK2)
    ax3.set_ylabel("quarter return, %"); ax3.set_ylim(-70, 95); ax3.set_yticks([-50, 0, 50])
    ax3.text(0.995, 0.04, f"last bar: {qr.index[-1].to_period('Q')} to {c.index.max().date()} (partial)", transform=ax3.transAxes, ha="right", fontsize=7.5, color=MUTED)
    ax3.legend(handles=[Patch(color=BTC_RED, label="quarter of −20% or worse"), Patch(color="#e8a5a5", label="other negative quarter"), Patch(color="#9ec5f4", label="positive quarter")], loc="upper left", fontsize=7.5, frameon=False, ncol=3)
    for a_ in axes:
        a_.tick_params(length=0); a_.grid(False)
    axes[-1].set_xlim(c.index.min(), c.index.max())
    fig.tight_layout()
    fig.savefig(FIG / "fig16_btc_prolonged_declines.png", dpi=160, facecolor=SURF)
    # ---- console summary ----
    show = pd.DataFrame(legs)[["peak", "trough", "days", "depth_pct", "shock_sessions", "shock_share_of_fall", "spy_pct", "prob_up_h7", "share_signal_long", "exposure_weighted_ret_pct"]]
    pd.set_option("display.width", 240); print(show.to_string(index=False))
    print("\nbenchmark:", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "return_in_each_leg_pct"} for k, v in bench.items()}, indent=1))
    print("\nquarters <= -20%:", cal[(cal.period_type == "quarter") & (cal.ret_pct <= -20)][["period", "ret_pct", "spy_pct", "prob_up_h7", "share_signal_long", "exposure_weighted_ret_pct"]].to_string(index=False))
    print("\nhalf-years <= -20%:", cal[(cal.period_type == "half-year") & (cal.ret_pct <= -20)][["period", "ret_pct", "spy_pct", "prob_up_h7", "share_signal_long", "exposure_weighted_ret_pct"]].to_string(index=False))
    for l in legs:
        if l["headline_themes"]: print(l["peak"], "→", l["trough"], "themes:", l["headline_themes"], "| decline headlines:", l["decline_headlines"])


if __name__ == "__main__":
    main()
