# research/ — news-shock event study of the seven-session forecast

Offline, partially reproducible evaluation of a deployed analog
forecaster around information-intensive and large-return observations (e.g. the 2026-08-19 White House crypto
summit), across three asset types — coin (BITO/BITI, BTC), index (SPXL/SPXS,
SPY) and single stocks (AAPL, MSFT, TSLA, NVDA) — plus a simulation of acting on
the seven-session schedule daily, weekly or once. Nothing here touches the
running service. The proprietary production modules are not included.

Preliminary paper: [papers/arxiv_prefinding/paper.md](papers/arxiv_prefinding/paper.md).
The broader [PAPER.md](PAPER.md) and legacy companion manuscripts are not
submission-ready. Engineering summary: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md).
Figures: `output/figures/`. Data manifest: [DATA_DEPOSIT.md](DATA_DEPOSIT.md).

## Run

> **Model boundary.** Steps 1–2 call the proprietary forecasting engine, which is
> not published in this repository (see [`../model/INTERFACE.md`](../model/INTERFACE.md)).
> Archived forecast-score rows permit downstream reanalysis, but the proprietary
> forecasts cannot be independently regenerated. The existing Zenodo v1 deposit
> predates the narrow preliminary-paper artifact and requires a rights review.
> To audit *your own* forecaster, implement the two functions in `model/`.


```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r research/requirements-publish.txt

MPLCONFIGDIR=/tmp/mplconfig .venv/bin/python research/arxiv_prefinding.py
.venv/bin/python research/build_arxiv_prefinding.py

.venv/bin/python research/reproduce.py      # 1. rebuild detailed frames for all 8 instruments, fidelity checks (~2.5 min)
.venv/bin/python research/event_study.py    # 2. rolling-origin forecasts + scoring + shock events (~3 min; accepts keys)
.venv/bin/python research/robustness.py     # 3. 50-origin sampling illusion, 3-day signal, z sensitivity
.venv/bin/python research/news_events.py    # 4. headline-defined events, dashboard-as-displayed replay
.venv/bin/python research/effectiveness_tests.py  # 5. Pesaran-Timmermann, HAC Brier vs coin, log Bayes factor, Kelly
.venv/bin/python research/asset_types.py    # 6. asset-type fingerprints (11 instruments) -> fig9, fig10
.venv/bin/python research/action_policies.py # 7. act daily / weekly / once simulation -> fig11
.venv/bin/python research/scheduled_events.py # 8. FOMC / payrolls / earnings-calendar test (Table 10)
.venv/bin/python research/stock_event_catalogue.py # 9. single-stock increase catalogue with news attribution -> STOCK_EVENTS.md
.venv/bin/python research/predictability_gap.py # 10. variance share of shock sessions and accuracy ceilings (Table 14)
.venv/bin/python research/universe_run.py   # 11. 46 further S&P stocks: reproduce + rolling-origin study (6 workers, ~10 min)
.venv/bin/python research/universe_aggregate.py # 12. 50-stock cross-section -> universe_cross_section.{csv,json}, fig12
.venv/bin/python research/gate_experiment.py # 13. exploratory event-conditional gate, 8 instruments -> gate_experiment.json
.venv/bin/python research/gate_experiment.py --universe # 14. pooled gate over 50 stocks -> gate_experiment_universe.json
.venv/bin/python research/gate_figure.py    # 15. fig13
.venv/bin/python research/entry_delay.py    # 15b. in-sample entry-delay table (Table 19)
.venv/bin/python research/entry_rule_backtest.py # 15c. walk-forward, cost-adjusted entry rule (Table 20)
.venv/bin/python research/rebalancing.py    # 15d. 60/40 policies SPY/TLT, BTC/TLT (Table 21, fig14)
.venv/bin/python research/multiplicity.py   # 16. Benjamini-Hochberg FDR for selected predefined families
.venv/bin/python research/figures.py        # 17. fig1..fig8
.venv/bin/python research/deposit_manifest.py # 18. DATA_DEPOSIT.md (sizes + SHA-256 of inputs/outputs)
.venv/bin/python research/to_latex.py       # 19. PAPER.md -> paper.tex; papers/build_companions.py for the three companions (pandoc via pypandoc_binary)
```

Dataset keys: `bito btc spxl spy aapl msft tsla nvda` (+ `bito_unfrozen spxl_unfrozen`; universe keys are lower-case tickers). Total wall time about 25 minutes including the universe. Seeds are fixed; outputs are deterministic
given the inputs below.

## Inputs

The licensed raw inputs below are **not** redistributed. The manifest records
their SHA-256 hashes and provenance, but the public repository does not currently
contain a complete retrieval utility. `output/` holds figures, summaries, and
small result tables.


- `data/alpaca/underlying_daily.csv` — adjusted daily bars (BITO, BITI, …), SIP feed.
  Two prints per (symbol, day) exist (IEX + SIP); `common.py` keeps the higher-volume row.
- `data/alpaca/crypto_daily.csv` — BTC/USD daily bars (two pulls per day; later pull kept).
- `data/alpaca/news.jsonl` — Benzinga items 2024-02 → 2026-08 (crypto-tagged subset used).
- `output/public_<dataset>.json` — snapshots of the public datasets (b01, b04,
  s01–s04) taken 2026-09-03; the live signals are frozen from them (ETF/coin from
  2026-01-01, stocks from 2026-07-30). Delete to refresh (requires network).
- `output/stocks_yf_snapshot.csv` — Yahoo adjusted daily history with splits for
  AAPL/MSFT/TSLA/NVDA (2010 →), saved 2026-09-03 so the stock runs stay offline.
- `output/spy_yf_snapshot.csv`, `output/qqq_yf_snapshot.csv` — SPY/QQQ 2009 → for the market-wide flag.
- `output/earnings_dates.csv` — quarterly report timestamps for the four stocks
  (Yahoo, 2002 →), saved 2026-09-03. FOMC decision days are hard-coded in
  `scheduled_events.py` (2016 → 2026-07); payroll days follow the first-Friday rule.

## Modules

| file | role |
|---|---|
| `common.py` | data loading, dedupe, production-shaped OHLC, published-signal cache, `run_simulation` wrapper |
| `reproduce.py` | builds `detailed_*.pkl`; writes `reproduction_fidelity.json` |
| `event_study.py` | exhaustive point-in-time `build_forecast` calls, scoring, z-shock events, August case |
| `robustness.py` | resampled 50-origin evaluator, published 3-day signal hit rate, z-threshold sensitivity |
| `news_events.py` | headline-spike (return-independent) event test; what the dashboard evaluator would have shown each day of 2026 |
| `effectiveness_tests.py` | formal effectiveness-in-series tests per horizon and regime → `effectiveness.json` |
| `asset_types.py` | return-process fingerprints + forecaster metrics by instrument/type → `asset_types.{csv,json}`, fig9–10 |
| `action_policies.py` | hold / act daily / act weekly / act once / 3-day signal, 5 bp turnover cost → `action_policies.json`, `policy_nav_*.csv`, fig11 |
| `scheduled_events.py` | calendar-timed events (FOMC, approximate payroll dates, earnings) vs the day-before forecast → `scheduled_events.json` |
| `stock_event_catalogue.py` | classifies stock shocks and retains licensed-archive counts/hashes rather than headline text → `STOCK_EVENTS.md`, `stock_events_catalogue.csv` |
| `predictability_gap.py` | share of sessions/variance on shock days, calm vs shock accuracy, ceilings at 60/70% calm skill → `predictability_gap.{csv,json}` |
| `universe_run.py` / `universe_aggregate.py` | 46 further S&P stocks (yfinance snapshot `universe_yf_snapshot.csv`, published s00 signals) and the 50-stock cross-section |
| `gate_experiment.py` / `gate_figure.py` | exploratory gates (calendar / headline / shock) with walk-forward event-conditional replacement; Winkler, coverage, Brier; pooled over the universe |
| `entry_delay.py` / `entry_rule_backtest.py` | act k sessions after a shock: in-sample entry-delay returns, and a walk-forward rule (side from prior events, 5/25 bp per side) by instrument and by stock-shock cause |
| `rebalancing.py` | 60/40 stock/bond policies (drift, monthly, quarterly, ±5-pt band, shock tilt) at 5 bp; SPY/TLT vs BTC/TLT → `rebalancing.json`, fig14 |
| `multiplicity.py` | BH false-discovery control within and across test families → `multiplicity.{csv,json}` |
| `deposit_manifest.py` | writes `DATA_DEPOSIT.md` with sizes and SHA-256 for a Zenodo-style deposit |
| `to_latex.py` | converts `PAPER.md` to `paper.tex` with the bundled pandoc |
| `figures.py` | all figures |

## Caveats worth remembering

- Offline reproduction sets the sector-rotation feature to neutral (no sector ETF archive)
  and uses Alpaca instead of Yahoo prices: the *unfrozen* engine agrees with the published
  2026 signals on 76% of days. The study uses the *frozen* frame, so 2026 signals are exact.
- The cash-mode 200-day trend filter forces Long on 90–93% of stock sessions (100% of
  published 2026 rows for AAPL and NVDA): stock "predictions" are mostly the trend flag.
- Zero interval coverage on |z| ≥ 2.5 days at h=1 is nearly tautological.
  Headline-count spikes avoid return-defined selection but target-day counts can
  respond to the price move, so their association is not causal.
