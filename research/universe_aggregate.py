"""Cross-sectional summary of the deployed forecaster over the wider stock universe
(47 s00 names + the 4 core stocks): per-stock metrics, pooled tests, earnings-day
behaviour and shock categories; figure fig12."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR  # noqa: E402
from effectiveness_tests import newey_west_mean_test, pesaran_timmermann  # noqa: E402
from scheduled_events import earnings_reaction_days, to_sessions  # noqa: E402
from universe_run import key_for  # noqa: E402

FIG = OUTPUT_DIR / "figures"
CORE = {"aapl": "AAPL", "msft": "MSFT", "tsla": "TSLA", "nvda": "NVDA"}
MARKET_Z = 2.0


def market_z() -> pd.DataFrame:
    out = {}
    for sym in ("spy", "qqq"):
        c = pd.read_csv(OUTPUT_DIR / f"{sym}_yf_snapshot.csv", parse_dates=["date"]).set_index("date")["c"].astype(float)
        r = c.pct_change()
        out[f"{sym}_z"] = r / r.rolling(20).std(ddof=0).shift(1)
    return pd.DataFrame(out)


def per_stock(key: str, symbol: str, mz: pd.DataFrame) -> dict | None:
    fpath = OUTPUT_DIR / f"forecasts_{key}.csv"
    if not fpath.exists():
        return None
    fc = pd.read_csv(fpath, parse_dates=["origin"]).dropna(subset=["realized"])
    day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
    ev = pd.read_csv(OUTPUT_DIR / f"events_{key}.csv", parse_dates=["event_date"])
    h1 = fc[fc["horizon"] == 1]; h7 = fc[fc["horizon"] == 7]
    pt = pesaran_timmermann(h1["actual_up"].to_numpy(int), h1["pred_up"].to_numpy(int))
    nw = newey_west_mean_test((h1["prob_up"].to_numpy(float) - h1["actual_up"].to_numpy(float)) ** 2 - 0.25, lag=1)
    shock = h1["window_has_shock"].astype(bool)
    rec = {
        "symbol": symbol, "key": key, "origins": int(h1["pos"].nunique()), "first_origin": str(h1["origin"].min().date()),
        "h1_hit": float(h1["hit"].mean()), "h1_always_up": float(h1["actual_up"].mean()), "h1_pt": pt.get("statistic"),
        "h1_brier_minus_025": float(h1["brier"].mean() - 0.25), "h1_brier_nw_t": nw["t_stat"], "h1_coverage": float(h1["covered"].mean()),
        "h7_hit": float(h7["hit"].mean()), "h7_always_up": float(h7["actual_up"].mean()), "h7_coverage": float(h7["covered"].mean()),
        "hit_calm": float(h1.loc[~shock, "hit"].mean()), "hit_shock": float(h1.loc[shock, "hit"].mean()),
        "shock_share_pct": 100 * float(shock.mean()),
        "pre_event_h1_hit": float(ev["pre_h1_hit"].mean()), "pre_event_h1_coverage": float(ev["pre_h1_covered"].mean()),
        "consensus_aligned_pct": 100 * float(ev["consensus_already_aligned"].mean()),
        "consensus_latency_median": float(ev["consensus_latency_sessions"].dropna().median()) if ev["consensus_latency_sessions"].notna().any() else np.nan,
        "n_shocks": int(len(ev)), "continuation_7d_pct": float(ev["continuation_7d_pct"].mean()),
    }
    # earnings sessions
    try:
        earn = to_sessions(earnings_reaction_days(symbol, day.index), day.index)
    except Exception:
        earn = np.array([], dtype=int)
    if len(earn) > 8:
        is_e = h1["target_pos"].isin(earn)
        e, o = h1[is_e], h1[~is_e]
        rec.update({"earnings_sessions": int(is_e.sum()), "earnings_coverage": float(e["covered"].mean()), "other_coverage": float(o["covered"].mean()),
                    "earnings_abs_surprise": float(e["surprise_z"].abs().mean()), "other_abs_surprise": float(o["surprise_z"].abs().mean()),
                    "earnings_hit": float(e["hit"].mean()), "earnings_shock_share_pct": 100 * float((e["target_abs_z"] >= 2.5).mean())})
    # shock categories for increases
    up = ev[ev["direction"] == "up"].copy()
    earn_set = set(day.index[earn]) if len(earn) else set()
    cats = []
    for _, r in up.iterrows():
        d = r["event_date"]
        if d in earn_set:
            cats.append("earnings")
        else:
            sz = mz["spy_z"].get(d, np.nan); qz = mz["qqq_z"].get(d, np.nan)
            if any(np.isfinite(v) and abs(v) >= MARKET_Z and v > 0 for v in (sz, qz)):
                cats.append("market-wide")
            else:
                cats.append("idiosyncratic")
    up["category"] = cats
    for c in ("earnings", "market-wide", "idiosyncratic"):
        rec[f"up_{c}_share_pct"] = 100 * float((up["category"] == c).mean()) if len(up) else np.nan
    rec["up_shocks"] = int(len(up))
    return rec


def main() -> None:
    tickers = json.load(open(OUTPUT_DIR / "universe_tickers.json"))["tickers"]
    mz = market_z()
    rows = [per_stock(k, s, mz) for k, s in CORE.items()] + [per_stock(key_for(t), t, mz) for t in tickers]
    rows = [r for r in rows if r]
    table = pd.DataFrame(rows)
    table.to_csv(OUTPUT_DIR / "universe_cross_section.csv", index=False)
    # pooled tests
    pooled = []
    for r in rows:
        fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{r['key']}.csv").dropna(subset=["realized"])
        h1 = fc[fc["horizon"] == 1][["actual_up", "pred_up", "prob_up", "hit", "covered", "window_has_shock"]]
        h1["symbol"] = r["symbol"]; pooled.append(h1)
    pooled = pd.concat(pooled)
    pt_pool = pesaran_timmermann(pooled["actual_up"].to_numpy(int), pooled["pred_up"].to_numpy(int))
    pts = table["h1_pt"].dropna().to_numpy(float)
    summary = {
        "stocks": int(len(table)), "total_h1_forecasts": int(len(pooled)),
        "median_h1_hit": round(float(table["h1_hit"].median()), 4), "iqr_h1_hit": [round(float(table["h1_hit"].quantile(q)), 4) for q in (0.25, 0.75)],
        "median_h1_always_up": round(float(table["h1_always_up"].median()), 4),
        "pooled_h1_pt": pt_pool, "share_stocks_pt_above_1.645": round(float((pts > 1.645).mean()), 3), "share_stocks_pt_below_-1.645": round(float((pts < -1.645).mean()), 3),
        "mean_pt": round(float(pts.mean()), 3), "sd_pt": round(float(pts.std(ddof=1)), 3),
        "ks_pt_vs_standard_normal_p": round(float(stats.kstest(pts, "norm").pvalue), 4),
        "share_stocks_brier_worse_than_coin": round(float((table["h1_brier_minus_025"] > 0).mean()), 3),
        "share_stocks_brier_significantly_worse_5pct": round(float((table["h1_brier_nw_t"] > 1.96).mean()), 3),
        "median_h7_hit": round(float(table["h7_hit"].median()), 4), "median_h7_always_up": round(float(table["h7_always_up"].median()), 4),
        "share_stocks_always_up_beats_model_h7": round(float((table["h7_always_up"] > table["h7_hit"]).mean()), 3),
        "median_hit_calm": round(float(table["hit_calm"].median()), 4), "median_hit_shock": round(float(table["hit_shock"].median()), 4),
        "median_pre_event_hit": round(float(table["pre_event_h1_hit"].median()), 4),
        "median_consensus_aligned_pct": round(float(table["consensus_aligned_pct"].median()), 1),
        "median_consensus_latency": round(float(table["consensus_latency_median"].median()), 1),
        "median_continuation_7d_pct": round(float(table["continuation_7d_pct"].median()), 3),
        "share_stocks_positive_continuation_7d": round(float((table["continuation_7d_pct"] > 0).mean()), 3),
    }
    if "earnings_coverage" in table:
        e = table.dropna(subset=["earnings_coverage"])
        summary.update({"stocks_with_earnings_dates": int(len(e)),
                        "median_earnings_coverage": round(float(e["earnings_coverage"].median()), 3), "median_other_coverage": round(float(e["other_coverage"].median()), 3),
                        "median_earnings_abs_surprise": round(float(e["earnings_abs_surprise"].median()), 3), "median_other_abs_surprise": round(float(e["other_abs_surprise"].median()), 3),
                        "median_earnings_shock_share_pct": round(float(e["earnings_shock_share_pct"].median()), 1),
                        "share_stocks_earnings_coverage_below_other": round(float((e["earnings_coverage"] < e["other_coverage"]).mean()), 3),
                        "median_earnings_hit": round(float(e["earnings_hit"].median()), 3)})
    summary["median_up_shock_category_share_pct"] = {c: round(float(table[f"up_{c}_share_pct"].median()), 1) for c in ("earnings", "market-wide", "idiosyncratic")}
    (OUTPUT_DIR / "universe_cross_section.json").write_text(json.dumps(summary, indent=2, default=float))
    # figure
    FIG.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    ax = axes[0]; ax.hist(pts, bins=np.arange(-3.5, 3.6, 0.5), density=True, color="#B23A34", alpha=0.7, label=f"{len(pts)} stocks")
    xs = np.linspace(-3.5, 3.5, 200); ax.plot(xs, stats.norm.pdf(xs), "k--", lw=1, label="N(0,1): no skill")
    ax.axvline(1.645, color="grey", ls=":"); ax.set_title("h=1 Pesaran–Timmermann statistic across stocks"); ax.set_xlabel("PT statistic"); ax.legend(fontsize=8)
    ax = axes[1]; ax.scatter(table["h7_always_up"], table["h7_hit"], color="#B23A34", s=18)
    lim = [min(table["h7_hit"].min(), table["h7_always_up"].min()) - 0.02, max(table["h7_hit"].max(), table["h7_always_up"].max()) + 0.02]
    ax.plot(lim, lim, "k--", lw=1); ax.set_xlabel("always-up base rate, h=7"); ax.set_ylabel("model directional accuracy, h=7"); ax.set_title("Base rate vs model, seven sessions")
    ax = axes[2]
    if "earnings_coverage" in table:
        e = table.dropna(subset=["earnings_coverage"]).sort_values("earnings_coverage")
        ax.scatter(e["other_coverage"], e["earnings_coverage"], color="#B23A34", s=18)
        ax.axhline(0.8, color="grey", ls=":"); ax.axvline(0.8, color="grey", ls=":"); ax.plot([0, 1], [0, 1], "k--", lw=1)
        ax.set_xlim(0.6, 0.9); ax.set_ylim(0, 0.9); ax.set_xlabel("10–90 coverage, other sessions"); ax.set_ylabel("10–90 coverage, earnings sessions"); ax.set_title("Interval coverage on earnings sessions")
    fig.suptitle(f"Deployed forecaster across {len(table)} S&P 500 stocks", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(FIG / "fig12_universe_cross_section.png", dpi=160); plt.close(fig)
    print(json.dumps(summary, indent=1, default=float))
    with pd.option_context("display.width", 250, "display.max_columns", 30, "display.float_format", "{:.3f}".format):
        print(table[["symbol", "origins", "h1_hit", "h1_always_up", "h1_pt", "h1_brier_nw_t", "h7_hit", "h7_always_up", "hit_calm", "hit_shock", "pre_event_h1_hit",
                     "consensus_aligned_pct", "continuation_7d_pct"] + (["earnings_coverage", "other_coverage", "earnings_abs_surprise"] if "earnings_coverage" in table else [])].to_string(index=False))


if __name__ == "__main__":
    main()
