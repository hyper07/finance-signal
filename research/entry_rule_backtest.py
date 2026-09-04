"""Walk-forward, cost-adjusted backtest of acting k sessions after a shock.

Rule (decided at each shock T using ONLY prior, fully observed events):
  history = sign-adjusted returns from close of T'+k to close of T'+7 over prior
            shocks T' with T'+7 <= T (>= MIN_EVENTS of them)
  trade continuation if trailing t-stat > +1.0, reversal if < -1.0, else skip
  enter at the close of T+k, exit at the close of T+7, pay COST per side

Groups: BTC, BITO, SPY, SPXL (own history); 50 stocks pooled by event cause
(earnings / idiosyncratic / market-wide), history pooled across stocks in time.
Reference: 'always continuation' with no filter on the same out-of-sample events.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR  # noqa: E402
from scheduled_events import earnings_reaction_days, to_sessions  # noqa: E402
from universe_run import key_for  # noqa: E402

MIN_EVENTS = 20
T_FILTER = 1.0
ENTRIES = (0, 1, 2, 3)
COSTS_BPS = (5, 25)
MARKET_Z = 2.0


def market_z() -> pd.DataFrame:
    out = {}
    for sym in ("spy", "qqq"):
        c = pd.read_csv(OUTPUT_DIR / f"{sym}_yf_snapshot.csv", parse_dates=["date"]).set_index("date")["c"].astype(float)
        r = c.pct_change(); out[f"{sym}_z"] = r / r.rolling(20).std(ddof=0).shift(1)
    return pd.DataFrame(out)


def event_paths(key: str) -> pd.DataFrame:
    """One row per shock: date, sign, and close-to-close returns r_k = C[T+k]/C[T]-1 for k=0..7."""
    day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
    close = day["close"].to_numpy(float)
    ev = pd.read_csv(OUTPUT_DIR / f"events_{key}.csv", parse_dates=["event_date"])
    rows = []
    for _, e in ev.iterrows():
        T = day.index.get_loc(e["event_date"])
        if T + 7 >= len(close):
            continue
        rows.append({"key": key, "date": e["event_date"], "T": T, "sign": 1 if e["direction"] == "up" else -1,
                     **{f"r{k}": close[T + k] / close[T] - 1.0 for k in range(0, 8)}})
    return pd.DataFrame(rows)


def leg_return(df: pd.DataFrame, k: int) -> pd.Series:
    """Sign-adjusted return from close of day k to close of day 7."""
    return df["sign"] * ((1 + df["r7"]) / (1 + df[f"r{k}"]) - 1.0)


def backtest(events: pd.DataFrame, k: int, cost_bps: float, pooled_dates: bool = False) -> dict:
    """Walk-forward: decision at each event from prior fully observed events (by date order)."""
    df = events.sort_values("date").reset_index(drop=True)
    x = leg_return(df, k).to_numpy(float)
    dates = df["date"].to_numpy()
    # an event T' is observable at T if its exit (T'+7 sessions) happened before T: approximate with 11 calendar days
    obs_by = dates + np.timedelta64(11, "D")
    trades = []
    for i in range(len(df)):
        hist = x[(obs_by < dates[i])]
        if len(hist) < MIN_EVENTS:
            continue
        t = hist.mean() / (hist.std(ddof=1) / np.sqrt(len(hist))) if hist.std(ddof=1) > 0 else 0.0
        if t > T_FILTER:
            side = 1
        elif t < -T_FILTER:
            side = -1
        else:
            side = 0
        gross_cont = x[i]
        net = side * gross_cont - (2 * cost_bps / 1e4 if side != 0 else 0.0)
        trades.append({"date": dates[i], "side": side, "gross_continuation": gross_cont, "net": net, "trailing_t": t})
    tr = pd.DataFrame(trades)
    if tr.empty:
        return {"oos_events": 0}
    def summ(net: np.ndarray, label: str) -> dict:
        if len(net) == 0:
            return {"n": 0}
        t, p = stats.ttest_1samp(net, 0) if len(net) > 4 else (np.nan, np.nan)
        nav = np.cumprod(1 + net); dd = (nav / np.maximum.accumulate(nav) - 1).min()
        return {"n": int(len(net)), "mean_net_pct": round(100 * net.mean(), 3), "median_net_pct": round(100 * np.median(net), 3),
                "hit_rate": round(float((net > 0).mean()), 3), "t": round(float(t), 2), "p": round(float(p), 4),
                "total_compounded_pct": round(100 * (nav[-1] - 1), 1), "max_drawdown_pct": round(100 * float(dd), 1),
                "mean_over_sd": round(float(net.mean() / net.std(ddof=1)), 3) if len(net) > 1 and net.std(ddof=1) > 0 else None}
    active = tr[tr["side"] != 0]
    out = {"oos_events": int(len(tr)), "traded": int(len(active)), "share_traded": round(float(len(active) / len(tr)), 3),
           "share_continuation": round(float((active["side"] == 1).mean()), 3) if len(active) else None,
           "rule": summ(active["net"].to_numpy(float), "rule"),
           "rule_since_2024": summ(active.loc[active["date"] >= np.datetime64("2024-01-01"), "net"].to_numpy(float), "rule2024"),
           "rule_since_2025": summ(active.loc[active["date"] >= np.datetime64("2025-01-01"), "net"].to_numpy(float), "rule2025"),
           "always_continuation_same_events": summ((tr["gross_continuation"] - 2 * cost_bps / 1e4).to_numpy(float), "always")}
    return out


def main() -> None:
    groups: dict[str, pd.DataFrame] = {}
    for key in ("btc", "bito", "spy", "spxl"):
        groups[key.upper()] = event_paths(key)
    # stocks pooled by cause
    tickers = json.load(open(OUTPUT_DIR / "universe_tickers.json"))["tickers"]
    keys = {"aapl": "AAPL", "msft": "MSFT", "tsla": "TSLA", "nvda": "NVDA"}
    keys.update({key_for(t): t for t in tickers})
    mz = market_z()
    pooled = {"earnings": [], "idiosyncratic": [], "market-wide": []}
    for key, sym in keys.items():
        if not (OUTPUT_DIR / f"events_{key}.csv").exists():
            continue
        ep = event_paths(key)
        if ep.empty:
            continue
        day_index = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True).index
        try:
            earn = set(day_index[to_sessions(earnings_reaction_days(sym, day_index), day_index)])
        except Exception:
            earn = set()
        for _, e in ep.iterrows():
            d = e["date"]
            if d in earn:
                cat = "earnings"
            else:
                sz, qz = mz["spy_z"].get(d, np.nan), mz["qqq_z"].get(d, np.nan)
                cat = "market-wide" if any(np.isfinite(v) and abs(v) >= MARKET_Z and np.sign(v) == e["sign"] for v in (sz, qz)) else "idiosyncratic"
            pooled[cat].append(e)
    for cat, rows in pooled.items():
        groups[f"stocks pooled: {cat}"] = pd.DataFrame(rows)
    result = {}
    for gname, ev in groups.items():
        result[gname] = {"events": int(len(ev)), "by_entry": {}}
        for k in ENTRIES:
            result[gname]["by_entry"][str(k)] = {f"{c}bps": backtest(ev, k, c) for c in COSTS_BPS}
    (OUTPUT_DIR / "entry_rule_backtest.json").write_text(json.dumps(result, indent=1, default=str))
    for gname, r in result.items():
        print(f"\n== {gname} ({r['events']} shocks)")
        for k, byc in r["by_entry"].items():
            for c, b in byc.items():
                if b.get("oos_events", 0) == 0:
                    continue
                s, a, s25 = b["rule"], b["always_continuation_same_events"], b["rule_since_2025"]
                print(f"  enter day {k} @{c:>5}: OOS events {b['oos_events']}, traded {b['traded']} ({b['share_traded']:.0%}, cont {b['share_continuation']}) | "
                      f"rule mean {s.get('mean_net_pct')}% hit {s.get('hit_rate')} t {s.get('t')} total {s.get('total_compounded_pct')}% maxDD {s.get('max_drawdown_pct')}% | "
                      f"always-cont mean {a.get('mean_net_pct')}% hit {a.get('hit_rate')} t {a.get('t')} | since-2025 rule n {s25.get('n')} mean {s25.get('mean_net_pct')}% hit {s25.get('hit_rate')}")


if __name__ == "__main__":
    main()
