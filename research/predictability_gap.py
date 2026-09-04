"""The predictability gap: how much of price movement sits on information-shock
sessions a price-conditioned model cannot see, and what ceiling that implies."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR  # noqa: E402
from event_study import DATASETS  # noqa: E402

KEYS = ["btc", "bito", "spxl", "spy", "aapl", "msft", "tsla", "nvda"]


def main() -> None:
    rows = []
    for key in KEYS:
        fc = pd.read_csv(OUTPUT_DIR / f"forecasts_{key}.csv")
        day = pd.read_csv(OUTPUT_DIR / f"days_{key}.csv", index_col=0, parse_dates=True)
        h1 = fc[fc["horizon"] == 1]
        shock = h1["window_has_shock"].astype(bool)
        # variance and absolute-move share carried by shock sessions (scored sessions only)
        r = day["ret"].iloc[h1["target_pos"].to_numpy()].to_numpy(float)
        var_share = float(np.nansum(r[shock.to_numpy()] ** 2) / np.nansum(r ** 2))
        abs_share = float(np.nansum(np.abs(r[shock.to_numpy()])) / np.nansum(np.abs(r)))
        pi = float(shock.mean())
        a_calm = float(h1.loc[~shock, "hit"].mean()); a_shock = float(h1.loc[shock, "hit"].mean()); a_all = float(h1["hit"].mean())
        base = float(h1["actual_up"].mean())
        covered = h1.dropna(subset=["target_news_ratio"])
        spike = covered["target_news_ratio"] >= 2.0
        rows.append({
            "key": key, "instrument": DATASETS[key]["symbol"], "asset_type": DATASETS[key]["asset_type"],
            "sessions": int(len(h1)), "shock_share_pct": round(100 * pi, 1),
            "variance_share_of_shock_sessions_pct": round(100 * var_share, 1),
            "abs_move_share_of_shock_sessions_pct": round(100 * abs_share, 1),
            "hit_calm": round(a_calm, 3), "hit_shock": round(a_shock, 3), "hit_all": round(a_all, 3), "always_up": round(base, 3),
            "headline_spike_share_pct": round(100 * float(spike.mean()), 1) if len(covered) else None,
            "hit_headline_spike": round(float(covered.loc[spike, "hit"].mean()), 3) if spike.sum() > 5 else None,
            "ceiling_if_calm_skill_60pct": round((1 - pi) * 0.60 + pi * 0.5, 3),
            "ceiling_if_calm_skill_70pct": round((1 - pi) * 0.70 + pi * 0.5, 3),
            "shock_contribution_to_accuracy_pts": round(100 * pi * (a_shock - a_calm), 2),
        })
    table = pd.DataFrame(rows)
    table.to_csv(OUTPUT_DIR / "predictability_gap.csv", index=False)
    (OUTPUT_DIR / "predictability_gap.json").write_text(json.dumps(rows, indent=1))
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(table.drop(columns=["key"]).to_string(index=False))


if __name__ == "__main__":
    main()
