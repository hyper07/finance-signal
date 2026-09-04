"""Effectiveness of daily actions: how often should the user act on the forecast?

The published payload is a seven-session exposure schedule.  We simulate four
ways of using it, all point-in-time (the forecast used on day t was built from
data through t) and all charged ONE_WAY_COST_BPS per unit of turnover:

  hold          buy-and-hold the long leg (100% exposure)
  act_daily     every session set exposure to that day's fresh h=1 target
  act_weekly    at t commit to the 7-row schedule and follow it for 7 sessions
                without re-forecasting, then re-plan
  act_once_hold set exposure to the h=1 target at t and change nothing for 7
                sessions ("I did nothing after the first day")
  signal_3day   the deployed 3-day Long/Hold/Short signal, for reference

Negative exposure (inverse-ETF datasets) earns the actual inverse leg's return
(BITI / SPXS) from the reproduced frame, as production does.  Cash mode floors
exposure at zero.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR  # noqa: E402
from event_study import DATASETS  # noqa: E402

COST_BPS = 5.0
FIG = OUTPUT_DIR / "figures"
PER_YEAR = {"crypto": 365.25}


def load(key: str):
    spec = DATASETS[key]
    frame = pd.read_pickle(OUTPUT_DIR / spec["pickle"])
    frame.index = pd.to_datetime(frame.index).normalize()
    fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{key}.csv", parse_dates=["origin"])
    org = pd.read_csv(OUTPUT_DIR / f"origins_{key}.csv", parse_dates=["origin"]).set_index("origin")
    return spec, frame, fc, org


def exposure_paths(frame: pd.DataFrame, fc: pd.DataFrame, org: pd.DataFrame, lower: float) -> pd.DataFrame:
    """Exposure held DURING session i (decided at the close of i-1), per policy."""
    n = len(frame)
    idx = frame.index
    pos_of = {d: i for i, d in enumerate(idx)}
    targets = fc.pivot(index="origin", columns="horizon", values="target_pct") / 100.0
    first_pos = min(pos_of[d] for d in targets.index)

    daily = pd.Series(np.nan, index=idx)
    weekly = pd.Series(np.nan, index=idx)
    once = pd.Series(np.nan, index=idx)
    for origin, row in targets.iterrows():
        p = pos_of[origin]
        if p + 1 < n:
            daily.iloc[p + 1] = row[1]
    # weekly / once: re-plan every 7 sessions starting at the first origin
    for p in range(first_pos, n - 1, 7):
        origin = idx[p]
        if origin not in targets.index:
            continue
        row = targets.loc[origin]
        for h in range(1, 8):
            if p + h < n:
                weekly.iloc[p + h] = row[h]
                once.iloc[p + h] = row[1]
    signal = frame["strategy_signal"].shift(1).clip(lower=lower, upper=1.0)
    paths = pd.DataFrame({"hold": 1.0, "act_daily": daily, "act_weekly": weekly, "act_once_hold": once,
                          "signal_3day": signal}, index=idx)
    paths = paths.iloc[first_pos + 1:]
    return paths.ffill().fillna(0.0).clip(lower=lower, upper=1.0)


def metrics(exposure: pd.Series, long_ret: pd.Series, short_ret: pd.Series, per_year: float) -> dict:
    e = exposure.to_numpy(float)
    gross = np.where(e >= 0, e * long_ret.to_numpy(float), (-e) * short_ret.to_numpy(float))
    turnover = np.abs(np.diff(np.r_[0.0, e]))
    net = gross - turnover * COST_BPS / 1e4
    nav = np.cumprod(1 + net)
    dd = nav / np.maximum.accumulate(nav) - 1
    years = len(net) / per_year
    ann = nav[-1] ** (1 / years) - 1 if years > 0 else np.nan
    vol = net.std(ddof=1) * np.sqrt(per_year)
    return {
        "sessions": int(len(net)),
        "total_return_pct": round(float((nav[-1] - 1) * 100), 2),
        "annualised_return_pct": round(float(ann * 100), 2),
        "annualised_vol_pct": round(float(vol * 100), 2),
        "sharpe": round(float(net.mean() * per_year / vol), 3) if vol > 0 else None,
        "max_drawdown_pct": round(float(dd.min() * 100), 2),
        "turnover_per_year": round(float(turnover.sum() / years), 2),
        "fee_drag_pct_total": round(float((np.prod(1 + gross) - nav[-1]) * 100), 2),
        "mean_exposure": round(float(e.mean()), 3),
    }


def run(key: str) -> dict:
    spec, frame, fc, org = load(key)
    lower = -1.0 if spec["short_mode"] == "inverse_etf" else 0.0
    per_year = PER_YEAR.get(spec["asset_type"], 252.0)
    paths = exposure_paths(frame, fc, org, lower)
    long_ret = frame["daily_ret"].reindex(paths.index).fillna(0.0)
    short_ret = frame.get("daily_ret_short", pd.Series(0.0, index=frame.index)).reindex(paths.index).fillna(0.0)
    if spec["short_mode"] != "inverse_etf":
        short_ret = pd.Series(0.0, index=paths.index)
    out = {"dataset": spec["label"], "asset_type": spec["asset_type"], "short_mode": spec["short_mode"],
           "period": f"{paths.index.min().date()} → {paths.index.max().date()}", "cost_bps_one_way": COST_BPS,
           "policies": {}, "policies_2026": {}, "policies_shock_windows": {}}
    day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
    shock_pos = np.flatnonzero(day["shock_z"].to_numpy())
    in_window = np.zeros(len(day), dtype=bool)
    for p in shock_pos:
        in_window[max(0, p - 1): p + 8] = True
    window_mask = pd.Series(in_window, index=day.index).reindex(paths.index).fillna(False).to_numpy(bool)
    for name in paths.columns:
        out["policies"][name] = metrics(paths[name], long_ret, short_ret, per_year)
        m26 = paths.index >= "2026-01-01"
        out["policies_2026"][name] = metrics(paths[name][m26], long_ret[m26], short_ret[m26], per_year)
        # shock windows: sessions T-1..T+7 around each shock, concatenated
        out["policies_shock_windows"][name] = metrics(paths[name][window_mask], long_ret[window_mask], short_ret[window_mask], per_year)
    # how different are the actions? share of sessions where daily re-forecast differs from the committed schedule
    diff = (paths["act_daily"] - paths["act_weekly"]).abs()
    out["daily_vs_weekly_mean_abs_exposure_gap"] = round(float(diff.mean()), 3)
    out["daily_vs_weekly_share_sessions_differ_ge_25pts"] = round(float((diff >= 0.25).mean()), 3)
    # NAV series for the figure
    navs = {}
    for name in paths.columns:
        e = paths[name].to_numpy(float)
        gross = np.where(e >= 0, e * long_ret.to_numpy(float), (-e) * short_ret.to_numpy(float))
        turnover = np.abs(np.diff(np.r_[0.0, e]))
        navs[name] = np.cumprod(1 + gross - turnover * COST_BPS / 1e4)
    pd.DataFrame(navs, index=paths.index).to_csv(OUTPUT_DIR / f"policy_nav_{key}.csv")
    return out


def figure(keys: list[str]) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    keys = [k for k in keys if (OUTPUT_DIR / f"policy_nav_{k}.csv").exists()]
    fig, axes = plt.subplots(1, len(keys), figsize=(4.2 * len(keys), 3.8), squeeze=False)
    styles = {"hold": ("black", "-"), "act_daily": ("#1F5F8B", "-"), "act_weekly": ("#B7791F", "-"),
              "act_once_hold": ("#B23A34", "--"), "signal_3day": ("grey", ":")}
    for ax, key in zip(axes[0], keys):
        nav = pd.read_csv(OUTPUT_DIR / f"policy_nav_{key}.csv", index_col=0, parse_dates=True)
        nav = nav.loc["2026-01-01":]
        nav = nav / nav.iloc[0]
        for col in nav.columns:
            c, ls = styles[col]
            ax.plot(nav.index, nav[col], color=c, ls=ls, lw=1.4, label=col)
        ax.set_title(f"{DATASETS[key]['symbol']}: 2026, NAV from Jan 2", fontsize=10)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.axvspan(pd.Timestamp("2026-08-18 12:00"), pd.Timestamp("2026-08-21 12:00"), color="orange", alpha=0.15)
    axes[0][0].legend(fontsize=7)
    fig.suptitle("Acting on the forecast: every day vs. once a week vs. once-and-hold (5 bp per unit turnover)", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG / "fig11_action_policies_2026.png", dpi=160)
    plt.close(fig)


def main() -> None:
    keys = sys.argv[1:] or [k for k in DATASETS if (OUTPUT_DIR / f"forecasts_{k}.csv").exists()]
    result = {k: run(k) for k in keys}
    (OUTPUT_DIR / "action_policies.json").write_text(json.dumps(result, indent=2))
    figure(["bito", "spxl", "aapl", "nvda"])
    for k, r in result.items():
        print(f"\n== {k}: {r['dataset']}  {r['period']}  (daily vs weekly gap {r['daily_vs_weekly_mean_abs_exposure_gap']}, differ>=25pts on {r['daily_vs_weekly_share_sessions_differ_ge_25pts']:.0%} of sessions)")
        for scope in ("policies", "policies_2026", "policies_shock_windows"):
            print(f"  -- {scope}")
            for name, m in r[scope].items():
                print(f"     {name:14s} total={m['total_return_pct']:+8.2f}%  ann={m['annualised_return_pct']:+7.2f}%  vol={m['annualised_vol_pct']:6.2f}%  sharpe={m['sharpe']}  maxDD={m['max_drawdown_pct']:7.2f}%  turnover/yr={m['turnover_per_year']:6.2f}  exp={m['mean_exposure']:+.2f}")


if __name__ == "__main__":
    main()
