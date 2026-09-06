When the News Arrives: Calibration Failure of a Pattern-Based Seven-Session Forecast Around Exogenous Information Shocks in Bitcoin Markets

Working paper — draft v1.0 (2026-09-04). Target: applied mathematics / quantitative finance venue (e.g. Quantitative Finance, Journal of Forecasting, Applied Mathematical Finance, or Frontiers in Applied Mathematics and Statistics).

Kibaek Kim, Kiok Kim, Danielle Ahn — dotori.ai

Code and data pipeline: research/ in the signal repository (see Appendix A).

---

Abstract

Products in the AI market that are aimed at retail investors are increasingly providing multi-day directional forecasts. This study looks at a seven-session historical-analog forecaster which has been issuing live, unchangeable daily signals for the Bitcoin ETF pair (BITO/BITI) on signal.dotori.ai since 2026-01-02. By using the same production code, all the forecasts that the model could have produced between 2022 and 2026 were reconstructed with an offline Alpaca price database (1,125 sources for BITO; 1,973 for BTC/USD spot), and the seven-horizon predictive distributions were compared with the actual outcomes. Unconditionally, directional accuracy is 46–51% at each horizon for both instruments and never significantly goes above 50%, while the nominal-80% prediction intervals include 78–82% of the outcomes — the model is interval-calibrated but is directionally uninformative under calm conditions. The analysis then considers exogenous information shocks defined as (i) spikes in headline news items (crypto-tagged newswire items at least twice the trailing median, not referring to returns) and (ii) standardized return shocks with $|z|\ge 2.5$. On days with a headline spike, the next-session directional accuracy of BTC forecasts falls to 39.0% (95% CI 29.8–49.0, $p=0.04$ compared to 50%), the standardized forecast surprise increases by about one third (Mann–Whitney $p=0.02$), and interval coverage decreases by 10 percentage points; forecasts issued the day before a shock show 0% coverage and an average absolute surprise of 3.6 band-$\sigma$. After a shock, prices continue in the direction of the shock for a week (BTC: +2.98% sign-adjusted over seven sessions, $t=3.06$, $p=0.003$, 98 events), yet the model’s seven-vote consensus agrees with the shock direction in only 6–10% of cases and takes a median of five to six sessions to reach agreement. A walk-forward, cost-adjusted rule shows that continuation can only be taken advantage of in Bitcoin and only if action is taken within one session (+2.3% net per event at 5 bp, 64% of events), while attempts to follow index or single-stock movements result in losses when costs are taken into account. The 2026-08-19 White House crypto summit, during which Bitcoin rose by 21% over three sessions (the largest short liquidation in its history), is examined as a case study: on 2026-08-18 the model advised a $-100%$ (fully inverse) tactical position, and its seven-session P90 path reached a peak of +3.8%. The analysis shows that the 60–65% accuracy figures remembered from the product’s 50-origin evaluator are consistent with sampling noise (the standard deviation is approximately 0.06–0.07 per reading; at least one of the seven horizons reached 60% or above on 14% of days in 2026). Formal sequential tests confirm this: no horizon passes the Pesaran–Timmermann directional test, the Brier score is significantly worse than the constant $\tfrac12$ forecast at almost every horizon (HAC $t$ = 1.7–4.9), and the cumulative log Bayes factor against a fair coin is negative throughout ($-9$ to $-78$ nats, below zero 89–100% of the time). When the protocol is extended to the deployed S&P 500 pair (SPXL/SPXS), SPY and 50 individual stocks (2,584–4,097 origins each; 204,129 next-session stock forecasts), the same engine performs differently depending on the asset type: index shocks are two-thirds downward, revert ($-0.5$ to $-1.4%$ over seven sessions) and reduce the forecaster’s accuracy from 0.60–0.62 to 0.34–0.36 within the shock period, whereas single-stock shocks are idiosyncratic own-news jumps (headline spikes for the individual ticker triple the shock probability) on which the forecaster is no better or worse than during calm periods; at seven sessions the simple "always up" rule outperforms the forecaster on all eight instruments. Simulations of acting on the published schedule on a daily, weekly, or monthly basis show no dominant strategy—the rankings vary from instrument to instrument and over time—and the committed weekly schedule differs from daily re-forecasting by at least 25 exposure points on 66–75% of sessions. A fully exogenous test based on calendar events confirms the mechanism: on earnings days (known years in advance) the stocks’ nominal-80% bands cover 25–27% of the outcomes and forecast surprise is 3–4 times larger ($p<10^{-5}$), on FOMC days SPY accuracy drops to 0.40 ($p=0.016$), and crypto is not affected by FOMC days — the forecaster has no event calendar of any kind; when the 50 stocks are pooled the Pesaran–Timmermann statistic is 3.08, indicating a real but economically negligible 0.3-point directional dependence, while the Brier score is worse than that of a coin for 98% of the stocks. A constructive test concludes the analysis: a causal, event-conditional gate estimated in a walk-forward manner improves the interval score on earnings sessions by 16% across the 50 stocks (coverage rises from 0.49 to 0.68, confidence interval does not include zero) and after crypto shocks by 7–17%, while the same rule has a negative effect on the stocks and the index on calendar days—the choice of gate depends on the type of event. Under Benjamini–Hochberg control over all 228 reported tests, no directional-skill test survives, although distributional failures remain. The findings support the use of type-specific model families rather than a single shared indicator-voter set. The central thesis is expressed as a bound: for a price-conditioned forecaster, directional accuracy is bounded above by the frequency and sign-unpredictability of information arrivals and below by the skill observed during calm periods; in this study, 3–5% of sessions account for 28–37% of return variance, accuracy during calm periods is at chance level, and the returns that the product appears to capture are due to exposure, not prediction. The results indicate that human reaction to news represents an unmodelled state process — a jump followed by a behavioural response kernel — and a research programme in mathematics and neuroscience is proposed to measure this kernel so that it can be incorporated into forecasting models rather than remaining as unexplained error.

Keywords: forecast calibration; event study; historical analogs; nearest-neighbour forecasting; Bitcoin; news shocks; post-announcement drift; behavioral finance; neuroeconomics; proper scoring rules.

---

1. Introduction

Forecasting models based on price patterns—such as technical-indicator ensembles, nearest-neighbour (“analog”) predictors, and small supervised classifiers—take into account only the historical course of the price itself. The assumption that underlies these models is that the state variables important for the next few sessions are determined by that historical course. Exogenous information (a policy announcement, a regulatory decision, an executive statement) violates this assumption: the information arrives as a jump that no price feature anticipates, and the market’s response to it is produced by human agents whose behavior (attention, herding, forced liquidation, delayed reaction) is not in the model’s state space either.

This paper asks a narrow, measurable question about one such model that is actually deployed: how does the quality of its seven-session predictive distribution change on and around days when exogenous news arrives, and how do humans trade after those days relative to what the model recommends? We deliberately evaluate the production code rather than a re-implementation, and we use the model’s own frozen live signals for 2026 so that no hindsight enters the reproduction.

Three features distinguish the design from a typical backtest report:

1. Exhaustive, point-in-time evaluation. Every origin between the warm-up period and the end of the archive is scored, not a 50-origin sample. The various features and analog pools are calculated based on the data observed at or before the origin; the code path used is the one that publishes live.
2. Two independent event definitions. Return-based shocks ($|z|\ge 2.5$) are the natural definition but partially tautological for interval coverage, since a $2.5\sigma$ move lies outside a $\pm 1.3\sigma$ band by construction. For this reason we also make use of a definition which is based on the number of headlines and which never examines the return.
3. A human-behavior counterfactual. For every shock we measure what a trader who acts after seeing the news (buying/selling at the shock-day close) would have earned over the next 1–7 sessions, and how many sessions the model needed to agree.

1.1 Related work

The problem of technical rules and data snooping is dealt with by citing Brock et al. (1992), who found that moving-average and trading-range rules showed apparent predictive ability; Sullivan et al. (1999) showed that, when looking at the complete set of rules under examination, the best rule's performance is in line with chance, and Bailey et al. (2014) expressed this phenomenon as backtest overfitting. The example in section 4.2 is a small-scale case: a 50-origin evaluation which, when it prints seven horizons, shows 60% or more on one of them 14% of the time. Analog forecasting stems from Lorenz's (1969) atmospheric analogues and from Farmer and Sidorowich's (1987) local prediction of chaotic series; in finance, any kind of return predictability is fragile when tested out of sample (Timmermann, 2018; Welch & Goyal, 2008). The methods used to evaluate forecasts are the ones we follow: proper scoring rules (Brier, 1950; Gneiting & Raftery, 2007), comparative accuracy tests (Diebold & Mariano, 1995; Newey & West, 1987), the directional test of Pesaran and Timmermann (1992), the variance ratio of Lo and MacKinlay (1988) and false-discovery control (Benjamini & Hochberg, 1995). Regarding news and returns, Tetlock (2007) connected media content to price pressure; Chan (2003) found a drift following news and a reversal following no-news moves; Bernard and Thomas (1989) identified the post-earnings-announcement drift which section 5.5 reproduces in a small way; Hong et al. (2000) and Frazzini (2006) associate slow diffusion and under-reaction with investor behaviour; Hirshleifer et al. (2009) and Da et al. (2011) indicate that attention constraints affect the speed of reaction. The inefficiency of cryptocurrencies and their sensitivity to news are documented by Urquhart (2016), Corbet et al. (2019) and Liu and Tsyvinski (2021); the behavioural models of Barberis et al. (1998), Daniel et al. (1998) and Hong and Stein (1999) provide the vocabulary of under- and over-reaction that we use.

In this regard, the paper makes the following contributions: (i) an audit protocol for a retail forecasting product that uses immutable live signals—comprehensive, point-in-time, and based on the production code; (ii) the use of exogenous events defined in three different ways (headline spikes, return shocks, and public calendars) together with the sign of a failure, revealing a pattern model which is contrarian to moves driven by news that continue; (iii) formal sequential effectiveness tests and basic propositions that explain why the sign is as it is; (iv) evidence that the same system fails in three different ways when applied to crypto, an equity index and individual stocks, with a type-specific architecture obtained from measured fingerprints; and (v) a simulation of the actions a user should take according to a multi-day schedule, demonstrating that no particular cadence stands out. Overall, the results are mostly negative for the forecaster and support the behavioural hypothesis, which is why the discussion in Section 8 is included.

---

2. Data and the deployed model

2.1 Price data

Column 1	Column 2	Column 3	Column 4	Column 5
Series	Source	Rows	Span	Notes
BITO, BITI (adjusted daily OHLC)	Alpaca Market Data, SIP feed	1,220	2021-10-19 → 2026-08-28	Long/inverse ETF pair used by the deployed b04_prediction_us_coin dataset
BTC/USD (daily)	Alpaca crypto	2,068	2021-01-01 → 2026-08-30	24/7 calendar days
SPXL, SPXS, SPY, QQQ, TLT, GLD (adjusted daily)	Alpaca, SIP	2,679 each (SPXS 2,346)	2016-01-04 → 2026-08-28	deployed b01_prediction_us_snp pair; index/bond/commodity comparators
AAPL, MSFT, TSLA, NVDA (adjusted daily, splits)	Yahoo snapshot saved in research/output	4,070–4,192	2010-01-04 → 2026-09-02	deployed s01–s04 datasets
46 further S&P 500 stocks (adjusted daily, splits) + earnings dates	Yahoo snapshot	3,593–4,192 each	2010/2012 → 2026-09-02	deployed s00 datasets (Section 5.7)
Newswire items	Alpaca News (Benzinga)	7,374	2024-02-01 → 2026-08-28	Crypto-tagged subset used for news intensity
Published live signals (b01, b04, s01–s04)	signal.dotori.ai public API	168 each	2026-01-02 → 2026-09-02	Immutable; frozen cache (stocks live from 2026-07-30)


The Alpaca archive contains two entries for each (symbol, day) combination—those for IEX and for the consolidated SIP—and we retain the row with the higher volume (SIP). Adjusted prices are used for indicators, matching production (auto_adjust=True in the deployed fetcher).

2.2 The deployed signal engine (3-day classifier)

The production engine (in model/strategy.py::run_simulation) computes approximately 40 binary technical indicator signals every day and, each day, selects the seven indicators which have the highest hit rate when compared to the direction three days ahead, based on a 10-day look-back period that ends three sessions prior to the decision date (in this way making sure that all the labels used have already been realised). A weighted vote leads to a signal $S_t\in{-1,0,+1}$ (Short/Hold/Long). In the case of BITO the Short position involves the inverse ETF BITI and the signals which have been made live from 2026-01-01 are kept in a cache and are never recomputed.

2.3 The seven-session forecast (model/forecast.py, version historical_analog_v3_consensus)

At origin $t$ the model forms a feature vector
$$x_t=\big(r_t,;m^{(5)}t,;m^{(20)}t,;\tau_t,;\sigma^{(20)}t,;\rho_t,;\pi_t\big),$$
For each horizon h belonging to the set {1, ..., 7}, the trailing 750 candidate origins i are taken whose outcome R{i,h} = C{i+h}/C_i - 1 has already been observed, each of these outcomes is then rescaled by a factor of min(max(σ_t/σ_i, 0.5), 2) to take account of the current volatility environment, and the K = 60 closest analogs are selected using the standardized Euclidean distance.
$$d(x_t,x_i)=\Big(\tfrac{1}{7}\sum_j \big((x{t,j}-x_{i,j})/s_j\big)^2\Big)^{1/2}.$$
The empirical distribution of the 60 rescaled outcomes yields $\hat q_{10},\hat q_{50},\hat q_{90}$, $\hat p_h=\hat P(R>0)$, the probability per session of an up move, and a Buy/Sell/Hold vote for each horizon (a Buy is indicated if $\hat q^{sess}{50}>0$ and $\hat p^{sess}\ge0.55$; Sell is decided in a symmetric manner). A consensus of six or more concordant votes is considered "confirmed" (this results in a full move to the target exposure), while exactly five is a "warning" (this corresponds to a half move). There is also a separate schedule which transforms the score $0.45(2\hat p_h-1)+0.35,\hat q{50}/\text{risk}+0.20,\pi_t$ into a tactical exposure path restricted to the interval $[-100%,100%]$ for inverse-ETF datasets.

2.4 Offline reproduction and its fidelity

We reconstructed the production detailed frame from the Alpaca archive using the deployed run_simulation, keeping the 168 published 2026 signals fixed in exactly the same way as the live service does. To evaluate how accurate the unfrozen engine is, we ran it without freezing and then compared the results to the published records for the 165 overlapping days: the signal agreement was 76.4% (on a monthly basis this is 70/95/36/71/85/91/91/75%); the adjusted-close discrepancy relative to the median of the published series was 0.004%, the highest being 0.20%. The reasons for the discrepancies are (a) the different adjustment procedures between Yahoo and Alpaca and (b) the sector-rotation attention feature, which includes eleven sector ETFs that we do not archive and which is set to its neutral value (0) when the system is offline. Because our study uses the frozen frame, all of the 2026 results exactly match the signals that the public saw; the pre-2026 signals are the engine’s own walk-forward outputs, as in production (and these generate the pre-live rows). The rotation feature has a neutral effect in all of our analog distance measurements; this is a known deviation from production and is the main factor preventing an exact replication of the production forecasts. For the other deployed datasets, the agreement when the engine is unfrozen is 84.2% for the S&P pair (over 165 days; median close gap 0.001%) and 93 to 100% for the four stocks (AAPL and NVDA at 100%, MSFT at 94%, TSLA at 93%; with regard to the 25 live rows since 2026-07-30: 100/100/100/76%). The high level of agreement among the stocks is rather uncomfortable because the cash-mode 200-day trend filter results in "Long" being selected for 90 to 93% of all sessions and for each of the 168 published 2026 rows for both AAPL and NVDA, so there is very little for the indicator voters to disagree about.

---

3. Methods

3.1 Rolling-origin protocol

For every origin position t (ranging from the 60th row to the penultimate row) we call build_forecast on the frame that has been truncated at t (this truncation is what ensures the no-look-ahead guarantee; the same method is employed in the model’s unit test test_future_rows_cannot_change_point_in_time_forecast). The realised returns are based on position: R_{t,h} = C_{t+h}/C_t - 1 and the session return is r_{t+h} = C_{t+h}/C_{t+h-1} - 1. (In the production payload the crypto-flagged datasets are labelled with calendar dates even though the instrument in question is an exchange-traded ETF; we calculate the returns on a positional basis, since that is exactly what the analogous construction does, and mention the defect relating to the date labelling in Appendix B.)

3.2 Scoring rules

For origin $t$ and horizon $h$:

* Direction hit $H_{t,h}=\mathbf 1{\hat p_{t,h}\ge 0.5}=\mathbf 1{R_{t,h}>0}$ (the evaluator’s convention).
* Brier score $(\hat p_{t,h}-\mathbf 1{R_{t,h}>0})^2$ (Brier, 1950), a strictly proper score for the probability.
* Interval coverage $\mathbf 1{\hat q_{10}\le R_{t,h}\le \hat q_{90}}$, nominal 0.80.
* Standardized surprise $s_{t,h}=(R_{t,h}-\hat q_{50})\big/\big((\hat q_{90}-\hat q_{10})/2.5631\big)$, which expresses the realized outcome in units of the forecast’s own dispersion (for a Gaussian band the 10–90 width is $2\times1.2816\sigma$). $|s|>1.28$ means “outside the band”.
* Base rate $\bar u_h=\text{mean},\mathbf 1{R_{t,h}>0}$, so that accuracy can be compared with “always up”.

3.3 Event definitions (fixed before scoring)

* Return shock (z-shock). $z_T=r_T/\hat\sigma^{(20)}_{T-1}$ with the trailing SD computed through $T-1$; a shock is $|z_T|\ge 2.5$. Sensitivity at 2.0, 3.0, 3.5 is reported.
* There's a headline spike. $N_T$ represents the number of Benzinga articles on day $T$ that are tagged BTCUSD/BITO/IBIT/BITI/MSTR/COIN or contain the words bitcoin|crypto|btc|stablecoin|digital asset; articles published over the weekend are assigned to the following session. The intensity ratio is given by $\nu_T = (N_T + 1)/(\tilde N^{(30)}_{T-1} + 1)$, where $\tilde N^{(30)}$ is the median of the figures from the previous 30 days; a spike is identified when $\nu_T \ge 2$ occurs at least twice. Coverage began on 2024-02-01.
* Three-day episode. $|C_T/C_{T-3}-1|\ge 10%$ (used only descriptively).

A “shock window” is any $(t,h)$ pair whose target span $(t,t+h]$ contains a z-shock day.

3.4 Human-behavior counterfactual and model latency

For every z-shock day T with direction D_T equal to the sign of r_T, we note the sign-adjusted continuation D_T,(C_{T+k}/C_T - 1) for k in the set {1, 2, 3, 5, 7}: this relates to the return obtained by a trader who, having observed the news and the price movement, takes a position in the direction of the shock at the close of day T. We also record whether the 3-day signal and the seven-vote consensus were already in line with D_T on the previous day, T-1; and if they were not, we note the number of sessions after T until they first become aligned (with a maximum of 15).

3.5 Inference

We apply Wilson score intervals and exact binomial tests to the hit rates; in the case of the differences between the overlapping-horizon groups we use a moving-block bootstrap (with a block length of 7 and 4,000 draws); Mann–Whitney U tests are applied to the surprise distributions; Spearman rank correlation is used to look at monotone dependence on news intensity; one-sample t tests are carried out for the continuation returns. Rather than merely reporting the best horizon we report all the horizons and address the problem of multiplicity in Section 7.

3.6 Pre-specified rules and multiplicity

The event definitions (Section 3.3), the scoring rules (3.2), the horizons, the shock threshold, the news-intensity threshold and the policy cadences (6.4) were all set prior to any forecasting being scored, and no rule was altered after the results had been observed; sensitivity with respect to the shock threshold is given (Section 5.1). Since the study includes eight instruments × seven horizons × several conditioning splits, we classify each p-value reported into pre-specified groups (direction versus ½; Pesaran–Timmermann skill; Brier versus the coin; shock versus calm; pre-event direction; post-shock continuation; headline-spike direction and surprise; scheduled-event direction and surprise) and apply the Benjamini–Hochberg false-discovery control both within each group and jointly across all the groups (Section 4.4). For horizons h>1 the Pesaran–Timmermann statistic that enters the group is the average of the h non-overlapping subsequences, not the overlap-inflated full-sample value.

---

4. Results I — unconditional calibration and the “65%” question

4.1 Directional accuracy is not distinguishable from 50%

Table 1. Rolling-origin calibration by horizon, all origins. (Fig. 3)

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9	Column 10	Column 11	Column 12
	BITO — hit	95% CI	base $\bar u$	Brier	cover.		BTC — hit	95% CI	base $\bar u$	Brier	cover.
$h=1$	0.506	.477–.535	.487	.254	.777		0.488	.466–.510	.495	.255	.784
$h=2$	0.471	.443–.501	.496	.260	.787		0.500	.478–.522	.512	.257	.788
$h=3$	0.460	.431–.489	.510	.264	.795		0.489	.467–.511	.519	.259	.794
$h=4$	0.479	.450–.509	.512	.262	.800		0.489	.467–.511	.511	.261	.796
$h=5$	0.481	.452–.510	.518	.264	.810		0.476	.454–.498	.514	.264	.796
$h=6$	0.495	.466–.525	.513	.263	.816		0.483	.461–.505	.514	.266	.794
$h=7$	0.479	.450–.508	.519	.268	.810		0.467	.445–.489	.510	.269	.790


The time period in question is from $n=1{,}119$ to $1{,}125$ (for BITO, 4 March 2022 to 27 August 2026) and from $1{,}967$ to $1{,}973$ (for BTC, 5 April 2021 to 29 August 2026). In both cases the figures are well below 0.5 (BITO having $h=3$ and $p=0.007$; BTC having $h=7$ and $p=0.004$), although neither of them is significantly above this level. The Brier scores, which vary between 0.25 and 0.27, are either at or worse than those obtained with the fixed forecast $\hat p=0.5$ (which has a Brier score of 0.25). If we consider only the year 2026 (the live period), the scores are BITO 0.45 to 0.52 and BTC 0.41 to 0.50 (for BTC with $h=7$: 0.413, $p=0.009$). The proportion of votes given per session (taking into account only the Buy and Sell options) is 49 to 52%.

Figure 3. Directional accuracy (95% Wilson) and 10–90 coverage by horizon.

On the other hand, interval calibration is satisfactory: at each horizon the empirical 10–90 coverage ranges from 0.78 to 0.82 compared with the nominal value of 0.80, and the mean absolute standardized surprise is 0.77 to 0.89 (which is about what would be expected, namely 0.80, for a well-calibrated Gaussian band). The model therefore knows the width of the distribution under normal conditions but does not know which side the outcome will fall on—this is a typical case of a 'calibrated but not sharp' forecaster.

4.2 Where a 60–65% reading comes from

The evaluator (evaluate_forecast.py) normally uses 50 origins, with these being selected once every five sessions. When this design is re-applied to the full set of results (2,000 random 50-origin windows) the accuracy for h=1 is on average 0.514 with a standard deviation of 0.060 for BITO and an average of 0.498 with a standard deviation of 0.065 for BTC; 14% (in the case of BITO) and 10% (for BTC) of the windows show a value of at least 0.60, and 0.7 to 1.4% show a value of at least 0.65 (the highest values observed being 0.66 and 0.70). When it is recalculated what the evaluator would have shown each day in 2026 for BITO, the h=5 figure varied between 0.44 and 0.58 and never reached 0.60; the best reading across all the horizons was at h=4 on 2026-06-26 with a value of 0.62, and at least one of the seven horizons reached at least 0.60 on 14% of the days (Fig. 8). The remembered figure of "61–63% on day 5" is therefore very probably a noisy reading based on a different dataset or the result of a look-elsewhere effect across the seven horizons; with n=50 the 95% Wilson interval around 0.62 extends from 0.48 to 0.74.

Figure 8. Distribution of the evaluator's 50-origin accuracy when the exhaustive rate is about 50%.

The next-day directional hit rate for the 3-day published signal—which includes the period of 2026 and comprises 133 active Long/Short days—is 0.534 (with a p-value of 0.49), this figure varying from 0.67 in February to 0.385 in July; the +77% cumulative return of the strategy as compared to a -13.6% buy-and-hold result is the result of exposure asymmetry (since of the inverse position taken during the spring drawdown) and not because of directional accuracy.

4.3 Formal tests of predictive effectiveness in series

The three standard sequential criteria are applied in order to establish what is meant by "effectiveness in series", each of the criteria being computed over the whole original sequence (see Table 2). (i) The Pesaran–Timmermann (1992) statistic is employed to determine whether the predicted and actual directions are independent, taking into account possibly unequal base rates; it has an asymptotic distribution of $N(0,1)$, and any values above 1.645 signify a degree of skill at the 5% one-sided level. Since for $h>1$ there is overlap among consecutive outcomes, we also calculate the statistic for the $h$ non-overlapping subsequences (that is, every $h$-th origin) and give the mean and the range of these. (ii) A Diebold–Mariano-type test is carried out on the Brier loss against the constant forecast $\hat p\equiv\tfrac12$ (loss 0.25): $d_t=(\hat p_t-y_t)^2-0.25$, using the Newey–West long-run variance (Bartlett kernel, lag $h$); a positive mean indicates that the model is performing worse than the coin. (iii) The cumulative log Bayes factor $\Lambda_n=\sum_{t\le n}\big[y_t\log\hat p_t+(1-y_t)\log(1-\hat p_t)+\log 2\big]$ (with the probabilities clipped to $[0.02,0.98]$) is used, and under calibration the expected value at each step is equal to the Kullback–Leibler divergence $\mathrm{KL}(\hat p_t,|,\tfrac12)\ge0$ — consequently, an effective probabilistic forecaster produces a submartingale that tends to increase, and the even-odds Kelly bet of fraction $2\hat p_t-1$ has a positive expected log growth. We provide $\Lambda_n$, the proportion of the sequence that is below zero, and the realized Kelly growth per session.

Table 2. Effectiveness in series, all origins. PT = Pesaran–Timmermann statistic (all origins / mean over non-overlapping subsequences [min, max]); NW $t$ = HAC $t$ of mean Brier excess over 0.25; $\Lambda_n$ in nats; Kelly in basis points of log wealth per session.

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9	Column 10	Column 11
$h$	BITO PT all	PT non-overlap	Brier−0.25 (NW $t$)	$\Lambda_n$	Kelly bps	BTC PT all	PT non-overlap	Brier−0.25 (NW $t$)	$\Lambda_n$	Kelly bps
1	+0.13	+0.13	+0.0040 (1.72)	−9.3	−82	−1.09	−1.09	+0.0050 (3.27)	−20.3	−103
2	−1.98	−1.42 [−1.46, −1.38]	+0.0096 (3.81)	−22.2	−198	+0.01	−0.01 [−0.39, +0.38]	+0.0072 (3.67)	−29.6	−150
3	−2.65	−1.54 [−2.25, −1.09]	+0.0136 (4.50)	−31.7	−282	−1.12	−0.63 [−1.68, +0.27]	+0.0089 (3.93)	−36.3	−184
4	−1.25	−0.62 [−1.36, +0.02]	+0.0115 (2.99)	−27.0	−241	−0.94	−0.48 [−1.52, +0.35]	+0.0106 (3.98)	−43.3	−220
5	−1.08	−0.47 [−1.78, +0.59]	+0.0140 (3.41)	−33.0	−295	−2.17	−0.98 [−1.72, −0.65]	+0.0137 (4.24)	−56.4	−286
6	−0.07	−0.04 [−1.08, +1.30]	+0.0128 (2.56)	−30.9	−276	−1.62	−0.67 [−1.43, +0.20]	+0.0161 (4.46)	−66.6	−338
7	−1.17	−0.45 [−1.18, +0.36]	+0.0181 (3.23)	−43.6	−390	−2.91	−1.10 [−2.33, +1.37]	+0.0190 (4.92)	−78.1	−397


On neither instrument is there a horizon at which the value reaches PT $>1.645$ in the entire sequence, and this is also true for no non-overlapping subsequence (the highest value being 1.37). The Brier score exceeds that of the coin at all horizons and is significant for BITO at $h\ge2$ and at all values of $h$ for BTC: the model is not just uninformative but is confidently miscalibrated. $\Lambda_n$ is negative at all horizons, lies below zero for 89 to 100% of the sequence, and results in a loss of 0.012 to 0.057 bits per forecast; if even odds had been used when betting according to the stated probabilities, a loss of 82 to 397 bp of log wealth per session would have occurred. For the conditional case at $h=1$ (as shown in Table 3), the calm sessions cannot be distinguished from those of the coin (PT +0.47 / −0.54), whereas during shock sessions BTC shows a significant lack of skill (PT −2.49, one-sided $p=0.994$; Kelly −390 bp per session) and on headline-spike days the PT is −1.81; this is the empirical content of Proposition 2 below.

Table 3. $h=1$ effectiveness by regime.

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9
subset	BITO $n$	PT	Brier NW $t$	Kelly bps	BTC $n$	PT	Brier NW $t$	Kelly bps
calm sessions	1,077	+0.47	1.25	−61	1,875	−0.54	2.75	−88
shock sessions ($\lvert z\rvert\ge2.5$)	48	−1.71	2.25	−572	98	−2.49	2.69	−390
quiet news days	612	−0.24	0.62	−39	847	−0.03	2.43	−105
headline-spike days	34	+1.22	1.79	−422	95	−1.81	1.94	−288
live period 2026	164	−1.40	2.08	−252	241	−1.07	2.34	−148


4.4 What survives false-discovery control

The analysis shown in Table 13 a applies Benjamini–Hochberg control to all of the p-values provided in the paper (including 228 tests spread over ten pre-determined families; see Section 3.6). This pattern represents the paper's argument in tabular form. No Pesaran–Timmermann skill test remains significant at any horizon for any instrument (0 out of 56, whether within-family or pooled). The distributional findings are still valid: the Brier score is worse than the constant forecast in 22 out of 56 instrument–horizon combinations; the shock-window accuracy deficit persists for 5 of the 8 instruments (BITO, SPXL, SPY, AAPL, MSFT); forecast surprise is greater on scheduled-event days in 10 of the 16 instrument–calendar pairs (for all four earnings sets, the payrolls for SPY and SPXL, and the BTC payrolls) and on headline-spike days for both crypto instruments. Of the 34 results that are significantly above ½ and that survive, all relate to index or single-stock horizons where the always-up base rate is higher than the model’s accuracy — that is, to base-rate inflation rather than to skill — and the two that survive below ½ are connected with crypto horizons. The per-event directional results are the paper’s weakest points when multiplicity is taken into account: the 37% pre-shock accuracy (BTC q = 0.09 within family, 0.035 pooled; BITO q = 0.26), the 39% headline-spike accuracy (BTC q = 0.08) and the drop in FOMC-day accuracy on SPY (q = 0.60) are only suggestive at q ≤ 0.10 or lower and should be interpreted as such; the BTC seven-session continuation does survive (q = 0.023). The conclusions on which the paper is based — the absence of skill, confident miscalibration, and the degradation of the predictive distribution on days with exogenous events — are the ones that remain.

Table 13. Benjamini–Hochberg survivors at $q\le0.05$ by family (within-family / pooled across all 228 tests).

Column 1	Column 2	Column 3	Column 4	Column 5
family	tests	survive within	survive pooled	reading
A direction vs ½ (binomial)	56	36	35	34 above ½ (index/stock drift, below base rate), 2 below ½ (crypto)
B Pesaran–Timmermann skill	56	0	0	no directional skill anywhere
C Brier worse than coin (HAC)	56	22	21	confident miscalibration
D shock-window vs calm hit	8	5	5	BITO, SPXL, SPY, AAPL, MSFT
E pre-event $h$=1 direction	8	0	1	suggestive only
F 7-session continuation	8	1	1	BTC
G headline-spike direction	2	0	0	suggestive only
H headline-spike surprise	2	2	1	BITO, BTC
I scheduled-event direction	16	0	0	none
J scheduled-event surprise	16	10	9	all earnings sets; payrolls
all	228	—	73 (79 at $q\le0.10$)	


---

5. Results II — forecasts around information shocks

5.1 Return-defined shocks

Table 4. Shock windows vs calm windows (all horizons pooled).

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7
	BITO shock	BITO calm	Δ (block-bootstrap 95% CI)	BTC shock	BTC calm	Δ
$n$ (origin×horizon)	1,079	6,775		2,315	11,475	
direction hit	0.359	0.501	−0.143 (−0.196, −0.089)	0.460	0.489	−0.029 (−0.072, +0.013)
10–90 coverage	0.361	0.869	−0.508 (−0.567, −0.451)	0.393	0.872	−0.480 (−0.518, −0.438)
mean $	s	$	1.97	0.64		1.93
Brier	0.288	0.258		0.270	0.260	


The decrease in coverage is to some extent the result of mechanical factors (as mentioned in Section 1). However, the directional aspect of it is not: with regard to BITO, the forecasts that have a target span covering a shock are wrong 64% of the time, representing a 14-point deficit which is still significant at all thresholds from $|z|\ge2.0$ to $3.5$ (the figure for shocks within the window being 0.36–0.40 as compared with 0.49–0.51 for calm periods). In the case of BTC the deficit is smaller (0.46 compared to 0.49) and is not significant.

When the moves realised in the following session are grouped according to their size (see Fig. 4, left), the accuracy for $h=1$ remains at about 0.50 up to $|z|<2.5$ before dropping to 0.375 (BITO, $n=48$) and 0.367 (BTC, $n=98$, $p=0.011$). The model is consistently incorrect when it comes to the largest moves, a result that is to be expected if the analogues are based on mean-reverting calm periods since, after a two-day rise, the nearest neighbours say "fade" and news-driven trends do not fade.

Figure 4. Next-session direction and coverage by realized |z| and by headline intensity.

5.2 Headline-defined shocks (non-tautological)

Table 5. Next-session forecasts on headline-spike days ($\nu_T\ge2$) vs quiet days, 2024-02 → 2026-08.

Column 1	Column 2	Column 3	Column 4	Column 5
	BITO spike	BITO quiet	BTC spike	BTC quiet
days	34	612	95	847
direction hit (95% CI)	0.529 (.37–.69)	0.500	0.390 (.30–.49), $p=0.04$	0.499
10–90 coverage	0.676	0.776	0.684	0.783
Δ coverage (bootstrap CI)	−0.100 (−0.227, +0.013), $p=0.08$		−0.099 (−0.220, +0.011), $p=0.08$	
mean / median $	s	$	1.27 / 1.05	0.87 / 0.71
Mann–Whitney $	s	$ spike > quiet	$p=0.005$	
mean $	r	$ (%)	2.76	2.36
share of days with $	z	\ge2.5$	8.8%	3.3%


The relationship between headline spikes and large returns is only weak (returns are 2.7 to 2.8 times the base rate of $|z|\ge2.5$ days, but 88 to 92% of the days on which there is a spike are not z-shocks), so this test is mostly independent of Section 5.1. However, on days when there are spikes the forecast surprise is much higher for both instruments, coverage falls by about 10 points, and for BTC the directional accuracy drops to 39%. Over the entire sample of days on which news is covered, the Spearman correlations of $\nu_T$ with coverage are −0.11 (for BITO, p=0.004) and −0.18 (for BTC, p<10^{-4}), and with $|s|$ they are +0.15 and +0.23 (p≤10^{-4}); the correlation with the direction hit is approximately zero in both cases (see Fig. 4, right). News does not just impair the model's ability to predict the sign; it also degrades the model's distribution, since the more headlines there are, the further the actual outcome lies from the median forecast, measured in the forecast's own units.

On the day preceding the spike (for each of the seven horizons) the forecast paths were at 0.43 (BITO) and 0.45 (BTC) with coverage levels of 0.58 and 0.66, while on other days the figures were 0.50/0.81 and 0.49/0.79.

5.3 The forecast issued the day before a shock

Table 6. Forecasts made at $T-1$ for the 48 (BITO) and 98 (BTC) z-shock days.

Column 1	Column 2	Column 3
	BITO	BTC
events (up / down)	48 (26 / 22)	98 (55 / 43)
$h=1$ direction hit (Wilson 95%)	0.375 (.25–.52), $p=0.11$	0.367 (.28–.47), $p=0.011$
$h=1$ coverage	0.000	0.000
mean $	s_1	$
7-session path coverage	0.277	0.300
direction hits over $h=1…7$ (of 7)	2.54	3.26
3-day signal already aligned at $T-1$	50%	48%
7-vote consensus already aligned at $T-1$	10.4%	6.1%


The 3-day signal agrees with the upcoming shock as often as a coin toss, while the seven-session consensus almost never does (Fig. 7).

Figure 5. Standardized surprise at h=1 on calm vs shock sessions.

5.4 Other asset types: the index pair and single stocks

The service currently uses a single indicator-voter engine and one analog forecaster for cryptocurrencies, for the S&P 500 pair and for several hundred individual stocks; the only variations being the cash-mode trend/multi-horizon filters and the inverse leg. In the case of applying the same protocol to the S&P dataset that is in use (SPXL/SPXS, with the 2026 signals fixed), compared to SPY spot and the four major stocks (AAPL, MSFT, TSLA, NVDA; with the live signals from 2026-07-30 onwards held fixed), it turns out that the common engine is dealing with a different prediction problem for each of the asset types. (Fig. 9, 10)

The forecaster deployed by instrument is given by Table 9. PT refers to Pesaran–Timmermann at a lag of h=1; 'shock' means that the target span includes a |z| greater than or equal to 2.5 days; 'pre-event' indicates that the forecast was issued at time T-1; and 'latency' is the median number of sessions until the consensus agrees with the shock direction.

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9	Column 10
instrument	type	origins	$h$=1 hit / always-up	PT	$h$=7 hit / always-up	shock hit / calm hit (Δ)	pre-event $h$=1 hit ($n$)	consensus aligned	latency
BTC/USD	crypto	1,973	.488 / .495	−1.09	.467 / .510	.460 / .489 (−.03)	.367 (98)	6%	6
BITO	crypto	1,125	.506 / .487	+0.13	.479 / .519	.359 / .501 (−.14)	.375 (48)	10%	5
SPXL	index	2,584	.527 / .548	−0.90	.594 / .615	.337 / .599 (−.26)	.385 (96)	10%	2
SPY	index	2,584	.526 / .551	−1.23	.612 / .635	.355 / .621 (−.27)	.418 (98)	12%	2
AAPL	stock	4,097	.513 / .530	−0.10	.565 / .586	.507 / .556 (−.05)	.494 (170)	15%	4
MSFT	stock	4,097	.518 / .523	+1.48	.537 / .582	.486 / .546 (−.06)	.515 (163)	15%	7
TSLA	stock	3,975	.496 / .517	−0.80	.514 / .541	.508 / .513 (−.01)	.497 (171)	11%	4
NVDA	stock	4,097	.506 / .529	−1.00	.542 / .577	.551 / .531 (+.02)	.560 (141)	17%	4


There are three regularities. (i) With regard to each instrument, the "always up" rule outperforms the forecaster in seven out of the sessions (for example, SPY 0.635 compared with 0.612, and AAPL 0.586 compared with 0.565): the index and stock accuracies ranging from 0.54 to 0.61, which appear to indicate skill, are in fact due to base-rate inflation caused by positive drift, which is why the PT statistic—never exceeding 1.48—is the appropriate measure to use. (ii) The shock-window deficit varies by type: it is −26 points for the index, −14 for BITO, −3 for BTC, and between −5 and +2 for individual stocks. (iii) The speed of recovery is also type-specific: after a shock to the index the consensus realigns with a median of two sessions, but requires four to seven sessions for stocks and five to six for crypto.

Table 10. Asset-type fingerprints (from 2016 to 2026; for BTC and stocks the period starts in 2016 in order to allow for comparison). Continuation refers to the return adjusted for sign following a $|z|\ge2.5$ shock; the 'own-news spike' makes use of the type's own headline profile (crypto words/tags; broad-market tags plus macro words; the ticker's own tag).

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9	Column 10	Column 11	Column 12	Column 13
instrument	type	ann. vol %	excess kurtosis	shocks / yr	shock up-share	lag-1 autocorr	VR(5)	cont. 3d %	cont. 7d % ($t$)	shocks clustered ≤3d	$\lvert r\rvert$ spike ÷ quiet	shock share: spike vs quiet days
BTC/USD	crypto	57.5	4.0	17.5	57%	−.041	.97	+1.24	+2.98 (3.1)	21%	1.20	11.6% vs 4.1%
BITO	crypto	54.4	3.6	10.3	54%	−.041	.94	+1.38	+1.71 (1.0)	31%	1.17	8.8% vs 3.3%
SPY	index	17.5	12.7	9.2	34%	−.119	.86	−0.22	−0.52 (−1.5)	26%	0.95	6.9% vs 3.6%
SPXL	index	51.9	11.9	9.0	33%	−.097	.88	−0.45	−1.39 (−1.4)	25%	0.96	6.9% vs 3.4%
QQQ	index	22.3	7.4	8.5	40%	−.120	.82	−0.12	−0.35 (−0.9)	17%	0.90	3.4% vs 3.6%
TLT	bond	14.7	5.2	7.4	52%	−.020	.85	−0.07	+0.38 (1.3)	18%	1.39	6.9% vs 2.9%
GLD	commodity	16.5	6.9	10.4	54%	−.004	.96	+0.40	+0.30 (0.9)	21%	0.90	3.4% vs 3.2%
AAPL	stock	28.9	6.7	10.5	48%	−.054	.90	−0.45	−0.91 (−1.9)	14%	1.85	14.9% vs 4.0%
MSFT	stock	27.5	8.9	9.7	53%	−.123	.80	−0.31	−0.77 (−1.7)	19%	1.46	9.9% vs 3.2%
TSLA	stock	58.6	4.3	10.3	51%	−.009	1.03	+0.35	+0.52 (0.5)	17%	1.91	14.5% vs 2.4%
NVDA	stock	49.3	7.9	9.1	55%	−.079	.90	+0.70	+0.87 (1.0)	9%	1.53	12.0% vs 2.3%


Figure 9a. Return-process fingerprints by asset type.

The fingerprints are not based on a single pattern. Crypto features a near-random walk (with a VR of 0.94 to 0.97) and has relatively light tails, symmetric shocks, strong clustering and positive continuation after shocks — that is the behavioural drift described in Section 6 — because the policy and headline news that influences it does not follow a fixed calendar. The index, on the other hand, has the heaviest tails (with a kurtosis of 12 to 13), two-thirds of its shocks are downwards, it mean-reverts over a week (with a VR of 0.82 to 0.88 and a lag-1 autocorrelation between –0.10 and –0.12), and it reverses following a shock; its own-news spikes do not result in any extra volatility (the ratio is 0.95) since macro news is mostly scheduled and partly already reflected in prices. Individual stocks fall somewhere in between: they show idiosyncratic own-news jumps (when there is a headline about the company in question, the value of $|r|$ rises by 1.5 to 1.9 times and the probability of a shock is tripled or quadrupled), they exhibit heterogeneous continuation (AAPL and MSFT revert while TSLA and NVDA continue), and have weaker clustering. The difference between the types lies in the speed rather than in sensitivity: shock sessions account for the same proportion of return variance in stocks (30 to 37%) as they do in crypto (34 to 35%), earnings sessions move a stock by 3 to 4 times its normal range, and every recorded stock price change is an information event — but by the end of the session a stock has absorbed the news, whereas Bitcoin takes a whole week to absorb it. There are four structural reasons for this: earnings and macro releases are quantifiable (analysts recalculate the fair value within hours), while a policy statement regarding a crypto bill is debated over days on social media platforms; the fifty stocks that have been studied are the most heavily covered and arbitraged securities in the world, and news travels slowly only in areas where coverage is limited (Hong et al., 2000); crypto leverage leads to liquidation cascades which mechanically extend a price movement; and crypto news is unscheduled and tends to cluster, whereas earnings dates and FOMC dates are known in advance and can be anticipated. A voter set designed to respond to one of these regimes is incorrectly specified when applied to the other two: the contrarian behaviour which is disastrous during clustered crypto shocks is about right in the case of index reversals (which is why there is a two-session latency) and is irrelevant in the case of earnings jumps.

Figure 9b. News response and forecaster behaviour by asset type.

Figure 10. Post-shock sign-adjusted return by instrument.

5.5 Fully exogenous events: FOMC decisions, payroll releases, earnings dates

Headline counts are only an approximation; return shocks are to some extent circular. Publicly available calendars do not have this feature: the dates on which the FOMC makes its decisions (from 2016 to 2026-07, 85 meetings), the dates of the Employment Situation releases (the first Friday, 123 meetings) and the quarterly earnings announcement sessions for each individual stock (63 to 65 per stock from 2010) are known in advance and do not refer to prices or to headlines. We compare the $h=1$ forecast released the day before each event with all the other forecasts (Table 12). Table 12.

Table 12. Next-session forecasts issued the day before a scheduled event vs all other days.

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9	Column 10	Column 11
instrument	event	$n$	hit event / other	up-rate event / other	coverage event / other	mean $\lvert s\rvert$ event / other (MWU $p$)	mean $\lvert r\rvert$ %	shock share	consensus aligned	continuation 1d / 3d / 7d (%)
SPY	FOMC	83	0.398 / 0.530 (Δ −0.13, CI −0.20…−0.02, $p$=0.016)	.45 / .56	0.675 / 0.771	1.09 / 0.87 (0.10)	0.93 / 0.72	8.4% / 3.6%	17%	0.0 / 0.0 / 0.0
SPXL	FOMC	83	0.458 / 0.530	.43 / .55	0.687 / 0.772	1.08 / 0.87 (0.19)	2.78 / 2.13	8.4% / 3.6%	18%	0.0 / 0.1 / 0.1
SPY	payrolls	123	0.569 / 0.523	.63 / .55	0.675 / 0.773	1.08 / 0.87 (0.001)	0.88 / 0.71	4.9% / 3.7%	27%	0.1 / 0.0 / 0.2
SPXL	payrolls	123	0.569 / 0.525	.63 / .54	0.683 / 0.774	1.09 / 0.86 (0.001)	2.61 / 2.13	4.9% / 3.7%	19%	0.2 / 0.0 / 0.7
BITO	FOMC	36	0.472 / 0.507	.44 / .49	0.806 / 0.776	0.71 / 0.90 (0.86)	2.15 / 2.47	0% / 4.4%	17%	0.2 / 1.3 / 1.7
BTC/USD	FOMC	43	0.558 / 0.486	.54 / .49	0.767 / 0.784	0.86 / 0.85 (0.36)	2.33 / 1.99	2.3% / 5.0%	2%	−0.5 / −1.3 / −0.7
BTC/USD	payrolls	64	0.500 / 0.488	.55 / .49	0.656 / 0.788	1.03 / 0.85 (0.011)	2.59 / 1.97	7.8% / 4.9%	6%	0.2 / 0.8 / 0.0
AAPL	earnings	65	0.492 / 0.514	.49 / .53	0.246 / 0.780	3.08 / 0.84 (<10⁻⁵)	3.88 / 1.20	49% / 3.4%	12%	+0.57 ($p$=.007) / +0.16 / +0.28
MSFT	earnings	65	0.462 / 0.519	.60 / .52	0.262 / 0.792	3.41 / 0.82 (<10⁻⁵)	3.90 / 1.10	54% / 3.2%	17%	+0.38 / +0.86 ($p$=.011) / +0.53
TSLA	earnings	63	0.524 / 0.495	.51 / .52	0.270 / 0.786	2.79 / 0.84 (<10⁻⁵)	7.54 / 2.43	54% / 3.5%	6%	+0.67 / +1.02 / +1.79
NVDA	earnings	65	0.600 / 0.505 (Δ +0.10, $p$=0.022)	.60 / .53	0.246 / 0.779	3.35 / 0.85 (<10⁻⁵)	6.39 / 1.93	48% / 2.7%	17%	+0.10 / +0.72 / +1.10


There are three findings that are specific to each type, and none of them relates to a return or headline-defined event. For individual stocks, on earnings days the forecaster's nominal-80% band includes one quarter of the outcomes, the degree of surprise is 3 to 4 band-σ (as opposed to 0.8 in other cases), and half of all earnings sessions involve $|z|\ge2.5$ shocks — even though the analog model produces calm-regime bands for an event that has been on the calendar for months. The direction of the movements is at the base rate (there is no anti-skill since earnings surprises are not autocorrelated the way policy news is), and a small post-earnings drift is observed (AAPL rises by 0.57% in the following session and MSFT by 0.86% over three sessions), which is the pattern described by Bernard and Thomas (1989). With regard to the index, on FOMC days the SPY's accuracy in the next session drops from 0.53 to 0.40 and its coverage is reduced by 10 points; on those days the skew is downward (45% up compared to 56%), so part of the decline is due to a base-rate shift that the forecaster does not notice. On payroll days there is the clearest distinction between direction and distribution: accuracy is higher (0.57, since 63% of payroll sessions are upward movements) although coverage falls and surprise increases significantly — a directional score would regard this as a good day for the model; a proper score would consider it a bad one. In the case of crypto, FOMC days have no measurable impact on the forecasts for BITO or BTC (neither coverage nor surprise changes), and payroll days have only a slight spillover effect on BTC — the reason being that crypto shocks are unscheduled, which is precisely why a headline-intensity state variable, rather than a calendar, should be included for this type (Section 8.3).

5.6 What moved the stocks: a catalogue of significant increases

If you want to find out about the single-stock shocks, then each increase of $|z|\ge2.5$ in the four stocks (346 sessions, from 2010 to 2026-09) was classified according to a fixed rule — first as an earnings reaction session (or the following one), then as a market-wide move (that is, SPY or QQQ showing a $|z|\ge2$ on the same day with the same sign), and finally as an idiosyncratic move — and this was combined with the ticker-tagged headlines from the Alpaca/Benzinga archive for the periods covered (from 2024-02 onwards, 52 events); in the case of the 23 largest earlier idiosyncratic moves, attributions were checked against the contemporaneous coverage available from CNBC, Bloomberg, CNN Money, TechCrunch, Forbes, GeekWire and Fortune (using the research/manual_attributions.json file). Two of the Microsoft events (on 2010-09-13 and 2011-01-06) are based entirely on the event date and are marked with an asterisk *. The full catalogue is listed in research/STOCK_EVENTS.md and in output/stock_events_catalogue.csv.

Table 14. Significant single-stock increases by category ($n$ = 346). Pre-event metrics are for the forecast issued the day before; continuation is the further move after the event close.

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9
category	$n$	share	mean move %	pre-event $h$=1 coverage	mean $\lvert s\rvert$	consensus aligned	latency (median)	continuation 1d / 3d / 7d % ($t$)
earnings reaction	78	22.5%	8.7	0.00	5.42	15.4%	5.0	+0.72 / +1.94 / +2.26 (2.68, $p$=0.0089)
idiosyncratic news	166	48.0%	6.03	0.00	3.36	24.1%	4.5	+0.24 / +0.15 / +1.10 (1.56)
market-wide day	99	28.6%	6.19	0.00	3.02	24.2%	4.5	-0.65 / +0.05 / +0.58 (0.83)


(Three further “earnings+1” sessions are omitted.) By stock: TSLA’s increases are mostly idiosyncratic (66 of 95), NVDA’s are the most earnings-driven (24 of 79), AAPL and MSFT split roughly a third each between company news and market-wide days.

Table 15. The three largest percentage increases per stock and the factors that caused them. Band equals the percentage of the day-before P10/P90; "aligned" means that the consensus had already agreed with the upcoming move by the previous day (T−1); an asterisk indicates an attribution inferred solely from the event date.

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9
stock	date	+%	$z$	category	what happened	P(up), band	consensus	+1d / +3d / +7d %
AAPL	2017-02-01	+6.1	11.9	earnings	earnings report	0.48, [-0.5, +0.7]	Hold	-0.2 / +1.2 / +3.1
AAPL	2014-04-24	+8.2	9.5	earnings	earnings report	0.45, [-1.3, +1.2]	Hold	+0.7 / +4.3 / +5.8
AAPL	2016-07-27	+6.5	7.5	earnings	earnings report	0.50, [-1.2, +0.8]	Hold	+1.4 / +3.0 / +5.0
MSFT	2017-10-27	+6.4	12.8	earnings	earnings report	0.53, [-0.6, +0.4]	Hold	+0.1 / -0.8 / +0.5
MSFT	2015-10-23	+10.1	9.7	earnings	earnings report	0.42, [-1.5, +1.1]	Hold	+2.6 / +2.1 / +2.4
MSFT	2026-07-30	+15.5	9.7	earnings	earnings report	0.47, [-2.0, +1.9]	Hold	+3.0 / +9.2 / +12.2
NVDA	2016-11-11	+29.8	14.1	earnings	earnings report	0.57, [-2.0, +2.1]	Hold	-4.9 / +4.2 / +6.5
NVDA	2017-05-10	+17.8	11.8	earnings	earnings report	0.55, [-1.8, +2.8]	Hold	+4.3 / +10.7 / +12.2
NVDA	2023-05-25	+24.4	11.2	earnings	earnings report	0.55, [-2.1, +3.0]	Hold	+2.5 / -0.4 / +1.8
TSLA	2011-03-31	+17.0	10.2	idiosyncratic	Morgan Stanley (Adam Jonas) upgraded Tesla to Overweight with a $70 target, calling it ‘America’s fourth automaker’	0.50, [-2.0, +2.3]	Hold	-3.9 / -3.8 / -8.9
TSLA	2021-10-25	+12.7	9.2	idiosyncratic	Hertz ordered 100,000 Teslas (~$4bn); market value passed $1 trillion	0.58, [-2.3, +2.4]	Buy (aligned)	-0.6 / +5.1 / +18.4
TSLA	2019-10-24	+17.7	8.5	earnings	earnings report	0.53, [-2.9, +2.7]	Hold	+9.5 / +5.5 / +5.9


Here are three points. The first is that each recorded increase constitutes an information event—such as an earnings release, a day affecting the market as a whole, an analyst's target, an announcement relating to a product or to management, a large order, or a legal settlement—and none of these constitutes a pattern in the previous price movements; this is the single-stock form of Proposition 1. The second is that, in each category, the forecasting model produced forecast bands of approximately ±2 to ±4% for changes ranging from +12% to +30%, and the combined assessment agreed on 15 to 24% of the events (this is an improvement on the figure for crypto, which is 6 to 10%, since the cash-mode engine is long most of the time, not because it had anticipated the news). The third point is that the various categories behave differently after the event, a fact which is important for the specific design of Section 8.3: earnings increases continue to drift (+2.3% over seven sessions, t=2.7), mirroring the drift observed after an earnings announcement; idiosyncratic-news increases show only weak drift (+1.1%, t=1.6); market-wide increases revert part of their move the following day (−0.65%) and then level off. The stock model should therefore incorporate an earnings calendar with a drift element, regard market-wide days as equivalent to having index exposure, and treat other company news as a jump with no follow-through—that is, it should be based on three distinct regimes rather than a single voter set.

5.7 The stock cross-section: 50 S&P 500 names

To check whether the four stocks are representative, the procedure was carried out on 46 other companies which are part of the S&P 500 and include all the sectors that have published s00 datasets (the live signals were frozen on 2026-07-30; the histories go back to 2010, and 204,129 next-session forecasts were scored; Berkshire Hathaway was excluded since it had no tagged headlines). Table 17 gives a summary of the cross-section; the per-stock table is available in universe_cross_section.csv.

Table 17. The deployed forecaster across 50 stocks (medians unless stated).

Column 1	Column 2
metric	value
$h$=1 directional accuracy (IQR)	0.509 (0.506–0.517); always-up 0.523
pooled Pesaran–Timmermann, $h$=1 (204,129 forecasts)	3.08 ($p$=0.001): $\hat P$ = 0.5107 vs 0.5075 under independence
per-stock PT: mean / SD; share > 1.645 / < −1.645	0.26 / 0.91; 8% / 4% (KS vs $N(0,1)$ $p$=0.0099)
stocks with Brier worse than the coin / significantly worse (HAC, 5%)	98% / 88%
$h$=7 accuracy vs always-up; stocks where always-up wins	0.525 vs 0.558; 98%
$h$=1 accuracy on calm / shock sessions; day-before-shock	0.512 / 0.493; 0.493
consensus aligned before a shock; latency (median sessions)	12.1%; 4.5
7-session continuation after shocks; stocks with positive continuation	-0.18%; 32%
earnings sessions (48 stocks): 10–90 coverage vs other sessions	0.28 vs 0.79 (below on 100% of stocks); mean $\lvert s\rvert$ 2.86 vs 0.84; 43.8% of earnings sessions are $\lvert z\rvert\ge2.5$ shocks
significant increases by cause (median shares)	earnings 19.3%, market-wide 25.4%, idiosyncratic 56.1%


The cross-section does not only enhance the four-stock picture in one respect but also strengthens it in all the other respects. When the 204,129 forecasts are combined, the Pesaran–Timmermann statistic reaches 3.08: there is a statistically detectable directional dependence at one session for individual stocks — this amounts to 0.32 percentage points above the level of independence, and 8% of the stocks exceed the 5% critical value as compared with 4% falling below it. The economic importance of this is negligible and is more than offset by miscalibration: for 98% of the stocks the Brier score is worse than a constant ½ (and this is significant for 88% of them), the always-up rule performs better than the model at seven sessions for 98% of the stocks, and on earnings sessions the nominal-80% band includes 28% of the outcomes for the median stock and covers less than the amount that it covers during calm sessions for each of the 48 stocks with earnings dates. For the median stock the response after a shock is only very slightly mean-reverting (by -0.18% over seven sessions; only 32% of the stocks continue), the opposite of what is observed in crypto. (Fig. 12.)

Figure 12. The deployed forecaster across 50 stocks: PT distribution vs N(0,1); model vs always-up at h=7; earnings-session coverage.

---

6. Results III — after the news: human traders versus the model

6.1 Post-shock drift

Table 7. Sign-adjusted continuation after the shock close (position opened at $C_T$ in the shock direction). (Fig. 6)

Column 1	Column 2	Column 3	Column 4
$k$ sessions	BITO mean % (share > 0)	BTC mean % (share > 0)	BTC $t$ ($p$)
1	+0.07 (56%)	+0.13 (49%)	0.34 (0.73)
2	+0.34 (54%)	+0.95 (58%)	2.18 (0.032)
3	+1.15 (56%)	+1.22 (58%)	2.20 (0.030)
5	+2.00 (60%)	+2.45 (61%)	2.91 (0.005)
7	+1.61 (54%)	+2.98 (62%)	3.06 (0.003)


Concerning BTC (98 events), the drift is monotonic and significant from the second session onward: in 62% of cases a trader who merely follows the movement on the news day ends up with about 3% more over the following week, the result being positive. When looked at in terms of direction, up-shocks still produce a return of +3.8% after seven sessions and down-shocks lead to a return of −1.9% (for BTC); for BITO, up-shocks still yield +3.4% while down-shocks show a slight reversal (+0.4%, with $n=22$). This is precisely the type of post-announcement drift or under-reaction which is described in the behavioural finance literature (Barberis et al., 1998; Chan, 2003; Hong & Stein, 1999), the pattern having been observed in a 24/7 asset with the exception of the small sample size.

Figure 6. Post-shock continuation with 95% CI.

6.1.1 When to act: entry delay and a walk-forward rule

If people respond with a delay, the practical issue for the user becomes whether or not acting one, two or three sessions after the news still yields any results. Table 19 provides the in-sample answer: it shows the sign-adjusted return from the close of session k to the close of session 7, by event set. Table 20 then examines this as a trading rule using a walk-forward approach and taking into account transaction costs; at each shock the decision regarding the direction (that is, continuation or reversal) is based on the trailing $t$-statistic of the previous, fully observed events only (at least 20 events; $|t|>1$ is required in order to trade), the position is opened at the close of session k and closed at the close of session 7, and 5 or 25 basis points are charged per side (the latter being an approximation of the crypto spreads on the days of the shock). Compounded totals are not given for the pooled stock groups since dozens of stocks experience a shock on the same day; the means, hit rates and $t$-statistics are stated on a per-event basis.

Table 19. Return from entering k sessions after a shock and holding to session 7, sign-adjusted, % (share of events positive), in-sample.

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6
event set	enter day 0	day 1	day 2	day 3	day 5
BTC, all 98 shocks	+2.98 (62%)	+2.79 (64%)	+1.95 (61%)	+1.69 (59%)	+0.50 (49%)
BTC, 55 up-shocks	+3.83 (65%)	+3.26 (69%)	+2.04 (62%)	+1.75 (60%)	+0.60 (49%)
BITO, 46 shocks	+1.61 (54%)	+1.69 (61%)	+1.50 (59%)	+0.60 (50%)	-0.20 (52%)
SPY, 98 shocks	-0.52 (43%)	-0.25 (43%)	-0.37 (41%)	-0.31 (48%)	-0.03 (50%)
SPXL, 96 shocks	-1.38 (41%)	-0.78 (45%)	-1.12 (41%)	-1.06 (45%)	-0.13 (49%)
4 stocks, 77 earnings up-jumps	+2.26 (64%)	+1.44 (64%)	+0.82 (64%)	+0.30 (56%)	+0.78 (68%)
4 stocks, 166 idiosyncratic up-jumps	+1.10 (51%)	+0.82 (51%)	+1.07 (53%)	+0.86 (52%)	-0.06 (54%)
4 stocks, 99 market-wide up days	+0.58 (55%)	+1.23 (58%)	+0.41 (56%)	+0.56 (58%)	+0.75 (55%)


Table 20. Walk-forward, cost-adjusted rule: enter at the close of session k, exit at session 7; side chosen from prior events only.

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8
group	enter day	OOS events / traded	side chosen	net per event, 5 bp (hit, t)	net per event, 25 bp (hit, t)	since 2025, 5 bp	always-continuation, 5 bp (hit, t)
BTC	0	77 / 77	continuation	+2.51% (61%, t 2.32)	+2.11% (60%, t 1.95)	2.207% (n 30)	+2.51% (61%, t 2.32)
BTC	1	77 / 77	continuation	+2.33% (64%, t 2.5)	+1.93% (61%, t 2.07)	2.359% (n 30)	+2.33% (64%, t 2.5)
BTC	2	77 / 77	continuation	+1.34% (60%, t 1.64)	+0.94% (56%, t 1.15)	1.424% (n 30)	+1.34% (60%, t 1.64)
BTC	3	77 / 70	continuation	+1.24% (60%, t 1.59)	+0.84% (53%, t 1.08)	1.451% (n 30)	+1.37% (61%, t 1.89)
BITO	1	26 / 0	filter never fires	—	—	—	4.013% (0.692, t 2.6)
SPY	0	78 / 54	reversal	-0.01% (48%, t -0.03)	-0.41% (46%, t -0.77)	0.677% (n 16)	-0.56% (41%, t -1.38)
SPXL	0	76 / 37	reversal	-0.23% (51%, t -0.13)	-0.63% (46%, t -0.36)	0.535% (n 11)	-1.28% (41%, t -1.04)
50 stocks: earnings shocks (both signs)	0	1366 / 1014	continuation 94%	+0.18% (53%, t 1.13)	-0.22% (48%, t -1.45)	0.63% (n 162)	+0.25% (52%, t 1.9)
50 stocks: earnings shocks	1	1366 / 126	mixed	-0.50% (44%, t -1.45)	-0.90% (38%, t -2.62)	-0.724% (n 20)	+0.03% (52%, t 0.22)
50 stocks: idiosyncratic shocks	0	3845 / 168	rarely fires	-0.31% (45%, t -0.99)	-0.71% (40%, t -2.26)	—% (n 0)	-0.09% (48%, t -1.02)
50 stocks: market-wide shocks	0	2800 / 2733	reversal 92%	+0.30% (53%, t 2.65)	-0.10% (49%, t -0.93)	1.54% (n 214)	-0.64% (43%, t -5.82)
50 stocks: market-wide shocks	2	2800 / 2750	reversal	+0.17% (53%, t 1.63)	-0.23% (48%, t -2.22)	2.361% (n 214)	-0.70% (43%, t -6.88)


The result is very narrow. With respect to Bitcoin, yes — within a single session. If you enter at the close following the shock or at the next close, you achieve a net return of +2.51% and +2.33% per event at a spread of 5 bp (61% and 64% of the events being positive, with $t$ values of 2.32 and 2.5 respectively) and +1.93% at 25 bp; the trailing filter always selected continuation at each decision, so the rule is only out of sample in the sense that 21 previous events were required, and it performed well in the period 2025–26 (+2.36%, 70% success rate, based on 30 events). By the second session the edge is halved (+1.34%, $t$ = 1.64) and is no longer significant; by the third it is even weaker; by the fifth it has disappeared. BITO has too few events for the filter to activate. As for the index, no: chasing leads to a loss of -0.56% per event at 5 bp and -0.96% at 25 bp ($t$ = -2.36), and the reversal, which is the one the filter chooses, yields no net return. For individual stocks, no in general: across 1,390 earnings shocks involving 50 companies the walk-forward continuation produces a return of +0.25% per event at 5 bp and -0.15% at 25 bp — the +2.3% mentioned in Table 14 came from the four large-cap companies' upward price jumps, not from the entire range of stocks — idiosyncratic movements show no drift, and broad market moves reverse (+0.30% at 5 bp, $t$ = 2.65; -0.10% at 25 bp). The per-event dispersion is 7 to 10% compared to a mean of 2 to 3% even in the case of Bitcoin, so about four out of every ten events result in a loss even in the best scenario for entry. The defensible product statement is therefore purely descriptive and specific to type: following a crypto shock, do not fade it, and any action taken should be carried out within one session and held for about a week; after index shocks and on days when the market as a whole moves, do not chase; after earnings and other company news, the historical drift is too small to cover real-world costs.

6.2 How long the model takes to agree

When the system is not aligned at time $T-1$, the 3-day signal agrees with the direction of the shock for a median of 2 sessions in the case of BITO and 3 in the case of BTC; of the 98 BTC events, 24 never showed agreement within 15 sessions. For the seven-vote consensus, a median of 5 sessions is required for BITO and 6 for BTC (see Fig. 7). Since there is a drift as shown in Table 7, the model's agreement occurs after most of the exploitable continuation has already passed, and for the BTC instrument the 3-day signal's cash-mode trend filter causes "Long" to be indicated for long periods, so the alignment in that case is in part coincidental.

Figure 7. Sessions until the 3-day signal and the consensus agree with the shock direction.

6.3 Case study: the 2026-08-19 White House crypto summit

On August 19, 2026, President Trump invited crypto executives along with the chairs of the SEC and CFTC to a reception at the White House and asked Congress to pass the CLARITY Act; between August 19 and 21, Bitcoin increased from $64,686 (which was the closing price on August 18) to $69,311, then to $73,012 and afterwards to $78,332 (+7.2%, +5.3%, +7.3%; an overall rise of 21.1% over the three sessions), marking the biggest single-day short liquidation in the history of Bitcoin (amounting to approximately $1.42 billion). BITO rose by 5.96%, 6.05% and 6.12% respectively. The value of $|z|$ on August 19 is the highest in our sample period from 2024 to 2026 and represents a headline spike ($\nu=2.0$; 2.25 on August 20).

Table 8. Deployed BITO forecast issued 2026-08-18 (close 8.73), 3-day signal Short, consensus Hold (2 Buy / 3 Sell), next-session tactical target −100% (fully in the inverse ETF BITI). (Fig. 1, 2)

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9
$h$	session	$\hat p$	P10 %	P50 %	P90 %	realized %	covered	$s$
1	Aug 19	0.55	−1.81	+0.32	+2.06	+5.96	no	3.7
2	Aug 20	0.53	−2.06	+0.17	+2.80	+12.37	no	6.4
3	Aug 21	0.58	−2.22	+0.70	+3.82	+19.24	no	7.9
4	Aug 24	0.58	−5.76	+0.68	+3.34	+21.76	no	5.9
5	Aug 25	0.58	−8.30	+0.29	+4.44	+22.05	no	4.4
6	Aug 26	0.52	−9.49	+0.17	+4.91	+21.31	no	3.8
7	Aug 27	0.47	−10.76	−0.39	+4.24	+23.48	no	4.1


There are two lessons to be drawn. The first is that directional accuracy is the incorrect criterion: according to the $\hat p\ge0.5$ rule, this forecast achieved a hit in six out of seven horizons, whereas the actual path was lying between 4 and 8 band-$\sigma$ above each median and outside each interval. The second point is that the payload's two exposure mechanisms were at odds: the analog-schedule target showed $-100\%$ (since the negative 3-day signal was the main factor in its score), while the vote consensus advised a Hold. The strategy return that was published on August 19 was $-5.86\%$ (with a long position in BITI). The 3-day signal turned to Long at the close of August 19 (after having increased by +6%), the consensus only reached "Buy / warning" on August 21 (having risen by +19%), and the signal then changed back to Short with a $-100\%$ target on August 24. With respect to BTC spot, the forecast issued on August 18 was poorer: consensus Sell / confirmed (0 Buy, 6 Sell), $h=1$ band $[-1.6\%,+1.2\%]$ compared to +7.15\% ($s=6.7$), $h=3$ $s=9.5$, 0/7 coverage, 1/7 direction hits. A "news chaser" who bought BITO at the close of August 19 obtained returns of +6.1%, +12.5%, +14.9% and +14.5% after one, two, three and five sessions respectively.

Figure 1. Point-in-time forecast issued 2026-08-18 against realized prices.

Figure 2. Day-by-day model state, Aug 5–28 2026.

6.4 Effectiveness of daily actions: act every day, once a week, or once

The payload includes a seven-session exposure plan, which enables the user to address it in different ways. We simulate on a point-in-time basis with a rate of 5 basis points per unit of turnover, by (a) acting on a daily basis—setting the exposure to the fresh $h=1$ target each day; (b) acting weekly—committing to the seven-session schedule and sticking to it without re-forecasting or re-planning at each seven-session interval; (c) acting once and then holding—taking the $h=1$ target and making no changes for the seven sessions; as against (d) the buy-and-hold strategy and (e) the deployed 3-day signal. When the exposure is negative, the actual inverse-ETF return (BITI, SPXS) is obtained. (Table 11, Fig. 11)

Table 11. Policy performance: annualised return % / Sharpe / max drawdown % (full sample) and total return % / Sharpe / max drawdown % (2026 live period).

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7
instrument	period	hold	act daily	act weekly	act once, hold	3-day signal
BITO	full (2022-03→), ann.	+15.8 / .55 / −68	+5.5 / .37 / −49	−1.1 / .17 / −53	−23.4 / −.32 / −67	+4.7 / .37 / −56
BITO	2026, total	−13 / −.29 / −41	+64 / 2.47 / −21	+39 / 1.92 / −13	+21 / 1.08 / −21	+75 / 2.66 / −21
BTC/USD	full (2021-04→), ann.	+5.5 / .37 / −77	−0.4 / .18 / −75	+7.8 / .40 / −47	+17.4 / .60 / −57	+3.3 / .30 / −74
BTC/USD	2026, total	−10 / −.10 / −40	−4 / −.07 / −27	+4 / .33 / −29	−5 / .00 / −33	−5 / −.04 / −29
SPXL	full (2016-05→), ann.	+30.7 / .78 / −77	−8.3 / .00 / −78	−12.0 / −.26 / −77	−15.7 / −.23 / −87	−8.9 / .04 / −80
SPXL	2026, total	+32 / 1.25 / −27	+45 / 2.02 / −16	−14 / −1.10 / −19	−16 / −.72 / −31	+45 / 1.80 / −19
SPY	full, ann.	+15.6 / .91 / −34	+10.3 / .88 / −23	+3.1 / .43 / −14	+10.8 / .88 / −25	+13.5 / .89 / −29
SPY	2026, total	+13 / 1.49 / −9	+9 / 1.41 / −7	+7 / 1.88 / −4	+10 / 1.49 / −7	+13 / 1.47 / −9
AAPL	full (2010-05→), ann.	+26.2 / .97 / −44	+18.2 / .90 / −35	+9.7 / .73 / −23	+19.5 / .94 / −35	+23.8 / .94 / −42
MSFT	full, ann.	+21.4 / .87 / −37	+14.8 / .81 / −33	+8.0 / .65 / −20	+18.1 / .94 / −23	+18.4 / .82 / −41
TSLA	full, ann.	+39.1 / .86 / −74	+30.4 / .83 / −52	+21.3 / .79 / −47	+36.9 / .94 / −50	+36.7 / .85 / −61
NVDA	full, ann.	+50.5 / 1.12 / −66	+38.7 / 1.13 / −49	+19.0 / .88 / −34	+36.6 / 1.08 / −48	+51.6 / 1.18 / −59


No policy has priority. When looking at the full samples, the buy-and-hold approach achieves success on seven out of eight instruments (BTC spot is the exception, in which the act-once-and-hold strategy wins); on the leveraged and inverse instruments, acting every day outperforms sticking to the weekly schedule, but on cash-mode stocks the once-and-hold approach is better than the daily one; in 2026 the ranking reverses for BITO and SPXL (the daily approach yields +64% versus +45%, compared to the hold strategy at −13% and +32%) since that year included periods of drawdowns in which the inverse component provided a return — this is a regime effect, not a result of better forecast skill, as Sections 4–5 demonstrate. The only consistent finding relates to the schedule: the weekly committed schedule and the daily re-forecasting differ by at least 25 exposure points on 66 to 75 per cent of sessions (the mean absolute gap is 0.30 to 0.50 of full exposure), so "doing nothing after day one" is a materially different strategy from acting daily — and in neither case is one clearly the better option. Acting daily also incurs a cost of 60 to 140 units of turnover per year (2 to 8% of NAV in fees at a rate of 5 basis points), and for SPXL and SPXS every forecast-based policy lost 8 to 16% per year over the decade compared to a yearly return of +31% for hold, because a $-100% target in a 3× leveraged pair turns volatility drag into a structural loss.

Figure 11. 2026 NAV of the five action policies.

6.5 A constructive test: does a type-specific gate help?

If the issue is the lack of an event state variable, then introducing such a variable—even in a very rough way—should lead to an improvement in the predictive distribution exactly at those points where the paper says it fails and at no other places. To check this we carry out an out-of-sample test using causal gates that are constructed solely from information available at the origin and with thresholds as specified in Section 3: calendar (the target session is an FOMC or payroll day for the index or an earnings reaction session for a stock), headline (the previous session's own-news ratio $\nu_{t-1}\ge2$), and shock (the origin session itself was a $\lvert z\rvert\ge2.5$ move). For the gated forecasts, the model's quantiles are replaced by an event-conditional distribution which is estimated on a walk-forward basis from the past only: either the empirical quantiles from past same-type event sessions (earnings, FOMC or payroll; at least 8 events) or the sign-adjusted post-shock continuation distribution (at least 10 shocks); in all other cases a trailing 250-window climatology is used. The scores include the Winkler interval score (with α=0.2), coverage and Brier; the differences are calculated using block bootstrapping. (See Table 18 and Fig. 13.) Table 18.

Table 18. Event-conditional gate vs deployed model on gated forecasts (all origins; walk-forward estimation).

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7
instrument	gate	forecasts	Winkler model → gated	improvement [95% CI of difference]	coverage	Brier
BTC/USD	shock	686	0.2954 → 0.2630	+11.0% [-0.0985, +0.0274]	0.71 → 0.76	0.2575 → 0.2531
BTC/USD	headline	663	0.2116 → 0.1888	+10.8% [-0.0744, +0.0244]	0.73 → 0.75	0.2641 → 0.2470
BITO	shock	333	0.3648 → 0.3395	+7.0% [-0.1349, +0.0840]	0.65 → 0.77	0.2579 → 0.2475
BITO	headline	231	0.3768 → 0.3143	+16.6% [-0.2108, +0.0732]	0.56 → 0.65	0.2709 → 0.2377
SPY	calendar	1,440	0.0728 → 0.0793	-8.9% [-0.0111, +0.0246]	0.72 → 0.72	0.2434 → 0.2402
SPXL	calendar	1,440	0.2180 → 0.2380	-9.2% [-0.0307, +0.0743]	0.72 → 0.71	0.2506 → 0.2445
SPY	shock	686	0.0895 → 0.0949	-6.1% [-0.0173, +0.0288]	0.69 → 0.70	0.2604 → 0.2507
50 stocks, pooled	earnings	21,763	0.2585 → 0.2184	+15.5% [-0.0529, -0.0270], $p$=0.0	0.49 → 0.68	0.2543 → 0.2567 (94% of stocks improved)
50 stocks, pooled	headline	21,538	0.1781 → 0.1706	+4.2% [-0.0175, +0.0022], $p$=0.1255	0.77 → 0.75	0.2564 → 0.2519 (86% of stocks improved)
50 stocks, pooled	shock	56,509	0.1397 → 0.1451	-3.8% [+0.0006, +0.0103], $p$=0.027	0.74 → 0.75	0.2543 → 0.2538 (18% of stocks improved)


There are two findings. The first is that the gate works where the mechanism is most effective and shows statistical significance only when the results from 50 stocks during earnings sessions are pooled: the interval score improves by 15.5% (the confidence interval does not include zero), coverage increases from 0.49 to 0.68, and 94% of the stocks see an improvement; following crypto shocks and on days when crypto headlines are published, the improvement per instrument is 7 to 17% with coverage returning to normal, but when there are 95 to 686 forecasts per cell the intervals include zero. Although the headline gate leads to a significant reduction in the stocks' Brier score, it does not improve their intervals. The second point is that the same rule is incorrect for the other types: the post-shock distribution is detrimental to the stocks (−3.8%, the confidence interval excludes zero — this is because the stocks revert, meaning that the continuation distribution is incorrectly specified) and the FOMC/payroll distribution is harmful to the index (−9%), since the index's calendar-day bands are already well covered. The overall gains across all the forecasts are small (ranging from −2% to +2% during the 2025–26 hold-out period) because gated sessions account for only 6 to 20% of the forecasts. The gate functions as a remedy for coverage rather than as a source of alpha; its benefit is in turning a silent failure to reach 25% coverage into a flagged, calibrated 'I do not know'; and the decision about which gate to use is itself one that depends on the type, which is the paper's main constructive contribution.

Figure 13. Improvement in the Winkler interval score on gated forecasts from the event-conditional replacement, by gate type and instrument, with 95% bootstrap CIs.

---

7. Discussion and limitations

7.1 Propositions: why a price-conditioned predictor cannot be effective on news days

Let $\mathcal F^P_t=\sigma(C_s:s\le t)$ be the price filtration and write the next session return as
$$r_{t+1}=\mu_t+\sigma_t,\varepsilon_{t+1}+\xi_{t+1}N_{t+1},$$
The variables $\mu_t$ and $\sigma_t$ are $\mathcal F^P_t$-measurable, $\varepsilon_{t+1}$ is continuous and symmetric with $\varepsilon_{t+1}\perp!!!\perp(\mathcal F^P_t,N_{t+1},\xi_{t+1})$, $N_{t+1}$ is the news indicator taking values in {0,1} and $\xi_{t+1}$ is the news impact. The exogeneity of the variables means that $(N_{t+1},\xi_{t+1})\perp!!!\perp\mathcal F^P_t$; let $q$ denote $P(\xi>0\mid N=1)$. A price-conditioned predictor is any $\mathcal F^P_t$-measurable variable $D_t$ belonging to {-1,+1} (an example of such a predictor is the analog forecaster’s $\mathbf 1{\hat p_t\ge\tfrac12}$). The accuracy with respect to an event $E$ is defined as $A(E)=P(D_t=\operatorname{sgn} r_{t+1}\mid E)$.

Proposition 1 (news-day accuracy does not depend on the predictor). On $E_c={N_{t+1}=1,\ |\xi_{t+1}|\ge c,\sigma_t}$,
$$\big|A(E_c)-\big[q,P(D_t=+1)+(1-q),P(D_t=-1)\big]\big|;\le;P\big(|\varepsilon_{t+1}+\mu_t/\sigma_t|\ge c\big),$$
For Gaussian $\varepsilon$ and with $|\mu_t|\ll\sigma_t$ the value is at most $2\Phi(-c)$ (this is 0.012 when $c=2.5$). Specifically, $A(E_c)\le\max(q,1-q)+2\Phi(-c)$, and if the direction of the news is unpredictable ($q=\tfrac{1}{2}$) then each price-conditioned predictor has a news-day accuracy of $\tfrac{1}{2}\pm0.012$ — in that case the predictor is irrelevant.

Proof. On the set $E_c$, we have $\operatorname{sgn} r_{t+1} = \operatorname{sgn}\xi_{t+1}$ except when $|\mu_t+\sigma_t\varepsilon_{t+1}| \ge |\xi_{t+1}| \ge c\sigma_t$, which is an event having probability at most $P(|\varepsilon + \mu_t/\sigma_t| \ge c)$. On the complement of this set, ${D_t = \operatorname{sgn} r_{t+1}}$ is equal to ${D_t = \operatorname{sgn}\xi_{t+1}}$, and since $D_t$ is $\mathcal F^P_t$-measurable whereas $\xi_{t+1}$ is independent of $\mathcal F^P_t$, it follows that $P(D_t = \operatorname{sgn}\xi_{t+1}) = \sum_{d=\pm1} P(D_t = d) P(\operatorname{sgn}\xi_{t+1} = d) = qP(D_t = +1) + (1-q)P(D_t = -1)$. $\square$

With respect to Proposition 2 (in which clustered news and a contrarian predictor result in an accuracy below one half), assume that the successive news shocks are positively dependent, specifically that $P(\operatorname{sgn}\xi_{t+1}=\operatorname{sgn}\xi_t\mid N_t=N_{t+1}=1)=\tfrac{1+\rho}{2}$ where $\rho\in(0,1]$, and that the predictor dampens large movements, defined by $D_t=-\operatorname{sgn} r_t$ when ${N_t=1}$. Then on consecutive days with jump-dominant news we have $A=\tfrac{1-\rho}{2}<\tfrac12$.

Proof. On a day t when jumps are dominant, $\operatorname{sgn} r_t=\operatorname{sgn}\xi_t$, and therefore $D_t=-\operatorname{sgn}\xi_t$ while $A=P(\operatorname{sgn}\xi_{t+1}=-\operatorname{sgn}\xi_t)=1-\tfrac{1+\rho}{2}$.  $\square$

When there are large price changes, the analog forecaster behaves in a contrarian manner because the companies nearby are located in periods marked by calmness, during which large one-day movements tend to partly reverse; of the 98 instances of BTC shocks and 48 instances of BITO shocks, 21 and 10 respectively were followed by another shock within three sessions, almost always of the same sign (the most clear example being the period from August 19 to 21, 2026). Proposition 2 therefore predicts the observed lack of skill on shock days (see Table 3: PT = $-2.49$ for BTC; accuracy at h=1 is 0.37).

Proposition 3 (the interval coverage on news days is bounded by the jump size): Let [L_t, U_t] = [μ_t + σ_t z_{0.1}, μ_t + σ_t z_{0.9}] be the central 80% interval from the diffusion component with Gaussian ε. When N_{t+1} = 1, ξ_{t+1} = c, and σ_t,
$$P\big(r_{t+1}\in[L_t,U_t]\big)=\Phi(z_{0.9}-c)-\Phi(z_{0.1}-c)\le\Phi(1.2816-c),$$
At c=2.5 it is equal to $0.111$ and at c=3.5 it is $0.013$. Since the observed coverage for the period |z|≥2.5 on days when c is present is within the mechanical bound, it provides no information about the forecaster; it is the coverage statistics conditioned on headline intensity (Table 5) that are informative, and these do not determine the value of c.

Proof. r_{t+1} is in the interval [L_t, U_t] if and only if ε_{t+1} + c is in [z_{0.1}, z_{0.9}]; we then take the probabilities and eliminate the negative term. Q.E.D.

The aggregate effectiveness is limited by the frequency of the news. If $\pi=P(N_{t+1}=1)$ and $q=\tfrac{1}{2}$, then $A=(1-\pi)A_{\text{calm}}+\pi A_{\text{news}}\le(1-\pi)A_{\text{calm}}+\tfrac{\pi}{2}+\pi,2\Phi(-c)$, and, under the assumptions of Proposition 2, the news term can drop to $\pi\tfrac{1-\rho}{2}$. In order to have a reading headline accuracy of 0.65 with $\pi$ equal to 0.05, it would be necessary for $A_{\text{calm}}$ to be at least 0.658; the PT statistics from the calm sessions of +0.47 and -0.54 (as given in Table 3) reject any skill during such calm periods.

Remark (sequential effectiveness). When a probabilistic forecaster’s $\hat p_t$ coincides with the true conditional probability, Gibbs’ inequality implies that $E[\Lambda_{t+1}-\Lambda_t\mid\mathcal F_t]=\mathrm{KL}(\hat p_t,|,\tfrac12)\ge0$, and so $\Lambda_n$ is a submartingale with non-negative expected log growth, which is precisely what is meant by saying that the even-odds Kelly bet is effective in series. The fact that the actual value of $\Lambda_n$ is less than zero at each stage (as shown in Table 2) shows that the forecaster’s deviations from $\tfrac12$ are, on average, in the wrong direction — and this is precisely the situation that Propositions 1–2 predict when a proportion $\pi$ of the sessions are news-driven and the predictor is contrarian regarding them.

7.2 What is and is not mechanical

What is and what is not mechanical. The zero interval coverage on $|z|\ge2.5$ days at $h=1$ is essentially a consequence of the definitions (Section 1) and so it is not regarded as constituting evidence. The evidence instead consists of: (i) directional accuracy falling below 50% on the largest moves and on days with a headline spike; (ii) a monotonic decline in both coverage and surprise when using a news measure which never observes returns; (iii) the drift that occurs after shocks; and (iv) the latency before the model reaches agreement. Together, (i) through (iv) are precisely what one would expect from a forecaster whose analog pool is mainly composed of calm, mean-reverting regimes and which lacks the ability to represent "information has arrived".

The reason is that an analog forecaster fails in this case.
$$r_t=\mu(x_{t-1})+\sigma(x_{t-1}),\varepsilon_t+J_t,\qquad J_t=\sum_{k:\tau_k\le t}\xi_k,K(t-\tau_k;\theta),$$
The news arrival times are denoted by $\tau_k$, the impact sizes by $\xi_k$, and $K(\cdot;\theta)$ represents a response kernel which describes how the population of traders processes the news in the subsequent sessions (Merton, 1976, in the case of a jump; the kernel is the behavioural component). A method using the nearest neighbour approach can estimate only the conditional distribution of $r$ given $x_{t-1}$. Since $x_{t-1}$ provides no information about $\tau_k$ or $\xi_k$, the forecast at time $T-1$ is incapable of detecting the jump; more seriously, as the kernel $K$ is not available in the state, the forecasts at times $T$ and $T+1$ record a large positive value of $r_T$ and, basing themselves on calm analogues, predict a partial reversal, which is exactly the opposite of the drift shown in Table 7. Shocks also have a tendency to cluster — in the case of BITO, 10 out of 48 and in the case of BTC, 21 out of 98 shock days are followed by another shock within three sessions (August 19, 20 and 21 were consecutive z-shocks; 2026-02-05/06; 2024-08-05/08) — showing self-excitation (Bacry et al., 2015; Hawkes, 1971) both in the arrival of news and in the human response.

The failure modes specific to each type are illustrated in section 5.4: with respect to crypto the system becomes contrarian and responds to clustered news shocks (this is contrary to the required skill); for the index the accuracy of its directional predictions is based on the base rate of inflation and it fails when subjected to the mainly downward, heavy-tailed shocks (of -26 points), even though its contrarian bias is in the correct direction afterwards (this is a quick re-alignment); in the case of individual stocks the trend filter ends up being 'always Long' and the shocks are idiosyncratic earnings or product news for which the analog pool provides no information regardless of the direction. It is not possible for one set of indicators, one selection window, one vote threshold and one analog feature vector to be correctly specified at the same time for a 24/7 momentum-prone asset, a mean-reverting negatively skewed index and a cross-section of idiosyncratic jump processes.

A corollary regarding portfolios. The same classification shows that it is the index—which has no earnings of its own—that has enabled long-term investing to remain stable: an index comprising five hundred idiosyncratic information streams exactly cancels out the risk that this paper identifies as unforecastable, thereby leaving behind the scheduled macro news, the shocks that revert (as shown in Table 8) and the equity premium, all of which are accounted for by the always-positive base rate in Table 9. The approach also involves the conventional 60/40 stock–bond strategy with rebalancing—that is, selling bonds to buy stocks after a decline and carrying out the opposite operation after a rise—which is a concave, contrarian rule within the taxonomy developed by Perold and Sharpe (1988): it generates profits when markets are oscillating and offsets its insurance costs when they are trending, with a rebalancing bonus equal to about half the variance that is eliminated (Bernstein & Wilkinson, 1997; Hallerbach, 2014). On this archive the strategy performs as the type results predict (Appendix E, Table 21, Fig. 14): in the SPY/TLT portfolio over the period 2016–2026, a rebalanced 60/40 allocation reduced volatility from 17.5% to 11% and the maximum drawdown from −34% to −27%, without increasing returns or the Sharpe ratio, because long-term Treasuries lost money and fell in line with the stocks in 2022 (the daily return correlation between SPY and TLT was −0.4 from 2016 to 2020 and became positive in every year from 2022; see Appendix E); in the BTC/TLT case the rebalancing bonus of an asset with 58% volatility produced additional returns, while buying at the bottom of the week following a crypto market shock resulted in a loss—the continuation of Section 6.1 once again. Constant-mix rebalancing is therefore the appropriate policy for the index type and the wrong reaction to take during the first week after a crypto market shock; we are presenting it here as an example, not as an asset allocation recommendation, since drawing such a conclusion would require longer data samples, a standard bond proxy, and tests that compare Sharpe ratios.

For the product that has been put into use (with no changes to the code in this study): divide the models into separate families according to asset type (Section 8.3); use the appropriate rules (Brier, pinball/CRPS) rather than relying on directional accuracy; indicate that forecasts do not apply when $\nu_t\ge 2$ or $|s_{t-1}|\ge2.5$ instead of providing confident bands; combine the schedule target and the vote consensus into a single recommendation; and label the crypto-flagged ETF datasets by trading sessions rather than by calendar days.

There are some limitations. (1) The offline reproduction differs from the production in respect of the rotation feature and the price source (76% of the signal agreement is unfrozen); the signals for 2026 are exact. (2) News intensity is determined by the number of Benzinga headlines, which serves as a crude proxy for the level of information, salience and sentiment. (3) There are two crypto instruments, two index instruments and 50 stocks; the crypto window extends from 4.5 to 5.5 years and includes 48 and 98 shock events; the 46 stocks in the universe have not been individually verified for fidelity against the production. (4) The overlapping time horizons result in dependence; even though block bootstraps are used, the effective sample size is less than the number of rows. (5) With seven time horizons and multiple splits there is a possibility of multiplicity; we give details for all the horizons and advise the reader to treat results with $p\approx0.03$ as only suggestive. (6) Survivorship is not an issue (since there is only one instrument), but there is regime dependence: the period from 2024 to 2026 includes an ETF-approval bull run, a 2026 drawdown and a policy-driven rally.

7.3 The predictability gap

The data given in Table 16 examine the ceiling-and-floor argument associated with Proposition 4. For each instrument, the sessions with $|z|\ge2.5} represent only 3.4 to 5.0% of the total sample but account for 28.5 to 36.5% of the return variance and 13 to 18% of the absolute price movement; headline-spike days contribute an additional 5 to 14% of the sessions. It is precisely on these sessions that, according to Proposition 1, the directional accuracy of a price-conditioned model is brought down to the news-sign base rate (which is found to be 0.37–0.56) and its interval coverage is mechanically very close to zero. The accuracy during calm sessions — the one situation in which skill could in principle exist — is 0.49–0.53, so that it is no different from that of a coin and is in fact below the always-up base rate on the instruments which are drifting. The figures show that if the model had had 60% (70%) directional skill during calm sessions, its overall accuracy could still not have exceeded about 0.60 (about 0.69). The 60–70% figures claimed by retail signal products are therefore not a reasonable average; they reflect the ceiling that would result from a high level of skill during calm periods, a skill which this model — and, as shown in Section 1.1, most technical models — does not possess. The gap that this paper identifies is between the ceiling and the coin: about one third of all price variance occurs on days when the model classifies the session as ordinary and nothing that is based on past prices can explain that one third.

Table 16. The predictability gap by instrument ($h$=1). Shock = target session with $|z|\ge2.5$; ceiling = $(1-\pi)A_{\text{calm}}+\pi/2$ evaluated at hypothetical calm skill of 60% / 70%.

Column 1	Column 2	Column 3	Column 4	Column 5	Column 6	Column 7	Column 8	Column 9	Column 10	Column 11
instrument	type	shock sessions $\pi$	variance on shock sessions	$\lvert r\rvert$ on shock sessions	hit calm	hit shock	hit all	always-up	headline-spike sessions	ceiling at 60% / 70% calm skill
BTC-USD	crypto	5.0%	35.4%	17.8%	0.494	0.367	0.488	0.495	10.1%	0.59 / 0.69
BITO	crypto	4.3%	34.4%	15.3%	0.512	0.375	0.506	0.487	5.3%	0.60 / 0.69
SPXL	index	3.7%	28.5%	13.2%	0.533	0.385	0.527	0.548	4.5%	0.60 / 0.69
SPY	index	3.8%	28.8%	13.4%	0.530	0.418	0.526	0.551	4.5%	0.60 / 0.69
AAPL	stock	4.1%	32.6%	14.9%	0.514	0.494	0.513	0.530	11.4%	0.60 / 0.69
MSFT	stock	4.0%	35.2%	15.0%	0.518	0.515	0.518	0.523	14.0%	0.60 / 0.69
TSLA	stock	4.3%	36.5%	16.4%	0.496	0.497	0.496	0.516	10.6%	0.60 / 0.69
NVDA	stock	3.4%	30.1%	12.6%	0.504	0.560	0.506	0.529	7.7%	0.60 / 0.69


The gap measure has two limitations. The first is that it relies on the return-defined shock set, so the fraction of unpredictable events gives only a lower bound—one that could be raised by also including headline spikes and calendar sessions (see Sections 5.2 and 5.5); and the second is that if a model had a completely different information set—for instance, news text, order flow, or options positioning—it would not be affected by Proposition 1, the reason being that the proposition only places a bound on price-conditioned predictors, while the deployed engine and the technical-rule literature concern themselves with exactly that.

---

8. Future research: measuring the human response kernel (mathematics × neuroscience)

An important empirical fact given in this paper is that the errors committed by a pattern-based forecaster are not white; instead, they happen around and after news arrives and show a sign (the model does not account for movements that continue). This kind of structure is the result of human behaviour. Therefore, in order to cope with news events a model has to include a model of how people respond to news – a question which belongs to the field of neuroscience and which has a mathematical interface.

8.1 Mathematical program.

1. State augmentation: add to $x_t$ an observable news-intensity process $\nu_t$ and the previous standardized surprise $s_{t-1}$; estimate the conditional distribution of $r$ given $(x_{t-1},\nu_{t-1},s_{t-1})$ and check whether the drift in Table 7 becomes predictable when using out-of-sample data (using a purged, embargoed walk-forward approach as in López de Prado 2018). Second, kernel identification: estimate $K(\cdot;\theta)$ non-parametrically from the cross-section of shocks (this involves a deconvolution/Volterra problem); test the parametric cases of exponential decay (indicating a single-speed reaction), gamma (showing a delayed peak, in line with the idea of gradual information diffusion, as noted by Hong & Stein 1999), and mixtures (representing a fast algorithmic group plus a slow discretionary group). Third, self-excitation: fit marked Hawkes processes to the arrival times of shocks with headline marks; compare the branching ratios in periods of calm with those in periods when a lot of policy news is present. Fourth, regime gating: use hidden-Markov or change-point gating (as in Hamilton, 1989) so that the system switches from the analog forecaster to either abstention or a drift model when the posterior probability of the "news regime" goes above a certain threshold; assess the performance using CRPS rather than accuracy.

8.2 Neuroscience programme. The kernel K combines the individual reaction functions whose neural basis has already been partly mapped: dopaminergic reward-prediction-error signalling (Schultz et al., 1997), anticipatory nucleus accumbens activity before risk-seeking errors and anterior-insula activity before risk-averse errors (Kuhnen & Knutson, 2005), subcortical coding of the expected reward and risk (Preuschoff et al., 2006), and autonomic arousal in professional traders when volatility occurs (Lo & Repin, 2002); Frydman and Camerer (2016) explain how such measurements help to discipline behavioural-finance models. Three types of measurement could be used to identify K: (a) reaction-time distributions to salient financial headlines, by expertise, from behavioural tasks using EEG/fMRI in a subsample – the mixture of the population provides a first-order estimate of K; (b) the separation of forced flow (for example the $1.42 billion of short covering on 2026-08-19, which can be observed in order-book and funding data) from discretionary flow (from survey and laboratory studies), since the two have different kernels; and (c) longitudinal panels, because if forecasters and their users learn from the published errors the kernel is non-stationary (Lo, 2004).

8.3 A type-specific architecture. The fingerprints of Table 10 translate directly into different state variables, event calendars and validation targets; a shared “voter” pool cannot express them.

Column 1	Column 2	Column 3	Column 4
	crypto (BTC, BITO)	index (SPXL/SPXS, SPY)	single stocks
dominant shock source	unscheduled policy/headline news; liquidation cascades	scheduled macro (FOMC, CPI, payrolls, expiries); heavy left tail	own-ticker news: earnings, guidance, product; 3–4× shock odds on own-headline spikes
post-shock dynamics	continuation +1.2–3.0% (3–7 sessions), clustering 21–31%	reversal −0.5–1.4%, VR 0.82–0.88	heterogeneous; revert (AAPL/MSFT) or continue (TSLA/NVDA)
state variables to add	headline intensity $\nu_t$, last surprise $s_{t-1}$, funding/liquidation flow, post-shock age	event-calendar dummies, VIX level/term structure, skew, drawdown state	earnings-date proximity (embargo), sector-ETF residual return, beta-adjusted momentum, split state
session calendar	7-day; weekend bars	NYSE sessions	NYSE sessions
forecaster form	regime-gated: analog in calm, drift/kernel model $K$ after shocks, abstain when $\nu_t\ge2$	mean-reversion/vol-regime model with asymmetric loss; explicit inverse-ETF drag in the exposure map	cross-sectionally pooled analogs (peer stocks), earnings-aware; benchmark-relative gate instead of a 200-day filter
validation gate	CRPS + Kelly growth on shock and calm sessions separately	PT statistic against the always-up base rate; drawdown on shock windows	PT vs base rate per stock and pooled; embargoed purged CV around earnings


The common element is not the voter set but the evaluation contract: every type is scored against its own base rate with a proper rule, on calm and shock sessions separately, before anything is published.

8.4 News, social media and the neuroscience of collective reaction. The rally on 19 August 2026, the documented impact of Elon Musk's posts on cryptocurrency prices (Ante, 2023) and presidential posts on Truth Social all indicate the presence of a chain of transmission that goes from post to attention to arousal to herding to order flow to price, with this process becoming increasingly mediated through social platforms rather than through newswires. There is an empirical foundation for each stage of this chain: attention capture and attention-induced trading (Barber et al., 2022; Da et al., 2011), disagreement and herding on investor social networks (Cookson & Niessner, 2020; Pedersen, 2022), the epidemic spread of narratives (Shiller, 2017), and measurable collective mood (Bollen et al., 2011; Ranco et al., 2015). The neuroscience of social influence provides the underlying mechanisms: herd information changes the striatal valuation signals involved in financial decisions (Burke et al., 2010), conformity is caused by a reinforcement-learning error signal (Klucharev et al., 2009), the opinions of others influence reward-related valuation (Campbell-Meiklejohn et al., 2010), and anticipatory neural activity can predict financial decisions (Knutson & Bossaerts, 2007). A specific programme consists of: (a) extending the event list in Tables 14–15 into a labelled corpus containing the source (executive, political, regulator, analyst, wire), the channel (social post or newswire), the reach and the sentiment; (b) estimating the response kernel $K$ by source and channel — the hypothesis is that shocks originating on social media have a quicker onset, a greater continuation over the short term and stronger clustering than those from newswires; (c) in the laboratory, carrying out reaction-time and choice tasks with social cues (a post showing visible engagement) compared with matched neutral headlines, and recording arousal (measured by pupil size and skin conductance) and, in a subset of cases, fMRI, in order to obtain individual kernels whose average makes up $K$; (d) incorporating the results into the forecaster as a social-intensity state variable $\nu^{\text{SNS}}_t$ and as a post-shock drift term, and training the model on labelled information events rather than on price patterns — that is, learning about behaviour rather than about noise. This kind of measurement of social contagion in financial markets should be pre-registered and must respect privacy.

The aim in practice is not to predict the news—since that cannot be done on the basis of prices—but to determine at the moment the news arrives how the crowd will eventually react, and to have the model state that it does not know until that time has come. In this way, the current silent 0%-coverage failures would become flagged and quantifiable regimes, and the drift mentioned in Table 7 could be modelled instead of just being lost.

---

9. Conclusion

When the seven-session analog forecaster for Bitcoin instruments is examined in full detail and at each point in time, it is directionally uninformative (showing accuracy of 46–51% at all horizons), is well-calibrated in terms of the width of its predictions during periods of calm, but becomes systematically wrong in both the direction and the width of its forecasts when exogenous news occurs: on days when a shock or a headline spike takes place, its next-session accuracy is only 37–39%, it provides no coverage the day before a shock, and its mean surprise is 3.6 band-$\sigma$. Prices tend to move in the direction of the shock for about a week, whereas the model's consensus takes 5 to 6 sessions to catch up. The 2026-08-19 CLARITY-Act rally, a case in which the model advised a fully inverse position, is an example of this kind of failure. The root of the problem is structural in that human reactions to information do not depend on past prices, which shows that a combination of mathematical and neuroscientific methods is needed if this kind of response is to be measured and modelled. The failure is also specific to the type of situation: the same forecasting engine is contrarian when there are continuing shocks in crypto, is base-rate-inflated and prone to collapse when applied to the negatively skewed index, and is ineffective when dealing with individual stocks that experience sudden jumps due to their own news; no one schedule (whether daily, weekly, or once) performs best across all instruments. The constructive test shows the advantages of using such families of models: an event-conditioned gate that is estimated entirely from historical data restores coverage during earnings sessions (the interval coverage rising from 0.49 to 0.68 across 50 stocks, with a +15% improvement in interval score) and after crypto shocks, while using the wrong gate for a given type of event is harmful. The gap is quantified in that 3 to 5 per cent of the sessions account for 28 to 37 per cent of the return variance and cannot be predicted in terms of sign from prices, so even if the model has 60 to 70 per cent skill during calm periods, its overall accuracy would still only reach 0.60 to 0.69, and the actual skill during calm periods is negligible. For users, the practical advice is limited: after a crypto shock, take action within one session or don't act at all; after moves in the index or in individual stocks, do not chase. To close this gap it is necessary to model the human reaction to news and social media—specifically the attention, arousal, and herding behaviour described in Section 8.4—rather than simply the path that prices take afterwards.

