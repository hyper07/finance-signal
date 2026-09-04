"""Asset-type fingerprints: why one voter set cannot serve coin, index and stocks.

For each instrument we compute return-process diagnostics that a forecaster's
design must respond to (jump frequency, tail weight, autocorrelation, volatility
clustering, variance ratio, post-shock continuation, news sensitivity under the
type's own news profile) and, where the rolling-origin study exists, the deployed
analog forecaster's calibration on that instrument.

Outputs: asset_types.csv / asset_types.json and figures fig9, fig10.
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
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR, load_btc_daily, load_equity_daily, load_stock_snapshot  # noqa: E402
from event_study import DATASETS, NEWS_COVERAGE_START, Z_SHOCK, align_news, news_counts  # noqa: E402
from effectiveness_tests import pesaran_timmermann  # noqa: E402

FIG = OUTPUT_DIR / "figures"

INSTRUMENTS = [
    # name, source, symbol, asset type, news profile, study key (None = no forecaster run)
    ("BTC/USD", "crypto", "BTC/USD", "crypto", "crypto", "btc"),
    ("BITO", "equity", "BITO", "crypto", "crypto", "bito"),
    ("SPY", "equity", "SPY", "index", "index", "spy"),
    ("SPXL", "equity", "SPXL", "index", "index", "spxl"),
    ("QQQ", "equity", "QQQ", "index", "index", None),
    ("TLT", "equity", "TLT", "bond", "index", None),
    ("GLD", "equity", "GLD", "commodity", "index", None),
    ("AAPL", "stock", "AAPL", "stock", "stock:AAPL", "aapl"),
    ("MSFT", "stock", "MSFT", "stock", "stock:MSFT", "msft"),
    ("TSLA", "stock", "TSLA", "stock", "stock:TSLA", "tsla"),
    ("NVDA", "stock", "NVDA", "stock", "stock:NVDA", "nvda"),
]
TYPE_COLOR = {"crypto": "#B7791F", "index": "#1F5F8B", "stock": "#B23A34", "bond": "#5A6472", "commodity": "#7A6A3A"}


def closes(source: str, symbol: str) -> pd.Series:
    if source == "crypto":
        frame = load_btc_daily()
    elif source == "equity":
        frame = load_equity_daily(adjusted=True)
    else:
        frame = load_stock_snapshot()
    sub = frame.loc[frame["symbol"] == symbol].sort_values("date")
    series = pd.Series(sub["c"].to_numpy(float), index=pd.DatetimeIndex(sub["date"]))
    return series.loc["2016-01-01":]


def variance_ratio(r: pd.Series, q: int = 5) -> float:
    r = r.dropna()
    var1 = r.var(ddof=1)
    rq = r.rolling(q).sum().dropna()
    return float(rq.var(ddof=1) / (q * var1))


def fingerprint(name: str, source: str, symbol: str, asset_type: str, profile: str, key: str | None,
                counts: pd.Series) -> dict:
    c = closes(source, symbol)
    r = c.pct_change()
    vol20 = r.rolling(20).std(ddof=0).shift(1)
    z = r / vol20
    shock = z.abs() >= Z_SHOCK
    news = align_news(counts, c.index)
    ratio = (news + 1.0) / (news.rolling(30, min_periods=10).median().shift(1) + 1.0)
    ratio[c.index < NEWS_COVERAGE_START] = np.nan
    covered = ratio.notna()
    per_year = 365.25 if source == "crypto" else 252.0
    rec = {
        "instrument": name, "asset_type": asset_type, "news_profile": profile, "sessions": int(r.notna().sum()),
        "span": f"{c.index.min().date()} → {c.index.max().date()}",
        "trades_weekends": bool(source == "crypto"),
        "annualised_vol_pct": round(float(r.std(ddof=1) * np.sqrt(per_year) * 100), 1),
        "excess_kurtosis": round(float(stats.kurtosis(r.dropna(), fisher=True)), 2),
        "skew": round(float(stats.skew(r.dropna())), 2),
        "shock_days_per_year": round(float(shock.sum() / (r.notna().sum() / per_year)), 2),
        "shock_share_pct": round(float(shock.mean() * 100), 2),
        "lag1_autocorr_ret": round(float(r.autocorr(1)), 3),
        "lag1_autocorr_abs_ret": round(float(r.abs().autocorr(1)), 3),
        "variance_ratio_5d": round(variance_ratio(r, 5), 3),
        "shock_up_share_pct": round(float((r[shock] > 0).mean() * 100), 1),
    }
    # post-shock sign-adjusted continuation
    pos = np.flatnonzero(shock.to_numpy())
    cl = c.to_numpy(float); sg = np.sign(r.to_numpy(float))
    for k in (1, 3, 7):
        vals = [sg[p] * (cl[p + k] / cl[p] - 1) * 100 for p in pos if p + k < len(cl)]
        vals = np.array(vals)
        t, pval = stats.ttest_1samp(vals, 0.0) if len(vals) > 4 else (np.nan, np.nan)
        rec[f"continuation_{k}d_pct"] = round(float(vals.mean()), 3) if len(vals) else None
        rec[f"continuation_{k}d_t"] = round(float(t), 2) if len(vals) > 4 else None
        rec[f"continuation_{k}d_n"] = int(len(vals))
    # shock clustering: share of shocks followed by another within 3 sessions
    if len(pos) > 1:
        gaps = np.diff(pos)
        rec["shock_cluster_share_pct"] = round(float((gaps <= 3).mean() * 100), 1)
    # news sensitivity (type-specific profile)
    if covered.sum() > 100:
        rc = r[covered]; rt = ratio[covered]
        spike = rt >= 2.0
        rec["news_days_covered"] = int(covered.sum())
        rec["news_spike_days"] = int(spike.sum())
        rec["abs_ret_on_spike_vs_quiet_ratio"] = round(float(rc[spike].abs().mean() / rc[~spike].abs().mean()), 2) if spike.sum() > 3 else None
        rec["shock_share_on_spike_days_pct"] = round(float(shock[covered][spike].mean() * 100), 1) if spike.sum() > 3 else None
        rec["shock_share_on_quiet_days_pct"] = round(float(shock[covered][~spike].mean() * 100), 1)
        rho, p = stats.spearmanr(rt, rc.abs())
        rec["spearman_news_ratio_vs_abs_ret"] = [round(float(rho), 3), round(float(p), 4)]
    # deployed forecaster on this instrument (from the rolling-origin study)
    if key is not None and (OUTPUT_DIR / f"forecasts_{key}.csv").exists():
        fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{key}.csv")
        h1 = fc[fc["horizon"] == 1]
        pt = pesaran_timmermann(h1["actual_up"].to_numpy(int), h1["pred_up"].to_numpy(int))
        rec["forecaster_origins"] = int(h1["pos"].nunique())
        rec["forecaster_h1_hit"] = round(float(h1["hit"].mean()), 3)
        rec["forecaster_h1_pt"] = pt.get("statistic")
        rec["forecaster_h1_brier_minus_025"] = round(float(h1["brier"].mean() - 0.25), 4)
        rec["forecaster_h1_coverage"] = round(float(h1["covered"].mean()), 3)
        rec["forecaster_h1_hit_on_shock_sessions"] = round(float(h1.loc[h1["window_has_shock"], "hit"].mean()), 3)
        rec["forecaster_h1_hit_on_calm_sessions"] = round(float(h1.loc[~h1["window_has_shock"], "hit"].mean()), 3)
        rec["forecaster_h7_hit"] = round(float(fc.loc[fc["horizon"] == 7, "hit"].mean()), 3)
        rec["forecaster_h7_coverage"] = round(float(fc.loc[fc["horizon"] == 7, "covered"].mean()), 3)
        spike_h1 = h1[h1["target_news_ratio"] >= 2.0]
        rec["forecaster_h1_hit_on_news_spike_days"] = round(float(spike_h1["hit"].mean()), 3) if len(spike_h1) > 5 else None
        rec["forecaster_h1_news_spike_n"] = int(len(spike_h1))
        ev_path = OUTPUT_DIR / f"events_{key}.csv"
        if ev_path.exists():
            ev = pd.read_csv(ev_path)
            rec["consensus_aligned_before_shock_pct"] = round(float(ev["consensus_already_aligned"].mean() * 100), 1)
            rec["consensus_latency_median"] = (float(ev["consensus_latency_sessions"].dropna().median())
                                               if ev["consensus_latency_sessions"].notna().any() else None)
    return rec


def figures(table: pd.DataFrame) -> None:
    FIG.mkdir(parents=True, exist_ok=True)

    def panel_grid(metrics, fname, title):
        fig, axes = plt.subplots(1, len(metrics), figsize=(4.4 * len(metrics), 4.2))
        for ax, (col, ttl, ref) in zip(np.atleast_1d(axes), metrics):
            sub = table.dropna(subset=[col])
            ax.barh(sub["instrument"], sub[col], color=[TYPE_COLOR[t] for t in sub["asset_type"]])
            ax.set_title(ttl, fontsize=10); ax.invert_yaxis(); ax.tick_params(labelsize=8)
            if ref is not None:
                ax.axvline(ref, color="grey", ls="--", lw=1)
        handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in TYPE_COLOR.values()]
        fig.legend(handles, list(TYPE_COLOR.keys()), loc="lower center", ncol=5, fontsize=9, frameon=False)
        fig.suptitle(title, fontsize=12)
        fig.tight_layout(rect=(0, 0.07, 1, 0.94))
        fig.savefig(FIG / fname, dpi=160)
        plt.close(fig)

    # fig9a: the return process itself
    panel_grid([("shock_days_per_year", "shock days per year (|z| ≥ 2.5)", None),
                ("excess_kurtosis", "excess kurtosis of daily returns", None),
                ("variance_ratio_5d", "5-day variance ratio (1 = random walk)", 1.0)],
               "fig9a_return_process_by_type.png", "Return-process fingerprints by asset type")
    # fig9b: news response and the deployed forecaster
    panel_grid([("continuation_7d_pct", "post-shock continuation, 7 sessions (%)", 0.0),
                ("abs_ret_on_spike_vs_quiet_ratio", "|return| on own-news spike days ÷ quiet days", 1.0),
                ("forecaster_h1_hit_on_shock_sessions", "deployed forecaster: h=1 accuracy on shock sessions", 0.5)],
               "fig9b_news_response_by_type.png", "News response and forecaster behaviour by asset type")
    # fig10: post-shock continuation curves by instrument
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for _, row in table.iterrows():
        ys = [row.get("continuation_1d_pct"), row.get("continuation_3d_pct"), row.get("continuation_7d_pct")]
        if any(pd.isna(ys)):
            continue
        ax.plot([1, 3, 7], ys, marker="o", color=TYPE_COLOR[row["asset_type"]], alpha=0.85, label=f"{row['instrument']} ({row['asset_type']})")
    ax.axhline(0, color="grey", lw=1)
    ax.set_xlabel("sessions after the shock close"); ax.set_ylabel("sign-adjusted return, % (mean)")
    ax.set_title("After a |z| ≥ 2.5 shock: crypto continues, index and single stocks do not")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout(); fig.savefig(FIG / "fig10_post_shock_by_type.png", dpi=160); plt.close(fig)


def main() -> None:
    counts_cache: dict[str, pd.Series] = {}
    rows = []
    for name, source, symbol, asset_type, profile, key in INSTRUMENTS:
        if profile not in counts_cache:
            counts_cache[profile] = news_counts(profile)
        rows.append(fingerprint(name, source, symbol, asset_type, profile, key, counts_cache[profile]))
        print("done", name)
    table = pd.DataFrame(rows)
    table.to_csv(OUTPUT_DIR / "asset_types.csv", index=False)
    (OUTPUT_DIR / "asset_types.json").write_text(json.dumps(rows, indent=2, default=str))
    figures(table)
    show = ["instrument", "asset_type", "annualised_vol_pct", "excess_kurtosis", "shock_days_per_year", "lag1_autocorr_ret",
            "variance_ratio_5d", "continuation_3d_pct", "continuation_7d_pct", "continuation_7d_t", "shock_cluster_share_pct",
            "abs_ret_on_spike_vs_quiet_ratio", "shock_share_on_spike_days_pct", "shock_share_on_quiet_days_pct",
            "forecaster_h1_hit", "forecaster_h1_pt", "forecaster_h1_coverage", "forecaster_h1_hit_on_shock_sessions",
            "forecaster_h1_hit_on_news_spike_days", "consensus_aligned_before_shock_pct", "consensus_latency_median"]
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(table[[c for c in show if c in table]].to_string(index=False))


if __name__ == "__main__":
    main()
