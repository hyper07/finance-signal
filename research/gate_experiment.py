"""Constructive out-of-sample test: does a type-specific gate improve the
predictive distribution?

Gates are causal (known at the origin close) and use the thresholds fixed in
Section 3 before any scoring:

  calendar   the target session is a scheduled event: FOMC decision or payroll
             release (index), earnings reaction session (stocks); none for crypto
  headline   the previous session's own-news headline ratio nu_{t-1} >= 2
  shock      the origin session itself was a |z| >= 2.5 move

Variants scored on every (origin, horizon):
  model        the deployed analog forecast as published
  climatology  trailing 250-window empirical quantiles of the h-step return and
               the trailing base rate P(up) -- the honest "I do not know"
  gated        model, except climatology on gated forecasts
  gated+drift  gated, and on shock-gated forecasts the climatology quantiles are
               shifted by the trailing mean sign-adjusted post-shock continuation
               (walk-forward, >= 10 prior shocks) -- the human-reaction kernel
               estimated from the past only

Scores: Brier (P(up)), 10-90 coverage, Winkler interval score (alpha = 0.2),
mean pinball loss at 0.1/0.5/0.9. Held-out window: origins >= 2025-01-01.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR  # noqa: E402
from event_study import DATASETS, align_news, block_bootstrap_diff, news_counts  # noqa: E402
from scheduled_events import FOMC_DECISION_DAYS, earnings_reaction_days, payroll_days, to_sessions  # noqa: E402

ALPHA = 0.2
CLIM_WINDOW = 250
HOLDOUT_START = pd.Timestamp("2025-01-01")
NEWS_COVERAGE_START = pd.Timestamp("2024-02-01")


def winkler(l: np.ndarray, u: np.ndarray, y: np.ndarray) -> np.ndarray:
    return (u - l) + (2 / ALPHA) * np.where(y < l, l - y, 0.0) + (2 / ALPHA) * np.where(y > u, y - u, 0.0)


def pinball(q10: np.ndarray, q50: np.ndarray, q90: np.ndarray, y: np.ndarray) -> np.ndarray:
    out = np.zeros_like(y, dtype=float)
    for tau, q in ((0.1, q10), (0.5, q50), (0.9, q90)):
        d = y - q
        out += np.maximum(tau * d, (tau - 1) * d)
    return out / 3.0


def climatology(close: np.ndarray, horizon: int) -> pd.DataFrame:
    """Trailing empirical quantiles / base rate of the h-step return, observable by origin p."""
    n = len(close)
    rh = np.full(n, np.nan)
    rh[: n - horizon] = close[horizon:] / close[:-horizon] - 1.0
    s = pd.Series(rh)
    roll = s.rolling(CLIM_WINDOW, min_periods=60)
    q10, q50, q90, up = roll.quantile(0.1), roll.quantile(0.5), roll.quantile(0.9), roll.apply(lambda x: np.mean(x > 0), raw=True)
    # value at index i covers windows i-249..i; origin p may use i = p - horizon
    out = pd.DataFrame({"c_q10": q10.shift(horizon), "c_q50": q50.shift(horizon), "c_q90": q90.shift(horizon), "c_up": up.shift(horizon)})
    return out


def trailing_drift(close: np.ndarray, z: np.ndarray, horizon: int) -> np.ndarray:
    """Walk-forward mean sign-adjusted continuation after prior |z|>=2.5 shocks, for each origin."""
    n = len(close)
    shocks = np.flatnonzero(np.abs(np.nan_to_num(z)) >= 2.5)
    cont = {s: np.sign(close[s] - close[s - 1]) * (close[s + horizon] / close[s] - 1.0) for s in shocks if s + horizon < n and s >= 1}
    drift = np.zeros(n)
    hist: list[float] = []
    ptr = 0
    ordered = sorted(cont.items())
    for p in range(n):
        while ptr < len(ordered) and ordered[ptr][0] + horizon <= p:   # continuation fully observed by p
            hist.append(ordered[ptr][1]); ptr += 1
        drift[p] = float(np.mean(hist)) if len(hist) >= 10 else 0.0
    return drift


def event_conditional(close: np.ndarray, sessions: np.ndarray, horizon: int, min_events: int = 8) -> pd.DataFrame:
    """Walk-forward empirical quantiles / base rate of the h-step return whose TARGET is a
    past session of the same type (e.g. earnings or FOMC sessions), observable by origin p."""
    n = len(close)
    rows = {"e_q10": np.full(n, np.nan), "e_q50": np.full(n, np.nan), "e_q90": np.full(n, np.nan), "e_up": np.full(n, np.nan)}
    ordered = sorted(int(c) for c in sessions if c - horizon >= 0)
    vals: list[float] = []
    ptr = 0
    for p in range(n):
        while ptr < len(ordered) and ordered[ptr] <= p:           # target session observed by p
            c = ordered[ptr]; vals.append(close[c] / close[c - horizon] - 1.0); ptr += 1
        if len(vals) >= min_events:
            a = np.asarray(vals)
            rows["e_q10"][p], rows["e_q50"][p], rows["e_q90"][p], rows["e_up"][p] = np.quantile(a, 0.1), np.quantile(a, 0.5), np.quantile(a, 0.9), float(np.mean(a > 0))
    return pd.DataFrame(rows)


def post_shock_conditional(close: np.ndarray, z: np.ndarray, horizon: int, min_events: int = 10) -> pd.DataFrame:
    """Walk-forward quantiles of the sign-adjusted h-step continuation after prior |z|>=2.5 shocks."""
    n = len(close)
    rows = {"s_q10": np.full(n, np.nan), "s_q50": np.full(n, np.nan), "s_q90": np.full(n, np.nan), "s_up": np.full(n, np.nan)}
    shocks = [int(s) for s in np.flatnonzero(np.abs(np.nan_to_num(z)) >= 2.5) if s >= 1 and s + horizon < n]
    vals: list[float] = []
    ptr = 0
    for p in range(n):
        while ptr < len(shocks) and shocks[ptr] + horizon <= p:
            s_ = shocks[ptr]; vals.append(np.sign(close[s_] - close[s_ - 1]) * (close[s_ + horizon] / close[s_] - 1.0)); ptr += 1
        if len(vals) >= min_events:
            a = np.asarray(vals)
            rows["s_q10"][p], rows["s_q50"][p], rows["s_q90"][p], rows["s_up"][p] = np.quantile(a, 0.1), np.quantile(a, 0.5), np.quantile(a, 0.9), float(np.mean(a > 0))
    return pd.DataFrame(rows)


def scores(q10, q50, q90, pup, y) -> dict:
    up = (y > 0).astype(float)
    return {"brier": float(np.mean((pup - up) ** 2)), "coverage": float(np.mean((y >= q10) & (y <= q90))),
            "winkler": float(np.mean(winkler(q10, q90, y))), "pinball": float(np.mean(pinball(q10, q50, q90, y))), "n": int(len(y))}


_LAST_ARRAYS: dict = {}


def run(key: str, spec: dict | None = None) -> dict:
    spec = spec or DATASETS[key]
    fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{key}.csv", parse_dates=["origin"]).dropna(subset=["realized"])
    day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
    close = day["close"].to_numpy(float); z = day["z"].to_numpy(float); idx = day.index
    # causal headline ratio at origin-1
    counts = news_counts(spec["news"])
    news = align_news(counts, idx)
    ratio = (news + 1.0) / (news.rolling(30, min_periods=10).median().shift(1) + 1.0)
    ratio[idx < NEWS_COVERAGE_START] = np.nan
    ratio_prev = ratio.shift(1).to_numpy(float)
    # calendar sessions
    cal = np.zeros(len(idx), dtype=bool)
    if spec["asset_type"] == "index":
        cal[to_sessions(pd.to_datetime(FOMC_DECISION_DAYS), idx)] = True
        cal[to_sessions(payroll_days(str(idx.min().date()), str(idx.max().date())), idx)] = True
    elif spec["asset_type"] == "stock":
        try:
            cal[to_sessions(earnings_reaction_days(spec["symbol"], idx), idx)] = True
        except Exception:
            pass
    pos = fc["pos"].to_numpy(int); tpos = fc["target_pos"].to_numpy(int); h = fc["horizon"].to_numpy(int)
    y = fc["realized"].to_numpy(float)
    m_q10, m_q50, m_q90, m_up = fc["p10"].to_numpy(float), fc["p50"].to_numpy(float), fc["p90"].to_numpy(float), fc["prob_up"].to_numpy(float)
    c_q10 = np.full(len(fc), np.nan); c_q50 = c_q10.copy(); c_q90 = c_q10.copy(); c_up = c_q10.copy(); drift = np.zeros(len(fc))
    e_q10 = c_q10.copy(); e_q50 = c_q10.copy(); e_q90 = c_q10.copy(); e_up = c_q10.copy()
    s_q10 = c_q10.copy(); s_q50 = c_q10.copy(); s_q90 = c_q10.copy(); s_up = c_q10.copy()
    cal_sessions = np.flatnonzero(cal)
    for hh in range(1, 8):
        m = h == hh
        clim = climatology(close, hh)
        c_q10[m] = clim["c_q10"].to_numpy()[pos[m]]; c_q50[m] = clim["c_q50"].to_numpy()[pos[m]]
        c_q90[m] = clim["c_q90"].to_numpy()[pos[m]]; c_up[m] = clim["c_up"].to_numpy()[pos[m]]
        drift[m] = trailing_drift(close, z, hh)[pos[m]] * np.sign(np.nan_to_num(z[pos[m]]))
        if len(cal_sessions):
            ec = event_conditional(close, cal_sessions, hh)
            e_q10[m] = ec["e_q10"].to_numpy()[pos[m]]; e_q50[m] = ec["e_q50"].to_numpy()[pos[m]]
            e_q90[m] = ec["e_q90"].to_numpy()[pos[m]]; e_up[m] = ec["e_up"].to_numpy()[pos[m]]
        ps = post_shock_conditional(close, z, hh)
        sgn = np.sign(np.nan_to_num(z[pos[m]]))
        lo, mid, hi = ps["s_q10"].to_numpy()[pos[m]], ps["s_q50"].to_numpy()[pos[m]], ps["s_q90"].to_numpy()[pos[m]]
        # sign-adjusted distribution mapped back to the direction of the origin shock
        s_q10[m] = np.where(sgn >= 0, lo, -hi); s_q90[m] = np.where(sgn >= 0, hi, -lo); s_q50[m] = sgn * mid
        s_up[m] = np.where(sgn >= 0, ps["s_up"].to_numpy()[pos[m]], 1.0 - ps["s_up"].to_numpy()[pos[m]])
    ok = np.isfinite(c_q10) & np.isfinite(c_up)
    g_cal = cal[tpos]; g_news = np.nan_to_num(ratio_prev[pos]) >= 2.0; g_shock = np.abs(np.nan_to_num(z[pos])) >= 2.5
    gate = g_cal | g_news | g_shock
    # gated forecasts
    def gated(q10, q50, q90, up, mask, shift=None):
        gq10, gq50, gq90, gup = m_q10.copy(), m_q50.copy(), m_q90.copy(), m_up.copy()
        gq10[mask], gq50[mask], gq90[mask], gup[mask] = q10[mask], q50[mask], q90[mask], up[mask]
        if shift is not None:
            sm = mask & g_shock
            gq10[sm] += shift[sm]; gq50[sm] += shift[sm]; gq90[sm] += shift[sm]
            gup[sm] = np.clip(gup[sm] + np.sign(shift[sm]) * 0.1, 0.05, 0.95)
        return gq10, gq50, gq90, gup
    # event-conditional replacement: calendar -> same-type past sessions; shock -> post-shock distribution;
    # headline-only gates and any gate lacking enough history -> climatology
    ev_q10, ev_q50, ev_q90, ev_up = c_q10.copy(), c_q50.copy(), c_q90.copy(), c_up.copy()
    use_e = g_cal & np.isfinite(e_q10)
    ev_q10[use_e], ev_q50[use_e], ev_q90[use_e], ev_up[use_e] = e_q10[use_e], e_q50[use_e], e_q90[use_e], e_up[use_e]
    use_s = g_shock & ~use_e & np.isfinite(s_q10)
    ev_q10[use_s], ev_q50[use_s], ev_q90[use_s], ev_up[use_s] = s_q10[use_s], s_q50[use_s], s_q90[use_s], s_up[use_s]
    variants = {
        "model": (m_q10, m_q50, m_q90, m_up),
        "climatology": (c_q10, c_q50, c_q90, c_up),
        "gated_event_conditional": gated(ev_q10, ev_q50, ev_q90, ev_up, gate),
        "gated": gated(c_q10, c_q50, c_q90, c_up, gate),
        "gated_calendar_only": gated(c_q10, c_q50, c_q90, c_up, g_cal),
        "gated_headline_only": gated(c_q10, c_q50, c_q90, c_up, g_news),
        "gated_shock_only": gated(c_q10, c_q50, c_q90, c_up, g_shock),
        "gated_drift": gated(c_q10, c_q50, c_q90, c_up, gate, shift=drift),
    }
    origin = fc["origin"].to_numpy()
    _LAST_ARRAYS.clear()
    _LAST_ARRAYS.update({"ok": ok, "g_cal": g_cal, "g_news": g_news, "g_shock": g_shock, "y": y,
                         "wm": winkler(m_q10, m_q90, y), "we": winkler(variants["gated_event_conditional"][0], variants["gated_event_conditional"][2], y),
                         "bm": (m_up - (y > 0)) ** 2, "be": (variants["gated_event_conditional"][3] - (y > 0)) ** 2,
                         "cm": ((y >= m_q10) & (y <= m_q90)).astype(float),
                         "ce": ((y >= variants["gated_event_conditional"][0]) & (y <= variants["gated_event_conditional"][2])).astype(float)})
    windows = {"holdout_2025_2026": ok & (origin >= np.datetime64(HOLDOUT_START)), "full": ok}
    out = {"dataset": spec["label"], "asset_type": spec["asset_type"], "windows": {}}
    for wname, wmask in windows.items():
        block = {"n_forecasts": int(wmask.sum()), "share_gated_pct": round(100 * float(gate[wmask].mean()), 1),
                 "share_calendar_pct": round(100 * float(g_cal[wmask].mean()), 1), "share_headline_pct": round(100 * float(g_news[wmask].mean()), 1),
                 "share_shock_pct": round(100 * float(g_shock[wmask].mean()), 1), "variants": {}, "gated_forecasts_only": {}}
        for vname, (q10, q50, q90, up) in variants.items():
            block["variants"][vname] = {k: round(v, 5) if isinstance(v, float) else v for k, v in scores(q10[wmask], q50[wmask], q90[wmask], up[wmask], y[wmask]).items()}
        # per-gate-type subsets: where does the event-conditional replacement help?
        block["by_gate_type"] = {}
        for gname, gmask_type in (("calendar", g_cal), ("headline", g_news), ("shock", g_shock)):
            sub = wmask & gmask_type
            if sub.sum() >= 20:
                entry = {}
                for vname in ("model", "climatology", "gated_event_conditional"):
                    q10, q50, q90, up = variants[vname]
                    entry[vname] = {k: round(v, 5) if isinstance(v, float) else v for k, v in scores(q10[sub], q50[sub], q90[sub], up[sub], y[sub]).items()}
                we_ = winkler(variants["gated_event_conditional"][0], variants["gated_event_conditional"][2], y)
                wm_ = winkler(m_q10, m_q90, y)
                entry["winkler_event_conditional_minus_model"] = block_bootstrap_diff(we_[sub], wm_[sub])
                entry["winkler_improvement_pct"] = round(100 * (1 - entry["gated_event_conditional"]["winkler"] / entry["model"]["winkler"]), 2)
                block["by_gate_type"][gname] = entry
        gm = wmask & gate
        if gm.sum() > 20:
            for vname in ("model", "climatology", "gated_drift", "gated_event_conditional"):
                q10, q50, q90, up = variants[vname]
                block["gated_forecasts_only"][vname] = {k: round(v, 5) if isinstance(v, float) else v for k, v in scores(q10[gm], q50[gm], q90[gm], up[gm], y[gm]).items()}
        # paired differences with block bootstrap (gated - model): negative = improvement
        wm, wg, wd = winkler(m_q10, m_q90, y), winkler(variants["gated"][0], variants["gated"][2], y), winkler(variants["gated_drift"][0], variants["gated_drift"][2], y)
        bm, bg = (m_up - (y > 0)) ** 2, (variants["gated"][3] - (y > 0)) ** 2
        we = winkler(variants["gated_event_conditional"][0], variants["gated_event_conditional"][2], y)
        block["winkler_gated_minus_model"] = block_bootstrap_diff(wg[wmask], wm[wmask])
        block["winkler_event_conditional_minus_model"] = block_bootstrap_diff(we[wmask], wm[wmask])
        if gm.sum() > 20:
            block["winkler_event_conditional_minus_model_gated_only"] = block_bootstrap_diff(we[gm], wm[gm])
            be = (variants["gated_event_conditional"][3] - (y > 0)) ** 2
            block["brier_event_conditional_minus_model_gated_only"] = block_bootstrap_diff(be[gm], bm[gm])
        block["winkler_event_conditional_improvement_pct"] = round(100 * (1 - block["variants"]["gated_event_conditional"]["winkler"] / block["variants"]["model"]["winkler"]), 2)
        block["winkler_gated_drift_minus_model"] = block_bootstrap_diff(wd[wmask], wm[wmask])
        block["brier_gated_minus_model"] = block_bootstrap_diff(bg[wmask], bm[wmask])
        block["winkler_improvement_pct"] = round(100 * (1 - block["variants"]["gated"]["winkler"] / block["variants"]["model"]["winkler"]), 2)
        block["winkler_drift_improvement_pct"] = round(100 * (1 - block["variants"]["gated_drift"]["winkler"] / block["variants"]["model"]["winkler"]), 2)
        block["brier_improvement_pct"] = round(100 * (1 - block["variants"]["gated"]["brier"] / block["variants"]["model"]["brier"]), 2)
        out["windows"][wname] = block
    return out


def pooled_universe(keys: list[str], specs: dict) -> dict:
    """Pool the by-gate-type differences across many stocks: paired forecast-level
    Winkler / Brier / coverage for model vs event-conditional on each gate type."""
    rows = {g: {"wm": [], "we": [], "bm": [], "be": [], "cm": [], "ce": []} for g in ("calendar", "headline", "shock")}
    per_stock = []
    for key in keys:
        r = run(key, specs[key])
        w = r["windows"]["full"]
        rec = {"key": key, "symbol": specs[key]["symbol"]}
        for g, e in w.get("by_gate_type", {}).items():
            rec[f"{g}_n"] = e["model"]["n"]; rec[f"{g}_winkler_improvement_pct"] = e["winkler_improvement_pct"]
            rec[f"{g}_cov_model"] = e["model"]["coverage"]; rec[f"{g}_cov_ec"] = e["gated_event_conditional"]["coverage"]
        per_stock.append(rec)
        # forecast-level arrays for pooling (recompute quickly)
        _pool_arrays(key, specs[key], rows)
    out = {"stocks": len(keys), "per_stock": per_stock, "pooled_full_sample": {}}
    for g, a in rows.items():
        if len(a["wm"]) < 50:
            continue
        wm, we = np.asarray(a["wm"]), np.asarray(a["we"]); bm, be = np.asarray(a["bm"]), np.asarray(a["be"]); cm, ce = np.asarray(a["cm"]), np.asarray(a["ce"])
        out["pooled_full_sample"][g] = {
            "n_forecasts": int(len(wm)), "winkler_model": round(float(wm.mean()), 5), "winkler_event_conditional": round(float(we.mean()), 5),
            "winkler_improvement_pct": round(100 * (1 - we.mean() / wm.mean()), 2),
            "winkler_diff_bootstrap": block_bootstrap_diff(we, wm),
            "brier_model": round(float(bm.mean()), 5), "brier_event_conditional": round(float(be.mean()), 5), "brier_diff_bootstrap": block_bootstrap_diff(be, bm),
            "coverage_model": round(float(cm.mean()), 4), "coverage_event_conditional": round(float(ce.mean()), 4),
            "share_stocks_improved": round(float(np.mean([r.get(f"{g}_winkler_improvement_pct", np.nan) > 0 for r in per_stock if f"{g}_winkler_improvement_pct" in r])), 3),
        }
    return out


def _pool_arrays(key: str, spec: dict, rows: dict) -> None:
    """Append the forecast-level arrays cached by the last run() call, split by gate type."""
    a = _LAST_ARRAYS
    for g, mask in (("calendar", a["g_cal"]), ("headline", a["g_news"]), ("shock", a["g_shock"])):
        m = a["ok"] & mask
        for name in ("wm", "we", "bm", "be", "cm", "ce"):
            rows[g][name].extend(a[name][m].tolist())


def main() -> None:
    if sys.argv[1:2] == ["--universe"]:
        import json as _json
        from universe_run import key_for, spec_for
        tickers = _json.load(open(OUTPUT_DIR / "universe_tickers.json"))["tickers"]
        specs = {key_for(t): spec_for(t) for t in tickers}
        for k in ("aapl", "msft", "tsla", "nvda"):
            specs[k] = DATASETS[k]
        keys = [k for k in specs if (OUTPUT_DIR / f"forecasts_{k}.csv").exists()]
        pooled = pooled_universe(keys, specs)
        (OUTPUT_DIR / "gate_experiment_universe.json").write_text(json.dumps(pooled, indent=1, default=float))
        for g, e in pooled["pooled_full_sample"].items():
            print(f"POOLED {g:9s} stocks={pooled['stocks']} n={e['n_forecasts']} Winkler {e['winkler_model']:.4f} -> {e['winkler_event_conditional']:.4f} ({e['winkler_improvement_pct']:+.1f}%, CI {e['winkler_diff_bootstrap']['ci95']}, p={e['winkler_diff_bootstrap']['p_two_sided']}) | cov {e['coverage_model']:.3f} -> {e['coverage_event_conditional']:.3f} | Brier {e['brier_model']:.4f} -> {e['brier_event_conditional']:.4f} (CI {e['brier_diff_bootstrap']['ci95']}) | stocks improved {e['share_stocks_improved']:.0%}")
        return
    keys = sys.argv[1:] or ["bito", "btc", "spxl", "spy", "aapl", "msft", "tsla", "nvda"]
    path = OUTPUT_DIR / "gate_experiment.json"
    result = json.loads(path.read_text()) if path.exists() else {}
    for key in keys:
        result[key] = run(key)
        w = result[key]["windows"]["holdout_2025_2026"]
        v = w["variants"]
        g = w["gated_forecasts_only"]
        print(f"[{key}] holdout n={w['n_forecasts']} gated {w['share_gated_pct']}% (cal {w['share_calendar_pct']}, news {w['share_headline_pct']}, shock {w['share_shock_pct']})")
        print(f"   ALL   Winkler model {v['model']['winkler']:.4f} clim {v['climatology']['winkler']:.4f} gated {v['gated']['winkler']:.4f} ({w['winkler_improvement_pct']:+.1f}%) "
              f"event-cond {v['gated_event_conditional']['winkler']:.4f} ({w['winkler_event_conditional_improvement_pct']:+.1f}%, CI {w['winkler_event_conditional_minus_model']['ci95']}) | "
              f"Brier {v['model']['brier']:.4f} -> ec {v['gated_event_conditional']['brier']:.4f} | cov {v['model']['coverage']:.3f} -> ec {v['gated_event_conditional']['coverage']:.3f}")
        for gname, e in w.get("by_gate_type", {}).items():
            print(f"   {gname:9s} n={e['model']['n']:4d} Winkler model {e['model']['winkler']:.4f} clim {e['climatology']['winkler']:.4f} event-cond {e['gated_event_conditional']['winkler']:.4f} ({e['winkler_improvement_pct']:+.1f}%, CI {e['winkler_event_conditional_minus_model']['ci95']}) | cov {e['model']['coverage']:.3f} -> {e['gated_event_conditional']['coverage']:.3f} | Brier {e['model']['brier']:.4f} -> {e['gated_event_conditional']['brier']:.4f}")
        wf = result[key]["windows"]["full"]
        for gname, e in wf.get("by_gate_type", {}).items():
            print(f"   FULL {gname:9s} n={e['model']['n']:4d} Winkler {e['model']['winkler']:.4f} -> {e['gated_event_conditional']['winkler']:.4f} ({e['winkler_improvement_pct']:+.1f}%, CI {e['winkler_event_conditional_minus_model']['ci95']}) | cov {e['model']['coverage']:.3f} -> {e['gated_event_conditional']['coverage']:.3f} | Brier {e['model']['brier']:.4f} -> {e['gated_event_conditional']['brier']:.4f}")
        if g:
            print(f"   GATED n={g['model']['n']} Winkler model {g['model']['winkler']:.4f} clim {g['climatology']['winkler']:.4f} event-cond {g['gated_event_conditional']['winkler']:.4f} "
                  f"({100*(1-g['gated_event_conditional']['winkler']/g['model']['winkler']):+.1f}%, CI {w.get('winkler_event_conditional_minus_model_gated_only',{}).get('ci95')}) | "
                  f"cov model {g['model']['coverage']:.3f} -> ec {g['gated_event_conditional']['coverage']:.3f} | Brier {g['model']['brier']:.4f} -> ec {g['gated_event_conditional']['brier']:.4f}")
    path.write_text(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
