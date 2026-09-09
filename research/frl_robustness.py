"""Sensitivity checks for the Finance Research Letters submission."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arxiv_prefinding import load_forecasts  # noqa: E402
from event_study import block_bootstrap_group_diff  # noqa: E402

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
ASSETS = ("btc", "bito")
BLOCK_LENGTHS = (3, 7, 14, 21)
MOVE_THRESHOLDS = (2.0, 2.5, 3.0)
NEWS_THRESHOLDS = (1.5, 2.0, 2.5, 3.0)


def contrasts(frame, mask: np.ndarray, block: int = 7) -> dict:
    return {
        "directional_accuracy": block_bootstrap_group_diff(
            frame["hit"].to_numpy(float), mask, block=block
        ),
        "interval_coverage": block_bootstrap_group_diff(
            frame["covered"].to_numpy(float), mask, block=block
        ),
        "absolute_surprise": block_bootstrap_group_diff(
            frame["surprise_z"].abs().to_numpy(float), mask, block=block
        ),
    }


def analyse(key: str) -> dict:
    frame = load_forecasts(key)
    news = frame.loc[frame["target_news_ratio"].notna()].reset_index(drop=True)
    move_mask = frame["target_abs_z"].to_numpy(float) >= 2.5
    news_mask = news["target_news_ratio"].to_numpy(float) >= 2.0
    return {
        "block_length": {
            str(block): {
                "large_move": contrasts(frame, move_mask, block),
                "headline_spike": contrasts(news, news_mask, block),
            }
            for block in BLOCK_LENGTHS
        },
        "large_move_threshold": {
            str(threshold): contrasts(
                frame,
                frame["target_abs_z"].to_numpy(float) >= threshold,
            )
            for threshold in MOVE_THRESHOLDS
        },
        "headline_ratio_threshold": {
            str(threshold): contrasts(
                news,
                news["target_news_ratio"].to_numpy(float) >= threshold,
            )
            for threshold in NEWS_THRESHOLDS
        },
    }


def main() -> None:
    result = {key: analyse(key) for key in ASSETS}
    path = OUTPUT / "frl_robustness.json"
    path.write_text(json.dumps(result, indent=2))
    print("written:", path)
    for key in ASSETS:
        print(f"\n{key.upper()}")
        for block, row in result[key]["block_length"].items():
            move = row["large_move"]["directional_accuracy"]
            news = row["headline_spike"]["absolute_surprise"]
            print(
                f" block={block:>2} move accuracy Δ={move['difference']:+.3f} "
                f"CI={move['ci95']} | news |s| Δ={news['difference']:+.3f} "
                f"CI={news['ci95']}"
            )


if __name__ == "__main__":
    main()
