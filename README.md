# finance-signal — research code for *When the News Arrives*

Reproducible audit of a **deployed** seven-session market forecaster around
exogenous information shocks: cryptocurrency (BITO/BITI, BTC/USD), the S&P 500
pair (SPXL/SPXS, SPY) and 50 S&P 500 single stocks — about 1.49 million
point-in-time forecasts scored origin by origin.

| resource | link |
|---|---|
| Working context / handover | [`research/HANDOVER.md`](research/HANDOVER.md) |
| Working paper (draft v1.0) | [`research/PAPER.md`](research/PAPER.md) |
| Engineering summary | [`research/IMPLEMENTATION_GUIDE.md`](research/IMPLEMENTATION_GUIDE.md) |
| Companion manuscripts | [`research/papers/`](research/papers/) |
| Data deposit (derived outputs, CC BY 4.0) | [10.5281/zenodo.22308637](https://doi.org/10.5281/zenodo.22308637) |
| Event catalogue (346 single-stock increases, attributed) | [`research/STOCK_EVENTS.md`](research/STOCK_EVENTS.md) |

## What this repository is — and is not

It **is** the complete analysis pipeline: rolling-origin scoring, the event
studies (return shocks, headline spikes, FOMC/payroll/earnings calendars), the
sequential effectiveness tests, false-discovery control, the predictability-gap
computation, the gate experiment, the action-policy and entry-delay backtests,
and every figure and table in the paper.

It is **not** the forecasting engine being audited. That model is proprietary and
is not published here. In its place, [`model/INTERFACE.md`](model/INTERFACE.md)
specifies exactly what the audited engine must produce — two functions and one
payload schema — which means **the audit runs on any forecaster** that satisfies
that contract. Substituting your own model is a documented, supported path, and
the resulting scores are directly comparable to the paper's.

## Three ways to run it

**1. Reproduce the published results (no engine, no licensed data).**
Download `derived_outputs.zip` from the [Zenodo deposit](https://doi.org/10.5281/zenodo.22308637),
unzip into `research/output/`, then run the analysis steps (3 onward) in
[`research/README.md`](research/README.md). Every table and figure regenerates in
a few minutes.

**2. Audit your own forecaster.** Implement `run_simulation` and
`build_forecast` per [`model/INTERFACE.md`](model/INTERFACE.md) and run the full
pipeline from step 1.

**3. Rebuild the inputs from scratch.** The licensed price and news data are not
redistributed. `research/deposit/RAW_INPUTS_MANIFEST.md` in the Zenodo record
gives the SHA-256 hash and the exact retrieval command for every raw file, so a
fresh pull can be verified byte-for-byte before rerunning.

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r research/requirements.txt
.venv/bin/python research/event_study.py bito btc spxl spy      # etc.
```

## Headline findings

- Directional accuracy is **46–53% at every horizon on every instrument** and
  never passes the Pesaran–Timmermann test; pooled over 50 stocks the statistic
  is 3.08 — a real but economically negligible 0.3-point dependence — while the
  Brier score is worse than a constant ½ for 98% of stocks.
- Nominal-80% intervals cover 78–82% of outcomes on calm sessions, **28% on
  earnings sessions** and **0% the day before a large move**.
- 3–5% of sessions carry **28–37% of return variance** and are unpredictable in
  sign from prices, which caps any price-conditioned forecaster near the coin.
- After shocks, prices behave by type: crypto **continues** (+3.0% over seven
  sessions), the index **reverts**, single stocks split by cause. The model's
  consensus needs 2–7 sessions to agree.
- A causal, walk-forward **event-conditional gate** restores earnings-session
  coverage from 0.49 to 0.68 across 50 stocks (interval score +15.5%) — while the
  same rule *hurts* the other asset types, which is the paper's argument in
  constructive form.

## Layout

```
model/            interface specification and stubs (engine not published)
research/         analysis pipeline, paper, guide, manuscripts
  output/         figures and small result files; the full set is on Zenodo
  papers/         four manuscripts, cover letters, submission plan
```

## Citing

> Kim, K., Kim, K., & Ahn, D. (2026). *When the News Arrives: Calibration Failure of a Deployed Price-Pattern Forecaster Around Information Shocks in Crypto, Index and Single-Stock Markets.*
> Working paper.
> Data: Zenodo, https://doi.org/10.5281/zenodo.22308637

## Licence

Code in this repository: **Apache License 2.0** (see [`LICENSE`](LICENSE)).
The deposited data and the manuscripts: **CC BY 4.0**
([10.5281/zenodo.22308637](https://doi.org/10.5281/zenodo.22308637)).
The licensed market data and news text that the study consumes are neither
redistributed nor covered by these licences.

## Disclosure

The authors operate the forecasting service audited here. All event definitions,
scoring rules and thresholds were fixed before any forecast was scored; the
deployed model was not changed during the study; and the code and data manifest
are released so that the evaluation can be repeated by third parties. Nothing in
this repository is investment advice.
