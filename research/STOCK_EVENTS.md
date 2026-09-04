# Single-stock shock catalogue

645 shock sessions (|z| ≥ 2.5) for AAPL, MSFT, TSLA, NVDA, 2010 → 2026-09; 346 are increases.
Category priority: earnings reaction session (or the session after) → market-wide (SPY or QQQ |z| ≥ 2 same sign) → idiosyncratic.
Headlines from the Alpaca/Benzinga archive cover 2024-02 → 2026-08 (52 of the 346 increases); earlier idiosyncratic events carry manual attributions where looked up.

## Increases by category

| category | n | share | mean |r| % | pre-event h=1 coverage | mean |s| | consensus aligned | latency (median) | continuation 1d / 3d / 7d % (t) |
|---|---|---|---|---|---|---|---|---|
| earnings | 78 | 22.5% | 8.7 | 0.0 | 5.42 | 15.4% | 5.0 | +0.72 / +1.94 / +2.26 (2.68) |
| earnings+1 | 3 | 0.9% | 5.73 | 0.0 | 3.25 | 33.3% | 0.0 | +1.48 / +1.59 / +2.74 (None) |
| idiosyncratic | 166 | 48.0% | 6.03 | 0.0 | 3.36 | 24.1% | 4.5 | +0.24 / +0.15 / +1.10 (1.56) |
| market-wide | 99 | 28.6% | 6.19 | 0.0 | 3.02 | 24.2% | 4.5 | -0.65 / +0.05 / +0.58 (0.83) |

## Increases by stock

- **AAPL**: idiosyncratic 33, market-wide 31, earnings 18, earnings+1 1
- **MSFT**: idiosyncratic 37, market-wide 32, earnings 20
- **NVDA**: idiosyncratic 30, earnings 24, market-wide 23, earnings+1 2
- **TSLA**: idiosyncratic 66, earnings 16, market-wide 13

## Largest increases per stock (top 12 by z)

### AAPL

| date | +% | z | SPY z | category | what happened | source | model the day before: P(up), band %, covered | consensus | latency | +1d / +3d / +7d % |
|---|---|---|---|---|---|---|---|---|---|---|
| 2017-02-01 | +6.1 | 11.9 | 0.1 | earnings | earnings report | earnings calendar | 0.48, [-0.5, -0.0, +0.7], no | Hold | 14 | -0.2 / +1.2 / +3.1 |
| 2014-04-24 | +8.2 | 9.5 | 0.24 | earnings | earnings report | earnings calendar | 0.45, [-1.3, -0.0, +1.2], no | Hold | 5 | +0.7 / +4.3 / +5.8 |
| 2016-07-27 | +6.5 | 7.5 | -0.16 | earnings | earnings report | earnings calendar | 0.50, [-1.2, +0.0, +0.8], no | Hold | 5 | +1.4 / +3.0 / +5.0 |
| 2024-06-11 | +7.3 | 7.3 | 0.45 | idiosyncratic | ticker-tagged archive match; causal attribution unverified | licensed archive metadata (text not redistributed) | 0.52, [-0.9, +0.0, +1.7], no | Hold |  | +2.9 / +2.6 / +0.2 |
| 2012-01-25 | +6.2 | 6.5 | 1.29 | earnings | earnings report | earnings calendar | 0.47, [-1.7, -0.1, +1.4], no | Buy (aligned) |  | -0.5 / +1.4 / +2.9 |
| 2018-08-01 | +5.9 | 6.3 | -0.31 | earnings | earnings report | earnings calendar | 0.47, [-1.5, -0.1, +1.4], no | Hold | 2 | +2.9 / +3.8 / +3.4 |
| 2020-07-31 | +10.5 | 6.2 | 0.96 | earnings | earnings report | earnings calendar | 0.63, [-1.8, +0.4, +1.8], no | Hold | 2 | +2.5 / +3.6 / +3.1 |
| 2025-08-06 | +5.1 | 6.2 | 1.24 | idiosyncratic | ticker-tagged archive match; causal attribution unverified | licensed archive metadata (text not redistributed) | 0.53, [-1.4, +0.1, +1.4], no | Hold | 5 | +3.2 / +6.7 / +8.7 |
| 2017-08-02 | +4.7 | 6.1 | 0.14 | earnings | earnings report | earnings calendar | 0.40, [-0.6, -0.1, +1.1], no | Hold | 1 | -1.0 / +1.1 / +0.6 |
| 2022-01-28 | +7.0 | 5.7 | 3.04 | earnings | earnings report | earnings calendar | 0.50, [-2.0, -0.0, +1.6], no | Hold | 11 | +2.6 / +3.2 / +2.8 |
| 2019-03-11 | +3.5 | 5.5 | 2.85 | market-wide | market-wide move | SPY/QQQ same-day z | 0.47, [-1.0, -0.0, +1.3], no | Hold | 5 | +1.1 / +2.7 / +5.2 |
| 2019-05-01 | +4.9 | 5.4 | -2.38 | earnings | earnings report | earnings calendar | 0.53, [-1.1, +0.0, +1.1], no | Hold | 0 | -0.7 / -1.0 / -6.0 |

### MSFT

| date | +% | z | SPY z | category | what happened | source | model the day before: P(up), band %, covered | consensus | latency | +1d / +3d / +7d % |
|---|---|---|---|---|---|---|---|---|---|---|
| 2017-10-27 | +6.4 | 12.8 | 3.07 | earnings | earnings report | earnings calendar | 0.53, [-0.6, +0.0, +0.4], no | Hold |  | +0.1 / -0.8 / +0.5 |
| 2015-10-23 | +10.1 | 9.7 | 1.06 | earnings | earnings report | earnings calendar | 0.42, [-1.5, -0.2, +1.1], no | Hold |  | +2.6 / +2.1 / +2.4 |
| 2026-07-30 | +15.5 | 9.7 | 2.56 | earnings | earnings-window archive match | earnings calendar; licensed archive metadata (text not redistributed) | 0.47, [-2.0, -0.1, +1.9], no | Hold | 0 | +3.0 / +9.2 / +12.2 |
| 2015-04-24 | +10.5 | 9.0 | 0.41 | earnings | earnings report | earnings calendar | 0.42, [-1.6, -0.2, +0.9], no | Hold | 8 | +0.3 / +2.5 / -0.6 |
| 2013-04-09 | +3.6 | 7.3 | 0.64 | idiosyncratic | No single catalyst: minor items (XP anniversary, Lumia usage, earnings-date notice) in a multi-day rally | TechCrunch 2013-11-14 'Parsing Microsoft's 42% gain in 2013' | 0.53, [-0.7, +0.0, +0.8], no | Hold |  | +2.3 / -2.8 / -2.8 |
| 2025-04-09 | +10.1 | 6.7 | 5.44 | market-wide | market-wide move | licensed archive metadata (text not redistributed) | 0.57, [-1.2, +0.2, +2.0], no | Hold |  | -2.3 / -0.7 / -8.0 |
| 2013-08-23 | +7.3 | 6.6 | 0.6 | idiosyncratic | Steve Ballmer announced he would retire as CEO within twelve months; shares closed +7.3% | GeekWire 2013-08-23; CNN Money 2013-08-23; CNBC 2013-08-23 | 0.42, [-1.6, -0.2, +1.2], no | Hold |  | -1.7 / -5.0 / -10.2 |
| 2025-07-31 | +3.9 | 6.2 | -0.92 | earnings | earnings-window archive match | earnings calendar; licensed archive metadata (text not redistributed) | 0.60, [-0.8, +0.1, +1.0], no | Buy (aligned) |  | -1.8 / -1.1 / -2.2 |
| 2014-07-16 | +3.8 | 6.2 | 0.96 | idiosyncratic | Reports (confirmed 17 Jul) of the largest layoffs in company history, 18,000 jobs, after the Nokia acquisition | NPR 2014-07-18; Motley Fool 2014-07-15/17 | 0.48, [-0.8, -0.0, +0.9], no | Hold |  | +1.0 / +1.7 / +1.0 |
| 2013-10-25 | +6.0 | 5.7 | 0.56 | earnings | earnings report | earnings calendar | 0.53, [-1.3, +0.1, +1.8], no | Hold | 14 | -0.4 / -0.5 / +2.5 |
| 2016-10-21 | +4.2 | 5.7 | 0.08 | earnings | earnings report | earnings calendar | 0.55, [-0.8, +0.1, +1.3], no | Hold | 13 | +2.2 / +1.6 / +0.2 |
| 2018-03-26 | +7.6 | 5.7 | 2.57 | market-wide | market-wide move | SPY/QQQ same-day z | 0.52, [-2.5, +0.1, +2.7], no | Hold | 8 | -4.6 / -2.7 / -1.5 |

### NVDA

| date | +% | z | SPY z | category | what happened | source | model the day before: P(up), band %, covered | consensus | latency | +1d / +3d / +7d % |
|---|---|---|---|---|---|---|---|---|---|---|
| 2016-11-11 | +29.8 | 14.1 | -0.36 | earnings | earnings report | earnings calendar | 0.57, [-2.0, +0.3, +2.1], no | Hold | 0 | -4.9 / +4.2 / +6.5 |
| 2017-05-10 | +17.8 | 11.8 | 0.4 | earnings | earnings report | earnings calendar | 0.55, [-1.8, +0.1, +2.8], no | Hold | 0 | +4.3 / +10.7 / +12.2 |
| 2023-05-25 | +24.4 | 11.2 | 0.99 | earnings | earnings report | earnings calendar | 0.55, [-2.1, +0.3, +3.0], no | Hold |  | +2.5 / -0.4 / +1.8 |
| 2016-05-13 | +15.2 | 11.2 | -1.55 | earnings | earnings report | earnings calendar | 0.53, [-1.8, +0.3, +2.1], no | Hold |  | +3.0 / +5.8 / +11.0 |
| 2015-08-07 | +12.4 | 10.2 | -0.3 | earnings | earnings report | earnings calendar | 0.52, [-1.2, +0.1, +1.3], no | Hold | 10 | +3.5 / +3.2 / +0.9 |
| 2015-11-06 | +13.9 | 8.3 | -0.07 | earnings | earnings report | earnings calendar | 0.48, [-1.9, -0.0, +1.3], no | Hold | 5 | -0.4 / -3.3 / -3.6 |
| 2024-02-22 | +16.4 | 6.6 | 2.78 | earnings | earnings-window archive match | earnings calendar; licensed archive metadata (text not redistributed) | 0.57, [-3.3, +0.4, +3.3], no | Hold |  | +0.4 / +0.2 / +8.5 |
| 2021-11-04 | +12.0 | 6.6 | 0.89 | idiosyncratic | Wells Fargo (Aaron Rakers) raised target to \$320 from \$245 ahead of Omniverse Enterprise general availabilit | Investing.com 'Bull of the Day'; TheStreet 2021-11 | 0.60, [-2.0, +0.2, +2.2], no | Hold |  | -0.2 / +2.9 / +0.8 |
| 2013-11-08 | +6.9 | 6.3 | 2.27 | earnings | earnings report | earnings calendar | 0.47, [-1.1, -0.1, +1.7], no | Hold |  | +0.8 / +3.8 / -0.2 |
| 2011-01-06 | +13.8 | 6.2 | -0.59 | idiosyncratic | CES 2011 follow-through: Project Denver and Tegra 2 design wins; Windows on ARM | Engadget 2011-01-05; Digitimes 2011-01-06; Motley Fool 2011-01-10 | 0.53, [-1.8, +0.1, +3.0], no | Buy (aligned) |  | +2.8 / +5.1 / +19.2 |
| 2014-08-08 | +8.8 | 6.1 | 1.74 | earnings | earnings report | earnings calendar | 0.65, [-1.5, +0.3, +1.8], no | Buy (aligned) |  | -0.5 / +0.1 / +2.4 |
| 2025-04-09 | +18.7 | 5.1 | 5.44 | market-wide | market-wide move | licensed archive metadata (text not redistributed) | 0.60, [-4.5, +0.8, +4.8], no | Hold |  | -5.9 / -3.2 / -15.2 |

### TSLA

| date | +% | z | SPY z | category | what happened | source | model the day before: P(up), band %, covered | consensus | latency | +1d / +3d / +7d % |
|---|---|---|---|---|---|---|---|---|---|---|
| 2011-03-31 | +17.0 | 10.2 | -0.13 | idiosyncratic | Morgan Stanley (Adam Jonas) upgraded Tesla to Overweight with a \$70 target, calling it 'America's fourth auto | Morgan Stanley note 31 Mar 2011; confirmed via contemporaneous coverage (web check 2026-09-04) | 0.50, [-2.0, +0.0, +2.3], no | Hold |  | -3.9 / -3.8 / -8.9 |
| 2021-10-25 | +12.7 | 9.2 | 0.61 | idiosyncratic | Hertz ordered 100,000 Teslas (~\$4bn); market value passed \$1 trillion | CNBC 2021-10-25; NPR 2021-10-25; Forbes 2021-10-25 | 0.58, [-2.3, +0.1, +2.4], no | Buy (aligned) |  | -0.6 / +5.1 / +18.4 |
| 2019-10-24 | +17.7 | 8.5 | 0.19 | earnings | earnings report | earnings calendar | 0.53, [-2.9, +0.3, +2.7], no | Hold |  | +9.5 / +5.5 / +5.9 |
| 2024-10-24 | +21.9 | 8.5 | 0.37 | earnings | earnings-window archive match | earnings calendar; licensed archive metadata (text not redistributed) | 0.42, [-4.2, -0.4, +3.5], no | Hold | 11 | +3.3 / -0.4 / -6.8 |
| 2013-04-01 | +15.9 | 7.5 | -0.85 | idiosyncratic | Tesla announced it expected its first-ever quarterly profit for Q1 2013; Model S sales beat the 4,500 target | CNN Money 2013-04-01 'Tesla expects its first-ever profit' | 0.45, [-3.2, -0.2, +2.8], no | Hold |  | +0.9 / -4.4 / -4.7 |
| 2018-08-02 | +16.2 | 7.4 | 1.04 | earnings | earnings report | earnings calendar | 0.42, [-3.5, -0.2, +3.9], no | Hold |  | -0.4 / +8.6 / +2.0 |
| 2013-05-09 | +24.4 | 7.0 | -0.32 | earnings | earnings report | earnings calendar | 0.52, [-3.1, +0.4, +4.5], no | Hold | 5 | +10.6 / +19.9 / +29.6 |
| 2014-06-16 | +8.8 | 6.6 | 0.21 | idiosyncratic | Reports of BMW and Nissan joining talks on charging standards, four days after Tesla opened its patents | Green Car Reports 2014-06-16; Benzinga 'Why Tesla Is Up Over 8%'; Forbes 2014-06-16 | 0.53, [-1.6, +0.1, +2.0], no | Hold |  | +3.1 / +1.4 / +5.5 |
| 2014-01-14 | +15.7 | 6.3 | 1.78 | market-wide | Q4 2013 Model S deliveries of 6,900, ~20% above guidance | TechCrunch 2014-01-14; Bloomberg 2014-01-14 | 0.43, [-2.8, -0.2, +2.8], no | Hold | 8 | +1.8 / +5.4 / +8.3 |
| 2011-11-03 | +13.1 | 5.6 | 1.03 | earnings | earnings report | earnings calendar | 0.50, [-3.4, +0.0, +3.2], no | Sell |  | -0.5 / -1.9 / +2.3 |
| 2020-02-03 | +19.9 | 5.4 | 1.01 | idiosyncratic | Argus raised target to \$808 from \$556; Panasonic reported first quarterly profit at the Tesla battery JV | CNBC 2020-02-03; Forbes 2020-02-03 | 0.57, [-3.8, +0.5, +4.9], no | Buy (aligned) |  | +13.7 / -4.0 / -1.6 |
| 2012-03-26 | +9.7 | 5.3 | 2.12 | market-wide | market-wide move | SPY/QQQ same-day z | 0.52, [-2.2, +0.0, +2.8], no | Hold |  | +1.4 / -0.2 / -6.4 |

## Increases with licensed-archive coverage (2024-02 → 2026-08)

Headline text is not redistributed. Counts and abbreviated SHA-256 fingerprints permit record matching by an authorised user.

- **AAPL 2024-04-11** +4.3% (z 3.3, market-wide): 2 matches; SHA-256 prefixes edb175270755, 3992c3573354
- **AAPL 2024-05-03** +6.0% (z 3.8, earnings): 3 matches; SHA-256 prefixes 23ede59104f9, 3d61ead4afd1, 126bf0a1f59c
- **AAPL 2024-06-11** +7.3% (z 7.3, idiosyncratic): 4 matches; SHA-256 prefixes 5f46ed165a8f, 5a0838177599, 4d6eb2670dac
- **AAPL 2024-09-19** +3.7% (z 3.3, market-wide): 1 matches; SHA-256 prefixes 88891743c308
- **AAPL 2025-04-09** +15.3% (z 5.0, market-wide): 6 matches; SHA-256 prefixes cfa600a2f5a8, 0ec3377fa57d, 836d9b365834
- **AAPL 2025-05-12** +6.3% (z 3.0, market-wide): 1 matches; SHA-256 prefixes e59d4c076d62
- **AAPL 2025-08-06** +5.1% (z 6.2, idiosyncratic): 2 matches; SHA-256 prefixes fde85a908d13, adf0ecbac3e4
- **AAPL 2025-08-08** +4.2% (z 2.7, idiosyncratic): 4 matches; SHA-256 prefixes b4d2f07f56b5, bb6d47b03f85, b6896cfb6c81
- **AAPL 2025-09-22** +4.3% (z 2.8, idiosyncratic): 5 matches; SHA-256 prefixes 1a9adf3cafa5, aea1c4a8d5ab, e986bcb5fee2
- **AAPL 2025-10-20** +3.9% (z 2.6, idiosyncratic): 3 matches; SHA-256 prefixes 7d518c00f365, 94831b02e3ab, 63924c940a7b
- **AAPL 2026-01-26** +3.0% (z 3.3, idiosyncratic): 6 matches; SHA-256 prefixes 14580a9ea8d1, 8fb5b0d2b495, ea2ae0739813
- **AAPL 2026-02-02** +4.1% (z 3.3, earnings+1): 3 matches; SHA-256 prefixes b42ef5cb655d, 078efc0a2cf8, 69efff4ef3f1
- **AAPL 2026-03-31** +2.9% (z 2.9, market-wide): 2 matches; SHA-256 prefixes 25321037eb96, cd66d3ee96e6
- **AAPL 2026-06-02** +2.9% (z 2.8, idiosyncratic): 2 matches; SHA-256 prefixes 927cfa67a96b, ddaa014bb815
- **MSFT 2024-07-01** +2.2% (z 2.8, idiosyncratic): 2 matches; SHA-256 prefixes 3689a95e64e3, 00e0e8a14b72
- **MSFT 2024-10-22** +2.1% (z 2.6, idiosyncratic): 2 matches; SHA-256 prefixes 8ce6ec306eff, 35f840fe554d
- **MSFT 2025-01-22** +4.1% (z 4.0, idiosyncratic): 1 matches; SHA-256 prefixes 89e6f6162a1d
- **MSFT 2025-03-05** +3.2% (z 3.1, idiosyncratic): 1 matches; SHA-256 prefixes 97c329a5ba9b
- **MSFT 2025-04-09** +10.1% (z 6.7, market-wide): 3 matches; SHA-256 prefixes 0ec3377fa57d, a2c326724f36, 836d9b365834
- **MSFT 2025-05-01** +7.6% (z 2.6, earnings): 2 matches; SHA-256 prefixes 4641fe72d3be, a71032b76ee4
- **MSFT 2025-07-31** +3.9% (z 6.2, earnings): 5 matches; SHA-256 prefixes c11c42edd41c, 6266a240e095, ee7db26ceea7
- **MSFT 2025-10-06** +2.2% (z 2.7, idiosyncratic): 3 matches; SHA-256 prefixes e33ba03be08f, 174fbcbd3ed4, 420d8b832d95
- **MSFT 2026-01-23** +3.3% (z 3.0, idiosyncratic): 1 matches; SHA-256 prefixes 69585fc468ed
- **MSFT 2026-03-31** +3.1% (z 2.7, market-wide): 3 matches; SHA-256 prefixes 25321037eb96, cd66d3ee96e6, 5fd3596b5464
- **MSFT 2026-04-13** +3.6% (z 2.7, idiosyncratic): 1 matches; SHA-256 prefixes 6b0c8449a879
- **MSFT 2026-04-15** +4.6% (z 2.8, idiosyncratic): 2 matches; SHA-256 prefixes a31a98d34cdc, b4676adfc5ce
- **MSFT 2026-05-29** +5.4% (z 3.4, idiosyncratic): 3 matches; SHA-256 prefixes 8790a8dbcfb3, 1c2648d9bace, 76ea65f06814
- **MSFT 2026-07-30** +15.5% (z 9.7, earnings): 5 matches; SHA-256 prefixes 760603b5bea2, 50bbea1fcbf2, 30ac88ed3d99
- **NVDA 2024-02-02** +5.0% (z 2.7, idiosyncratic): 4 matches; SHA-256 prefixes 25d40f1edb3d, 35014b38c218, ec8351ffedee
- **NVDA 2024-02-22** +16.4% (z 6.6, earnings): 6 matches; SHA-256 prefixes b55b32c7ac57, 14c2de1d79aa, 6ddc456962dd
- **NVDA 2024-05-23** +9.3% (z 3.8, earnings): 8 matches; SHA-256 prefixes 9fdfe60a53c5, 7b6e630d8ae8, d71ac8da6de2
- **NVDA 2024-07-31** +12.8% (z 3.6, market-wide): 5 matches; SHA-256 prefixes 95718ea044ce, c30618c1f2b1, 2dd9371640e2
- **NVDA 2025-04-09** +18.7% (z 5.1, market-wide): 4 matches; SHA-256 prefixes 0ec3377fa57d, a2c326724f36, 836d9b365834
- **NVDA 2025-06-25** +4.3% (z 2.5, idiosyncratic): 2 matches; SHA-256 prefixes ddbfa5ab8ecc, 42f55c3ada68
- **NVDA 2025-09-10** +3.8% (z 2.6, idiosyncratic): 0 matches; SHA-256 prefixes none
- **NVDA 2026-02-06** +7.9% (z 4.1, market-wide): 3 matches; SHA-256 prefixes 914727caa9fd, 1f91436425b2, 2cc28041e106
- **NVDA 2026-03-31** +5.6% (z 3.0, market-wide): 3 matches; SHA-256 prefixes 25321037eb96, cd66d3ee96e6, 5fd3596b5464
- **NVDA 2026-05-06** +5.8% (z 2.6, market-wide): 2 matches; SHA-256 prefixes 34ff200597fb, 31cff8c5410f
- **NVDA 2026-06-01** +6.3% (z 2.8, idiosyncratic): 5 matches; SHA-256 prefixes baa33e5e812c, 746303a0c641, c2ba00720020
- **NVDA 2026-08-27** +8.7% (z 4.3, earnings): 6 matches; SHA-256 prefixes 2f7c533a9659, eb8431b56946, 0a343b996651
- **TSLA 2024-04-24** +12.1% (z 4.3, earnings): 4 matches; SHA-256 prefixes 7b4ebf5ea503, d2a752ea46bc, 4cd8515117b5
- **TSLA 2024-04-29** +15.3% (z 3.8, idiosyncratic): 6 matches; SHA-256 prefixes 7961616648d3, 74e13165d6ca, 11cd8b8c191f
- **TSLA 2024-07-01** +6.1% (z 2.7, idiosyncratic): 4 matches; SHA-256 prefixes 00f7ffebb090, 3689a95e64e3, 00e0e8a14b72
- **TSLA 2024-07-02** +10.2% (z 4.0, idiosyncratic): 6 matches; SHA-256 prefixes 51087bb26ab1, dd3de6e71517, 03f411f90aad
- **TSLA 2024-10-24** +21.9% (z 8.5, earnings): 5 matches; SHA-256 prefixes 9907f61b7ef3, 0a62daf1be65, e2adf4e7edde
- **TSLA 2024-11-06** +14.8% (z 2.7, market-wide): 4 matches; SHA-256 prefixes 63e74eb2a7a3, 977a5a372bd0, a1a3317a3cad
- **TSLA 2025-04-09** +22.7% (z 4.2, market-wide): 6 matches; SHA-256 prefixes bc6205e47f2c, 0ec3377fa57d, 836d9b365834
- **TSLA 2025-08-22** +6.2% (z 3.1, market-wide): 0 matches; SHA-256 prefixes none
- **TSLA 2025-09-11** +6.0% (z 2.8, idiosyncratic): 2 matches; SHA-256 prefixes 60399acc9253, 00a9663c3497
- **TSLA 2025-09-12** +7.4% (z 3.0, idiosyncratic): 1 matches; SHA-256 prefixes 49ff8a46fd56
- **TSLA 2026-04-15** +7.6% (z 2.9, idiosyncratic): 2 matches; SHA-256 prefixes a31a98d34cdc, b4676adfc5ce
- **TSLA 2026-06-29** +8.5% (z 2.8, idiosyncratic): 3 matches; SHA-256 prefixes e13f125fea34, cd200c4354f9, fad5dd2263a5