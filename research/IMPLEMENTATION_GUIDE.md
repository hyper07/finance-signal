# From audit to architecture

## Implementing news‑aware, type‑specific forecasting in the signal model service

*Summary report for the engineering side of the study "When the News Arrives". Draft 2026‑09‑04.*

---

### 0. Executive summary

The audit showed that the deployed seven‑session forecaster (`model/forecast.py`) has no directional skill on any instrument, is well‑calibrated in width on ordinary days, and fails on the 3–5% of sessions that carry a third of all price variance — the sessions when information arrives. It fails *differently* by asset type: on crypto it fades moves that continue; on the index its "accuracy" is the market's upward drift; on single stocks the 200‑day trend filter forces "Long" on 90–93% of days and the bands cover 28% of earnings‑day outcomes. The remedy is not a better indicator vote. It is to give the model the state variables it is missing — **event calendars, information intensity, and the post‑event response by type** — as *attention layers* that decide when the price‑pattern forecast applies, when to replace it with an event‑conditional distribution, and when to say "no forecast". The out‑of‑sample test of the crudest version of this design (Section 6.5 of the paper) already restores earnings‑session coverage from 0.49 to 0.68 across 50 stocks and improves the interval score by 15%.

What this buys and what it does not: it will **not** lift directional accuracy above the coin on calm days — nothing conditioned on prices can. It **will** stop confident bands and −100% recommendations into +21% moves, make the published distribution honest on event days, and expose the one exploitable regularity (crypto continuation within one session) as a flagged regime rather than a hidden loss.

---

### 1. Design constraints established by the audit

| finding | number | design consequence |
|---|---|---|
| directional accuracy at every horizon, all 54 instruments | 46–53%, Pesaran–Timmermann never > 1.65 (pooled stocks 3.08 = +0.3 pt) | stop optimising and displaying hit rate; optimise the *distribution* (Brier, CRPS/Winkler, coverage) |
| interval coverage on calm sessions | 0.78–0.82 vs nominal 0.80 | keep the analog band as the calm‑regime component |
| coverage on earnings sessions (50 stocks) | 0.28 median; below calm coverage for 100% of stocks | earnings calendar is a required input for every stock model |
| coverage the day before a |z|≥2.5 shock | 0.00; surprise 3.6 band‑σ | need an information‑intensity gate that widens or abstains |
| post‑shock drift, crypto | +3.0% over 7 sessions; consensus aligned 6–10% before, 5–6 sessions to agree | crypto needs a post‑shock drift term, not a contrarian analog pool |
| post‑shock drift, index | −0.5 to −1.4% (reversal) | index needs a mean‑reversion component; do not apply the crypto drift |
| post‑shock drift, stocks | earnings +0.25%/event pooled (not exploitable after costs); idiosyncratic ≈ 0; market‑wide reverse | stocks need the earnings‑conditional *band*, not a drift bet |
| always‑up base rate at h=7 | beats the model on 98% of stocks | evaluate every horizon against its base rate |
| 50‑origin evaluator | SD 0.06–0.07; ≥60% on some horizon 14% of days | any displayed accuracy carries a Wilson interval and uses all origins |
| stock trend filter | Long on 90–93% of sessions (100% of 2026 rows for AAPL, NVDA) | replace with a benchmark‑relative gate; the voters are currently decorative |
| event‑conditional gate (walk‑forward) | earnings: Winkler +15.5%, coverage 0.49→0.68, 94% of stocks improve; crypto shocks: +7–17%; index calendar: −9%; stock shocks: −4% | gates are type‑specific; a shared rule is wrong for two of three types |

---

### 2. Architecture

Three model *families* — crypto, index, single stock — sharing one **information layer** and one **evaluation contract**. Everything below is a wrapper around the existing `build_forecast`; the analog forecaster becomes the calm‑regime component rather than the whole model.

```
                 ┌──────────────── information layer ───────────────┐
 prices ──►      │ calendars (earnings, FOMC, payrolls, expiries)    │
 news ───►       │ headline intensity ν_t (per-type profile)          │──► event flags e_t
 social ─►       │ social intensity ν^SNS_t (phase 3)                 │    post-shock age a_t
                 │ shock detector z_t, clustering, last surprise s_t-1│    intensity ν_t
                 └────────────────────────────────────────────────────┘
                                          │
            ┌─────────────────────────────┼──────────────────────────────┐
            ▼                             ▼                              ▼
   crypto family                   index family                  single-stock family
   analog band (calm)              analog band (calm)            pooled analogs (peers)
   + post-shock drift kernel K     + mean-reversion/vol regime   + earnings-conditional band
   + abstain when ν_t ≥ 2          + calendar-aware bands kept   + benchmark-relative gate
                                     (no widening)                (replaces 200-day filter)
            └─────────────────────────────┼──────────────────────────────┘
                                          ▼
                       predictive distribution q10/q50/q90, P(up)
                       + validity flag {forecast, widened, abstain}
                       + reason code (calendar / headline / shock)
                                          ▼
                       evaluation contract & promotion gates (validation_gates.py)
```

The **attention** vocabulary the service already uses (rotation attention, post‑split attention in `strategy.py`) generalises cleanly: each new layer is a weight $g_t\in[0,1]$ that says how much of today's forecast should come from the price‑pattern component and how much from an event‑conditional component:

$$
\hat F_t(\cdot) = (1-g_t)\,F^{\text{analog}}_t(\cdot) + g_t\,F^{\text{event}}_t(\cdot), \qquad g_t = g(e_t, \nu_t, a_t; \text{type}).
$$

In phase 1 $g_t$ is a rule (0 or 1 from the flags, exactly the gate tested in the paper); in phase 4 it is learned from the labelled event corpus.

---

### 3. State variables to add, by type

| variable | definition | source you already have | crypto | index | stock |
|---|---|---|---|---|---|
| earnings session flag | first session after the report (after‑close → next day); ±1 session window | `yfinance get_earnings_dates` (snapshot in `research/output/earnings_dates.csv`) | – | – | **required** |
| macro calendar flag | FOMC decision day; payroll release; CPI; option expiry | FOMC list in `scheduled_events.py`; BLS schedule | spillover only | **required** | secondary |
| headline intensity $\nu_t$ | (count + 1)/(trailing 30‑day median + 1), *type‑specific* headline profile (crypto words/tags; broad‑market tags + macro words; own ticker) | `data/alpaca/news.jsonl` via `event_study.news_counts`; needs a daily pull | **required** | secondary | required |
| shock flag / age | $|z_t|\ge2.5$ with $z_t=r_t/\hat\sigma_{20,t-1}$; sessions since last shock; cluster count in last 3 sessions | prices | **required** | required | required |
| last surprise $s_{t-1}$ | (realized − q50)/((q90−q10)/2.5631) of yesterday's forecast | forecast archive (`dataset_forecasts` table) | required | required | required |
| post‑shock kernel $K$ | walk‑forward quantiles of sign‑adjusted continuation after prior shocks (≥10) | `gate_experiment.post_shock_conditional` | **use** | do not use | do not use |
| event‑conditional band | walk‑forward quantiles of past same‑type event sessions (≥8) | `gate_experiment.event_conditional` | – | test only | **use** |
| benchmark‑relative gate | stock excess return vs sector ETF / SPY over 20–60 sessions | `rotation.py` sector map, SPY | – | – | replaces 200‑day filter |
| social intensity $\nu^{SNS}_t$ | post counts / engagement on X, Reddit, StockTwits for the ticker or "bitcoin" | new feed (phase 3) | high value | low | medium |

Rule of thumb from the fingerprints (paper Table 8): crypto is a near‑random walk with symmetric, clustering, continuing shocks; the index is heavy‑tailed, negatively skewed and mean‑reverting; stocks are idiosyncratic‑jump processes whose biggest moves are on the calendar.

---

### 4. The three families in detail

**4.1 Crypto (BITO/BITI, BTC).**
- Calm regime: keep the analog band. Its width is right (coverage 0.78).
- Headline gate: if $\nu_{t-1}\ge2$ → replace with the headline‑conditional distribution if ≥20 past spike days exist, else climatology (trailing 250‑window quantiles); flag `widened`.
- Shock gate: if $|z_t|\ge2.5$ → replace with the post‑shock kernel $K$ (sign‑adjusted continuation quantiles, mapped to the shock's sign); flag `post_shock`. Never emit a contrarian median in the seven sessions after a shock.
- Exposure: the −100% tactical target must be impossible on a `post_shock` or `widened` flag; cap the inverse leg at 0 for those sessions.
- Evaluation targets from the audit: shock‑session coverage 0.70 → ≥0.78; Winkler on gated sessions −7% to −17%.

**4.2 Index (SPXL/SPXS, SPY).**
- Calm regime: analog band.
- Calendar: keep the analog band on FOMC/payroll days (the event‑conditional replacement made it *worse*, −9%); instead widen by a fixed factor only if $\nu_{t-1}\ge2$ as well.
- Post‑shock: a mean‑reversion tilt (median toward −0.3 to −0.5% over 5–7 sessions after an up‑shock, symmetric after down) — estimated walk‑forward; small.
- Inverse leg: SPXS volatility drag made every forecast‑driven policy lose 8–16%/year over a decade; the exposure map must include the drag explicitly (expected decay of a 3× inverse product over the holding horizon) before any negative target is allowed.

**4.3 Single stocks (s00/s01… datasets).**
- Replace the 200‑day trend filter's veto with a *benchmark‑relative* gate: Long only while the stock's 60‑session excess return vs its sector ETF is ≥ 0 (or the sector's vs SPY); otherwise let the distribution speak. Test on the 50‑stock cross‑section before promotion; the current filter is 90–93% "Long".
- Earnings gate (the one with a significant pooled effect): on earnings sessions (and the session after) replace the band with the stock's own earnings‑conditional quantiles when ≥8 past reports exist, else the pooled cross‑sectional earnings distribution (scaled by the stock's trailing σ). Flag `earnings`.
- Do **not** apply the post‑shock kernel: stocks revert; the pooled test lost 3.8%.
- Pooled analogs: draw neighbours from the stock's peers (same sector, similar vol) as well as its own history; this multiplies the analog pool 10–20× for young or thinly traded names.
- Idiosyncratic headline spike ($\nu_{t-1}\ge2$, own ticker): widen (Brier improved significantly, intervals not) — flag `widened`, no directional change.

---

### 5. Training and data discipline

1. **Walk‑forward with purge and embargo.** Labels for horizon $h$ are unobservable until $t+h$; anything fitted at $t$ may use labels only up to $t-7$ (the seven‑session purge already used by `supervised7.py`). Event‑conditional quantiles and kernels are computed from events whose exit has occurred.
2. **Timestamps.** News counted for session $t$ must be created before that session's close (16:00 New York for equities; the crypto day is UTC). Earnings after the close belong to the *next* session. Both mistakes are look‑ahead and both inflate results.
3. **Frozen live signals.** Keep the immutable‑signal cache; the audit was only possible because of it. Store the *validity flag and reason code* with each published forecast so the next audit can score gated and ungated forecasts separately.
4. **A labelled event corpus** — the catalogue in `research/STOCK_EVENTS.md` is the seed: date, ticker, cause (earnings / market‑wide / idiosyncratic), source (executive, political, regulator, analyst, wire), channel (social vs wire), reach, sentiment. This is the training set for the learned gate in phase 4 and for kernels by source × channel.
5. **Type is a first‑class attribute.** Add `asset_type` to `Instrument` in `instruments.py` (`crypto | index | stock`) and route by it; the `"coin" in dataset` string test that produces weekend dates for BITO goes away with it.

---

### 6. The evaluation contract (must pass before anything is published)

Scored on all origins, point‑in‑time, separately for calm and event sessions, per instrument and pooled by type:

| test | pass condition | why |
|---|---|---|
| Pesaran–Timmermann vs base rate | report; no display of directional accuracy without it and a Wilson CI | accuracy alone is base‑rate inflated |
| Brier vs constant ½ | ≤ 0.25 on calm sessions; not worse than climatology on event sessions | today it is worse than a coin on 98% of stocks |
| Winkler (α=0.2) vs trailing climatology | model ≤ climatology on calm sessions; gated ≤ model on event sessions | the interval is the product |
| 10–90 coverage | 0.75–0.85 on calm **and** on event sessions | 0.28 on earnings days is the failure to fix |
| Benjamini–Hochberg over all instrument × horizon tests | headline claims survive q ≤ 0.05 | 8 instruments × 7 horizons × splits |
| turnover and inverse‑drag accounting | policy net of 5 and 25 bp per side; inverse decay modelled | the −100% target is a structural loss on 3× products |

Wire these into `validation_gates.py` next to the existing supervised7 promotion criteria; the shadow‑report pattern already there (two consecutive passing reports before promotion) is the right cadence.

---

### 7. Phased implementation in this repository

| phase | scope | code touched | acceptance (from the audit) |
|---|---|---|---|
| **0 — measure** (1 week) | compute and *store* flags only: earnings/FOMC/payroll sessions, $\nu_t$ per type, $z_t$, shock age, $s_{t-1}$; add `validity` + `reason` to the forecast payload, default `forecast` | new `model/event_layer.py`; `publisher.publish_forecast`; backend schema (+2 columns) | flags reproduce `scheduled_events.py` / `event_study.py` on the archive |
| **1 — rule gates** (1–2 weeks) | wrap `build_forecast`: `event_layer.apply(payload, flags, type)` with the paper's rules — earnings band for stocks, shock kernel for crypto, headline widening; `abstain`/`widened` flags; forbid negative targets on gated sessions | `forecast.py` (wrapper, not internals), `instruments.py` (`asset_type`), `event_layer.py` | shadow report: earnings coverage ≥ 0.65 pooled; crypto shock coverage ≥ 0.78; calm scores unchanged |
| **2 — stock engine** (2–3 weeks) | benchmark‑relative gate replacing the 200‑day veto; pooled peer analogs; earnings embargo in indicator selection | `strategy.py` (cash‑mode branch), `forecast._select_outcomes` (peer pool) | share of "Long" sessions 60–80%, not 93%; PT not worse; Brier improves on the 50‑stock cross‑section |
| **3 — crypto drift & social feed** (3–4 weeks) | kernel by source (executive/political/regulator/wire); X/Reddit/StockTwits intensity $\nu^{SNS}_t$; abstain on $\nu^{SNS}_t\ge2$ | `event_layer.py`, new `social_feed.py` | post‑shock 1‑session policy reproduces +2% net at 25 bp in shadow; no −100% target within 7 sessions of a shock |
| **4 — learned gate** (research) | logistic/GBM $g_t$ on the labelled corpus; kernels by source × channel; regime HMM | new `gate_model.py` | out‑of‑sample CRPS ≤ rule gate; passes the contract two reports running |

---

### 8. Code sketch (phase 1)

```python
# model/event_layer.py
from dataclasses import dataclass
import numpy as np, pandas as pd

@dataclass
class EventFlags:
    calendar: bool      # earnings (stock) / FOMC-payroll (index)
    headline: bool      # nu_{t-1} >= 2, type-specific headline profile
    shock: bool         # |z_t| >= 2.5
    shock_sign: int     # +1 / -1 / 0
    shock_age: int      # sessions since last shock (0 = today)

def flags_for(frame: pd.DataFrame, asset_type: str, calendars: set, news_ratio_prev: float) -> EventFlags: ...

def event_conditional(close: np.ndarray, sessions: np.ndarray, h: int, min_events: int = 8): ...   # from research/gate_experiment.py
def post_shock_kernel(close: np.ndarray, z: np.ndarray, h: int, min_events: int = 10): ...        # from research/gate_experiment.py
def climatology(close: np.ndarray, h: int, window: int = 250): ...

def apply(payload: dict, flags: EventFlags, asset_type: str, hist) -> dict:
    """Replace analog quantiles on gated sessions; set validity/reason; forbid inverse exposure when gated."""
    for row in payload["rows"]:
        h = row["horizon"]
        if asset_type == "stock" and flags.calendar:
            q = event_conditional(hist.close, hist.earnings_sessions, h) or climatology(hist.close, h)
            _replace(row, q); payload["validity"] = "widened"; payload["reason"] = "earnings"
        elif asset_type == "crypto" and flags.shock:
            q = post_shock_kernel(hist.close, hist.z, h)
            _replace(row, q, sign=flags.shock_sign); payload["validity"] = "post_shock"; payload["reason"] = "shock"
        elif flags.headline:
            _replace(row, climatology(hist.close, h)); payload["validity"] = "widened"; payload["reason"] = "headline"
        if payload.get("validity", "forecast") != "forecast":
            row["target_tactical_pct"] = max(row["target_tactical_pct"], 0.0)   # never inverse on a gated session
    return payload
```

`build_forecast` itself is untouched; `main._process` calls `event_layer.apply(...)` before `publish_forecast`. The research versions of every function above already exist and are tested against the archive in `research/gate_experiment.py`.

---

### 9. What not to do

- Do not push news counts into the nearest‑neighbour distance as an eighth feature. It dilutes the analog match on the 95% of calm days and does nothing on event days (the analogs still have no event in them). Gate; don't blend features.
- Do not train a classifier to predict the *direction* of news‑day moves from prices. Proposition 1 of the paper: on jump‑dominant days any price‑conditioned predictor's accuracy equals the news‑sign base rate.
- Do not apply the crypto shock kernel to stocks or the index (−4% and −9% in the tests), and do not apply the earnings band to the index.
- Do not publish a directional accuracy computed on 50 origins, and never one without its interval and the base rate beside it.
- Do not let two exposure mechanisms disagree in one payload (the schedule said −100% while the consensus said Hold on 2026‑08‑18). One recommendation, one reason code.

---

### 10. Expected outcomes and honest limits

- Earnings‑session coverage 0.28 → ≈0.68 across stocks; crypto shock‑session coverage 0.70 → ≈0.80; no −100% recommendations into policy shocks. These are the numbers the walk‑forward test already produced with the rule version.
- Overall interval scores improve 0–2% (event sessions are 6–20% of forecasts). Directional accuracy on calm days stays at the coin, and the product should say so — the honest metric is the calibrated band plus the validity flag.
- The one exploitable regularity is crypto continuation acted on within one session (+2.3% net per event, 64% of events, 2021–26). Present it descriptively, with dispersion (7–10% per event) and costs; it is a statistical edge over many events, not a per‑event promise, and it rests on one regime.
- Research extensions that would most change the design: a small‑cap stock sample (more drift expected), altcoins (is the kernel a class property or a Bitcoin one), and the social‑media feed — which is where the response kernel is generated in the first place.

---

### 11. The portfolio layer: a policy per type

The forecaster tells a user what the next week's distribution looks like; a *portfolio policy* tells them what to hold through it. The audit's type results imply one policy per type, and the archive lets us test the obvious candidate — 60/40 stock/bond with rebalancing (sell bonds to buy stocks after a fall, the reverse after a rise) — at 5 bp per unit turnover (`research/rebalancing.py`):

| pair, 2016–26 (BTC 2021–26) | policy | CAGR % | vol % | Sharpe | max DD % |
|---|---|---|---|---|---|
| SPY/TLT | 100% SPY | 15.16 | 17.51 | 0.896 | -33.8 |
| SPY/TLT | 60/40 drift (no rebalancing) | 11.09 | 12.39 | 0.913 | -26.4 |
| SPY/TLT | 60/40 quarterly rebalance | 9.29 | 11.13 | 0.855 | -27.7 |
| SPY/TLT | 60/40 ±5‑pt band | 9.06 | 11.3 | 0.826 | -27.6 |
| BTC/TLT | 100% BTC | 17.04 | 57.6 | 0.562 | -76.7 |
| BTC/TLT | 60/40 quarterly rebalance | 13.11 | 35.47 | 0.525 | -62.5 |
| BTC/TLT | 60/40 band + buy‑the‑dip after a crypto down‑shock | 8.82 | 36.11 | 0.415 | -64.3 |

Reading, by type:

- **Index → constant‑mix rebalancing (quarterly or a ±5‑point band), the honest version.** Why the index is the stable long‑horizon holding at all: it averages five hundred idiosyncratic earnings streams — exactly the unforecastable risk of Section 1 — leaving macro news that is scheduled and pre‑positioned, shocks that revert, and the equity premium. Rebalancing is a contrarian (concave) policy (Perold & Sharpe 1988) that harvests that reversal: in 2016–26 it cut volatility by a third and the drawdown from −34% to −27%. It did **not** add return in this decade — bonds lost money and fell with stocks in 2022 — so present it as risk control with a small, regime‑dependent rebalancing bonus, not as a return enhancer. The band rule reached the same risk reduction with 9 trades in ten years; a shock‑triggered tilt added 470 trades and nothing.
- **Crypto → rebalance slowly, never contrarian inside the first week after a shock.** Quarterly 60/40 BTC/TLT earned more than a drifting 60/40 (the rebalancing bonus is large when one asset has 58% volatility) at a far lower drawdown than 100% BTC, but buying the dip in the week after a crypto down‑shock lost — the continuation of Section 6.1 again. Cadence: monthly or quarterly bands; no event‑triggered buys.
- **Single stocks → diversify; the model cannot save a concentrated book.** The risk the forecaster fails on (earnings jumps, company news) is the risk diversification removes for free. The product's stock signals should be framed as tilts inside a diversified core, and the earnings gate of Section 4.3 should also cap position size into an earnings session.

Implementation: a `portfolio_policy` per `asset_type` in `instruments.py` (`constant_mix_band` for index, `slow_rebalance` for crypto, `diversified_core_tilt` for stocks) with the cadence and band as parameters, evaluated with the same contract as the forecasts (CAGR, vol, Sharpe, max DD, turnover, net of 5 and 25 bp) and shown to the user next to the forecast's validity flag.
