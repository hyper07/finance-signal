# Confidently wrong on the news: a live Bitcoin forecaster around information shocks

**Target: *Finance Research Letters* (short article, ≈2,500 words, 2 tables, 1 figure).** Companion to the full working paper *When the News Arrives* (arXiv, q‑fin.ST). This letter reports only the cryptocurrency results; the full paper and its code are cited for the index and single‑stock extensions.

*Kibaek Kim, Kiok Kim, Danielle Ahn — dotori.ai*

**Abstract.** We audit a deployed seven‑session historical‑analog forecaster that has published immutable daily signals for a Bitcoin ETF pair (BITO/BITI) since January 2026, regenerating every point‑in‑time forecast it could have issued on 1,125 (BITO) and 1,973 (BTC/USD) origins with the production code. Interval calibration is good in calm conditions (78–82% coverage of nominal‑80% bands) but directional accuracy is 46–51% at every horizon and never passes the Pesaran–Timmermann test, and the Brier score is significantly worse than a constant ½ forecast. Conditioning on information arrivals reverses the sign of what little the model does: the day before a |z|≥2.5 shock its next‑session accuracy is 37% (BTC, *p*=0.011), on headline‑spike days 39% (*p*=0.04), and its bands cover none of the shock outcomes. Prices then drift a further 3.0% in the shock direction over seven sessions (*t*=3.06) while the model's consensus takes a median of six sessions to agree. The 2026‑08‑19 White House crypto summit (+21% in three sessions), on which the model recommended a fully inverse position, is the textbook case. Five percent of sessions carry 35% of return variance and are unpredictable in sign from prices: this bounds any price‑conditioned forecaster near the coin, and explains why advertised 60–70% accuracies are ceilings rather than averages.

**Keywords:** Bitcoin; forecast evaluation; news shocks; post‑announcement drift; technical analysis; proper scoring rules. **JEL:** G14, G17, C53.

## 1. Introduction

Retail "AI signal" products publish multi‑day directional forecasts for cryptocurrencies, typically built from technical indicators and nearest‑neighbour analogs of the price path. Their implicit premise — that the state variables governing the next week are functions of past prices — fails by construction when information arrives exogenously, and the human response to that information is not in the state space either. Evidence on technical rules is that apparent skill disappears once data snooping is charged (Brock, Lakonishok & LeBaron 1992; Sullivan, Timmermann & White 1999), and Bitcoin is known to be inefficient but news‑sensitive (Urquhart 2016; Liu & Tsyvinski 2021). What has been missing is an audit of a *deployed* product, on its own frozen live signals, conditioned on exogenous events. This letter provides one and quantifies the gap it reveals.

## 2. Data and method

The forecaster (`historical_analog_v3_consensus`) forms a seven‑dimensional price‑state vector each session, selects the 60 nearest analogs among the trailing 750 sessions whose *h*‑step outcome is observed, volatility‑rescales their outcomes, and reports P10/P50/P90, *P*(up) and a Buy/Sell/Hold vote for *h*=1…7; six concordant votes are a "confirmed" consensus. Prices are Alpaca daily bars (BITO/BITI 2021‑10 → 2026‑08; BTC/USD 2021‑01 → 2026‑08); headlines are the 7,374 Benzinga items in the Alpaca news archive (2024‑02 → 2026‑08). The 168 signals published live in 2026 are frozen exactly as the public saw them; earlier signals are the deployed engine's own walk‑forward output.

For every origin *t* we call the production `build_forecast` on the frame truncated at *t* and score against realized positional outcomes: direction hit (*P̂*≥½ vs *R*>0), Brier score, 10–90 coverage, and standardized surprise *s* = (*R* − *q̂*₅₀)/((*q̂*₉₀ − *q̂*₁₀)/2.5631). Events are fixed before scoring: **return shocks** |*z_T*| = |*r_T*|/σ̂₂₀(*T*−1) ≥ 2.5; **headline spikes** ν*_T* = (*N_T*+1)/(median₃₀+1) ≥ 2, which never references returns. Inference uses Wilson intervals, exact binomial tests, moving‑block bootstraps (block 7) for overlapping horizons, Mann–Whitney tests, and the Pesaran–Timmermann (1992) statistic. All *p*‑values are grouped into families and Benjamini–Hochberg controlled in the full paper.

## 3. Results

**Table 1. Calibration and sequential effectiveness (all origins).**

| | BITO *h*=1 | BITO *h*=7 | BTC *h*=1 | BTC *h*=7 |
|---|---|---|---|---|
| origins | 1,125 | 1,119 | 1,973 | 1,967 |
| directional accuracy (95% CI) | 0.506 (.48–.54) | 0.479 (.45–.51) | 0.488 (.47–.51) | 0.467 (.45–.49) |
| always‑up base rate | 0.487 | 0.519 | 0.495 | 0.510 |
| Pesaran–Timmermann | +0.13 | −0.45* | −1.09 | −1.10* |
| Brier − 0.25 (HAC *t*) | +0.004 (1.7) | +0.018 (3.2) | +0.005 (3.3) | +0.019 (4.9) |
| 10–90 coverage | 0.777 | 0.810 | 0.784 | 0.790 |
| cumulative log Bayes factor vs coin | −9.3 | −43.6 | −20.3 | −78.1 |

\*mean over non‑overlapping subsequences. No horizon on either instrument passes PT>1.645; Brier is significantly worse than the coin at *h*≥2 (BITO) and every *h* (BTC); the cumulative log Bayes factor is negative throughout and below zero 89–100% of the time. Coverage, by contrast, is at nominal: the model knows how wide the distribution is, not which side.

**Table 2. Forecasts around information arrivals (*h*=1).**

| | BITO | BTC |
|---|---|---|
| shock‑window vs calm accuracy | 0.359 vs 0.501 (Δ −0.14, CI −0.20…−0.09) | 0.460 vs 0.489 |
| accuracy the day before a shock (*n*) | 0.375 (48) | **0.367 (98), *p*=0.011** |
| coverage the day before a shock | 0.000 | 0.000 |
| mean |*s*| the day before a shock | 3.68 | 3.59 |
| headline‑spike days: accuracy (*n*) | 0.529 (34) | **0.390 (95), *p*=0.04** |
| headline‑spike days: mean |*s*| vs quiet (MWU) | 1.27 vs 0.87 (*p*=0.005) | 1.15 vs 0.84 (*p*=0.023) |
| headline‑spike days: coverage vs quiet | 0.68 vs 0.78 | 0.68 vs 0.78 |
| consensus aligned with the shock at *T*−1 | 10% | 6% |
| sessions until consensus agrees (median) | 5 | 6 |
| continuation after the shock, 7 sessions (*t*) | +1.71% (1.0) | **+2.98% (3.06)** |

Zero coverage on |*z*|≥2.5 days is nearly mechanical (a 2.5σ move lies outside a ±1.3σ band); the informative results are the *below‑½* directional accuracy — the analog pool is drawn from calm, mean‑reverting regimes and fades moves that continue — and the headline‑spike degradation, whose event definition never sees the return. Shocks cluster (21 of 98 BTC shocks follow another within three sessions) and prices drift on: a trader who takes the shock direction at the shock close earns ≈3% over the week with 62% of events positive, the post‑announcement drift of Chan (2003) in a 24/7 asset, while the model needs six sessions to agree. As a walk‑forward rule net of costs (direction chosen from prior events only), entering at the shock close or the next close earned +2.5% and +2.3% per event at 5 bp (61–64% of events positive, *t* ≈ 2.3–2.5; +1.9–2.1% at 25 bp), halving by the second session and vanishing by the fifth.

**The case.** On 2026‑08‑19 the White House hosted crypto executives and the SEC/CFTC chairs and the President urged passage of the CLARITY Act; Bitcoin rose 7.2%, 5.3% and 7.3% on Aug 19–21 with the largest short liquidation in its history. On Aug 18 the deployed BITO model held a Short 3‑day signal, a Hold consensus (2 Buy/3 Sell) and a next‑session tactical target of −100% (fully in the inverse ETF); its seven‑session P90 path peaked at +3.8% against realized +19% to +23%, every interval missed by 4–8 band‑σ. For BTC spot the consensus was Sell/confirmed (0 Buy, 6 Sell). The consensus turned Buy only on Aug 21, after +19%. (Figure 1.)

**The gap.** Sessions with |*z*|≥2.5 are 5.0% (BTC) and 4.3% (BITO) of the sample but carry 35.4% and 34.4% of return variance. By a simple bound — for any price‑conditioned predictor, accuracy on jump‑dominant news days equals the news‑sign base rate regardless of the predictor — overall accuracy is at most (1−π)*A*_calm + π/2. Calm‑session accuracy here is 0.49–0.51, so the average is the coin; and even 60–70% calm skill would cap the average near 0.60–0.69. Advertised 60–70% figures are ceilings, not averages; in this product a 50‑origin evaluator prints ≥60% on some horizon 14% of days from sampling noise alone.

## 4. Conclusion

A live Bitcoin forecaster is interval‑calibrated but directionally uninformative in calm conditions and systematically on the wrong side of information shocks, whose continuation humans exploit and the model cannot see. Since a third of price variance arrives on such days, no price‑conditioned model can move the average far from ½; the constructive path is to detect when the forecast is unreliable (headline intensity) and to model the human reaction that follows the news rather than the price path that precedes it.

**Figure 1.** Point‑in‑time forecast issued 2026‑08‑18 (P10–P90 band, median) against realized BITO and BTC closes; the dash‑dot line marks the Aug 19 summit. *(research/output/figures/fig1_august_fan_chart.png)*

**Data and code.** Derived data, event catalogues, forecast scores and figures are deposited at Zenodo (DOI [10.5281/zenodo.22308637](https://doi.org/10.5281/zenodo.22308637), CC BY 4.0). Raw price bars (Alpaca Market Data) and news items (Benzinga via Alpaca) are licensed and not redistributed; SHA-256 hashes and the exact retrieval commands are included in the deposit, and all inputs regenerate from the code at https://github.com/hyper07/finance-signal (`research/`). **Conflict of interest.** The authors operate the service whose forecasts are evaluated; rules were fixed before scoring and the model was not changed during the study.

## References

Brock, W., Lakonishok, J., & LeBaron, B. (1992). Simple technical trading rules and the stochastic properties of stock returns. *Journal of Finance*, 47(5), 1731–1764.
Chan, W. S. (2003). Stock price reaction to news and no‑news: drift and reversal after headlines. *Journal of Financial Economics*, 70(2), 223–260.
Liu, Y., & Tsyvinski, A. (2021). Risks and returns of cryptocurrency. *Review of Financial Studies*, 34(6), 2689–2727.
Pesaran, M. H., & Timmermann, A. (1992). A simple nonparametric test of predictive performance. *Journal of Business & Economic Statistics*, 10(4), 461–465.
Sullivan, R., Timmermann, A., & White, H. (1999). Data‑snooping, technical trading rule performance, and the bootstrap. *Journal of Finance*, 54(5), 1647–1691.
Urquhart, A. (2016). The inefficiency of Bitcoin. *Economics Letters*, 148, 80–82.
