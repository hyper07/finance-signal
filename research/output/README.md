# Results

This folder holds the **small** artifacts: all figures, the per-instrument
`summary_*.json`, the aggregate result files (multiplicity, effectiveness, gate
experiment, cross-section, predictability gap, rebalancing, entry-rule backtest,
scheduled events) and a few small CSV tables.

`arxiv_prefinding.json` is the rights-safe aggregate for the narrow preliminary
paper. Its two figures are `fig_prefinding_conditionals.{pdf,png}` and
`fig_prefinding_august_case.{pdf,png}`.

`frl_robustness.json` contains the FRL block-length, large-move-threshold, and
headline-ratio-threshold checks. The combined journal figure is
`figures/fig_frl_combined.{pdf,png}`.

The existing Zenodo v1 record,
<https://doi.org/10.5281/zenodo.22308637>, predates the preliminary-paper
aggregate and must be reviewed before it is cited as the release artifact.
Licensed inputs (Alpaca bars, Benzinga news text, Yahoo snapshots) are not in
the current working tree; see `../DATA_DEPOSIT.md`. Forecast-score rows support
downstream reanalysis, but the proprietary forecast engine cannot be regenerated
from this repository.
