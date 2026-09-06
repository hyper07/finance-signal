"""Catalogue of significant Bitcoin decreases (single-session z <= -2.5) with attribution.

For every BTC/USD down-shock we record the same-session index and bond moves, the
FOMC/payroll calendar, the Benzinga crypto headline count and spike ratio (archive
coverage 2024-02 -> 2026-08), the most relevant headlines around the session, a
hand attribution for events before the archive (btc_manual_attributions.json,
with a confidence flag), the deployed model's forecast issued the day before and
the post-shock path. A factor label separates macro/systemic sessions from
crypto-specific ones. A lead-lag check asks whether headline spikes or index
drops the day before predicted the shock.

Outputs: output/btc_declines_catalogue.csv / .json, BTC_DECLINES.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import load_equity_daily  # noqa: E402
from scheduled_events import FOMC_DECISION_DAYS, payroll_days  # noqa: E402

OUT = HERE / "output"
NEWS_START = pd.Timestamp("2024-02-01")
CRYPTO_SYMS = {"BTCUSD", "BITO", "IBIT", "BITI", "MSTR", "COIN", "ETHUSD", "GBTC", "FBTC", "MARA", "RIOT"}
CRYPTO_WORDS = re.compile(r"bitcoin|crypto|btc|stablecoin|digital asset|ether", re.I)
DECLINE_WORDS = re.compile(r"plunge|crash|drop|sell ?-?off|tumble|liquidat|outflow|dip|bloodbath|slump|fall|nosedive|wipe|rout|freefall|low|escalat|tariff|yields jump|worst", re.I)
GENERIC = re.compile(r"^stock market today", re.I)   # pre-market futures notes; end-of-day wraps are explanatory
COMMENTARY = re.compile(r"schiff|kiyosaki|saylor|scorecard|which asset|brilliant|remember|only \d+ etfs|foresees|crushes|says|asks|polymarket|narrative|target", re.I)


def crypto_headlines() -> pd.DataFrame:
    rows = []
    with open(HERE.parent / "data" / "alpaca" / "news.jsonl") as fh:
        for line in fh:
            it = json.loads(line)
            syms = set(it.get("symbols") or [])
            h = it.get("headline", "")
            if syms & CRYPTO_SYMS or CRYPTO_WORDS.search(h):
                rows.append((pd.Timestamp(it["created_at"]).tz_convert(None), h, len(syms)))
    return pd.DataFrame(rows, columns=["ts", "headline", "nsym"]).sort_values("ts")


def rank_headlines(news: pd.DataFrame, day: pd.Timestamp) -> list[str]:
    """Headlines from the previous day through the next morning, most relevant first."""
    win = news[(news.ts >= day - pd.Timedelta(1, unit="D")) & (news.ts < day + pd.Timedelta(36, unit="h"))]
    scored = []
    for _, r in win.iterrows():
        h = r.headline
        s = 3 * bool(CRYPTO_WORDS.search(h[:60])) + 2 * bool(DECLINE_WORDS.search(h)) - 2 * (bool(GENERIC.search(h)) and not CRYPTO_WORDS.search(h[:60]))
        s -= max(0, r.nsym - 4) * 0.2
        s -= 3 * bool(COMMENTARY.search(h))
        s += 2 * bool(re.search(r"why|what is going on|liquidation|erased|below \$", h, re.I))
        s += 0.5 if r.ts.normalize() == day.normalize() else 0.0
        scored.append((s, h))
    return [h for _, h in sorted(scored, key=lambda x: -x[0])]


def main() -> None:
    days = pd.read_csv(OUT / "days_btc.csv", parse_dates=["date"]).set_index("date")
    ev = pd.read_csv(OUT / "events_btc.csv", parse_dates=["event_date"]).set_index("event_date")
    eq = load_equity_daily(); eq["date"] = pd.to_datetime(eq["date"])
    px = eq.pivot_table(index="date", columns="symbol", values="c"); rets = px.pct_change() * 100
    fomc = set(pd.to_datetime(FOMC_DECISION_DAYS))
    pay = set(payroll_days(str(days.index.min().date()), str(days.index.max().date())))
    manual = json.loads((HERE / "btc_manual_attributions.json").read_text())
    news = crypto_headlines()
    scale = 100 if days["ret"].abs().max() < 1 else 1

    def last(series: pd.Series, d: pd.Timestamp) -> float:
        s = series.loc[:d].dropna(); return float(s.iloc[-1]) if len(s) else np.nan

    rows = []
    for d, r in days[days["z"] <= -2.5].iterrows():
        e = ev.loc[d] if d in ev.index else pd.Series(dtype=float)
        spy_same = rets["SPY"].get(d, np.nan); spy_last = last(rets["SPY"], d); tlt_last = last(rets["TLT"], d); gld_last = last(rets["GLD"], d)
        cal = ("FOMC" if d in fomc else "") + (" payrolls" if d in pay else "")
        m = manual.get(str(d.date()), {})
        heads = rank_headlines(news, d) if d >= NEWS_START else []
        if m.get("type"):
            factor = m["type"]
        else:
            factor = "macro" if (spy_last <= -1.5 or cal.strip()) else "crypto"
        rows.append({
            "date": d.date(), "weekday": d.strftime("%a"), "ret_pct": round(r["ret"] * scale, 1), "z": round(r["z"], 1), "move3_pct": round(r["move3_pct"], 1),
            "spy_same_pct": None if pd.isna(spy_same) else round(spy_same, 2), "spy_last_pct": round(spy_last, 2), "tlt_last_pct": round(tlt_last, 2), "gld_last_pct": round(gld_last, 2),
            "calendar": cal.strip(), "news_count": None if pd.isna(r["news"]) else int(r["news"]), "news_ratio": None if pd.isna(r["news_ratio"]) else round(r["news_ratio"], 2),
            "news_ratio_prev": None if d - pd.Timedelta(1, unit="D") not in days.index or pd.isna(days.loc[d - pd.Timedelta(1, unit="D"), "news_ratio"]) else round(days.loc[d - pd.Timedelta(1, unit="D"), "news_ratio"], 2),
            "factor": factor, "cause": m.get("cause", "see archive headlines"), "attribution": ("manual, " + m["confidence"] + " confidence") if m else ("archive headlines" if heads else "none (before headline archive)"),
            "headlines": heads[:4],
            "pre_signal_3day": e.get("pre_signal_3day"), "pre_consensus": e.get("pre_consensus"), "pre_h1_prob_up": e.get("pre_h1_prob_up"),
            "pre_h1_band": None if pd.isna(e.get("pre_h1_p10_pct", np.nan)) else f"[{e['pre_h1_p10_pct']:+.1f}, {e['pre_h1_p90_pct']:+.1f}]",
            "pre_h1_covered": e.get("pre_h1_covered"), "pre_h1_surprise_z": e.get("pre_h1_surprise_z"),
            "post_1d_pct": e.get("post_ret_1d_pct"), "post_3d_pct": e.get("post_ret_3d_pct"), "post_7d_pct": e.get("post_ret_7d_pct"),
        })
    cat = pd.DataFrame(rows)
    cat.to_csv(OUT / "btc_declines_catalogue.csv", index=False)
    (OUT / "btc_declines_catalogue.json").write_text(json.dumps(rows, indent=1, default=str))

    # ---- lead-lag: did anything observable the day before flag the shock? ----
    shock = (days["z"] <= -2.5)
    nr_prev = days["news_ratio"].shift(1); spy_prev = rets["SPY"].reindex(days.index).ffill().shift(1)
    cov = days.index >= NEWS_START
    base_news = shock[cov].mean(); cond_news = shock[cov & (nr_prev >= 2)].mean(); n_news = int((cov & (nr_prev >= 2)).sum())
    base_all = shock.mean(); cond_spy = shock[spy_prev <= -1.5].mean(); n_spy = int((spy_prev <= -1.5).sum())
    same_day_spy = (cat["spy_last_pct"] <= -1.5).mean()
    lead = {"P(down-shock) all days": round(base_all, 4), "P(down-shock | SPY <= -1.5% previous session)": round(cond_spy, 4), "n SPY<=-1.5% days": n_spy,
            "P(down-shock) since 2024-02": round(base_news, 4), "P(down-shock | headline ratio >= 2 day before)": round(cond_news, 4), "n spike-days": n_news,
            "share of down-shocks with SPY <= -1.5% same/last session": round(same_day_spy, 3),
            "mean P(up) issued the day before": round(cat["pre_h1_prob_up"].astype(float).mean(), 3),
            "share with day-before consensus Sell": round((cat["pre_consensus"] == "Sell").mean(), 3),
            "share with day-before 3-day signal Short": round(cat["pre_signal_3day"].astype(str).str.contains("Short|-1").mean(), 3),
            "share covered by day-before 10-90 band": round(cat["pre_h1_covered"].astype(float).mean(), 3),
            "mean post 3d %": round(cat["post_3d_pct"].astype(float).mean(), 2), "mean post 7d %": round(cat["post_7d_pct"].astype(float).mean(), 2)}
    by = cat.groupby("factor").agg(n=("date", "size"), mean_ret=("ret_pct", "mean"), mean_spy=("spy_last_pct", "mean"), post7=("post_7d_pct", lambda s: pd.to_numeric(s).mean())).round(2)
    (OUT / "btc_declines_summary.json").write_text(json.dumps({"lead_lag": lead, "by_factor": by.reset_index().to_dict("records")}, indent=1, default=str))

    # ---- report ----
    L = ["# Significant Bitcoin decreases and what moved them", "",
         f"BTC/USD sessions with a standardized return $z\\le-2.5$ (return over the trailing 20-day SD), {days.index.min().date()} to {days.index.max().date()}: {len(cat)} sessions. "
         "Same-session S&P 500 (SPY), long Treasuries (TLT) and gold (GLD) returns use the last equity session on or before the crypto date. "
         "Headlines come from the Benzinga/Alpaca archive (coverage from 2024-02); earlier events carry hand attributions with a confidence flag. "
         "Factor: *macro* = the session is explained by a market-wide move or a scheduled release; *crypto* = an exchange, protocol, regulatory or flow event specific to crypto; *mixed* = both.", "",
         "## By factor", "", "| factor | sessions | mean BTC % | mean SPY % | mean BTC +7d % |", "|---|---|---|---|---|"]
    for _, b in by.reset_index().iterrows(): L.append(f"| {b['factor']} | {b['n']} | {b['mean_ret']:+.1f} | {b['mean_spy']:+.2f} | {b['post7']:+.1f} |")
    L += ["", "## Was there a leading signal?", ""] + [f"- {k}: {v}" for k, v in lead.items()] + ["",
          "## Catalogue", "", "| date | BTC % | z | 3d % | SPY % | calendar | factor | what happened | attribution | P(up), band day before | consensus | +1d / +3d / +7d % |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in cat.iterrows():
        what = r["cause"] if r["attribution"].startswith("manual") else (r["headlines"][0][:110] if r["headlines"] else r["cause"])
        pu = "" if pd.isna(r["pre_h1_prob_up"]) else f"{float(r['pre_h1_prob_up']):.2f}, {r['pre_h1_band']}"
        post = " / ".join("" if pd.isna(v) else f"{float(v):+.1f}" for v in (r["post_1d_pct"], r["post_3d_pct"], r["post_7d_pct"]))
        L.append(f"| {r['date']} ({r['weekday']}) | {r['ret_pct']:+.1f} | {r['z']} | {r['move3_pct']:+.1f} | {r['spy_last_pct']:+.2f} | {r['calendar']} | {r['factor']} | {what} | {r['attribution']} | {pu} | {r['pre_consensus'] or ''} | {post} |")
    L += ["", "## Archive headlines per event (2024-02 onward)", ""]
    for _, r in cat[cat["headlines"].map(len) > 0].iterrows():
        L.append(f"**{r['date']}** ({r['ret_pct']:+.1f}%, SPY {r['spy_last_pct']:+.2f}%, headline ratio {r['news_ratio']}): " + " | ".join(h[:130] for h in r["headlines"][:3]))
        L.append("")
    (HERE / "BTC_DECLINES.md").write_text("\n".join(L) + "\n")
    print(by.to_string()); print(json.dumps(lead, indent=1))
    print("\nwritten:", OUT / "btc_declines_catalogue.csv", HERE / "BTC_DECLINES.md")


if __name__ == "__main__":
    main()
