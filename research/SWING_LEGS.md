# Swing legs across asset types: Bitcoin, the index, Treasuries and four stocks

The same weeks-to-months lens applied to Bitcoin's declines is applied here to both directions and to every asset type the engine runs on, plus long Treasuries (TLT), on which it does not. A zig-zag with a volatility-scaled reversal threshold (a quarter of annualized volatility, floored at 5% and capped at 15%) segments each adjusted-close series into swings; a leg counts when the move exceeds 4/3 of that threshold. For each leg we record its depth and length, the share of the log move that came on shock sessions ($|z|\ge2.5$ in the leg's direction), the S&P 500 over the same window, the model's state across the leg where it exists, headline themes from the Benzinga archive (2024-02 onward) and a hand-written regime narrative for the largest legs with a confidence flag. Scripts: `swing_legs.py` (this report), `btc_prolonged_declines.py` (Bitcoin declines in detail, in `BTC_DECLINES.md`).

![Swing legs by asset](output/figures/fig17_swing_legs_by_asset.png)

![Leg anatomy: shock share and model capture](output/figures/fig18_leg_anatomy.png)

## The pattern, asset by asset

| asset | reversal / min leg | legs (down / up) | shock share of down legs (median) | shock share of up legs | P(up) 7s in down legs | P(up) 7s in up legs | loss captured in down legs |
|---|---|---|---|---|---|---|---|
| BTC/USD | 14% / 19% | 16 / 23 | 0.51 | 0.36 | 0.52 | 0.48 | 0.69 |
| S&P 500 (SPY) | 5% / 7% | 23 / 26 | 0.36 | 0.00 | 0.63 | 0.63 | 0.68 |
| 20y+ Treasuries (TLT) | 5% / 7% | 20 / 16 | 0.23 | 0.18 | no engine | — | — |
| Apple | 7% / 9% | 53 / 56 | 0.33 | 0.23 | 0.57 | 0.58 | 0.74 |
| Microsoft | 6% / 9% | 52 / 52 | 0.28 | 0.28 | 0.57 | 0.55 | 0.66 |
| Tesla | 14% / 19% | 45 / 53 | 0.33 | 0.25 | 0.53 | 0.53 | 0.79 |
| Nvidia | 11% / 15% | 42 / 51 | 0.06 | 0.18 | 0.55 | 0.57 | 0.73 |

Three regularities hold across types. First, most of a prolonged move is the grind, not the jumps: shock sessions carry about half of a Bitcoin down leg but a third or less of an index, stock or bond leg, and even less of up legs. Second, the model cannot tell a bear leg from a bull leg: its mean seven-session P(up) is the same inside down legs as inside up legs for every asset (0.52 vs 0.48 for Bitcoin, 0.63 vs 0.63 for the index, 0.53–0.58 either way for the stocks), so holding its exposure captures two-thirds to four-fifths of every down leg's loss. Third, up legs are where the base rate lives: the model's exposure captured most of each rally as well, which is the always-up result of the paper seen at the leg scale.

## Largest legs and what drove them

### BTC/USD

| leg | days | move | shock sessions (share) | SPY | P(up) 7s | signal Long | model capture | what drove it |
|---|---|---|---|---|---|---|---|---|
| 2022-03-29 → 2022-06-18 (down) | 81 | -60.1% | 5 (53%) | -20.4% | 0.50 | 0.49 | -40.8% | Tightening cycle (50 bp May, 75 bp June; CPI 8%+) with Terra, Celsius and Three Arrows failing inside it (high) |
| 2021-11-08 → 2022-01-22 (down) | 75 | -48.1% | 2 (31%) | -6.3% | 0.55 | 0.74 | -36.7% | Fed pivot to tightening (taper doubled, QT signalled), Omicron, Kazakhstan hash-rate hit, Russia ban proposal (high) |
| 2021-05-08 → 2021-06-08 (down) | 31 | -43.3% | 2 (51%) | +0.0% | 0.61 | 0.59 | -30.2% | Tesla stopped Bitcoin payments; China banned institutional services and mining (high) |
| 2026-01-14 → 2026-02-05 (down) | 22 | -35.3% | 4 (73%) | -1.8% | 0.51 | 0.35 | -20.4% | Greenland tariff scare (20 Jan), Fed pause (28-29 Jan), cross-asset deleveraging with the software and metals rout (5 Feb) — archive headlines (medium) |
| 2025-10-06 → 2025-11-22 (down) | 47 | -32.1% | 2 (32%) | -1.9% | 0.61 | 0.79 | -22.4% | 10 Oct tariff shock and record $19bn liquidation; ETF outflows and the break below $100k (4 Nov) — archive headlines (medium) |
| 2024-09-06 → 2024-12-17 (up) | 102 | +96.7% | 3 (35%) | +12.2% | 0.52 | 0.89 | +69.9% | Fed cutting cycle began (18 Sep); Trump's election win (5 Nov) priced as pro-crypto; $100k reached 5 Dec (high) |
| 2023-09-11 → 2024-01-08 (up) | 119 | +86.8% | 5 (50%) | +6.6% | 0.43 | 0.85 | +55.3% | Spot-ETF anticipation after Grayscale's court win (29 Aug) through approval on 10 Jan 2024 (high) |
| 2024-01-22 → 2024-03-13 (up) | 51 | +85.1% | 3 (36%) | +6.7% | 0.51 | 1.00 | +80.6% | Spot-ETF inflows after launch drove a new all-time high in March ahead of the halving (high) |

### S&P 500 (SPY)

| leg | days | move | shock sessions (share) | SPY | P(up) 7s | signal Long | model capture | what drove it |
|---|---|---|---|---|---|---|---|---|
| 2025-02-19 → 2025-04-08 (down) | 48 | -18.8% | 4 (75%) | -18.8% | 0.63 | 0.89 | -11.1% | Tariff escalation from February to 'Liberation Day' (2 Apr) and the China retaliation (high) |
| 2020-03-04 → 2020-03-12 (down) | 8 | -18.5% | 1 (36%) | -18.5% | 0.57 | 0.57 | -10.7% | COVID crash (this leg is the 4-12 March segment of it) (high) |
| 2018-12-03 → 2018-12-24 (down) | 21 | -15.6% | 1 (19%) | -15.6% | 0.67 | 1.00 | -11.4% | December 2018 Fed hike into a slowdown, trade war, government shutdown (high) |
| 2022-03-29 → 2022-05-19 (down) | 51 | -15.6% | 2 (39%) | -15.6% | 0.63 | 0.95 | -13.7% | 50 bp hike, 8%+ CPI, growth scare; Nasdaq bear market (high) |
| 2022-09-12 → 2022-09-30 (down) | 18 | -12.7% | 1 (33%) | -12.7% | 0.61 | 0.93 | -6.4% | Hot August CPI (13 Sep), 75 bp hike (21 Sep), UK gilt crisis (high) |
| 2016-06-27 → 2018-01-26 (up) | 578 | +48.0% | 9 (27%) | +48.0% | 0.59 | 0.94 | +38.4% | Post-Brexit recovery into the 2017 earnings and tax-cut melt-up (high) |
| 2020-10-30 → 2021-09-02 (up) | 307 | +40.2% | 1 (4%) | +40.2% | 0.66 | 1.00 | +40.2% | Vaccines, reopening and fiscal stimulus (high) |
| 2025-04-21 → 2025-10-29 (up) | 191 | +34.5% | 2 (16%) | +34.5% | 0.61 | 0.96 | +29.3% | Tariff pause (9 Apr) and the AI-capex earnings rebound (high) |

### 20y+ Treasuries (TLT)

| leg | days | move | shock sessions (share) | SPY | P(up) 7s | signal Long | model capture | what drove it |
|---|---|---|---|---|---|---|---|---|
| 2021-12-03 → 2022-06-14 (down) | 193 | -28.9% | 4 (36%) | -17.0% |  |  |  | Fed pivot to hikes with CPI above 8%; the 75 bp June hike (high) |
| 2022-08-01 → 2022-10-24 (down) | 84 | -22.7% | 0 (-0%) | -7.4% |  |  |  | Jackson Hole and two more 75 bp hikes; 10-year yield to 4.3% (high) |
| 2023-04-06 → 2023-10-19 (down) | 196 | -22.4% | 4 (41%) | +5.0% |  |  |  | 'Higher for longer', Fitch downgrade (1 Aug), heavy Treasury supply; 10-year touched 5% on 19 Oct (high) |
| 2020-08-04 → 2021-03-18 (down) | 226 | -21.3% | 3 (24%) | +19.6% |  |  |  | Reflation trade: vaccines and stimulus took the 10-year from 0.5% to 1.7% (high) |
| 2016-07-08 → 2016-12-14 (down) | 159 | -18.0% | 1 (22%) | +6.8% |  |  |  | From the post-Brexit yield low through the election reflation trade and the December hike (high) |
| 2018-11-02 → 2019-08-28 (up) | 299 | +34.5% | 8 (44%) | +7.9% |  |  |  | Fed pivot to patience then cuts (2019); trade-war flight to safety; curve inversion (high) |
| 2019-11-08 → 2020-03-09 (up) | 122 | +27.8% | 4 (48%) | -10.1% |  |  |  | COVID flight to safety and emergency cuts (high) |
| 2023-10-19 → 2023-12-27 (up) | 69 | +22.6% | 0 (0%) | +12.2% |  |  |  | Disinflation and the December 2023 Fed pivot toward cuts (high) |

### Apple

| leg | days | move | shock sessions (share) | SPY | P(up) 7s | signal Long | model capture | what drove it |
|---|---|---|---|---|---|---|---|---|
| 2025-02-24 → 2025-04-08 (down) | 43 | -30.2% | 3 (62%) | -16.6% | 0.57 | 0.59 | -13.5% | Tariffs on China-made iPhones; Liberation Day (high) |
| 2018-10-03 → 2018-11-23 (down) | 51 | -25.5% | 2 (39%) | -9.7% | 0.64 | 1.00 | -24.5% | Weak iPhone XR demand and supplier cuts; Apple stopped reporting unit sales (1 Nov); rate fears (high) |
| 2012-09-19 → 2012-11-15 (down) | 57 | -24.8% | 0 (-0%) |  | 0.63 | 1.00 | -24.5% | iPhone 5 supply constraints and the Maps fiasco; margin fears; year-end tax selling (medium) |
| 2015-11-03 → 2016-01-27 (down) | 85 | -23.5% | 2 (42%) |  | 0.53 | 0.76 | -20.9% | iPhone 6s demand slowdown; first guided year-on-year iPhone decline (26 Jan 2016); China worries (high) |
| 2022-03-29 → 2022-05-19 (down) | 51 | -23.1% | 0 (-0%) | -15.6% | 0.62 | 1.00 | -23.0% | Rates and Fed tightening; China lockdowns hit supply (high) |
| 2020-03-23 → 2020-09-01 (up) | 162 | +140.3% | 3 (18%) | +59.1% | 0.73 | 0.97 | +113.5% | COVID recovery: stimulus, work-from-home demand, the 4-for-1 split and 5G iPhone anticipation (high) |
| 2011-11-25 → 2012-04-09 (up) | 136 | +75.0% | 2 (17%) |  | 0.64 | 1.00 | +72.9% |  |
| 2019-08-05 → 2020-02-12 (up) | 191 | +70.8% | 0 (0%) | +19.9% | 0.66 | 1.00 | +69.6% |  |

### Microsoft

| leg | days | move | shock sessions (share) | SPY | P(up) 7s | signal Long | model capture | what drove it |
|---|---|---|---|---|---|---|---|---|
| 2026-06-01 → 2026-06-25 (down) | 24 | -23.4% | 0 (-0%) | -2.9% | 0.53 | 0.28 | -10.9% | June 2026 sell-off — archive headlines only (low) |
| 2025-01-28 → 2025-04-08 (down) | 70 | -20.6% | 2 (43%) | -17.6% | 0.57 | 0.76 | -7.9% | DeepSeek shock (27 Jan) raised AI-capex doubts; then the tariff sell-off (high) |
| 2022-08-15 → 2022-09-30 (down) | 46 | -20.5% | 2 (42%) | -16.4% | 0.65 | 0.88 | -14.8% | Fed tightening, strong dollar (FX warning), PC slump (high) |
| 2026-01-28 → 2026-02-23 (down) | 26 | -20.0% | 1 (47%) | -1.9% | 0.59 | 0.44 | -7.7% | Worst session since 2020 after January earnings (29 Jan) then the software rout of early February — archive headlines (medium) |
| 2010-04-22 → 2010-05-26 (down) | 34 | -20.0% | 4 (61%) |  | 0.42 | 0.00 | +0.0% |  |
| 2016-06-27 → 2018-01-31 (up) | 583 | +103.2% | 9 (38%) | +45.6% | 0.55 | 0.98 | +86.7% | Azure-led cloud re-rating under Nadella; 2017 tax cuts (high) |
| 2020-03-23 → 2020-09-02 (up) | 163 | +71.2% | 3 (25%) | +61.4% | 0.57 | 1.00 | +60.6% |  |
| 2019-06-03 → 2020-02-10 (up) | 252 | +58.5% | 1 (4%) | +23.7% | 0.63 | 1.00 | +54.9% |  |

### Tesla

| leg | days | move | shock sessions (share) | SPY | P(up) 7s | signal Long | model capture | what drove it |
|---|---|---|---|---|---|---|---|---|
| 2020-02-19 → 2020-03-18 (down) | 28 | -60.6% | 2 (38%) | -30.3% | 0.58 | 1.00 | -53.4% | COVID crash after the parabolic run-up (high) |
| 2024-12-17 → 2025-03-10 (down) | 83 | -53.7% | 3 (44%) | -6.9% | 0.44 | 1.00 | -51.9% | Post-election rally unwound: brand backlash over Musk's DOGE role, falling deliveries, tariffs (high) |
| 2019-01-17 → 2019-06-03 (down) | 137 | -48.5% | 4 (58%) | +4.9% | 0.53 | 0.51 | -17.5% | Demand worries, Q1 2019 loss, price cuts and a capital raise (May) (high) |
| 2022-08-15 → 2022-11-21 (down) | 98 | -45.7% | 2 (26%) | -7.6% | 0.57 | 0.89 | -42.7% | Musk sold shares to fund the Twitter purchase; rates; China demand (high) |
| 2023-12-27 → 2024-04-22 (down) | 117 | -45.7% | 2 (33%) | +5.2% | 0.53 | 0.24 | -26.1% | Price cuts, Q1 2024 delivery miss, Cybertruck recall, layoffs (high) |
| 2019-08-23 → 2020-02-04 (up) | 165 | +319.6% | 6 (51%) | +16.6% | 0.52 | 0.88 | +232.5% | Surprise Q3 2019 profit, Shanghai factory ramp, short squeeze (high) |
| 2012-10-15 → 2013-05-28 (up) | 225 | +303.7% | 6 (46%) |  | 0.56 | 0.97 | +241.0% | Model S launch to the first profitable quarter (Q1 2013) (high) |
| 2020-04-02 → 2020-07-20 (up) | 109 | +261.5% | 3 (22%) | +29.3% | 0.54 | 1.00 | +245.1% | Consecutive profitable quarters and S&P 500 inclusion speculation (high) |

### Nvidia

| leg | days | move | shock sessions (share) | SPY | P(up) 7s | signal Long | model capture | what drove it |
|---|---|---|---|---|---|---|---|---|
| 2022-03-29 → 2022-05-12 (down) | 44 | -43.6% | 0 (-0%) | -15.0% | 0.59 | 0.88 | -34.6% | Rates; collapse of crypto-mining GPU demand and gaming inventory (high) |
| 2022-08-04 → 2022-10-14 (down) | 71 | -41.6% | 2 (37%) | -13.3% | 0.50 | 0.61 | -27.7% | Q2 gaming miss; U.S. export restrictions on A100/H100 to China (31 Aug); Fed (high) |
| 2011-05-31 → 2011-08-08 (down) | 69 | -40.5% | 1 (19%) |  | 0.54 | 0.98 | -37.2% | PC and Tegra weakness into the debt-ceiling downgrade crash (medium) |
| 2010-03-17 → 2010-06-09 (down) | 84 | -39.7% | 3 (46%) |  | 0.20 | 0.13 | -2.2% | Fermi GPU delays; euro crisis and the flash crash (medium) |
| 2018-10-01 → 2018-10-29 (down) | 28 | -35.9% | 2 (41%) | -9.6% | 0.67 | 0.76 | -28.9% | Crypto-mining hangover and channel inventory in the October 2018 sell-off (high) |
| 2016-02-08 → 2016-12-27 (up) | 323 | +369.7% | 7 (46%) | +24.0% | 0.59 | 1.00 | +337.4% | Pascal GPUs, datacenter/AI and automotive re-rating (high) |
| 2022-12-28 → 2023-07-18 (up) | 202 | +238.5% | 2 (29%) | +21.5% | 0.57 | 0.96 | +237.4% | ChatGPT-driven AI capex boom; the May 2023 guidance shock (high) |
| 2020-03-16 → 2020-09-02 (up) | 170 | +192.4% | 2 (11%) | +49.9% | 0.57 | 1.00 | +165.3% | Datacenter and gaming boom, Mellanox, the Arm bid (high) |

## Calendar quarters beyond the leg threshold

| asset | quarters at or below −(min leg) | worst quarter | worst half-year |
|---|---|---|---|
| BTC/USD | 4 of 23: 2021Q2, 2022Q2, 2025Q4, 2026Q1 | 2022Q2 -56.2% | 2022H1 -56.8% |
| S&P 500 (SPY) | 3 of 43: 2018Q4, 2020Q1, 2022Q2 | 2020Q1 -19.6% | 2022H1 -20.0% |
| 20y+ Treasuries (TLT) | 7 of 43: 2016Q4, 2021Q1, 2022Q1, 2022Q2, 2022Q3, 2023Q3, 2024Q4 | 2021Q1 -13.9% | 2022H1 -21.9% |
| Apple | 11 of 67: 2012Q4, 2013Q1, 2013Q2, 2015Q3, 2016Q2, 2018Q4, 2020Q1, 2022Q2… | 2018Q4 -29.9% | 2013H1 -24.6% |
| Microsoft | 8 of 67: 2010Q2, 2012Q4, 2015Q1, 2018Q4, 2022Q2, 2022Q3, 2025Q1, 2026Q1 | 2026Q1 -23.3% | 2010H1 -25.0% |
| Tesla | 7 of 66: 2013Q4, 2018Q3, 2019Q2, 2022Q2, 2022Q4, 2024Q1, 2025Q1 | 2022Q4 -53.6% | 2022H2 -45.1% |
| Nvidia | 6 of 67: 2010Q2, 2011Q3, 2018Q4, 2022Q2, 2022Q3, 2025Q1 | 2018Q4 -52.4% | 2022H1 -48.4% |

Full tables: `output/swing_legs_calendar.csv` (every quarter and half-year with the model's P(up), signal-Long share and exposure return).

## A slow regime layer, asset by asset (yardstick, in-sample)

Hold when the close is above its 100- or 200-day moving average, cash when below, decided at the previous close; compared with holding the model's own exposure and with buy-and-hold from the first forecast origin. No costs, thresholds chosen after the fact — a yardstick for whether a quarter-scale state carries information, not a strategy.

| asset | from | MA100 CAGR / max DD | MA200 CAGR / max DD | model exposure CAGR / max DD | buy-and-hold CAGR / max DD |
|---|---|---|---|---|---|
| BTC/USD | 2021-04-05 | +23.8% / -37.8% | +18.4% / -35.9% | +6.0% / -72.5% | +5.8% / -76.7% |
| S&P 500 (SPY) | 2016-05-18 | +11.4% / -17.7% | +11.7% / -19.8% | +14.3% / -29.0% | +15.6% / -33.8% |
| 20y+ Treasuries (TLT) | 2016-12-29 | -1.6% / -37.8% | -2.4% / -45.5% | — | -0.9% / -48.4% |
| Apple | 2010-05-19 | +16.3% / -29.7% | +19.5% / -35.3% | +24.7% / -40.8% | +26.0% / -43.8% |
| Microsoft | 2010-05-19 | +7.7% / -36.6% | +12.5% / -40.2% | +19.5% / -39.9% | +21.3% / -37.1% |
| Tesla | 2010-11-10 | +14.2% / -67.7% | +15.7% / -71.2% | +38.5% / -60.6% | +40.6% / -73.6% |
| Nvidia | 2010-05-19 | +30.8% / -66.3% | +46.2% / -54.2% | +52.8% / -58.8% | +50.6% / -66.3% |

The answer is type-specific, like everything else in this study. On Bitcoin a trend filter transforms the record (CAGR 24% against 6%, drawdown −38% against −72%). On the index it halves the drawdown at a cost of four points of return. On the single stocks it cuts drawdowns modestly and gives up a large part of the return, because their up legs are long grinds the filter keeps exiting. On long Treasuries nothing helps: the 2020–23 bear market was one slow leg with almost no shock sessions, and both filters lose more than holding. A regime state is worth building for crypto and, more cautiously, for the index; for single stocks the earnings calendar (Section 5.5 of the paper) matters more than trend.
