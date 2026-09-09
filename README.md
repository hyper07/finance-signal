# finance-signal — audit code for a deployed Bitcoin forecaster

Exploratory audit of a **deployed** seven-session market forecaster around
information-intensive and large-return observations. The publication-ready
scope is currently limited to next-session BTC/USD and BITO results. Broader
index and single-stock analyses remain working material.

| resource | link |
|---|---|
| Working context / handover | [`research/HANDOVER.md`](research/HANDOVER.md) |
| Finance Research Letters draft | [`research/papers/frl_submission/`](research/papers/frl_submission/) |
| Preliminary arXiv paper | [`research/papers/arxiv_prefinding/paper.md`](research/papers/arxiv_prefinding/paper.md) |
| Preliminary-paper results | [`research/output/arxiv_prefinding.json`](research/output/arxiv_prefinding.json) |
| Full working paper (not submission-ready) | [`research/PAPER.md`](research/PAPER.md) |
| Engineering summary | [`research/IMPLEMENTATION_GUIDE.md`](research/IMPLEMENTATION_GUIDE.md) |
| Companion manuscripts | [`research/papers/`](research/papers/) |
| Existing data deposit (must be updated before posting) | [10.5281/zenodo.22308637](https://doi.org/10.5281/zenodo.22308637) |

## What this repository is — and is not

It contains the analysis pipeline: rolling-origin scoring, the event
studies (return shocks, headline spikes, FOMC/payroll/earnings calendars), the
sequential effectiveness tests, false-discovery control, the predictability-gap
computation, the gate experiment, the action-policy and entry-delay backtests,
and figure/table generation. Some broader-paper methods remain under revision.

It is **not** the forecasting engine being audited. That model is proprietary and
is not published here. In its place, [`model/INTERFACE.md`](model/INTERFACE.md)
specifies exactly what the audited engine must produce — two functions and one
payload schema — which means **the audit runs on any forecaster** that satisfies
that contract. Substituting your own model is a documented, supported path, and
the resulting scores are directly comparable to the paper's.

## Three ways to run it

**1. Reanalyse archived forecast scores (no engine).**
The narrow preprint starts from `forecasts_btc.csv` and `forecasts_bito.csv`.
Those rows can be rescored without the engine, but forecast generation itself
cannot be reproduced independently. A rights-safe, updated data archive is
required before public posting.

**2. Audit your own forecaster.** Implement `run_simulation` and
`build_forecast` per [`model/INTERFACE.md`](model/INTERFACE.md) and run the full
pipeline from step 1.

**3. Rebuild licensed inputs.** Raw price bars and news text are not
redistributed. The manifest records hashes and provenance, but the public
repository does not currently contain a complete retrieval utility.

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r research/requirements-publish.txt
MPLCONFIGDIR=/tmp/mplconfig .venv/bin/python research/arxiv_prefinding.py
.venv/bin/python research/build_arxiv_prefinding.py
# Requires Tectonic on PATH:
.venv/bin/python research/build_frl_submission.py
```

## Preliminary findings

- Next-session directional accuracy is **48.8% for BTC/USD** and **50.6% for
  BITO**, with marginal nominal-80% coverage of 78.4% and 77.7%.
- On outcome-defined large-move sessions, accuracy falls to **36.7%** and
  **37.5%**, and all P10-P90 intervals miss. The coverage result is partly
  mechanical and is reported only as a conditional diagnostic.
- Headline-count spikes increase standardized forecast error for both assets.
  Directional degradation appears for BTC but not BITO, so counts alone are not
  a reliable news gate.
- The paper does **not** measure human behavior. It motivates prospective work
  on which news changes behavior and how those responses propagate into prices.

## Layout

```
model/            interface specification and stubs (engine not published)
research/         analysis pipeline, paper, guide, manuscripts
  output/         figures and small result files; the full set is on Zenodo
  papers/         preliminary preprint and legacy journal drafts
tests/            regression tests for statistical helpers
```

## Citing

> Kim, K., Kim, K., & Ahn, D. (2026). *When information breaks the historical
> pattern: Preliminary evidence from a deployed Bitcoin forecaster.* Preprint.

## Licence

Code in this repository: **Apache License 2.0** (see [`LICENSE`](LICENSE)).
The licensed market data and news text consumed by the study are not covered by
that licence and are not included in the current working tree. Public catalogue
outputs retain counts and hashes rather than headline text. The existing Zenodo
version and prior Git history require a separate rights review before release.

## Disclosure

The authors operate the forecasting service audited here. The deployed model was
not changed during the study. The analysis was organized after the August 2026
case and was not preregistered. Archived score rows can be reanalysed by third
parties, but the proprietary forecasts cannot be regenerated independently.
Nothing in this repository is investment advice.
