"""Portfolio layer: why the index rewards rebalancing and crypto does not.

60/40 stock/bond portfolios from adjusted daily closes (SPY/TLT 2016-2026; BTC/TLT
2021-2026 for contrast), 5 bp per unit turnover:
  buy_hold           60/40 at start, weights drift
  monthly / quarterly rebalance to 60/40 on the first session of each period
  band_5pp           rebalance to 60/40 whenever the stock weight drifts > 5 points
                     (the user's rule: sell bonds to buy stocks after a fall, sell
                     stocks to buy bonds after a rise)
  band_5pp+shock_tilt band rule plus: after an index |z|>=2.5 DOWN session move to
                     70/30 for 7 sessions, then back (harvests the index reversal)
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR, load_equity_daily, load_btc_daily

COST = 5 / 1e4

def series(sym: str) -> pd.Series:
    if sym == "BTC":
        d = load_btc_daily(); s = pd.Series(d["c"].to_numpy(float), index=pd.DatetimeIndex(d["date"]))
    else:
        e = load_equity_daily(); sub = e[e.symbol == sym].sort_values("date"); s = pd.Series(sub["c"].to_numpy(float), index=pd.DatetimeIndex(sub["date"]))
    return s

def simulate(rs: pd.Series, rb: pd.Series, w_target: float, mode: str, band: float = 0.05, shock_tilt: bool = False, z: pd.Series | None = None) -> dict:
    idx = rs.index; n = len(idx)
    ws, wb = w_target, 1 - w_target
    nav = 1.0; navs = np.empty(n); turnover = 0.0; rebalances = 0; tilt_left = 0
    last_month = idx[0].month; last_q = (idx[0].month - 1) // 3
    for i in range(n):
        r_s, r_b = rs.iloc[i], rb.iloc[i]
        nav_new = nav * (ws * (1 + r_s) + wb * (1 + r_b))
        ws = ws * (1 + r_s) * nav / nav_new; wb = 1 - ws; nav = nav_new
        target = w_target
        if shock_tilt and z is not None:
            if tilt_left > 0: tilt_left -= 1; target = min(w_target + 0.10, 1.0)
            zi = z.iloc[i]
            if np.isfinite(zi) and zi <= -2.5: tilt_left = 7; target = min(w_target + 0.10, 1.0)
        do = False
        if mode == "monthly" and idx[i].month != last_month: do = True
        if mode == "quarterly" and (idx[i].month - 1) // 3 != last_q: do = True
        if mode == "band" and abs(ws - target) > band: do = True
        if shock_tilt and tilt_left in (7, 0) and abs(ws - target) > 0.005: do = True
        last_month = idx[i].month; last_q = (idx[i].month - 1) // 3
        if do:
            t = abs(target - ws); turnover += t; nav *= (1 - COST * t); ws, wb = target, 1 - target; rebalances += 1
        navs[i] = nav
    navs = pd.Series(navs, index=idx); rets = navs.pct_change().dropna()
    years = (idx[-1] - idx[0]).days / 365.25
    dd = (navs / navs.cummax() - 1).min()
    yearly = navs.resample("YE").last().pct_change().dropna()
    return {"cagr_pct": round(100 * (navs.iloc[-1] ** (1 / years) - 1), 2), "vol_pct": round(100 * rets.std() * np.sqrt(252), 2),
            "sharpe": round(float(rets.mean() / rets.std() * np.sqrt(252)), 3), "max_drawdown_pct": round(100 * float(dd), 1),
            "worst_year": f"{yearly.idxmin().year}: {100*yearly.min():.1f}%", "rebalances": rebalances, "turnover_total": round(turnover, 2),
            "final_nav": round(float(navs.iloc[-1]), 3), "_navs": navs}

def run(stock: str, bond: str, start: str) -> dict:
    s, b = series(stock).loc[start:], series(bond).loc[start:]
    df = pd.concat([s.rename("s"), b.rename("b")], axis=1).dropna()
    rs, rb = df["s"].pct_change().fillna(0), df["b"].pct_change().fillna(0)
    z = (rs / rs.rolling(20).std(ddof=0).shift(1))
    out = {"period": f"{df.index[0].date()} → {df.index[-1].date()}", "sessions": int(len(df)), "strategies": {}}
    out["strategies"][f"100% {stock}"] = simulate(rs, rb, 1.0, "none")
    out["strategies"][f"100% {bond}"] = simulate(rs, rb, 0.0, "none")
    out["strategies"]["60/40 buy-and-hold (drift)"] = simulate(rs, rb, 0.6, "none")
    out["strategies"]["60/40 monthly rebalance"] = simulate(rs, rb, 0.6, "monthly")
    out["strategies"]["60/40 quarterly rebalance"] = simulate(rs, rb, 0.6, "quarterly")
    out["strategies"]["60/40 band ±5pp (sell bonds after falls / stocks after rises)"] = simulate(rs, rb, 0.6, "band")
    out["strategies"]["60/40 band + shock tilt (70/30 for 7 sessions after a |z|≥2.5 down day)"] = simulate(rs, rb, 0.6, "band", shock_tilt=True, z=z)
    return out

def main() -> None:
    res = {"SPY/TLT": run("SPY", "TLT", "2016-01-04"), "SPXL/TLT": run("SPXL", "TLT", "2016-01-04"), "BTC/TLT": run("BTC", "TLT", "2021-01-04")}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, key in zip(axes, ("SPY/TLT", "BTC/TLT")):
        for name, r in res[key]["strategies"].items():
            ax.plot(r["_navs"].index, r["_navs"], lw=1.3, label=f"{name} (CAGR {r['cagr_pct']}%, maxDD {r['max_drawdown_pct']}%)")
        ax.set_yscale("log"); ax.set_title(f"{key} — {res[key]['period']}", fontsize=10); ax.legend(fontsize=6.5); ax.grid(alpha=.3)
    fig.suptitle("Rebalancing harvests the index's reversal; crypto's continuation is a different animal", fontsize=11)
    fig.tight_layout(); fig.savefig(OUTPUT_DIR / "figures" / "fig14_rebalancing.png", dpi=160)
    for k, r in res.items():
        print(f"\n== {k} {r['period']} ({r['sessions']} sessions)")
        for name, m in r["strategies"].items():
            print(f"  {name:75s} CAGR {m['cagr_pct']:6.2f}%  vol {m['vol_pct']:5.1f}%  Sharpe {m['sharpe']:5.2f}  maxDD {m['max_drawdown_pct']:6.1f}%  worst {m['worst_year']:14s} rebal {m['rebalances']:4d} turnover {m['turnover_total']}")
        for m in r["strategies"].values(): m.pop("_navs")
    (OUTPUT_DIR / "rebalancing.json").write_text(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
