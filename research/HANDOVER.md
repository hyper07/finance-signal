# Handover — state of the research as of 2026-09-06

This file is the working context for the study. It exists so that a new session (or a
new collaborator) can continue without re-deriving anything. Read it first, then
`PAPER.md`.

---

## 1. What this project is

An audit of a **deployed** retail forecasting product: a seven-session
historical-analog forecaster that has published immutable daily signals on
signal.dotori.ai since 2026-01-02. The audit regenerates every point-in-time forecast
the production code could have issued and scores it — about 1.49 million
forecast–horizon pairs across three asset types (crypto, the S&P 500 pair, 50 single
stocks).

**Central result.** The model is interval-calibrated but directionally uninformative,
and both properties fail around exogenous news. The band's coverage is matched by a
naive volatility formula, so the area carries no information beyond recent
volatility; the median and direction inside it are what fail.

**Paper title (final).** *When the News Arrives: Calibration Failure of a Deployed
Price-Pattern Forecaster Around Information Shocks in Crypto, Index and Single-Stock
Markets.* One paper, not split — this was decided after weighing a two-paper split.

---

## 2. Where everything is

| What | Where |
|---|---|
| The paper (source of truth) | `research/PAPER.md` |
| Journal copies | `research/papers/{ijf_full,frl_short,jbef_behavioral,frontiers_perspective}/paper.md` |
| Generated LaTeX | `research/paper.tex` (gitignored; rebuild with `to_latex.py`) |
| arXiv package | `research/arxiv/` (gitignored) — `paper.tex`, 20 PNGs, `abstract.txt`, `ARXIV_SUBMISSION.md` |
| Overleaf package | `research/overleaf_project.zip` — upload as a new project, compiler pdfLaTeX |
| Reports | `research/BTC_DECLINES.md`, `SWING_LEGS.md`, `STOCK_EVENTS.md`, `IMPLEMENTATION_GUIDE.md` |
| Derived data | `research/output/` (604 MB; the large per-instrument CSVs are gitignored, they live on Zenodo) |
| Licensed raw inputs | `data/alpaca/` — 20 MB, gitignored, **never commit** |
| Data deposit | Zenodo [10.5281/zenodo.22308637](https://doi.org/10.5281/zenodo.22308637), CC BY 4.0 |

### What was copied, and what was deliberately left behind

The private `signal` repository is 5.6 GB. Only 625 MB of it is this study; the rest
belongs to other work. Verified on 2026-09-06 by running all 17 analysis scripts here
— every one passes.

| Copied here | Size | Why |
|---|---|---|
| `research/output/` | 605 MB | every derived frame, including the cached `detailed_*.pkl` engine frames, so all downstream analysis reruns without the engine |
| `data/alpaca/` daily bars, news, sector and theme series | 20 MB | the only raw inputs the research code opens |

| Left behind | Size | Why |
|---|---|---|
| `alpha-agent/data/` | 2.1 GB | a different project (`allstocks_daily.csv` alone is 1.2 GB); nothing in this study reads it |
| `data/alpaca/optbars_*.csv`, `contracts_*.csv`, `underlying_minute.csv` | 476 MB | options and minute bars, used by the options-backtest strand, not by this paper |
| `model/validation_output/` | 689 MB | supervised7 training checkpoints belonging to the engine |
| `backups/` | 170 MB | database dumps |

If the rotation feature is ever restored to full production fidelity (Limitation 1 —
offline reproduction sets it neutral, giving 76% unfrozen signal agreement), the
sector and theme series it needs are already here.

**The forecasting engine is not in this repository.** `model/` holds an interface
specification and stubs that raise `NotImplementedError`. Anything that *regenerates*
forecasts (`reproduce.py`, `event_study.py`, `universe_run.py`) needs the private
`signal` repository. Everything *downstream* of the forecasts runs here from
`research/output/` — that is where all recent work has happened.

---

## 3. How to run

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r research/requirements.txt
cd research && ../.venv/bin/python band_ribbon.py      # smoke test, ~10 s
```

To rebuild the paper end to end (integrates any new sections, regenerates LaTeX, runs
the markup checks, compiles, refreshes the arXiv and Overleaf packages, commits):

```bash
zsh research/finish_update.sh      # must be run from the repository root
```

Compiling needs `tectonic` at `/tmp/tectonic` (or edit the script). The script strips
the `\pdfoutput=1` line before compiling because tectonic is XeTeX and rejects it;
arXiv needs that line, so it stays in the shipped file.

---

## 4. Scripts, and what each produces

**Core pipeline** (needs the private engine): `reproduce.py` → `event_study.py` →
`robustness.py`, `news_events.py`, `effectiveness_tests.py`, `universe_run.py`,
`universe_aggregate.py`.

**Analysis, all runnable here:**

| Script | Produces |
|---|---|
| `asset_types.py` | asset-type fingerprints, Figures 9–10 |
| `scheduled_events.py` | FOMC / payroll / earnings calendar test, Table 12 |
| `stock_event_catalogue.py` | 346 single-stock increases with news attribution → `STOCK_EVENTS.md`, Tables 14–15 |
| `predictability_gap.py` | variance share of shock sessions, accuracy ceilings, Table 16 |
| `gate_experiment.py` | causal event-conditional gate, Table 18 (`--universe` for the 50-stock pool) |
| `entry_delay.py`, `entry_rule_backtest.py` | when to act after a shock, Tables 19–20 |
| `action_policies.py` | act daily / weekly / once, Table 11, Figure 11 |
| `rebalancing.py` | 60/40 policies, Appendix E, Figure 14 |
| `multiplicity.py` | Benjamini–Hochberg control over all 228 tests, Table 13 |
| `band_ribbon.py` | model band vs naive volatility band, Table 22, Figure 19 |
| `btc_decline_catalogue.py` | 43 Bitcoin down-shocks with attribution → `BTC_DECLINES.md`, Tables 23–24 |
| `btc_decline_fans.py` | day-before forecast vs realized path, twelve declines, Figure 15 |
| `btc_prolonged_declines.py` | decline legs, quarters, half-years, trend yardstick, Tables 25–26, Figure 16 |
| `swing_legs.py` | swing legs across all asset types → `SWING_LEGS.md`, Tables 27–28, Figures 17–18 |

**Build and quality:** `to_latex.py` (Markdown → LaTeX), `papers/build_companions.py`,
`check_markup.py` (run before every build), `merge_grammarly.py` (see §6),
`integrate_findings.py` (one-shot, idempotent — already applied),
`finish_update.sh` (the whole build).

Hand-written attribution files, edited by a person, not generated:
`manual_attributions.json` (stocks), `btc_manual_attributions.json` (Bitcoin
down-shocks), `btc_decline_regimes.json` and `swing_leg_regimes.json` (leg
narratives). Each carries a confidence flag.

---

## 5. Findings a new session should not re-derive

- **Unconditional.** Directional accuracy 46–53% at every horizon on every
  instrument; no horizon passes Pesaran–Timmermann. Brier is worse than a constant ½
  for 98% of stocks. At seven sessions "always up" beats the model on all eight core
  instruments.
- **The band.** Coverage 0.78–0.79 against nominal 0.80, matched by
  ±1.28·σ₂₀·√h with a *better* Winkler score. Misses cluster: 63% of seven-session
  misses fall in shock windows that are 28% of sessions.
- **Around news.** Day before a shock: 37% next-session accuracy, 0% coverage, mean
  surprise 3.6 band-σ. Headline-spike days: 39% accuracy (BTC). Earnings sessions:
  the nominal-80% band covers 25–28%.
- **After news, by type.** Crypto continues (+2.98% over seven sessions, t=3.06);
  the index reverts; single stocks split by cause (earnings drift +2.3% for the four
  mega-caps, but only +0.25% per event across 50 stocks and negative after 25 bp costs).
- **Acting late.** Pays only in Bitcoin and only within one session (+2.3% net at 5 bp).
- **Horizon (added last).** Losses live in legs of one to four months, not in
  sessions. Only about half of a Bitcoin down leg's fall lands on shock sessions
  (a third or less for index, stock and bond legs). The model's P(up) is the same
  inside bear legs as inside bull legs on *every* asset type, so holding its own
  exposure captured 66–79% of every down leg's loss. A 100-day trend filter would
  have cut the Bitcoin drawdown from −72% to −38% — in-sample, no costs, a yardstick
  for the missing regime state, not a strategy.
- **Constructive.** A causal, walk-forward event-conditional gate restores
  earnings-session coverage from 0.49 to 0.68 across 50 stocks (interval score +15.5%)
  — and the same rule *hurts* the other asset types.

---

## 6. Conventions and traps (learned the hard way)

- **Grammarly round-trip.** The user proofreads by pasting `PAPER.md` into Grammarly
  and saving the export as `research/Grammer_PAPER.md`. That export is flat: no
  headings, tables become tab text, backticks and `$` are stripped, paragraphs
  interleave. **Never overwrite `PAPER.md` with it.** Run
  `merge_grammarly.py <out>` from `research/`, which takes Grammarly's wording
  sentence by sentence only where formulas, code and emphasis can be restored
  verbatim, and asserts "math preserved: True". It also refuses sentences where a
  technical term was renamed (Grammarly turned "origins" into "sources").
- **Currency dollars.** `$19bn` in a table cell is read by pandoc as a math
  delimiter and silently swallows the rest of the table. Write `\$19bn`.
  `check_markup.py` now fails the build on an odd number of unescaped `$` on any
  line, table rows included.
- **Mid-word insertions.** The merge can leave `in$t$ervals`, `stat*is*tic`.
  `check_markup.py` catches these too. All known instances were fixed on 2026-09-06.
- **Table sizing.** `to_latex.py` sizes every table itself: `column_needs` computes
  minimum and natural widths, `layout` picks small/footnotesize/scriptsize and then a
  landscape page, and the widths are written into the pipe-table separator dash counts
  (pandoc reads relative widths from them). Landscape is emitted as raw `\landscape` …
  `\endlandscape`; `\begin{landscape}` would make pandoc swallow the table as raw TeX.
- **Figure placement.** Figures are anchored `[H]` (package `float`) in `polish()`.
  Without it, twenty floats drift past the references.
- **Never** `s.index("SPLIT = re.compile")` when patching `to_latex.py` — it matches
  inside `MATH_SPLIT` and once wiped the file.
- **Table and figure numbers are stable identifiers**, deliberately not in order of
  appearance. Do not renumber them.

---

## 7. Open items

- **Push this repository.** Several commits are local only: `git push -u origin main`.
- **Zenodo record still shows the old title** — edit the metadata (a metadata edit
  does not create a new version). Also add the arXiv ID under *Related works* once
  it exists.
- **arXiv submission `submit/8038835`** was opened and expires 2026-09-18. Upload
  `research/arxiv/` or the tarball; metadata to paste is in
  `research/arxiv/ARXIV_SUBMISSION.md`. Read the conflict-of-interest paragraph once
  more before submitting — arXiv is permanent and the paper audits a service the
  authors operate.
- **Companions are one revision behind the main paper.** The three short manuscripts
  do not yet carry the horizon results of §6.6–6.7.
- **Figures 15–19 and the leg analysis are not in the Zenodo deposit** (added after
  version 1). Either deposit a version 2 or leave them repository-only; Appendix C
  says which files are affected.
- **The web summary page** still shows pre-Grammarly prose and the old title.
- Data files added after the deposit: `band_vs_naive.json`,
  `btc_declines_*.{csv,json}`, `btc_decline_legs.*`, `btc_decline_calendar.csv`,
  `btc_trend_filter_benchmark.json`, `swing_legs*.{csv,json}`.

---

## 8. Constraints that must not be relaxed

1. **The engine stays private.** Only the interface spec (`model/INTERFACE.md`) and
   stubs are published.
2. **Licensed data is never redistributed.** Alpaca price bars, Benzinga news text
   and Yahoo snapshots stay untracked; the deposit carries SHA-256 hashes and the
   retrieval commands instead. `.gitignore` enforces this — check `git status` before
   every commit.
3. **Disclosure stays in the paper.** The authors operate the audited service; all
   rules were fixed before scoring and the deployed model was not changed during the
   study.
