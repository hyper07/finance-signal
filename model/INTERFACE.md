# The model boundary

This repository contains the **audit** of a deployed forecasting service, not the
service's forecasting engine. The proprietary engine (`strategy.py`,
`forecast.py`, and the supporting modules in the private repository) is **not
published**. What *is* published is the exact interface the audit uses, so that

1. a reader can see precisely what the audited engine is required to produce, and
2. **anyone can re-run the entire study on their own forecaster** by supplying two
   functions with the signatures below.

That second point is the scientifically useful one: the audit protocol is
model-agnostic. Drop in any point-in-time forecaster that emits a seven-horizon
predictive distribution and every script in `research/` works unchanged.

The two stub modules in this folder raise `NotImplementedError` with a pointer to
this file, so the failure is legible rather than an obscure `ImportError`.

---

## 1. `strategy.run_simulation`

Used by `research/common.py::reproduce_detailed_frame` to rebuild the engine's
per-session state from prices.

```python
def run_simulation(
    df_input: pd.DataFrame,          # date, high, low, close, stock_split[, close_short]
    cache_csv: str,                  # frozen published signals (see below)
    short_mode: str,                 # "cash" | "inverse_etf"
    rotation_series: pd.Series | None = None,
    live_signal_start: str | None = None,   # signals on/after this date are frozen
    industry_signals: pd.DataFrame | None = None,
    stock_benchmark_gate: bool = False,
    dataset: str | None = None,
    supervised7_enabled: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (yearly_stats, detailed_frame, feature_ranks, selection_log)."""
```

Only the **second** element is used by the audit. It must be indexed by trading
date and contain at least:

| column | meaning |
|---|---|
| `close` | split/dividend-adjusted close |
| `strategy_signal` | the executed position, −1 / 0 / +1 |
| `rotation_score` | sector-rotation attention score (0.0 is acceptable) |
| `daily_ret` | `close.pct_change()` |
| `daily_ret_short` | return of the short leg (`0.0` in cash mode) |

**Frozen signals.** If `cache_csv` exists, rows dated on/after
`live_signal_start` must be taken from it verbatim rather than recomputed. This
is what makes the audit an audit: the 2026 signals scored in the paper are the
ones that were published live, not a later recomputation. The file is a CSV with
`Date(T),Prediction,Actual_Ret,Strategy_Ret` and predictions such as
`📈 Long` / `➖ Hold` / `📉 Short`; `research/common.py::write_signal_cache`
generates it from the service's public API.

## 2. `forecast.build_forecast`

Used by `research/event_study.py` at every origin. **The no-look-ahead guarantee
lives here:** the function must use only rows dated on or before `as_of_date`.

```python
def build_forecast(
    detailed_df: pd.DataFrame,       # the frame above
    dataset: str,
    symbol: str,
    short_mode: str,                 # "cash" | "inverse_etf"
    as_of_date: str | pd.Timestamp | None = None,
) -> dict:
```

Required payload:

```python
{
  "dataset": str, "as_of_date": "YYYY-MM-DD", "forecast_version": str,
  "source_close": float, "short_mode": "cash" | "inverse",
  "current_prediction": "Long" | "Hold" | "Short",
  "trailing_volatility": float,                    # annualised ratio
  "consensus": {
      "direction": "Buy" | "Sell" | "Hold", "status": "confirmed" | "warning" | "none",
      "directional_vote_count": int, "vote_counts": {"Buy": int, "Sell": int, "Hold": int},
      "action_fraction_pct": float,
      "target_tactical_pct": float, "current_tactical_pct": float,
  },
  "rows": [                                        # exactly 7, horizons 1..7
    {"horizon": int, "date": "YYYY-MM-DD",
     "p10_return_pct": float, "p50_return_pct": float, "p90_return_pct": float,
     "prob_up": float,                             # P(cumulative return > 0)
     "session_p50_return_pct": float, "session_prob_up": float,
     "price_low": float, "price_mid": float, "price_high": float,
     "target_tactical_pct": float,                 # exposure schedule, −100..100
     "consensus_vote": "Buy" | "Sell" | "Hold"},
  ],
  "validation": {"method": str, "fallback_horizons": list[int],
                 "sample_count_by_horizon": {"1": int, ...}},
}
```

Quantiles are percentages of the cumulative return from `source_close` over
`horizon` sessions and must satisfy `p10 ≤ p50 ≤ p90`.

---

## Substituting your own forecaster

```python
# model/forecast.py
def build_forecast(detailed_df, dataset, symbol, short_mode, as_of_date=None):
    frame = detailed_df.loc[:pd.Timestamp(as_of_date)]      # never look ahead
    ...                                                      # your model here
    return payload                                           # schema above
```

Then run the pipeline in `research/README.md`. Every score in the paper — the
Pesaran–Timmermann tests, the interval coverage, the event studies, the gate
experiment — is computed from these payloads and is therefore directly
comparable across forecasters.

## Verifying the published results without any engine

The audited engine's own outputs are deposited at Zenodo
([10.5281/zenodo.22308637](https://doi.org/10.5281/zenodo.22308637)). Unzip
`derived_outputs.zip` into `research/output/` and every analysis script
downstream of the forecasts runs unchanged (steps 3 onward in
`research/README.md`), reproducing every table and figure in the paper.
