# When information breaks the historical pattern: preliminary evidence from a deployed Bitcoin forecaster

**Abstract.** Historical-pattern forecasts may fail when information moves prices beyond historical support. We audit next-session forecasts from a deployed Bitcoin system. Across 1,973 BTC/USD and 1,125 BITO origins, directional accuracy was 48.8% and 50.6%, with near-nominal interval coverage. On ex-post return-defined large-move sessions, accuracy fell to 36.7% and 37.5%, and all nominal-80% intervals missed. Headline-count spikes increased standardized error for both instruments, but directional degradation appeared only for BTC and was imprecise. These exploratory results do not measure investor behavior; they motivate research into which news changes behavior and how responses propagate into prices.

**Keywords:** Bitcoin; forecast evaluation; information shocks; investor attention; historical analogs.  
**JEL:** G14, G17, C53.

## 1. Introduction

Price-pattern forecasters assume that a market state resembling a historical state has an informative historical continuation. This premise is fragile when new information changes beliefs, constraints, or attention faster than those changes enter a price-based state vector. Average performance can therefore conceal failures on observations that matter most.

We audit a deployed historical-analog forecasting system for BTC/USD and the ProShares Bitcoin Strategy ETF (BITO). We ask whether its next-session direction and nominal 80% interval are informative on average, whether performance changes with unusually high headline counts, and what happens when the realized move is far outside the recent volatility scale.

The last condition is diagnostic rather than predictive: a large-move session is defined using the realized return and cannot be known at forecast time. The target-day headline count is observable by day-end but may itself respond to the move. It measures information intensity, not content or causality. The contribution is therefore a preliminary reliability-boundary finding, not a theorem about news or investor behavior.

Technical-rule performance is often weak and data-sensitive (Brock et al., 1992; Sullivan et al., 1999), while information and attention are related to market activity (Chan, 2003; Da et al., 2011; Tetlock, 2007). Cryptocurrency also has distinctive risk (Liu and Tsyvinski, 2021; Urquhart, 2016). We connect these literatures by showing how the forecast distribution from a live pattern-based product changes conditionally around information-intensive and extreme-return observations.

## 2. Data and design

### 2.1 Forecasts and data

Members of the research team operate the audited service. Its seven-session historical-analog model maps recent price and indicator states to similar historical states and reports a probability of an increase, a median, and P10/P90 paths. We treat the engine as a black box.

The 2026 directional signals were frozen from the deployed service. Multi-horizon distributions were reconstructed with the production engine in a point-in-time harness. The public materials permit reanalysis of archived forecast-score rows, but the proprietary engine is not released and forecasts cannot be regenerated independently from raw prices.

We use 1,973 BTC/USD origins from 5 April 2021 through 29 August 2026 and 1,125 BITO origins from 4 March 2022 through 27 August 2026. Prices are licensed Alpaca daily bars. Headline counts use the licensed Benzinga feed available through Alpaca from February 2024. Headline text is not redistributed.

### 2.2 Scores, conditions, and inference

We score only the next session. Directional accuracy is

$$
H_t=\mathbf{1}\left\{\mathbf{1}(\hat p_t\ge 0.5)=\mathbf{1}(R_{t+1}>0)\right\},
$$

where $\hat p_t$ is the forecast probability of an increase and $R_{t+1}$ is the realized return. Interval coverage is one when the return lies between forecast P10 and P90. Standardized absolute surprise is

$$
|s_t|=\left|\frac{R_{t+1}-\hat q_{50,t}}{(\hat q_{90,t}-\hat q_{10,t})/2.5631}\right|.
$$

The denominator maps P10-P90 width to a normal-distribution scale without assuming normal returns.

A headline-count spike has a target-day count at least twice its trailing 30-day median, with one added to numerator and denominator. A large realized move has $|r_{t+1}|/\hat\sigma^{(20)}_t\ge2.5$, where volatility uses only information through the origin. Large-move results are ex-post diagnostics. Zero conditional coverage is partly mechanical because the event threshold is wider than a typical forecast interval.

Point estimates and 95% intervals use a circular moving-block bootstrap with seven-observation blocks and 4,000 deterministic draws. Conditional differences resample the complete ordered sequence with the event indicator attached. The analysis was not preregistered.

## 3. Results

### 3.1 Average and conditional performance

BTC/USD next-session accuracy is 0.488 (95% block interval 0.467 to 0.510), and BITO accuracy is 0.506 (0.479 to 0.532). Nominal 80% coverage is 0.784 (0.764 to 0.802) for BTC and 0.777 (0.752 to 0.801) for BITO. Intervals are approximately calibrated marginally, while forecast medians offer little directional separation.

**Table 1. Next-session performance by condition.** Large realized moves are outcome-defined diagnostics.

| instrument | condition | n | accuracy | coverage | mean absolute surprise |
|---|---:|---:|---:|---:|---:|
| BTC/USD | all origins | 1,973 | 0.488 | 0.784 | 0.852 |
| BTC/USD | quiet-news days | 847 | 0.499 | 0.783 | 0.844 |
| BTC/USD | headline-count spikes | 95 | 0.389 | 0.684 | 1.148 |
| BTC/USD | large realized moves | 98 | 0.367 | 0.000 | 3.593 |
| BITO | all origins | 1,125 | 0.506 | 0.777 | 0.889 |
| BITO | quiet-news days | 612 | 0.500 | 0.776 | 0.868 |
| BITO | headline-count spikes | 34 | 0.529 | 0.676 | 1.270 |
| BITO | large realized moves | 48 | 0.375 | 0.000 | 3.682 |

On BTC headline-count spike days, accuracy is 0.389 versus 0.499 on quiet-news days, a difference of -0.110 (95% block interval -0.216 to 0.003). Coverage falls by 0.099 (-0.205 to 0.006), and absolute surprise rises by 0.304 (0.036 to 0.605). BITO accuracy is 0.529 on 34 spike days and 0.500 on 612 quiet days, a difference of 0.029 (-0.138 to 0.229). Coverage differs by -0.100 (-0.273 to 0.074), while absolute surprise rises by 0.402 (0.040 to 0.822). The replicated signal is larger forecast error, not directional reversal.

On 98 BTC large-move sessions, accuracy is 0.367 versus 0.494 otherwise, a difference of -0.127 (-0.220 to -0.030). On 48 BITO large-move sessions, accuracy is 0.375 versus 0.512, a difference of -0.137 (-0.276 to 0.002). Every P10-P90 interval misses in both samples. This locates conditional distribution failure; it does not establish that every move was news-caused.

### 3.2 Sensitivity checks

Changing the bootstrap block length to 3, 14, or 21 observations leaves point estimates unchanged. At all four block lengths, the BTC large-move accuracy interval remains below zero and the headline-spike absolute-surprise interval remains above zero. BITO's headline-spike surprise interval also remains above zero; its large-move accuracy interval is near zero and changes inclusion of zero with block length.

For BTC, the large-move accuracy difference is -0.083 at $|z|\ge2.0$ (172 events), -0.127 at 2.5 (98), and -0.136 at 3.0 (59); all three intervals exclude zero. BITO estimates are less stable. Absolute-surprise differences are positive for both instruments at headline-ratio thresholds 1.5 and 2.0, but become imprecise at 2.5 and 3.0 as event counts fall to 31 and 19 for BTC and 16 and 14 for BITO. These checks support the narrow error-magnitude result, not a general directional news effect.

### 3.3 Motivating information event

On 18 August 2026, before a reported White House crypto-policy meeting and public push for the CLARITY Act, the BTC model assigned a next-session median return of -0.05% and P90 of +1.15%. BTC rose 7.15% the next session and 21.10% over three sessions, versus a three-session P90 of +2.61%. For BITO, the next-session median was +0.32% and P90 was +2.06%; realized returns were +5.96% in one session and +19.24% in three, versus a three-session P90 of +3.82%. BITO's direction was correct, but its forecast magnitude failed. Public reporting linked the rally to the policy event (CNBC, 2026; Ray, 2026).

![Figure 1. Panels A-B show directional accuracy and nominal-80% coverage by condition. Panels C-D show point-in-time forecasts issued at the 18 August 2026 close and subsequent paths. Dotted 0.5 and dashed 0.8 lines are directional and coverage references. The event line marks 19 August.](../../output/figures/fig_frl_combined.pdf)

## 4. Discussion and conclusion

Marginal calibration does not guarantee conditional reliability: approximately 78% overall coverage coexists with extreme conditional misses. Headline volume alone is too coarse for a reliability gate. It mixes anticipated and unexpected releases, favorable and unfavorable content, repeated reporting, and stories with different credibility or reach.

This audit does not observe behavior. Attention, belief updating, herding, forced liquidation, institutional rebalancing, and market-microstructure constraints cannot be distinguished from price errors alone. The next study should preregister a news taxonomy covering content, novelty, timing, credibility, and expectedness; link it to direct measures such as order flow, liquidations, search, or social attention; and prospectively test whether withholding or widening forecasts improves proper scores.

The evidence is limited to one proprietary product and two economically dependent Bitcoin exposures. Target-day headline counts may respond to price, large-move conditioning is ex post, and the study followed the motivating August event. Distributional forecasts before the live archive were reconstructed with production code. Results are exploratory and may combine properties of the engine with the reconstruction.

One deployed historical-pattern forecaster is marginally calibrated in interval width yet fails conditionally on large realized moves. High headline counts are associated with larger standardized errors in both instruments, while their directional relationship does not replicate. This is evidence of a reliability boundary, not a psychological mechanism. Identifying which information changes behavior and whether that response can warn a price-pattern model remains a prospective research question.

## Data availability

Rights-safe aggregate results and analysis code will be released in a public repository after review; anonymized materials are available to the editor on request. Raw licensed price bars and headline text are not redistributed. The proprietary forecast-generation engine is not included, so archived forecast-score rows can be reanalysed but forecasts cannot be regenerated independently.

## Declaration of competing interest

Members of the research team operate the forecasting service evaluated in this study. No investment recommendation is made.

## Declaration of generative AI and AI-assisted technologies in the writing process

During preparation of this work, the authors used Cursor with an OpenAI language model to assist with code review, test generation, figure preparation, and language editing. The authors reviewed and validated the resulting code, calculations, and text and take full responsibility for the content of the publication.

## References

- Brock, W., Lakonishok, J., and LeBaron, B. (1992). Simple technical trading rules and the stochastic properties of stock returns. *Journal of Finance*, *47*(5), 1731-1764. https://doi.org/10.1111/j.1540-6261.1992.tb04681.x
- Chan, W. S. (2003). Stock price reaction to news and no-news: Drift and reversal after headlines. *Journal of Financial Economics*, *70*(2), 223-260. https://doi.org/10.1016/S0304-405X(03)00146-6
- CNBC. (2026, August 20). Bitcoin surges 12% in two days as Trump, crypto executives lead final push for Clarity Act. <https://www.cnbc.com/2026/08/20/bitcoin-surges-as-trump-crypto-execs-lead-final-push-for-clarity-act.html>
- Da, Z., Engelberg, J., and Gao, P. (2011). In search of attention. *Journal of Finance*, *66*(5), 1461-1499. https://doi.org/10.1111/j.1540-6261.2011.01679.x
- Liu, Y., and Tsyvinski, A. (2021). Risks and returns of cryptocurrency. *Review of Financial Studies*, *34*(6), 2689-2727. https://doi.org/10.1093/rfs/hhaa113
- Ray, S. (2026, August 20). Bitcoin soars above \$70,000 after Trump calls for passage of Clarity Act at White House crypto event. *Forbes*. <https://www.forbes.com/sites/siladityaray/2026/08/20/bitcoin-soars-above-70000-after-trump-calls-for-passage-of-clarity-act-at-white-house-crypto-event/>
- Sullivan, R., Timmermann, A., and White, H. (1999). Data-snooping, technical trading rule performance, and the bootstrap. *Journal of Finance*, *54*(5), 1647-1691. https://doi.org/10.1111/0022-1082.00163
- Tetlock, P. C. (2007). Giving content to investor sentiment: The role of media in the stock market. *Journal of Finance*, *62*(3), 1139-1168. https://doi.org/10.1111/j.1540-6261.2007.01232.x
- Urquhart, A. (2016). The inefficiency of Bitcoin. *Economics Letters*, *148*, 80-82. https://doi.org/10.1016/j.econlet.2016.09.019
