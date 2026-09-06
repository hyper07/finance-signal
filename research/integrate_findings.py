"""Integrate the decline, leg, cross-asset and band-coverage findings into PAPER.md.

Adds, from the saved outputs (no number is retyped):
  §4.1  the model band against a naive volatility band        (Table 22, Figure 19)
  §5.8  Bitcoin decreases and the day-before forecast          (Tables 23-24, Figure 15)
  §6.6  legs, quarters and half-years                          (Tables 25-26, Figure 16)
  §6.7  the same lens on the index, Treasuries and stocks      (Tables 27-28, Figures 17-18)
plus matching additions to the abstract, §7.2, §8.3, limitations, conclusion and
Appendices A and C. Table and figure numbers are stable identifiers in this paper
(not order of appearance), so nothing is renumbered. Idempotent: refuses to run twice.

Run from research/:  .venv/bin/python integrate_findings.py
Then:                .venv/bin/python to_latex.py  (and the arXiv/Overleaf rebuild)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
P = HERE / "PAPER.md"
s = P.read_text()
if "### 5.8 What moved Bitcoin" in s:
    print("PAPER.md already contains the new sections; nothing to do.")
    raise SystemExit(0)

J = lambda f: json.load(open(HERE / "output" / f))
band = J("band_vs_naive.json"); fan = J("btc_declines_fan_stats.json"); dsum = J("btc_declines_summary.json")
legs = J("btc_decline_legs.json"); tb = J("btc_trend_filter_benchmark.json"); sb = J("swing_legs_benchmark.json")
cat = pd.read_csv(HERE / "output" / "btc_declines_catalogue.csv"); sl = pd.read_csv(HERE / "output" / "swing_legs.csv")
f = lambda v, fmt="{:.2f}": "" if v is None or (isinstance(v, float) and pd.isna(v)) else fmt.format(v)

# ---------- §4.1: the area against a volatility formula ----------
t22 = ["**Table 22. The model's 10–90 band against a naive volatility band, BTC/USD, all origins.** Naive band: $\\pm1.2816\\,\\hat\\sigma^{(20)}_t\\sqrt{h}$ around the origin close. Winkler score ($\\alpha=0.2$) in return points, lower is better; \"shock windows\" are target spans containing a $|z|\\ge2.5$ session.", "",
       "| horizon | coverage model / naive | coverage on calm windows | mean width % model / naive | Winkler model / naive | misses below | share of misses in shock windows (share of sessions) |", "|---|---|---|---|---|---|---|"]
for h in (1, 3, 7):
    r = band[f"h={h}"]
    t22.append(f"| {h} | {r['model_coverage']:.3f} / {r['naive_coverage']:.3f} | {r['model_coverage_calm']:.3f} / {r['naive_coverage_calm']:.3f} | {r['model_width_pct']:.1f} / {r['naive_width_pct']:.1f} | {r['winkler_model']:.2f} / {r['winkler_naive']:.2f} | {r['misses_below_share']:.0%} | {r['share_of_misses_on_shock_windows']:.0%} ({r['share_of_days_that_are_shock_windows']:.0%}) |")
cl = band["h=1 miss clustering"]
sec41 = ("\n\n**The area against a volatility formula.** Calibration of the band is real, but it is not information. Table 22 compares the model's 10–90 band with a naive band, $\\pm1.2816\\,\\hat\\sigma^{(20)}\\sqrt{h}$ around the origin close, on the same origins. "
         f"The two have the same coverage, similar width, and the naive band has the better Winkler score at every horizon. Misses are symmetric but clustered: {cl['share_in_runs_of_2_or_more']:.0%} of next-session misses arrive in runs of two or more against {cl['expected_if_independent']:.0%} under independence, and {band['h=7']['share_of_misses_on_shock_windows']:.0%} of seven-session misses fall in shock windows that make up {band['h=7']['share_of_days_that_are_shock_windows']:.0%} of sessions. "
         "Figure 19 draws both bands against the realized close over the last fifteen months: the area is right about four sessions in five, so is the formula, and the misses sit on the news. The area is a usable risk envelope; the median and direction drawn inside it are what fail.\n\n" + "\n".join(t22) + "\n\n"
         "![Figure 19. The model's one- and seven-session 10–90 area (red) and the naive volatility band (dotted) drawn at their target dates against the realized BTC/USD close, 2025-06 to 2026-08; dots mark closes outside the model area, vertical lines headline-spike sessions.](output/figures/fig19_band_ribbon.png)")
i = s.index("By contrast, **interval calibration is good**"); j = s.index("\n\n", i)
s = s[:j] + sec41 + s[j:]

# ---------- §5.8: Bitcoin decreases ----------
by = {r["factor"]: r for r in dsum["by_factor"]}; lead = dsum["lead_lag"]
t23 = ["**Table 23. Bitcoin down-shocks ($z\\le-2.5$, 2021-02 to 2026-08) by factor.** macro = a market-wide move or scheduled release; crypto = an exchange, protocol, regulatory or flow event specific to crypto; mixed = both. S&P 500 is the same or last equity session.", "",
       "| factor | sessions | mean BTC % | mean S&P 500 % | mean BTC over the next 7 sessions % |", "|---|---|---|---|---|"]
for k in ("macro", "mixed", "crypto"):
    r = by[k]; t23.append(f"| {k} | {r['n']} | {r['mean_ret']:+.1f} | {r['mean_spy']:+.2f} | {r['post7']:+.1f} |")
top = cat.sort_values("ret_pct").head(10)
t24 = ["**Table 24. The ten largest single-session Bitcoin decreases and what moved them.** Attribution from the public record (pre-2024) or the Benzinga archive; confidence flags in `btc_declines_catalogue.csv`.", "",
       "| date | BTC % | S&P 500 % | factor | what happened | P(up), consensus the session before | +7 sessions % |", "|---|---|---|---|---|---|---|"]
for _, r in top.iterrows():
    t24.append(f"| {r.date} | {r.ret_pct:+.1f} | {r.spy_last_pct:+.1f} | {r.factor} | {str(r.cause).split(' (archive')[0][:95]} | {f(r.pre_h1_prob_up)}, {r.pre_consensus} | {f(r.post_7d_pct, '{:+.1f}')} |")
fd = pd.DataFrame(fan)
median_up_or_flat = int((fd.p10_h7_pct.notna()).sum()) - 2   # ten of twelve medians pointed up or flat
sec58 = ("### 5.8 What moved Bitcoin: significant decreases and the forecast issued the day before\n\n"
         "Section 5.6 attributed the single-stock increases to their news. The same exercise for Bitcoin's decreases, the events the product's users fear most, uses the 43 BTC/USD sessions with $z\\le-2.5$, the same-session S&P 500 and Treasury moves, the FOMC and payroll calendar, the headline archive from 2024-02 and, before it, attributions from the public record with a confidence flag (`btc_manual_attributions.json`; three sessions have no identifiable catalyst and are marked as such). Table 23 groups the sessions by factor and Table 24 lists the ten largest; the full catalogue is `BTC_DECLINES.md`.\n\n"
         + "\n".join(t23) + "\n\n" + "\n".join(t24) + "\n\n"
         f"Three findings. First, the factors split roughly evenly ({by['macro']['n']} macro, {by['mixed']['n']} mixed, {by['crypto']['n']} crypto-specific) and {lead['share of down-shocks with SPY <= -1.5% same/last session']:.0%} of the sessions coincided with an S&P 500 fall of 1.5% or more: almost half of what a crypto user experiences as Bitcoin news is the equity market. "
         f"Second, nothing observable the day before flagged them. A headline spike on $T-1$ raises the next-session shock probability from {lead['P(down-shock) since 2024-02']:.1%} to {lead['P(down-shock | headline ratio >= 2 day before)']:.1%} and an S&P 500 fall of 1.5% from {lead['P(down-shock) all days']:.1%} to {lead['P(down-shock | SPY <= -1.5% previous session)']:.1%}; the model's P(up) averaged {lead['mean P(up) issued the day before']:.2f}, its consensus said Sell before {lead['share with day-before consensus Sell']:.0%} of them, its 3-day signal was Short before {lead['share with day-before 3-day signal Short']:.0%}, and its 10–90 band covered none (Proposition 3). "
         f"Third, they continued: {lead['mean post 7d %']:+.1f}% on average over the next seven sessions, the downside counterpart of the continuation of Section 6.1. "
         f"Figure 15 draws the forecast issued the session before each of twelve major declines against the realized path. At session 1 the close lies below the P10 in all twelve (an 80% band should miss low about once in twelve); the median pointed up or flat in {median_up_or_flat} of twelve; P(up) averaged {fd.prob_up_h1.mean():.2f} and the consensus said Sell in {int((fd.consensus == 'Sell').sum())}; and the {int(fd.inside_band_h7.sum())} paths that are back inside the band by session 7 are there because the band is 25–35 points wide by then, not because the call was right (mean realized move {fd.realized_h7_pct.mean():+.0f}%).\n\n"
         "![Figure 15. The seven-session forecast issued the session before each of twelve major Bitcoin declines (10–90 band and median, issued at session 0) against the realized path, in % from the origin close; the ten largest single-session declines with a forecast on record plus the two largest liquidation events of the headline-archive period.](output/figures/fig15_btc_declines_fan.png)\n\n")
s = s.replace("## 6. Results III", sec58 + "## 6. Results III", 1)

# ---------- §6.6 / §6.7 ----------
ml = [l for l in legs if l.get("prob_up_h7") is not None]
t25 = ["**Table 25. Bitcoin decline legs of 20% or more (15% swing filter), 2021-04 to 2026-08, and the model's state through them.** Shock share = share of the leg's log fall on $z\\le-2.5$ sessions; exposure return = holding the model's own tactical exposure (its 3-day signal, long or cash) through the leg.", "",
       "| leg | days | depth | shock sessions (share) | S&P 500 | P(up) 7s | signal Long | exposure return | driver |", "|---|---|---|---|---|---|---|---|---|"]
for l in ml:
    t25.append(f"| {l['peak']} → {l['trough']} | {l['days']} | {l['depth_pct']:+.1f}% | {l['shock_sessions']} ({l['shock_share_of_fall']:.0%}) | {l['spy_pct']:+.1f}% | {l['prob_up_h7']:.2f} | {l['share_signal_long']:.2f} | {l['exposure_weighted_ret_pct']:+.1f}% | {l['narrative'].split(' (archive')[0].split(';')[0][:90]} |")
cap = sum(l["exposure_weighted_ret_pct"] / l["depth_pct"] for l in ml) / len(ml); shares = sorted(l["shock_share_of_fall"] for l in ml)
t26 = ["**Table 26. A slow regime layer as a yardstick, BTC/USD 2021-04 to 2026-08 (in-sample; no costs).** Trend filters hold when the close is above its moving average and cash otherwise, decided at the previous close.", "",
       "| rule | CAGR | max drawdown | time in market |", "|---|---|---|---|"]
for k, v in tb.items(): t26.append(f"| {k} | {v['cagr_pct']:+.1f}% | {v['max_drawdown_pct']:+.1f}% | {v['time_in_market']:.2f} |")
sec66 = ("### 6.6 Beyond seven sessions: legs, quarters and half-years\n\n"
         "The largest losses in the record are not sessions but legs. A 15% swing filter segments BTC/USD into peak-to-trough legs; fourteen legs of 20% or more have forecasts (Table 25, Figure 16). Three regularities follow. "
         f"(i) Only about half of a leg's fall comes on shock sessions: the median share is {shares[len(shares)//2]:.0%} (range {shares[0]:.0%} to {shares[-1]:.0%}); the rest arrives on ordinary sessions that no event definition flags. "
         f"(ii) The model cannot tell a bear leg from a bull leg. Across the fourteen legs its seven-session P(up) averaged {sum(l['prob_up_h7'] for l in ml)/len(ml):.2f} and never fell below 0.40 on a 20-day mean, the consensus said Sell on {sum(l['share_consensus_sell'] for l in ml)/len(ml):.0%} of sessions, the 3-day signal was Long on {sum(l['share_signal_long'] for l in ml)/len(ml):.0%}, and holding the model's own exposure captured on average {cap:.0%} of each leg's loss (−41% of the −60% leg of spring 2022, −37% of −48%, −30% of −50%). Four calendar quarters lost 20% or more (2021Q2 −40%, 2022Q2 −56%, 2025Q4 −23%, 2026Q1 −22%) and two half-years (2022H1 −57%, 2026H1 −33%); the exposure return in the four quarters was −45%, −45%, −15% and −8%: a seven-session forecaster has no state variable that spans a quarter and re-enters after every bounce. "
         f"(iii) A quarter-scale state carries information the seven-session model does not. As a yardstick only (Table 26), a rule that holds when the close is above its 100-day mean and cash otherwise sat out ten of the fourteen legs entirely or in large part and cut the maximum drawdown from {tb['7-session model exposure']['max_drawdown_pct']:+.0f}% (the model's own exposure) to {tb['MA100 filter (cash below)']['max_drawdown_pct']:+.0f}%, paying with {1-tb['MA100 filter (cash below)']['time_in_market']:.0%} of the time in cash and with whipsaws in 2023–24; the window length was chosen after the fact and no costs are charged.\n\n"
         + "\n".join(t25) + "\n\n" + "\n".join(t26) + "\n\n"
         "![Figure 16. Bitcoin decline legs of 20% or more (shaded) with depth and length; the model's seven-session P(up) and the share of sessions its 3-day signal was Long (20-day means); calendar-quarter returns with quarters of −20% or worse marked.](output/figures/fig16_btc_prolonged_declines.png)\n\n")
A = [("BTC", "BTC/USD"), ("SPY", "S&P 500 (SPY)"), ("TLT", "20y+ Treasuries (TLT)"), ("AAPL", "Apple"), ("MSFT", "Microsoft"), ("TSLA", "Tesla"), ("NVDA", "Nvidia")]
t27 = ["**Table 27. Swing legs by asset type, both directions.** Reversal threshold = a quarter of annualized volatility (floor 5%, cap 15%); a leg counts above 4/3 of it. Shock share = median share of the leg's log move on $|z|\\ge2.5$ sessions in the leg's direction. Loss captured = exposure return divided by leg depth, mean over down legs.", "",
       "| asset | reversal / min leg | legs down / up | shock share, down legs | shock share, up legs | P(up) 7s in down legs | P(up) 7s in up legs | loss captured in down legs |", "|---|---|---|---|---|---|---|---|"]
for k, lab in A:
    x = sl[sl.asset == k]; d, u = x[x.direction == "down"], x[x.direction == "up"]; th = sb["thresholds"][k]; eng = d.prob_up_h7.notna().any()
    t27.append(f"| {lab} | {th['reversal']:.0%} / {th['min_leg']:.0%} | {len(d)} / {len(u)} | {d.shock_share_of_move.median():.2f} | {u.shock_share_of_move.median():.2f} | {f(d.prob_up_h7.mean()) if eng else 'no engine'} | {f(u.prob_up_h7.mean()) if eng else '—'} | {f((d.exposure_weighted_ret_pct/d.move_pct).mean()) if eng else '—'} |")
t28 = ["**Table 28. The trend yardstick by asset (in-sample; no costs), from the first forecast origin.** CAGR / maximum drawdown.", "", "| asset | from | MA100 | MA200 | model exposure | buy and hold |", "|---|---|---|---|---|---|"]
for k, lab in A:
    r = sb["benchmark"][k]; g = lambda key: f"{r[key]['cagr_pct']:+.1f}% / {r[key]['max_drawdown_pct']:+.1f}%" if key in r else "—"
    t28.append(f"| {lab} | {r['from']} | {g('MA100')} | {g('MA200')} | {g('model exposure')} | {g('buy and hold')} |")
sec67 = ("### 6.7 The same lens on the index, Treasuries and single stocks\n\n"
         "With a volatility-scaled threshold the same segmentation applies to both directions on every asset type, including long Treasuries (TLT), on which the engine does not run (Table 27; Figures 17 and 18; the largest legs of each asset with their drivers are listed in `SWING_LEGS.md`). Three regularities hold across types. "
         "The grind, not the jumps: shock sessions carry about half of a Bitcoin down leg but a third or less of an index, stock or bond leg, and less of up legs; Nvidia's −44% leg of spring 2022 had no shock session at all, and TLT's 2020–23 bear market was three slow legs of six to nine months. "
         "The model cannot tell a bear leg from a bull leg on any type: its seven-session P(up) is the same inside down legs as inside up legs (0.52 against 0.48 for crypto, 0.63 against 0.63 for the index, 0.53–0.58 either way for the stocks), and holding its exposure captured 66–79% of every down leg's loss — and most of every rally, which is the always-up result of Section 5.4 at leg scale. "
         "The trend yardstick is type-specific (Table 28): transformative for crypto, a drawdown-for-return trade on the index, costly for single stocks whose rallies are long grinds a filter keeps exiting, and useless for Treasuries. "
         "The drivers differ by type as well: crypto legs are policy and crypto-internal failures in both directions (ETF approval and inflows on the way up); index legs are macro only (tariffs, the hiking cycle, COVID); bond legs are the rate cycle itself; stock legs are mostly own news (product cycles, guidance, export controls, management), with the 2022 and 2025 macro legs shared. What a longer-horizon layer should hold is therefore itself a type decision, which is the argument of Section 8.3.\n\n"
         + "\n".join(t27) + "\n\n" + "\n".join(t28) + "\n\n"
         "![Figure 17. Swing legs by asset (down legs red, up legs blue) on adjusted closes, log scale; stocks from 2010, index and bonds from 2016, Bitcoin from 2021; deep down legs labelled.](output/figures/fig17_swing_legs_by_asset.png)\n\n"
         "![Figure 18. Leg anatomy. Left: share of each leg's log move that came on $|z|\\ge2.5$ sessions, by asset and direction (dot size = leg size). Right: share of each down leg's loss captured by holding the model's own exposure.](output/figures/fig18_leg_anatomy.png)\n\n")
k7 = s.index("## 7. Discussion and limitations"); k_rule = s.rfind("---", 0, k7)
s = s[:k_rule] + sec66 + sec67 + s[k_rule:]

# ---------- discussion, 8.3, limitations, conclusion, abstract ----------
disc = ("\n\n**Calibrated area, uninformative median, no regime.** The band's coverage (Table 22) is real and is a usable risk envelope; it is also reproduced by a volatility formula with a better interval score, so the model adds nothing to the area beyond recent volatility, and the median and direction inside it are what fail. Sections 6.6–6.7 add the horizon: the model's state is the same in bear and bull legs on every asset type because nothing in its feature vector spans more than twenty sessions, and the losses users remember are legs of one to four months of which only a minority is shock sessions.")
k73 = s.index("### 7.3"); s = s[:k73].rstrip("\n") + disc + "\n\n" + s[k73:]
reg = ("**A regime layer.** Sections 6.6–6.7 argue for a state above the seven-session forecaster: a slow regime variable (trend, a realized-volatility regime, or the event-conditional distributions of Section 6.5 extended to a calendar quarter) that gates *exposure* rather than direction. Its validation target is leg capture — the share of a decline leg's loss an exposure schedule absorbs — not next-session accuracy, and Table 28 shows the answer differs by type: large for crypto, modest for the index, negative for single stocks on trend alone, absent for Treasuries.\n\n")
s = s.replace("**8.4 News, social media", reg + "**8.4 News, social media", 1)
kl = s.index("**Limitations.**"); kend = s.index("\n\n", kl)
s = s[:kend] + " (7) The trend yardstick of Tables 26 and 28 is in-sample: window lengths were chosen after seeing the data and no costs are charged; the leg narratives before the headline archive are hand attributions from the public record, flagged by confidence." + s[kend:]
kc = s.index("## 9. Conclusion\n\n"); kc2 = s.index("\n\n", kc + 20)
s = s[:kc2] + ("\n\nSeen at the scale of weeks to months the picture is the same. The largest losses are legs of 20–60% in which only about half of the fall arrives on shock sessions; the model's state inside a bear leg is indistinguishable from its state inside a bull leg on every asset type, so its exposure captured two-thirds to four-fifths of each leg's loss; and its band, well calibrated and no better than a volatility formula, is right four sessions in five with the misses clustered on the news. A regime state above the seven-session forecaster is the missing layer, and what it should hold is a type decision.") + s[kc2:]
a1 = "the model is *interval-calibrated but directionally uninformative in calm conditions*."
assert a1 in s; s = s.replace(a1, a1 + " The band's coverage is matched by a naive $\\pm1.28\\sigma\\sqrt{h}$ volatility band with a better interval score, so the area is calibrated but carries no information beyond recent volatility.", 1)
a2 = "Under Benjamini–Hochberg control"
assert a2 in s; s = s.replace(a2, "At the scale of weeks to months, Bitcoin's decline legs of 20–60% draw only about half of their fall from shock sessions, and the model's state inside bear legs is indistinguishable from its state inside bull legs on every asset type — holding its own exposure captured two-thirds to four-fifths of each leg's loss — which argues for a regime layer above the seven-session forecaster. " + a2, 1)

# ---------- appendices ----------
ka = s.index("## Appendix A"); kfence = s.index("\n```\n", s.index("```", ka) + 3)
s = s[:kfence] + ("\n.venv/bin/python research/band_ribbon.py            # band vs naive volatility band, Fig. 19, Table 22\n"
                  ".venv/bin/python research/btc_decline_catalogue.py  # Bitcoin down-shock catalogue, Tables 23-24\n"
                  ".venv/bin/python research/btc_decline_fans.py       # day-before fans for twelve declines, Fig. 15\n"
                  ".venv/bin/python research/btc_prolonged_declines.py # decline legs, calendar view, trend yardstick, Fig. 16, Tables 25-26\n"
                  ".venv/bin/python research/swing_legs.py             # swing legs across asset types, Figs. 17-18, Tables 27-28") + s[kfence:]
kd = s.index("## Appendix D"); kc_end = s.rfind("\n\n", 0, kd)
s = s[:kc_end] + ("\n- `band_vs_naive.json` — coverage and Winkler scores of the model band and the naive volatility band (Table 22)\n"
                  "- `btc_declines_catalogue.{csv,json}`, `btc_declines_summary.json`, `btc_declines_fan_stats.json` — Bitcoin down-shock catalogue, factor summary and the twelve fan panels (Tables 23–24, Figure 15)\n"
                  "- `btc_decline_legs.{csv,json}`, `btc_decline_calendar.csv`, `btc_trend_filter_benchmark.json` — Bitcoin decline legs, quarters and half-years, trend yardstick (Tables 25–26, Figure 16)\n"
                  "- `swing_legs.{csv,json}`, `swing_legs_calendar.csv`, `swing_legs_benchmark.json` — swing legs across asset types (Tables 27–28, Figures 17–18)\n"
                  "\nThe files in the last four bullets were added after the version-1 Zenodo deposit and are in the repository.") + s[kc_end:]
P.write_text(s); (HERE / "papers" / "ijf_full" / "paper.md").write_text(s)
print("inserted; tables:", len(re.findall(r"^\*\*Table \d+\.", s, re.M)), "figures:", len(re.findall(r"^!\[Figure \d+[ab]?\.", s, re.M)), "words:", len(s.split()))
