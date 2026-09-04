# Why price‑pattern forecasters fail when people react: a neuroeconomic research agenda for news and social media in markets

**Target: *Frontiers in Behavioral Neuroscience* (Perspective) or *Frontiers in Neuroscience — Decision Neuroscience* (Perspective, ≈3,000 words, 1 figure).** Companion to *When the News Arrives* (arXiv, q‑fin.ST), which supplies the empirical motivation; this piece argues the research program.

*Kibaek Kim, Kiok Kim, Danielle Ahn — dotori.ai*

**Abstract.** Machine‑learning forecasters that condition on the past price path are widely deployed in retail finance. Auditing one such deployed model across cryptocurrency, an equity index and fifty single stocks shows a consistent structure: interval calibration is adequate in calm periods, directional skill is absent, and both collapse on the 3–5% of sessions when exogenous information arrives — sessions that carry roughly a third of all price variance and on which prices then drift for days in the direction of the news. The failure is not a modelling detail; it is the absence, from the model's state space, of the process that produces the move: human reaction to information, increasingly transmitted and amplified through social media. We propose a neuroeconomic program to measure that process — a population *response kernel* — through reaction‑time and arousal studies with social cues, the separation of forced from discretionary flow, and longitudinal panels, and we show how the resulting kernel can be placed inside forecasting models as a state variable and a post‑shock drift term. Predicting the news is impossible from prices; predicting how the crowd finishes reacting is a measurable neuroscience question.

**Keywords:** neuroeconomics; social influence; herding; attention; news; social media; financial forecasting; reward prediction error.

## 1. The empirical fact that motivates the program

Price‑pattern models — indicator ensembles, nearest‑neighbour analogs, small classifiers — assume that the variables governing the next several sessions are functions of the price path. A point‑in‑time audit of a deployed seven‑session analog forecaster on eight instruments (Kim, 2026) finds: directional accuracy of 46–53% that never passes the Pesaran–Timmermann test; Brier scores worse than a constant ½; nominal‑80% bands that cover 78–82% of outcomes in calm periods but 25% on earnings sessions and 0% the day before a |*z*|≥2.5 shock; and, after a shock, drift of +3% over seven sessions in Bitcoin and +2.3% after earnings increases in single stocks, while the model's consensus needs 4–6 sessions to agree. Sessions with |*z*|≥2.5 are 3–5% of the sample and carry 28–37% of return variance. A simple bound follows: for any price‑conditioned predictor, accuracy on jump‑dominant news days equals the news‑sign base rate, so the average cannot exceed (1−π)*A*_calm + π/2 — the coin when calm skill is nil, ≈0.60–0.69 even with 60–70% calm skill.

Three facts point past finance and into behaviour. First, the model's error has a *sign*: it fades moves that continue, because its analogs come from calm regimes in which large moves revert. Second, the continuation is produced by people arriving late — post‑announcement drift (Bernard & Thomas, 1989; Chan, 2003), under‑reaction (Frazzini, 2006; Hong et al., 2000), attention‑induced trading (Barber et al., 2022). Third, the arrival channel is changing: the 2026‑08‑19 rally followed a White House event amplified on social platforms; executive posts move cryptocurrency prices (Ante, 2023); investor social networks shape disagreement and herding (Cookson & Niessner, 2020; Pedersen, 2022); narratives spread epidemically (Shiller, 2017).

## 2. The missing state variable, written down

Write the session return as *r*_t = μ(*x*_{t−1}) + σ(*x*_{t−1})ε_t + *J*_t with *J*_t = Σ_k ξ_k *K*(t − τ_k; θ): news arrives at times τ_k with impact ξ_k, and *K* is a **response kernel** describing how the population of traders digests the information over the following sessions (Merton 1976 for the jump; the kernel is the behavioural addition). A price‑conditioned model estimates the law of *r* given *x*_{t−1} only; it cannot see τ_k or ξ_k, and — more damagingly — because *K* is not in its state, it observes a large *r*_T and predicts partial reversal, the opposite of what *K* produces. *K* is not a financial constant. It is the aggregate of individual reaction functions: how fast people notice (attention), how strongly they respond (arousal, valuation update), whether they copy others (social influence), and whether they are forced (margin and liquidation cascades — $1.42 bn of short covering on 2026‑08‑19).

## 3. What neuroscience already tells us about *K*

Each component has a neural literature. Reward‑prediction‑error signalling in dopaminergic circuits (Schultz et al., 1997) is the update mechanism a surprise engages. Anticipatory nucleus‑accumbens activity precedes risk‑seeking errors and anterior‑insula activity precedes risk‑averse errors (Kuhnen & Knutson, 2005); anticipatory activity predicts financial choices (Knutson & Bossaerts, 2007); expected reward and risk are coded separately in subcortical structures (Preuschoff et al., 2006). Social influence is not a metaphor: herd information changes striatal valuation signals during financial decisions (Burke et al., 2010), conformity is driven by a reinforcement‑learning error signal (Klucharev et al., 2009), and others' opinions shift reward‑related valuation (Campbell‑Meiklejohn et al. 2010). Professional traders show autonomic arousal during volatility (Lo & Repin, 2002). Frydman and Camerer (2016) review how such measurements have disciplined behavioural‑finance models. What is missing is the bridge from these individual‑level findings to the population kernel *K* that a forecaster needs.

## 4. A measurement program

**4.1 A labelled event corpus.** The audit produced a catalogue of 346 significant single‑stock increases classified as earnings (23%), market‑wide (29%) or idiosyncratic news (48%), with headline attribution; extend it across instruments and code each event by *source* (executive, political, regulator, analyst, wire), *channel* (social post vs newswire), reach, and sentiment.

**4.2 Kernel estimation by source × channel.** Estimate *K* non‑parametrically from the cross‑section of events (a deconvolution problem) and test parametric forms: exponential (single‑speed reaction), gamma (delayed peak; gradual diffusion, Hong & Stein 1999), mixtures (fast algorithmic and slow discretionary populations). Hypotheses: social‑media‑originated shocks show faster onset, larger short‑horizon continuation and stronger clustering (self‑excitation; Hawkes 1971; Bacry, Mastromatteo & Muzy 2015) than newswire shocks; earnings events show the slow, monotone drift of Bernard–Thomas; market‑wide days show reversal.

**4.3 Laboratory measurement of individual kernels.** Reaction‑time and choice tasks presenting matched financial headlines with and without social cues (a post with visible engagement), stratified by expertise, recording pupil dilation and skin conductance as arousal proxies and, in a subsample, fMRI of striatal and insular responses. The individual response function (latency, magnitude, social multiplier) is the object; the population mixture of these functions is a first estimate of *K*, to be compared with the market‑estimated kernel of 4.2.

**4.4 Forced versus discretionary flow.** Liquidation cascades are observable in order‑book and derivatives funding data and have a mechanical kernel; discretionary reaction does not. The two must be separated before any behavioural interpretation, using exchange data for the former and survey/laboratory data for the latter.

**4.5 Longitudinal panels.** If forecasters and their users learn from published errors, *K* is non‑stationary (Lo, 2004). Repeated measurement is required; a deployed product with public forecasts is, unusually, a natural panel.

## 5. Putting *K* back into the model

The forecaster does not need to predict the news. It needs (i) a state variable for *information intensity* — headline and social‑post counts relative to their trailing median, ν_t and ν^SNS_t — to know when its analog pool is uninformative and abstain or widen; (ii) a *post‑shock drift term* given by *K*, estimated walk‑forward by source and channel, to replace the calm‑regime reversal it currently predicts; and (iii) training on labelled information events rather than on price patterns, so that the model learns the behaviour rather than the noise. In the audit, a causal gate built from (i) and a walk‑forward drift term of type (ii) are tested out of sample; the result is reported in the companion paper.

## 6. Ethics and open science

Measuring social contagion in markets touches manipulation. Studies should be pre‑registered, use public posts only, protect participant identity, and publish kernels at the population level. The audit's protocol, code and data manifest are released so that the empirical claims can be re‑run by third parties.

**Figure 1.** The transmission chain *post → attention → arousal → herding → order flow → price*, with the neural and behavioural literature attached to each link and the response kernel *K* as the object the forecaster needs. *(schematic; to be drawn)*

**Data availability.** The audit's derived data, event catalogues and scores are deposited at Zenodo (DOI [10.5281/zenodo.22308637](https://doi.org/10.5281/zenodo.22308637), CC BY 4.0); licensed raw inputs are described by hash and retrieval command in the deposit.

**Conflict of interest.** The authors operate the forecasting service audited in the companion paper.

## References

Ante, L. (2023). How Elon Musk's Twitter activity moves cryptocurrency markets. *Technological Forecasting and Social Change*, *186*, 122112.
Bacry, E., Mastromatteo, I., & Muzy, J.‑F. (2015). Hawkes processes in finance. *Market Microstructure and Liquidity*, *1*(1), 1550005.
Barber, B. M., Huang, X., Odean, T., & Schwarz, C. (2022). Attention‑induced trading and returns: Evidence from Robinhood users. *Journal of Finance*, *77*(6), 3141–3190.
Bernard, V. L., & Thomas, J. K. (1989). Post‑earnings‑announcement drift. *Journal of Accounting Research*, *27*(Suppl.), 1–36.
Burke, C. J., Tobler, P. N., Schultz, W., & Baddeley, M. (2010). Striatal BOLD response reflects the impact of herd information on financial decisions. *Frontiers in Human Neuroscience*, *4*, 48.
Campbell‑Meiklejohn, D. K., Bach, D. R., Roepstorff, A., Dolan, R. J., & Frith, C. D. (2010). How the opinion of others affects our valuation of objects. *Current Biology*, *20*(13), 1165–1170.
Chan, W. S. (2003). Stock price reaction to news and no‑news. *Journal of Financial Economics*, *70*(2), 223–260.
Cookson, J. A., & Niessner, M. (2020). Why don't we agree? Evidence from a social network of investors. *Journal of Finance*, *75*(1), 173–228.
Frazzini, A. (2006). The disposition effect and underreaction to news. *Journal of Finance*, *61*(4), 2017–2046.
Frydman, C., & Camerer, C. F. (2016). The psychology and neuroscience of financial decision making. *Trends in Cognitive Sciences*, *20*(9), 661–675.
Hawkes, A. G. (1971). Spectra of some self‑exciting and mutually exciting point processes. *Biometrika*, *58*(1), 83–90.
Hong, H., & Stein, J. C. (1999). A unified theory of underreaction, momentum trading, and overreaction. *Journal of Finance*, *54*(6), 2143–2184.
Hong, H., Lim, T., & Stein, J. C. (2000). Bad news travels slowly. *Journal of Finance*, *55*(1), 265–295.
Kim, K., Kim, K., & Ahn, D. (2026). *When the news arrives: Calibration failure of a pattern-based seven-session forecast around exogenous information shocks* [Working paper]. Zenodo. https://doi.org/10.5281/zenodo.22308637
Klucharev, V., Hytönen, K., Rijpkema, M., Smidts, A., & Fernández, G. (2009). Reinforcement learning signal predicts social conformity. *Neuron*, *61*(1), 140–151.
Knutson, B., & Bossaerts, P. (2007). Neural antecedents of financial decisions. *Journal of Neuroscience*, *27*(31), 8174–8177.
Kuhnen, C. M., & Knutson, B. (2005). The neural basis of financial risk taking. *Neuron*, *47*(5), 763–770.
Lo, A. W., & Repin, D. V. (2002). The psychophysiology of real‑time financial risk processing. *Journal of Cognitive Neuroscience*, *14*(3), 323–339.
Lo, A. W. (2004). The Adaptive Markets Hypothesis. *Journal of Portfolio Management*, *30*(5), 15–29.
Merton, R. C. (1976). Option pricing when underlying stock returns are discontinuous. *Journal of Financial Economics*, *3*(1–2), 125–144.
Pedersen, L. H. (2022). Game on: Social networks and markets. *Journal of Financial Economics*, *146*(3), 1097–1119.
Preuschoff, K., Bossaerts, P., & Quartz, S. R. (2006). Neural differentiation of expected reward and risk in human subcortical structures. *Neuron*, *51*(3), 381–390.
Schultz, W., Dayan, P., & Montague, P. R. (1997). A neural substrate of prediction and reward. *Science*, *275*(5306), 1593–1599.
Shiller, R. J. (2017). Narrative economics. *American Economic Review*, *107*(4), 967–1004.
