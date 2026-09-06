"""Swing legs (up and down) across asset types: Bitcoin, the S&P 500 (SPY), long
Treasuries (TLT) and four single stocks.

A zig-zag with a volatility-scaled reversal threshold (a quarter of annualized
volatility, floored at 5% and capped at 15%) segments each close series into
swings; a leg counts when its move exceeds 4/3 of the threshold. For every leg:
depth, length, the share of the move that came on shock sessions (|z| >= 2.5 in the
leg's direction), the S&P 500 and TLT over the same window, the model's state where
the engine runs on the asset (mean P(up) at 7 sessions, consensus, 3-day signal,
exposure-weighted return), headline themes from the Benzinga archive (2024-02 on)
and a hand-written regime narrative for the largest legs (swing_leg_regimes.json).
Also: calendar quarter/half-year tables and a 100/200-day trend-filter yardstick.

Outputs: output/swing_legs.csv/.json, output/swing_legs_calendar.csv,
output/swing_legs_benchmark.json, output/figures/fig17_swing_legs_by_asset.png,
output/figures/fig18_leg_anatomy.png, SWING_LEGS.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import load_equity_daily, load_stock_snapshot  # noqa: E402

OUT = HERE / "output"; FIG = OUT / "figures"
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
DOWN, UP = "#d62728", "#2a78d6"
ASSETS = [  # key, label, type, model key (None = engine does not run on it)
    ("BTC", "BTC/USD", "crypto", "btc"), ("SPY", "S&P 500 (SPY)", "index", "spy"), ("TLT", "20y+ Treasuries (TLT)", "bond", None),
    ("AAPL", "Apple", "stock", "aapl"), ("MSFT", "Microsoft", "stock", "msft"), ("TSLA", "Tesla", "stock", "tsla"), ("NVDA", "Nvidia", "stock", "nvda"),
]
NEWS_START = pd.Timestamp("2024-02-01")
THEMES = {"tariffs": r"tariff", "Fed / rates": r"\bfed\b|fomc|powell|rate[- ]hike|rate cut|yields|treasur|inflation|cpi", "earnings / guidance": r"earnings|guidance|revenue|quarter|q[1-4]\b",
          "AI / product": r"\bai\b|chip|gpu|iphone|cloud|copilot|robotaxi|model", "regulation / legal": r"\bsec\b|regulat|lawsuit|antitrust|\bban\b|probe|doj", "flows": r"etf|outflow|inflow|buyback",
          "macro sell-off": r"sell-?off|recession|plunge|crash|rout|bloodbath|tumble", "geopolitics": r"iran|war|strike|china|russia|greenland", "management": r"musk|ceo|altman|nadella|cook|huang"}
DECLINE_UP = re.compile(r"plunge|crash|drop|sell ?-?off|tumble|slump|fall|rout|surge|soar|rally|jump|record|high|rebound|gain", re.I)


def load_prices() -> dict[str, pd.Series]:
    eq = load_equity_daily(); eq["date"] = pd.to_datetime(eq["date"]); px = eq.pivot_table(index="date", columns="symbol", values="c")
    st = load_stock_snapshot(); st["date"] = pd.to_datetime(st["date"]); sp = st.pivot_table(index="date", columns="symbol", values="c")
    btc = pd.read_csv(OUT / "days_btc.csv", parse_dates=["date"]).set_index("date")["close"]
    return {"BTC": btc, "SPY": px["SPY"].dropna(), "TLT": px["TLT"].dropna(), "GLD": px["GLD"].dropna(), **{s: sp[s].dropna() for s in ("AAPL", "MSFT", "TSLA", "NVDA")}}


def load_model(key):
    if key is None: return None
    org = pd.read_csv(OUT / f"origins_{key}.csv", parse_dates=["origin"]).set_index("origin")
    fc = pd.read_csv(OUT / f"forecasts_{key}.csv", parse_dates=["origin"]); h7 = fc[fc.horizon == 7].set_index("origin")
    return org, h7


def zigzag(c: pd.Series, rev: float):
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
    return [(c.index[i1], c.index[i2], "down" if k1 == "peak" else "up") for (k1, i1), (k2, i2) in zip(swings, swings[1:])]


def headlines(asset: str, sym_tags: set[str], words: re.Pattern):
    rows = []
    with open(HERE.parent / "data" / "alpaca" / "news.jsonl") as fh:
        for line in fh:
            it = json.loads(line); h = it.get("headline", ""); syms = set(it.get("symbols") or [])
            if syms & sym_tags or (words and words.search(h)): rows.append((pd.Timestamp(it["created_at"]).tz_convert(None), h))
    return pd.DataFrame(rows, columns=["ts", "headline"])


def model_state(model, c: pd.Series, a, b) -> dict:
    if model is None: return {}
    org, h7 = model; o = org.loc[a:b]
    if len(o) < 3: return {}
    f7 = h7.loc[a:b]; sig = o["strategy_signal"]; expo = o["current_tactical_pct"].fillna(0) / 100
    nxt = c.pct_change().shift(-1).reindex(o.index)
    return {"origins": int(len(o)), "prob_up_h7": round(float(f7["prob_up"].mean()), 3), "share_p50_h7_negative": round(float((f7["p50"] < 0).mean()), 3),
            "share_consensus_sell": round(float((o["consensus_direction"] == "Sell").mean()), 3), "share_consensus_buy": round(float((o["consensus_direction"] == "Buy").mean()), 3),
            "share_signal_long": round(float((sig > 0).mean()), 3), "mean_exposure_pct": round(float(expo.mean() * 100), 1),
            "exposure_weighted_ret_pct": round(float((np.prod(1 + (expo * nxt).dropna()) - 1) * 100), 1)}


def main() -> None:
    prices = load_prices(); regimes = json.loads((HERE / "swing_leg_regimes.json").read_text()) if (HERE / "swing_leg_regimes.json").exists() else {}
    all_legs, cal_rows, bench, thresholds = [], [], {}, {}
    for key, label, typ, mkey in ASSETS:
        c = prices[key]; r = c.pct_change(); vol = float(r.std() * np.sqrt(365 if typ == "crypto" else 252))
        rev = float(np.clip(0.25 * vol, 0.05, 0.15)); depth_min = 4 / 3 * rev; thresholds[key] = {"annual_vol": round(vol, 3), "reversal": round(rev, 3), "min_leg": round(depth_min, 3)}
        z = (r / r.rolling(20).std().shift(1))
        model = load_model(mkey)
        tags = {"BTC": {"BTCUSD", "BITO", "IBIT", "COIN", "MSTR"}, "SPY": {"SPY", "QQQ", "DIA"}, "TLT": {"TLT"}}.get(key, {key})
        words = {"BTC": re.compile(r"bitcoin|crypto|btc", re.I), "SPY": re.compile(r"stock market today|what's moving markets|s&p 500|wall street", re.I),
                 "TLT": re.compile(r"treasur|yield|\bfed\b|fomc|inflation|cpi|bond", re.I)}.get(key)
        news = headlines(key, tags, words) if (words or key in ("AAPL", "MSFT", "TSLA", "NVDA")) else pd.DataFrame(columns=["ts", "headline"])
        for a, b, direction in zigzag(c, rev):
            move = c.loc[b] / c.loc[a] - 1
            if abs(move) < depth_min: continue
            seg = c.loc[a:b]; lr = np.log(seg).diff().dropna(); zz = z.loc[a:b]
            shocks = lr[(zz.reindex(lr.index) <= -2.5) if direction == "down" else (zz.reindex(lr.index) >= 2.5)]
            win = news[(news.ts >= a) & (news.ts <= b + pd.Timedelta(1, unit="D"))] if len(news) else news
            win = win[win.headline.str.contains(DECLINE_UP)] if len(win) else win
            themes = {k: int(win.headline.str.contains(v, case=False, regex=True).sum()) for k, v in THEMES.items()} if len(win) else {}
            themes = {k: v for k, v in sorted(themes.items(), key=lambda kv: -kv[1])[:3] if v} if themes else None
            reg = regimes.get(f"{key}|{a.date()}", {})
            leg = {"asset": key, "label": label, "type": typ, "direction": direction, "start": str(a.date()), "end": str(b.date()), "days": int((b - a).days), "move_pct": round(move * 100, 1),
                   "shock_sessions": int(len(shocks)), "shock_share_of_move": round(float(shocks.sum() / lr.sum()), 2) if lr.sum() else None,
                   "spy_pct": round(float((prices["SPY"].asof(b) / prices["SPY"].asof(a) - 1) * 100), 1) if a >= prices["SPY"].index.min() else None,
                   "tlt_pct": round(float((prices["TLT"].asof(b) / prices["TLT"].asof(a) - 1) * 100), 1) if a >= prices["TLT"].index.min() else None,
                   "headline_themes": themes, "narrative": reg.get("narrative", ""), "narrative_confidence": reg.get("confidence", ""), **model_state(model, c, a, b)}
            all_legs.append(leg)
        # calendar
        for ptype, grp in (("quarter", c.index.to_period("Q").astype(str)), ("half-year", c.index.year.astype(str) + "H" + ((c.index.month > 6) + 1).astype(str))):
            for period, seg in c.groupby(grp):
                a, b = seg.index[0], seg.index[-1]; prev = c.loc[:a].iloc[-2] if len(c.loc[:a]) > 1 else seg.iloc[0]
                st = model_state(model, c, a, b)
                cal_rows.append({"asset": key, "period_type": ptype, "period": period, "ret_pct": round((seg.iloc[-1] / prev - 1) * 100, 1), "max_drawdown_pct": round(((seg / seg.cummax()) - 1).min() * 100, 1),
                                 "prob_up_h7": st.get("prob_up_h7"), "share_signal_long": st.get("share_signal_long"), "exposure_weighted_ret_pct": st.get("exposure_weighted_ret_pct")})
        # trend-filter yardstick
        start = model[0].index.min() if model else c.index[250]
        res = {}
        for n in (100, 200):
            ma = c.rolling(n).mean(); expo = (c.shift(1) > ma.shift(1)).astype(float); nav = (1 + (expo * r).loc[start:]).cumprod()
            res[f"MA{n}"] = {"cagr_pct": round(float(nav.iloc[-1] ** ((365 if typ == "crypto" else 252) / len(nav)) * 100 - 100), 1), "max_drawdown_pct": round(float(((nav / nav.cummax()) - 1).min() * 100), 1), "time_in_market": round(float(expo.loc[start:].mean()), 2)}
        if model:
            expo_m = (model[0]["current_tactical_pct"].fillna(0) / 100).reindex(c.index).ffill().shift(1).fillna(0); nav = (1 + (expo_m * r).loc[start:]).cumprod()
            res["model exposure"] = {"cagr_pct": round(float(nav.iloc[-1] ** ((365 if typ == "crypto" else 252) / len(nav)) * 100 - 100), 1), "max_drawdown_pct": round(float(((nav / nav.cummax()) - 1).min() * 100), 1), "time_in_market": round(float(expo_m.loc[start:].mean()), 2)}
        bh = (1 + r.loc[start:]).cumprod(); res["buy and hold"] = {"cagr_pct": round(float(bh.iloc[-1] ** ((365 if typ == "crypto" else 252) / len(bh)) * 100 - 100), 1), "max_drawdown_pct": round(float(((bh / bh.cummax()) - 1).min() * 100), 1), "time_in_market": 1.0}
        bench[key] = {"from": str(pd.Timestamp(start).date()), **res}
    legs = pd.DataFrame(all_legs); legs.to_csv(OUT / "swing_legs.csv", index=False); (OUT / "swing_legs.json").write_text(json.dumps(all_legs, indent=1))
    pd.DataFrame(cal_rows).to_csv(OUT / "swing_legs_calendar.csv", index=False); (OUT / "swing_legs_benchmark.json").write_text(json.dumps({"thresholds": thresholds, "benchmark": bench}, indent=1))

    # ---- figure 17: price with legs, one row per asset ----
    plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    fig, axes = plt.subplots(len(ASSETS), 1, figsize=(13.5, 14), sharex=True)
    for ax, (key, label, typ, mkey) in zip(axes, ASSETS):
        c = prices[key]; ax.set_yscale("log"); ax.plot(c.index, c, color=INK, lw=1.1, zorder=3)
        for l in [x for x in all_legs if x["asset"] == key]:
            a, b = pd.Timestamp(l["start"]), pd.Timestamp(l["end"]); big = abs(l["move_pct"]) >= 2.5 * thresholds[key]["min_leg"] * 100
            ax.axvspan(a, b, color=DOWN if l["direction"] == "down" else UP, alpha=0.13 if big else 0.07, lw=0, zorder=1)
            if big and l["direction"] == "down" and a in c.index: ax.text(a + (b - a) / 2, c.loc[a] * 1.05, f"{l['move_pct']:+.0f}%", ha="center", va="bottom", fontsize=7, color=INK2)
        ax.set_ylim(c.min() * 0.85, c.max() * 1.45); ax.yaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10, subs=(1.0, 2.0, 5.0), numticks=12))
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter()); ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.set_ylabel(label, fontsize=8); ax.tick_params(length=0)
        th = thresholds[key]; ax.text(0.005, 0.9, f"reversal {th['reversal']:.0%}, leg ≥ {th['min_leg']:.0%}; deep down legs labelled", transform=ax.transAxes, fontsize=7, color=MUTED)
    axes[0].set_title("Swing legs by asset: down legs red, up legs blue (volatility-scaled thresholds; stocks from 2010, index and bonds from 2016, Bitcoin from 2021)", loc="left", fontsize=10, pad=8)
    axes[0].legend(handles=[Patch(color=DOWN, alpha=0.3, label="down leg"), Patch(color=UP, alpha=0.3, label="up leg"), Line2D([], [], color=INK, lw=1.1, label="adjusted close (log)")], loc="center left", ncol=1, fontsize=8, frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "fig17_swing_legs_by_asset.png", dpi=150, facecolor=SURF); plt.close(fig)

    # ---- figure 18: anatomy — shock share of the move, and what the model captured ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    order = [k for k, *_ in ASSETS]; ypos = {k: i for i, k in enumerate(order)}
    ax = axes[0]
    for l in all_legs:
        if l["shock_share_of_move"] is None: continue
        y = ypos[l["asset"]] + (0.18 if l["direction"] == "up" else -0.18)
        ax.scatter(np.clip(l["shock_share_of_move"], -0.1, 1.1), y, s=18 + 1.4 * min(abs(l["move_pct"]), 100), color=UP if l["direction"] == "up" else DOWN, alpha=0.55, edgecolor=SURF, lw=0.8, zorder=3)
    ax.axvline(0.5, color=AXIS, lw=0.8, zorder=0); ax.set_yticks(range(len(order))); ax.set_yticklabels([lab for _, lab, *_ in ASSETS]); ax.invert_yaxis()
    ax.set_xlim(-0.12, 1.12); ax.set_xlabel("share of the leg's log move that came on |z| ≥ 2.5 sessions (dot size = leg size, capped)"); ax.set_title("How much of each leg happened on shock sessions", loc="left", fontsize=9.5)
    ax.tick_params(length=0)
    ax = axes[1]
    for l in all_legs:
        if l.get("exposure_weighted_ret_pct") is None or l["direction"] != "down": continue
        cap = l["exposure_weighted_ret_pct"] / l["move_pct"]
        ax.scatter(np.clip(cap, -0.3, 1.3), ypos[l["asset"]], s=18 + 1.4 * min(abs(l["move_pct"]), 100), color=DOWN, alpha=0.55, edgecolor=SURF, lw=0.8, zorder=3)
    ax.axvline(1, color=AXIS, lw=0.8, zorder=0); ax.axvline(0, color=AXIS, lw=0.8, zorder=0); ax.set_yticks(range(len(order))); ax.set_yticklabels([lab if k != "TLT" else lab + " (no engine)" for k, lab, *_ in ASSETS]); ax.invert_yaxis()
    ax.set_xlim(-0.35, 1.35); ax.set_xlabel("share of the down leg captured by the model's own exposure (1 = all, 0 = none)"); ax.set_title("What the model's exposure captured in down legs", loc="left", fontsize=9.5)
    ax.tick_params(length=0)
    fig.legend(handles=[Line2D([], [], marker="o", ls="", color=DOWN, alpha=0.6, label="down leg"), Line2D([], [], marker="o", ls="", color=UP, alpha=0.6, label="up leg")], loc="upper right", ncol=2, fontsize=8, frameon=False, bbox_to_anchor=(0.99, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(FIG / "fig18_leg_anatomy.png", dpi=160, facecolor=SURF); plt.close(fig)

    # ---- console ----
    pd.set_option("display.width", 250)
    print("thresholds:", json.dumps(thresholds))
    for key, *_ in ASSETS:
        sub = legs[legs.asset == key]
        print(f"\n=== {key}: {len(sub)} legs ({(sub.direction=='down').sum()} down / {(sub.direction=='up').sum()} up) ===")
        cols = ["direction", "start", "end", "days", "move_pct", "shock_sessions", "shock_share_of_move", "spy_pct", "prob_up_h7", "share_signal_long", "exposure_weighted_ret_pct"]
        print(sub.sort_values("move_pct")[[c for c in cols if c in sub]].head(8).to_string(index=False))
    print("\nbenchmark:", json.dumps(bench, indent=0)[:1800])


if __name__ == "__main__":
    main()
