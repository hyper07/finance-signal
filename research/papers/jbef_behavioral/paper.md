# After the news: post‑shock drift, model latency, and how users act on a multi‑day forecast

**Target: *Journal of Behavioral and Experimental Finance* (≈5,000 words, 5 tables, 3 figures).** Companion to *When the News Arrives* (arXiv, q‑fin.ST), which reports the forecast‑evaluation results; this paper reports the behavioral results and the research agenda.

*Kibaek Kim, Kiok Kim, Danielle Ahn — dotori.ai*

**Abstract.** We use a deployed seven‑session forecasting product — immutable daily signals for a Bitcoin ETF pair, the S&P 500 pair and single stocks — as a natural experiment on how prices, people and a machine respond after information arrives. Across a cryptocurrency pair, an equity index and 50 single stocks (2010–2026), we identify 3–5% of sessions as information shocks (|z|≥2.5) and find type‑specific after‑shock behavior: cryptocurrency continues in the shock direction (+3.0% over seven sessions, *t*=3.06), the index reverses (−0.5 to −1.4%), and single stocks split by cause — the four mega‑caps' post‑earnings increases drift (+2.3%, *t*=2.68) while idiosyncratic‑news and market‑wide increases do not; across 50 stocks the walk‑forward, cost‑adjusted post‑earnings continuation is only +0.25% per event and does not survive 25 bp costs. A walk‑forward rule shows that acting late pays only in Bitcoin and only within one session (+2.3% net per event, 64% of events). A catalogue of 346 significant single‑stock increases with news attribution shows every one to be an information event. The deployed model's seven‑vote consensus was aligned with the coming shock before only 6–17% of events and needed a median of 2 (index) to 5–7 (crypto, stocks) sessions to agree — after most of the exploitable drift. Simulating how a user should act on the published seven‑session exposure schedule (every day, once a week, once and hold) we find no dominant cadence: rankings flip across instruments and periods, and the committed weekly schedule differs from daily re‑forecasting by ≥25 exposure points on 66–75% of sessions. We interpret the pattern with a jump‑plus‑response‑kernel model in which the human reaction to news is the missing state variable, and set out a program to measure that kernel through news, social media and neuroeconomic experiments.

**Keywords:** post‑announcement drift; under‑reaction; herding; news; social media; forecast latency; investor behavior; neuroeconomics. **JEL:** G14, G40, G41, D91.

## 1. Introduction

Behavioral finance has documented that prices under‑react to information and drift for days or weeks — after earnings (Bernard & Thomas, 1989), after headlines (Chan, 2003), more slowly for firms with less coverage (Hong et al., 2000), and in ways tied to investor psychology (Barberis et al., 1998; Daniel et al., 1998; Frazzini, 2006; Hong & Stein, 1999) and attention (Barber et al., 2022; Da et al., 2011; Hirshleifer et al., 2009). A newer literature shows that social platforms are now a primary channel of both information and herding (Ante, 2023; Cookson & Niessner, 2020; Pedersen, 2022; Shiller, 2017).

This paper adds a third party to the picture: a *machine*. Retail investors increasingly act on algorithmic forecasts; the one studied here publishes, each session, a seven‑session exposure schedule and a Buy/Sell/Hold consensus for a crypto pair, an index pair and hundreds of stocks. Because its live signals are frozen and its code is available, we can ask three behavioral questions with unusual precision: (1) how do prices move after information shocks, by asset type and by cause; (2) how long does a pattern‑based model take to "notice", relative to the drift; and (3) how should a person act on a multi‑day schedule — and does it matter? The forecast‑accuracy audit itself (the model has no directional skill and is contrarian into shocks) is reported in the companion paper; here we take it as given and study behavior.

## 2. Data and definitions

Prices: Alpaca daily bars for BITO/BITI (2021‑10 →), BTC/USD (2021‑01 →), SPXL/SPXS and SPY (2016 →); Yahoo adjusted history for 50 S&P 500 stocks (2010 →), with quarterly earnings timestamps. Headlines: 7,374 Benzinga items (2024‑02 → 2026‑08). Model: the production engine and forecaster of signal.dotori.ai, run point‑in‑time on every origin (all forecasts are regenerated with the production code; 2026 live signals frozen as published).

A **shock** is a session with |*z_T*| = |*r_T*|/σ̂₂₀(*T*−1) ≥ 2.5. **Continuation** after a shock is the sign‑adjusted return *D_T*(*C*_{T+k}/*C_T* − 1), the return to a trader who takes the shock direction at the shock close. **Consensus latency** is the number of sessions after *T* until the model's seven‑vote consensus first agrees with *D_T*, conditional on not being aligned at *T*−1. Single‑stock increases are classified by a fixed rule: earnings reaction session → market‑wide (SPY or QQQ |*z*|≥2 same sign) → idiosyncratic, and attributed to headlines (archive) or verified press coverage.

## 3. What happens after the news

**Table 1. Post‑shock continuation by asset type (sign‑adjusted, %).**

| instrument | type | shocks | 1 session | 3 sessions | 7 sessions (*t*) | shocks clustered ≤3 sessions |
|----------|------|------|-------|--------|------------|---------|
| BTC/USD | crypto | 98 | +0.13 | +1.22 | **+2.98 (3.06)** | 21% |
| BITO | crypto | 48 | +0.07 | +1.15 | +1.61 (1.0) | 31% |
| SPY | index | 98 | −0.28 | −0.22 | −0.52 (−1.5) | 26% |
| SPXL | index | 96 | −0.75 | −0.45 | −1.39 (−1.4) | 25% |
| AAPL | stock | 170 | −0.05 | −0.33 | −0.73 (−2.0) | 14% |
| MSFT | stock | 163 | −0.42 | −0.36 | −0.71 (−2.1) | 19% |
| TSLA | stock | 171 | −0.24 | −0.01 | +0.52 (0.6) | 17% |
| NVDA | stock | 141 | +0.11 | +0.80 | +0.96 (1.3) | 9% |

Three types, three behaviors (Fig. 1). Crypto shocks continue and cluster — the momentum‑after‑news of an asset whose information arrives unscheduled, through political and social channels, and whose leverage produces liquidation cascades (the 2026‑08‑19 rally carried the largest short liquidation in Bitcoin's history). Index shocks — two‑thirds of them downward — revert, consistent with the mean‑reverting, negatively skewed dynamics of a diversified portfolio whose macro news is scheduled and largely priced. Single stocks are heterogeneous, and Table 2 shows why: the behavior depends on the *cause*. The contrast with crypto is one of *speed*, not *sensitivity* — shock sessions carry the same share of variance in stocks as in crypto and earnings sessions move a stock 3–4× its normal range — but a mega‑cap has absorbed the news by the close, while Bitcoin absorbs it over a week: quantifiable versus argued‑out information, deep versus thin arbitrage capital (Hong et al., 2000), leverage‑driven liquidation cascades, scheduled versus unscheduled arrival.

**Table 2. Single‑stock significant increases by cause (346 events, four core stocks; across the 50‑stock cross‑section the median stock has 19% earnings, 25% market‑wide and 56% idiosyncratic increases).**

| cause | *n* | share | mean move | continuation 1 / 3 / 7 sessions (%) | *t* (7) |
|----------------------------------------|----|-----|-----|---------------------|----------------|
| earnings reaction | 78 | 23% | +8.7% | +0.72 / +1.94 / **+2.26** | 2.68 (*p*=0.009) |
| idiosyncratic news (analyst target, product, management, order, settlement) | 166 | 48% | +6.0% | +0.24 / +0.15 / +1.10 | 1.56 |
| market‑wide day | 99 | 29% | +6.2% | −0.65 / +0.05 / +0.58 | 0.83 |

Post‑earnings drift appears with the classic profile — small on day one, cumulating over the week — reproducing Bernard and Thomas (1989) in a modern sample of mega‑caps. Idiosyncratic news produces a jump with little follow‑through. Market‑wide increases give back part of the move the next day. Every catalogued increase — the largest being NVDA +29.8% (earnings, 2016‑11‑11), TSLA +24.4% (earnings, 2013‑05‑09), TSLA +17.0% (Morgan Stanley upgrade, 2011‑03‑31), TSLA +12.7% (Hertz order, 2021‑10‑25), MSFT +7.3% (Ballmer retirement, 2013‑08‑23) — is an information event; none is a pattern in the prior price path.

### 3.1 When should a person act?

If people react late, the practical question is whether acting one, two or three sessions after the news still captures anything. Table 3a gives the in‑sample answer — the sign‑adjusted return from the close of session *k* to session 7 — and Table 3b tests it as a walk‑forward trading rule net of 5 and 25 bp per side, with the direction (continuation or reversal) chosen at each event from the trailing *t*‑statistic of prior, fully observed events only.

**Table 3a. Return from entering *k* sessions after a shock and holding to session 7, sign‑adjusted, % (share positive), in‑sample.**

| event set | enter day 0 | day 1 | day 2 | day 3 | day 5 |
|------------------------------------|-----------|-----------|-----------|-----------|-----------|
| BTC, all 98 shocks | +2.98 (62%) | +2.79 (64%) | +1.95 (61%) | +1.69 (59%) | +0.50 (49%) |
| BTC, 55 up-shocks | +3.83 (65%) | +3.26 (69%) | +2.04 (62%) | +1.75 (60%) | +0.60 (49%) |
| BITO, 46 shocks | +1.61 (54%) | +1.69 (61%) | +1.50 (59%) | +0.60 (50%) | -0.20 (52%) |
| SPY, 98 shocks | -0.52 (43%) | -0.25 (43%) | -0.37 (41%) | -0.31 (48%) | -0.03 (50%) |
| SPXL, 96 shocks | -1.38 (41%) | -0.78 (45%) | -1.12 (41%) | -1.06 (45%) | -0.13 (49%) |
| 4 stocks, 77 earnings up-jumps | +2.26 (64%) | +1.44 (64%) | +0.82 (64%) | +0.30 (56%) | +0.78 (68%) |
| 4 stocks, 166 idiosyncratic up-jumps | +1.10 (51%) | +0.82 (51%) | +1.07 (53%) | +0.86 (52%) | -0.06 (54%) |
| 4 stocks, 99 market-wide up days | +0.58 (55%) | +1.23 (58%) | +0.41 (56%) | +0.56 (58%) | +0.75 (55%) |

**Table 3b. Walk‑forward, cost‑adjusted rule (side chosen from prior events; ≥20 events; |t|>1 to trade).**

| group | enter day | OOS events / traded | side chosen | net per event, 5 bp (hit, t) | net per event, 25 bp (hit, t) | since 2025, 5 bp | always-continuation, 5 bp (hit, t) |
|---------------------------------------|-----|-----------|------------------|---------------------|---------------------|--------------|---------------------|
| BTC | 0 | 77 / 77 | continuation | **+2.51%** (61%, t 2.32) | +2.11% (60%, t 1.95) | 2.207% (n 30) | +2.51% (61%, t 2.32) |
| BTC | 1 | 77 / 77 | continuation | **+2.33%** (64%, t 2.5) | +1.93% (61%, t 2.07) | 2.359% (n 30) | +2.33% (64%, t 2.5) |
| BTC | 2 | 77 / 77 | continuation | **+1.34%** (60%, t 1.64) | +0.94% (56%, t 1.15) | 1.424% (n 30) | +1.34% (60%, t 1.64) |
| BTC | 3 | 77 / 70 | continuation | **+1.24%** (60%, t 1.59) | +0.84% (53%, t 1.08) | 1.451% (n 30) | +1.37% (61%, t 1.89) |
| BITO | 1 | 26 / 0 | filter never fires | — | — | — | 4.013% (0.692, t 2.6) |
| SPY | 0 | 78 / 54 | reversal | **-0.01%** (48%, t -0.03) | -0.41% (46%, t -0.77) | 0.677% (n 16) | -0.56% (41%, t -1.38) |
| SPXL | 0 | 76 / 37 | reversal | **-0.23%** (51%, t -0.13) | -0.63% (46%, t -0.36) | 0.535% (n 11) | -1.28% (41%, t -1.04) |
| 50 stocks: earnings shocks (both signs) | 0 | 1366 / 1014 | continuation 94% | **+0.18%** (53%, t 1.13) | -0.22% (48%, t -1.45) | 0.63% (n 162) | +0.25% (52%, t 1.9) |
| 50 stocks: earnings shocks | 1 | 1366 / 126 | mixed | **-0.50%** (44%, t -1.45) | -0.90% (38%, t -2.62) | -0.724% (n 20) | +0.03% (52%, t 0.22) |
| 50 stocks: idiosyncratic shocks | 0 | 3845 / 168 | rarely fires | **-0.31%** (45%, t -0.99) | -0.71% (40%, t -2.26) | —% (n 0) | -0.09% (48%, t -1.02) |
| 50 stocks: market-wide shocks | 0 | 2800 / 2733 | reversal 92% | **+0.30%** (53%, t 2.65) | -0.10% (49%, t -0.93) | 1.54% (n 214) | -0.64% (43%, t -5.82) |
| 50 stocks: market-wide shocks | 2 | 2800 / 2750 | reversal | **+0.17%** (53%, t 1.63) | -0.23% (48%, t -2.22) | 2.361% (n 214) | -0.70% (43%, t -6.88) |

Only Bitcoin supports acting late, and only by one session: +2.5% and +2.3% net per event at 5 bp when entering at the shock close or the next close (61–64% of events positive, *t* ≈ 2.3–2.5; +1.9–2.1% at 25 bp; +2.4% with 70% hit in 2025–26), halving and losing significance by the second session, gone by the fifth. Chasing index shocks loses (−0.6% per event, −1.0% at 25 bp). Across 1,390 earnings shocks in 50 stocks the continuation is +0.25% per event at 5 bp and negative at 25 bp — the +2.3% of Table 2 belongs to the four mega‑caps' upward jumps; idiosyncratic company news has no drift; market‑wide stock moves reverse by +0.3% at 5 bp and nothing at 25 bp. Dispersion is 7–10% per event against a 2–3% mean even for Bitcoin, so about four events in ten lose at the best entry. The behaviorally defensible guidance is descriptive and type‑specific: after a crypto shock, do not fade it and act within one session or not at all; after index and stock moves, do not chase.

## 4. How long the machine takes to notice

**Table 3. Model alignment and latency around shocks.**

| instrument | consensus aligned at *T*−1 | consensus latency (median sessions) | 3‑day signal latency | never aligned within 15 sessions |
|-------------------------|------------------|-------------|-------|-----------------|
| BTC/USD | 6% | 6 | 3 | 24 of 98 |
| BITO | 10% | 5 | 2 | 2 of 48 |
| SPY | 12% | 2 | 3 | 59 of 98 |
| SPXL | 10% | 2 | 1 | 9 of 96 |
| AAPL / MSFT / TSLA / NVDA | 15 / 15 / 11 / 17% | 4 / 7 / 4 / 4 | 0–2 | 86 / 65 / 61 / 54 |

The model almost never anticipates a shock (its analog pool has no news in it), and its speed of agreement afterwards is fastest exactly where agreement is least useful: on the index, where shocks revert, the contrarian analogs are directionally right within two sessions; on crypto, where shocks continue, the consensus takes five to six sessions — after most of the +3% drift of Table 1 has accrued; on stocks it takes four to seven, past the earnings‑drift window. The machine, in other words, reacts like a slow discretionary trader who has read nothing.

## 5. How a person should act on the schedule

The product publishes, each session, a seven‑row exposure schedule ("if you take no other action, here is your exposure for day 1, day 2, …"). We simulate, point‑in‑time and with 5 bp per unit turnover: **act daily** (fresh day‑1 target every session), **act weekly** (commit to the seven‑row schedule, re‑plan every seven sessions), **act once and hold** (day‑1 target, then nothing for a week), against **buy‑and‑hold** and the deployed **3‑day signal**. Negative exposure earns the actual inverse‑ETF return.

**Table 4. Annualised return % / Sharpe (full sample) and total return % / Sharpe (2026).**

| instrument | hold | act daily | act weekly | act once, hold |
|------------------|------------|------------|------------|------------|
| BITO (2022‑03→) | **+15.8 / .55** | +5.5 / .37 | −1.1 / .17 | −23.4 / −.32 |
| BITO 2026 | −13 / −.29 | **+64 / 2.47** | +39 / 1.92 | +21 / 1.08 |
| BTC/USD (2021‑04→) | +5.5 / .37 | −0.4 / .18 | +7.8 / .40 | **+17.4 / .60** |
| SPXL (2016‑05→) | **+30.7 / .78** | −8.3 / .00 | −12.0 / −.26 | −15.7 / −.23 |
| SPY | **+15.6 / .91** | +10.3 / .88 | +3.1 / .43 | +10.8 / .88 |
| AAPL (2010‑05→) | **+26.2 / .97** | +18.2 / .90 | +9.7 / .73 | +19.5 / .94 |
| MSFT | **+21.4 / .87** | +14.8 / .81 | +8.0 / .65 | +18.1 / .94 |
| TSLA | **+39.1 / .86** | +30.4 / .83 | +21.3 / .79 | +36.9 / .94 |
| NVDA | +50.5 / 1.12 | +38.7 / 1.13 | +19.0 / .88 | +36.6 / 1.08 |

No cadence dominates (Fig. 2). Holding wins seven of eight full samples; acting once‑and‑hold wins BTC; acting daily wins BITO and SPXL in 2026, a year whose drawdowns paid the inverse leg — a regime effect, not forecast skill. The robust finding is about the schedule itself: the committed weekly path and daily re‑forecasting disagree by ≥25 exposure points on 66–75% of sessions (mean absolute gap 0.30–0.50 of full exposure), so "doing nothing after day one" is a materially different strategy from acting daily, and neither is reliably better. Acting daily costs 60–140 units of turnover a year; on the 3× leveraged pair every forecast‑driven cadence lost 8–16% a year against +31% for holding, because a −100% target converts volatility drag into a structural loss. From the user's side, the behavioral risk is not choosing the wrong cadence; it is believing that any cadence extracts information the schedule does not contain. A portfolio corollary follows the same type logic. The classic 60/40 stock–bond policy with rebalancing — selling bonds to buy stocks after a fall and the reverse after a rise — is a contrarian (concave) rule (Perold & Sharpe, 1988) that harvests exactly the index reversal of Table 1: on SPY/TLT 2016–26 it cut volatility from 17.51% to 11.13% and the drawdown from -34% to -28%, though in a decade when bonds lost money it added no return (9.29% vs 11.09% for a drifting 60/40). Applied to Bitcoin the same rule adds return through the rebalancing bonus of a 58%-volatility asset (13.11% vs 9.98%), but buying the dip in the week after a crypto down-shock loses (8.82%): the contrarian policy is right where shocks revert and wrong where they continue, for the same behavioral reason the forecaster is.

## 6. Interpretation: the missing state variable is a human one

Write *r_t* = μ(*x*_{t−1}) + σ(*x*_{t−1})ε_t + Σ_k ξ_k *K*(t − τ_k; θ): news arrives at τ_k with impact ξ_k, and *K* is a **response kernel** describing how the population of traders digests it over the following sessions. Tables 1–2 are estimates of *K* by type and cause: a positive, slow kernel for crypto and for earnings; a negative one for index shocks; a spike without tail for idiosyncratic stock news. The deployed model conditions on *x*_{t−1} only; it cannot see τ_k or ξ_k, and because *K* is not in its state it predicts calm‑regime reversal after a large move — the opposite of Table 1 for crypto. Table 3 is the latency of a learner that has no representation of the thing it is trying to learn. The companion paper shows that a causal, event‑conditional replacement of the forecast on earnings sessions and after crypto shocks — an empirical *K* estimated walk‑forward — improves interval scores by 10–19% on those sessions and restores coverage to nominal, while the same rule hurts on the index: the kernel is type‑specific and must be modelled as such.

## 7. Research agenda: news, social media and the neuroscience of collective reaction

The kernel is produced by people, increasingly through social platforms: *post → attention → arousal → herding → order flow → price*. Each link has an empirical and a neural literature — attention capture and attention‑induced trading (Barber et al., 2022; Da et al., 2011); disagreement and herding on investor networks (Cookson & Niessner, 2020; Pedersen, 2022); narratives (Shiller, 2017); collective mood (Bollen et al., 2011; Ranco et al., 2015); reward‑prediction‑error signalling (Schultz et al., 1997); anticipatory neural activity before risky financial choices (Knutson & Bossaerts, 2007; Kuhnen & Knutson, 2005); striatal valuation shifted by herd information (Burke et al., 2010); conformity as a reinforcement‑learning signal (Klucharev et al., 2009); others' opinions re‑weighting value (Campbell‑Meiklejohn et al. 2010); trader arousal in volatility (Lo & Repin, 2002); see Frydman and Camerer (2016) for the bridge to models. We propose: (a) extend the event catalogue into a labelled corpus by source (executive, political, regulator, analyst, wire), channel (social post vs newswire), reach and sentiment; (b) estimate *K* by source × channel, testing whether social‑media‑originated shocks show faster onset, larger short‑horizon continuation and stronger clustering; (c) laboratory reaction‑time and arousal (pupil, skin conductance; fMRI subsample) studies with matched headlines with and without social cues, whose individual kernels mix into *K*; (d) separate forced flow (liquidations, observable in exchange data) from discretionary reaction; (e) longitudinal panels, since kernels learned by users of published forecasts are non‑stationary (Lo, 2004). Such work should be pre‑registered and privacy‑preserving.

## 8. Conclusion

After information arrives, prices behave in type‑specific ways that people have long exploited and that a pattern‑based machine cannot see until it is too late: crypto continues, the index reverts, earnings drift, other stock news does not. Users of the machine's multi‑day schedule cannot recover what it lacks by acting more or less often. The stocks here are the most‑covered mega‑caps; small‑caps and altcoins are the first extension. The path forward is to measure the human response kernel — in markets, on social platforms and in the laboratory — and put it inside the model.

**Figures.** Fig. 1 post‑shock continuation by instrument (`fig10_post_shock_by_type.png`); Fig. 2 2026 NAV of the action policies (`fig11_action_policies_2026.png`); Fig. 3 sessions until the model agrees with the shock direction (`fig7_adaptation_latency.png`).

**Data and code.** Derived data, event catalogues, forecast scores and figures are deposited at Zenodo (DOI [10.5281/zenodo.22308637](https://doi.org/10.5281/zenodo.22308637), CC BY 4.0). Raw price bars (Alpaca Market Data) and news items (Benzinga via Alpaca) are licensed and not redistributed; SHA-256 hashes and the exact retrieval commands are included in the deposit, and all inputs regenerate from the code at https://github.com/hyper07/finance-signal (`research/`). **Conflict of interest.** The authors operate the forecasting service studied; rules were fixed before scoring; the model was not changed.

## References

Ante, L. (2023). How Elon Musk's Twitter activity moves cryptocurrency markets. *Technological Forecasting and Social Change*, *186*, 122112.
Barber, B. M., Huang, X., Odean, T., & Schwarz, C. (2022). Attention‑induced trading and returns: Evidence from Robinhood users. *Journal of Finance*, *77*(6), 3141–3190.
Barberis, N., Shleifer, A., & Vishny, R. (1998). A model of investor sentiment. *Journal of Financial Economics*, *49*(3), 307–343.
Bernard, V. L., & Thomas, J. K. (1989). Post‑earnings‑announcement drift: Delayed price response or risk premium? *Journal of Accounting Research*, 27 (Suppl.), 1–36.
Bollen, J., Mao, H., & Zeng, X. (2011). Twitter mood predicts the stock market. *Journal of Computational Science*, *2*(1), 1–8.
Burke, C. J., Tobler, P. N., Schultz, W., & Baddeley, M. (2010). Striatal BOLD response reflects the impact of herd information on financial decisions. *Frontiers in Human Neuroscience*, *4*, 48.
Campbell‑Meiklejohn, D. K., Bach, D. R., Roepstorff, A., Dolan, R. J., & Frith, C. D. (2010). How the opinion of others affects our valuation of objects. *Current Biology*, *20*(13), 1165–1170.
Chan, W. S. (2003). Stock price reaction to news and no‑news: Drift and reversal after headlines. *Journal of Financial Economics*, *70*(2), 223–260.
Cookson, J. A., & Niessner, M. (2020). Why don't we agree? Evidence from a social network of investors. *Journal of Finance*, *75*(1), 173–228.
Da, Z., Engelberg, J., & Gao, P. (2011). In search of attention. *Journal of Finance*, *66*(5), 1461–1499.
Daniel, K., Hirshleifer, D., & Subrahmanyam, A. (1998). Investor psychology and security market under‑ and overreactions. *Journal of Finance*, *53*(6), 1839–1885.
Frazzini, A. (2006). The disposition effect and underreaction to news. *Journal of Finance*, *61*(4), 2017–2046.
Frydman, C., & Camerer, C. F. (2016). The psychology and neuroscience of financial decision making. *Trends in Cognitive Sciences*, *20*(9), 661–675.
Hirshleifer, D., Lim, S. S., & Teoh, S. H. (2009). Driven to distraction: Extraneous events and underreaction to earnings news. *Journal of Finance*, *64*(5), 2289–2325.
Hong, H., & Stein, J. C. (1999). A unified theory of underreaction, momentum trading, and overreaction in asset markets. *Journal of Finance*, *54*(6), 2143–2184.
Hong, H., Lim, T., & Stein, J. C. (2000). Bad news travels slowly. *Journal of Finance*, *55*(1), 265–295.
Klucharev, V., Hytönen, K., Rijpkema, M., Smidts, A., & Fernández, G. (2009). Reinforcement learning signal predicts social conformity. *Neuron*, *61*(1), 140–151.
Knutson, B., & Bossaerts, P. (2007). Neural antecedents of financial decisions. *Journal of Neuroscience*, *27*(31), 8174–8177.
Kuhnen, C. M., & Knutson, B. (2005). The neural basis of financial risk taking. *Neuron*, *47*(5), 763–770.
Lo, A. W., & Repin, D. V. (2002). The psychophysiology of real‑time financial risk processing. *Journal of Cognitive Neuroscience*, *14*(3), 323–339.
Lo, A. W. (2004). The Adaptive Markets Hypothesis. *Journal of Portfolio Management*, *30*(5), 15–29.
Pedersen, L. H. (2022). Game on: Social networks and markets. *Journal of Financial Economics*, *146*(3), 1097–1119.
Perold, A. F., & Sharpe, W. F. (1988). Dynamic strategies for asset allocation. *Financial Analysts Journal*, *44*(1), 16–27.
Ranco, G., Aleksovski, D., Caldarelli, G., Grčar, M., & Mozetič, I. (2015). The effects of Twitter sentiment on stock price returns. *PLoS ONE*, *10*(9), e0138441.
Schultz, W., Dayan, P., & Montague, P. R. (1997). A neural substrate of prediction and reward. *Science*, *275*(5306), 1593–1599.
Shiller, R. J. (2017). Narrative economics. *American Economic Review*, *107*(4), 967–1004.
