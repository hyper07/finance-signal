"""Catalogue of single-stock shock days with news attribution.

For every |z| >= 2.5 session of AAPL, MSFT, TSLA and NVDA the event is classified,
in priority order, as

  earnings        the session is the reaction session to a quarterly report
                  (report after the close -> next session), or the session after
  market-wide     SPY or QQQ moved |z| >= 2.0 in the same direction that day
  idiosyncratic   otherwise: company-specific news

and joined with (a) the ticker-tagged Benzinga headlines from the Alpaca archive
(2024-02 -> 2026-08) published from the prior close to the event close, (b) manual
attributions for earlier events looked up by hand (manual_attributions.json), and
(c) the deployed forecaster's behaviour around the event from events_<key>.csv.

Outputs: stock_events_catalogue.csv / .json, STOCK_EVENTS.md (report),
stock_events_by_category.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ALPACA_DIR, OUTPUT_DIR  # noqa: E402

HERE = Path(__file__).resolve().parent
STOCKS = {"aapl": "AAPL", "msft": "MSFT", "tsla": "TSLA", "nvda": "NVDA"}
MARKET_Z = 2.0
NEWS_START = pd.Timestamp("2024-02-01")


def market_z() -> pd.DataFrame:
    """Same-day standardized moves of SPY and QQQ (tech names need the tech index too)."""
    out = {}
    for sym in ("spy", "qqq"):
        c = pd.read_csv(OUTPUT_DIR / f"{sym}_yf_snapshot.csv", parse_dates=["date"]).set_index("date")["c"].astype(float)
        r = c.pct_change()
        out[f"{sym}_z"] = r / r.rolling(20).std(ddof=0).shift(1)
    return pd.DataFrame(out)


def earnings_sessions(symbol: str, index: pd.DatetimeIndex) -> set[pd.Timestamp]:
    table = pd.read_csv(OUTPUT_DIR / "earnings_dates.csv")
    out = set()
    for _, row in table[table["symbol"] == symbol].iterrows():
        ts = pd.Timestamp(row["report_datetime_ny"]).normalize()
        pos = index.searchsorted(ts, side="right" if row["after_close"] else "left")
        if pos < len(index):
            out.add(index[pos])
    return out


def headlines_by_ticker() -> dict[str, list[tuple[pd.Timestamp, str, str]]]:
    out: dict[str, list] = {s: [] for s in STOCKS.values()}
    with open(ALPACA_DIR / "news.jsonl") as handle:
        for line in handle:
            item = json.loads(line)
            syms = set(item.get("symbols", []))
            hit = syms & set(STOCKS.values())
            if not hit:
                continue
            ts = pd.Timestamp(item["created_at"]).tz_convert("America/New_York").tz_localize(None)
            for s in hit:
                out[s].append((ts, item.get("headline", ""), item.get("source", ""), len(syms)))
    for s in out:
        out[s].sort()
    return out


COMPANY = {"AAPL": ("apple", "iphone", "cupertino"), "MSFT": ("microsoft", "azure", "nadella"),
           "TSLA": ("tesla", "musk"), "NVDA": ("nvidia", "jensen", "huang")}
MOVE_WORDS = re.compile(r"surge|jump|soar|rall|climb|gain|record|beat|guidance|upgrade|target|deal|order|announce")
GENERIC = re.compile(r"stock market today|market clubhouse|morning memo|futures|s&p 500|nasdaq 100|dow jones|magnificent 7|redditor|etf|what's driving|10 stocks moving|most-searched")


def headlines_for(symbol: str, day: pd.Timestamp, prev_day: pd.Timestamp, news: dict) -> list[str]:
    """Headlines from the prior close to the event close, most relevant first.

    Benzinga tags broad market posts with every mega-cap ticker, so rank by:
    company name in the headline (+3), few tickers tagged (-1 per 5 beyond 3),
    move/announcement words (+1), and recency within the window (tie-break).
    """
    lo = prev_day + pd.Timedelta(16, unit="h")
    hi = day + pd.Timedelta(16, unit="h")
    scored = []
    for ts, h, _, n_sym in news.get(symbol, []):
        if not (lo <= ts <= hi):
            continue
        text = h.lower()
        early = any(w in text[:45] for w in COMPANY[symbol])
        anywhere = any(w in text for w in COMPANY[symbol])
        score = (4 if early else 2 if anywhere else 0) - max(0, (n_sym - 3) // 5) + (1 if MOVE_WORDS.search(text) else 0)
        if GENERIC.search(text) and not early:
            score -= 3
        scored.append((-score, -ts.value, h))
    return [h for _, _, h in sorted(scored)]


def company_named(symbol: str, headline: str | None, early: bool = True) -> bool:
    """True when the company is the subject of the headline (named in its first 45 characters)."""
    if not headline:
        return False
    text = headline.lower()[:45] if early else headline.lower()
    return any(w in text for w in COMPANY[symbol])


def main() -> None:
    spy_z = market_z()
    news = headlines_by_ticker()
    manual_path = HERE / "manual_attributions.json"
    manual = json.loads(manual_path.read_text()) if manual_path.exists() else {}
    rows = []
    for key, symbol in STOCKS.items():
        days = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
        events = pd.read_csv(OUTPUT_DIR / f"events_{key}.csv", parse_dates=["event_date"])
        idx = days.index
        earn = earnings_sessions(symbol, idx)
        earn_next = {idx[idx.get_loc(d) + 1] for d in earn if idx.get_loc(d) + 1 < len(idx)}
        for _, ev in events.iterrows():
            d = ev["event_date"]
            pos = idx.get_loc(d)
            prev = idx[pos - 1]
            mz = float(spy_z["spy_z"].get(d, np.nan))
            qz = float(spy_z["qqq_z"].get(d, np.nan))
            same_sign_market = any(np.isfinite(v) and abs(v) >= MARKET_Z and np.sign(v) == np.sign(ev["ret_pct"]) for v in (mz, qz))
            if d in earn:
                category = "earnings"
            elif d in earn_next:
                category = "earnings+1"
            elif same_sign_market:
                category = "market-wide"
            else:
                category = "idiosyncratic"
            local = headlines_for(symbol, d, prev, news) if d >= NEWS_START else []
            man = manual.get(f"{symbol}:{d.date().isoformat()}")
            rows.append({
                "symbol": symbol, "date": d.date().isoformat(), "direction": ev["direction"], "ret_pct": ev["ret_pct"], "z": ev["z"],
                "spy_z_same_day": round(mz, 2) if np.isfinite(mz) else None, "qqq_z_same_day": round(qz, 2) if np.isfinite(qz) else None, "category": category,
                "news_covered": bool(d >= NEWS_START), "headline_count": len(local),
                "headlines": local[:6],
                "attribution": (man["what"] if man
                                else (("earnings report" + (f" — {local[0]}" if local and company_named(symbol, local[0]) else "")) if category.startswith("earnings")
                                      else (local[0] if local and (company_named(symbol, local[0]) or category != "market-wide")
                                            else ("market-wide move" + (f" — {local[0]}" if local else "") if category == "market-wide" else None)))),
                "attribution_source": (man["source"] if man
                                       else ("earnings calendar" + ("; Alpaca/Benzinga archive" if local else "") if category.startswith("earnings")
                                             else ("Alpaca/Benzinga archive" if local else ("SPY/QQQ same-day z" if category == "market-wide" else None)))),
                "pre_h1_prob_up": ev["pre_h1_prob_up"], "pre_h1_band_pct": [ev["pre_h1_p10_pct"], ev["pre_h1_p50_pct"], ev["pre_h1_p90_pct"]],
                "pre_h1_hit": int(ev["pre_h1_hit"]), "pre_h1_covered": int(ev["pre_h1_covered"]), "pre_h1_surprise_z": ev["pre_h1_surprise_z"],
                "pre_path_coverage_1to7": ev["pre_path_coverage_1to7"], "pre_signal_3day": int(ev["pre_signal_3day"]),
                "pre_consensus": ev["pre_consensus"], "consensus_already_aligned": bool(ev["consensus_already_aligned"]),
                "consensus_latency_sessions": (None if pd.isna(ev["consensus_latency_sessions"]) else float(ev["consensus_latency_sessions"])),
                "post_1d_pct": ev["post_ret_1d_pct"], "post_3d_pct": ev["post_ret_3d_pct"], "post_7d_pct": ev["post_ret_7d_pct"],
                "continuation_7d_pct": ev["continuation_7d_pct"],
            })
    cat = pd.DataFrame(rows).sort_values(["symbol", "date"])
    cat.to_csv(OUTPUT_DIR / "stock_events_catalogue.csv", index=False)
    (OUTPUT_DIR / "stock_events_catalogue.json").write_text(json.dumps(rows, indent=1, default=str))

    # ---- aggregates by category (up-shocks and all) ----
    def agg(frame: pd.DataFrame) -> dict:
        out = {}
        for c, g in frame.groupby("category"):
            cont = g["continuation_7d_pct"].dropna()
            t, p = stats.ttest_1samp(cont, 0) if len(cont) > 4 else (np.nan, np.nan)
            out[c] = {"n": int(len(g)), "share_pct": round(100 * len(g) / len(frame), 1),
                      "mean_abs_ret_pct": round(float(g["ret_pct"].abs().mean()), 2),
                      "pre_h1_hit": round(float(g["pre_h1_hit"].mean()), 3), "pre_h1_coverage": round(float(g["pre_h1_covered"].mean()), 3),
                      "pre_h1_mean_abs_surprise": round(float(g["pre_h1_surprise_z"].abs().mean()), 2),
                      "pre_path_coverage": round(float(g["pre_path_coverage_1to7"].mean()), 3),
                      "consensus_aligned_pct": round(float(g["consensus_already_aligned"].mean() * 100), 1),
                      "consensus_latency_median": (float(g["consensus_latency_sessions"].dropna().median()) if g["consensus_latency_sessions"].notna().any() else None),
                      "continuation_1d_pct": round(float((np.sign(g["ret_pct"]) * g["post_1d_pct"]).mean()), 3),
                      "continuation_3d_pct": round(float((np.sign(g["ret_pct"]) * g["post_3d_pct"]).mean()), 3),
                      "continuation_7d_pct": round(float(cont.mean()), 3) if len(cont) else None,
                      "continuation_7d_t": round(float(t), 2) if len(cont) > 4 else None, "continuation_7d_p": round(float(p), 4) if len(cont) > 4 else None}
        return out
    up = cat[cat["direction"] == "up"]
    by_cat = {"up_shocks": agg(up), "all_shocks": agg(cat),
              "up_shocks_by_symbol": {s: {c: int(n) for c, n in g["category"].value_counts().items()} for s, g in up.groupby("symbol")},
              "news_covered_up_shocks": int(up["news_covered"].sum()),
              "idiosyncratic_up_shocks_without_attribution": int(((up["category"] == "idiosyncratic") & up["attribution"].isna()).sum())}
    (OUTPUT_DIR / "stock_events_by_category.json").write_text(json.dumps(by_cat, indent=2, default=str))

    # ---- report ----
    lines = ["# Single-stock shock catalogue", "",
             f"{len(cat)} shock sessions (|z| ≥ 2.5) for AAPL, MSFT, TSLA, NVDA, 2010 → 2026-09; {len(up)} are increases.",
             "Category priority: earnings reaction session (or the session after) → market-wide (SPY or QQQ |z| ≥ 2 same sign) → idiosyncratic.",
             f"Headlines from the Alpaca/Benzinga archive cover 2024-02 → 2026-08 ({by_cat['news_covered_up_shocks']} of the {len(up)} increases); earlier idiosyncratic events carry manual attributions where looked up.", ""]
    lines += ["## Increases by category", "", "| category | n | share | mean |r| % | pre-event h=1 coverage | mean |s| | consensus aligned | latency (median) | continuation 1d / 3d / 7d % (t) |", "|---|---|---|---|---|---|---|---|---|"]
    for c, v in by_cat["up_shocks"].items():
        lines.append(f"| {c} | {v['n']} | {v['share_pct']}% | {v['mean_abs_ret_pct']} | {v['pre_h1_coverage']} | {v['pre_h1_mean_abs_surprise']} | {v['consensus_aligned_pct']}% | {v['consensus_latency_median']} | {v['continuation_1d_pct']:+.2f} / {v['continuation_3d_pct']:+.2f} / {v['continuation_7d_pct']:+.2f} ({v['continuation_7d_t']}) |")
    lines += ["", "## Increases by stock", ""]
    for s, counts in by_cat["up_shocks_by_symbol"].items():
        lines.append(f"- **{s}**: " + ", ".join(f"{c} {n}" for c, n in counts.items()))
    lines += ["", "## Largest increases per stock (top 12 by z)", ""]
    for s, g in up.groupby("symbol"):
        lines += [f"### {s}", "", "| date | +% | z | SPY z | category | what happened | source | model the day before: P(up), band %, covered | consensus | latency | +1d / +3d / +7d % |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in g.sort_values("z", ascending=False).head(12).iterrows():
            band = r["pre_h1_band_pct"]
            what = (r["attribution"] or "—").replace("|", "/")
            lines.append(f"| {r['date']} | +{r['ret_pct']:.1f} | {r['z']:.1f} | {'' if r['spy_z_same_day'] is None or pd.isna(r['spy_z_same_day']) else r['spy_z_same_day']} | {r['category']} | {what[:110]} | {r['attribution_source'] or '—'} | {r['pre_h1_prob_up']:.2f}, [{band[0]:+.1f}, {band[1]:+.1f}, {band[2]:+.1f}], {'yes' if r['pre_h1_covered'] else 'no'} | {r['pre_consensus']}{' (aligned)' if r['consensus_already_aligned'] else ''} | {'' if r['consensus_latency_sessions'] is None or pd.isna(r['consensus_latency_sessions']) else int(r['consensus_latency_sessions'])} | {r['post_1d_pct']:+.1f} / {r['post_3d_pct']:+.1f} / {'' if pd.isna(r['post_7d_pct']) else f'{r[chr(112)+chr(111)+chr(115)+chr(116)+chr(95)+chr(55)+chr(100)+chr(95)+chr(112)+chr(99)+chr(116)]:+.1f}'} |")
        lines.append("")
    lines += ["## Increases with archive headlines (2024-02 → 2026-08)", ""]
    for _, r in up[up["news_covered"]].sort_values(["symbol", "date"]).iterrows():
        hl = "; ".join(h[:120] for h in r["headlines"][:3]) if r["headlines"] else "(no ticker-tagged headline in the archive window)"
        lines.append(f"- **{r['symbol']} {r['date']}** +{r['ret_pct']:.1f}% (z {r['z']:.1f}, {r['category']}): {hl}")
    (HERE / "STOCK_EVENTS.md").write_text("\n".join(lines))
    print(json.dumps(by_cat["up_shocks"], indent=1))
    print("by symbol:", by_cat["up_shocks_by_symbol"])
    print("need manual lookup (idiosyncratic, no attribution):")
    need = up[(up["category"] == "idiosyncratic") & up["attribution"].isna()].sort_values("z", ascending=False)
    print(need[["symbol", "date", "ret_pct", "z", "spy_z_same_day", "qqq_z_same_day"]].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
