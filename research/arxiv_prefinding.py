"""Build the statistics and figures for the narrow preliminary arXiv paper.

This analysis starts from deposited forecast-score CSVs. It does not call the
proprietary forecasting engine or load licensed headline text.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import (  # noqa: E402
    block_bootstrap_group_diff,
    block_bootstrap_mean,
)

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
FIGURES = OUTPUT / "figures"
ASSETS = {
    "btc": "BTC/USD",
    "bito": "BITO",
}
NEWS_RATIO = 2.0
SHOCK_Z = 2.5


def load_forecasts(key: str) -> pd.DataFrame:
    frame = pd.read_csv(
        OUTPUT / f"forecasts_{key}.csv",
        parse_dates=["origin", "target_date"],
    )
    return frame.loc[frame["horizon"] == 1].sort_values("pos").reset_index(drop=True)


def metric_block(frame: pd.DataFrame) -> dict:
    return {
        "n": int(len(frame)),
        "directional_accuracy": block_bootstrap_mean(
            frame["hit"].to_numpy(float), null=0.5
        ),
        "interval_coverage": block_bootstrap_mean(
            frame["covered"].to_numpy(float)
        ),
        "mean_absolute_surprise": block_bootstrap_mean(
            frame["surprise_z"].abs().to_numpy(float)
        ),
    }


def conditional_block(frame: pd.DataFrame, mask: np.ndarray,
                      event_label: str, comparison_label: str) -> dict:
    accuracy = block_bootstrap_group_diff(
        frame["hit"].to_numpy(float), mask
    )
    coverage = block_bootstrap_group_diff(
        frame["covered"].to_numpy(float), mask
    )
    surprise = block_bootstrap_group_diff(
        frame["surprise_z"].abs().to_numpy(float), mask
    )

    def side(which: str) -> dict:
        return {
            "n": accuracy[f"n_{which}"],
            "directional_accuracy": {
                "mean": accuracy[f"{which}_mean"],
                "ci95": accuracy[f"{which}_mean_ci95"],
                "method": accuracy["method"],
            },
            "interval_coverage": {
                "mean": coverage[f"{which}_mean"],
                "ci95": coverage[f"{which}_mean_ci95"],
                "method": coverage["method"],
            },
            "mean_absolute_surprise": {
                "mean": surprise[f"{which}_mean"],
                "ci95": surprise[f"{which}_mean_ci95"],
                "method": surprise["method"],
            },
        }

    return {
        "event_label": event_label,
        "comparison_label": comparison_label,
        "event": side("event"),
        "comparison": side("comparison"),
        "event_minus_comparison": {
            "directional_accuracy": accuracy,
            "interval_coverage": coverage,
            "absolute_surprise": surprise,
        },
    }


def case_study(key: str) -> dict:
    summary = json.loads((OUTPUT / f"summary_{key}.json").read_text())
    event = next(
        row for row in summary["august_2026_event"]
        if row["as_of"] == "2026-08-18"
    )
    return {
        "origin": event["as_of"],
        "signal_3day": event["signal_3day"],
        "consensus": event["consensus"],
        "next_target_pct": event["next_target_pct"],
        "forecast": event["rows"],
    }


def analyse_asset(key: str) -> dict:
    frame = load_forecasts(key)
    news = frame.loc[frame["target_news_ratio"].notna()].reset_index(drop=True)
    news_spike = news["target_news_ratio"].to_numpy(float) >= NEWS_RATIO
    large_move = frame["target_abs_z"].to_numpy(float) >= SHOCK_Z
    return {
        "label": ASSETS[key],
        "all_origins": metric_block(frame),
        "headline_spike": conditional_block(
            news, news_spike,
            f"headline-count ratio ≥ {NEWS_RATIO:g}",
            f"headline-count ratio < {NEWS_RATIO:g}",
        ),
        "large_realized_move": conditional_block(
            frame, large_move,
            f"|z| ≥ {SHOCK_Z:g}",
            f"|z| < {SHOCK_Z:g}",
        ),
        "august_2026_case": case_study(key),
    }


def figure_conditionals(results: dict) -> None:
    labels = ["All origins", "Quiet-news\ndays", "Headline-count\nspikes", "Large realized\nmoves"]
    colors = ("#0072B2", "#E69F00")
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), sharey=True)
    for ax, (key, title) in zip(axes, ASSETS.items()):
        result = results[key]
        all_block = result["all_origins"]
        news = result["headline_spike"]
        shock = result["large_realized_move"]
        blocks = [
            all_block,
            news["comparison"],
            news["event"],
            shock["event"],
        ]
        accuracy = [b["directional_accuracy"]["mean"] for b in blocks]
        coverage = [b["interval_coverage"]["mean"] for b in blocks]
        counts = [b["n"] for b in blocks]
        x = np.arange(len(labels))
        width = 0.35
        ax.bar(
            x - width / 2, accuracy, width,
            color=colors[0], edgecolor="black", linewidth=0.6,
            label="directional accuracy",
        )
        ax.bar(
            x + width / 2, coverage, width,
            color=colors[1], edgecolor="black", linewidth=0.6,
            hatch="//", label="P10–P90 coverage",
        )
        ax.axhline(0.5, color=colors[0], linestyle=":", linewidth=1.1)
        ax.axhline(0.8, color=colors[1], linestyle="--", linewidth=1.1)
        for pos, count in zip(x, counts):
            ax.text(pos, 1.015, f"n={count:,}", ha="center", va="bottom", fontsize=8)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_xticks(x, labels)
        ax.set_ylim(0, 1.1)
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("share of next-session forecasts", fontsize=9)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, legend_labels, loc="upper center", ncol=2,
        frameon=False, bbox_to_anchor=(0.5, 1.02), fontsize=9,
    )
    fig.suptitle(
        "Forecast performance changes when information intensity or realized moves are large",
        y=1.10, fontsize=12,
    )
    fig.text(
        0.5, -0.02,
        "Headline-count spikes use only licensed-archive counts; large moves are return-defined diagnostics, not exogenous events.",
        ha="center", fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.98))
    fig.savefig(FIGURES / "fig_prefinding_conditionals.pdf", bbox_inches="tight")
    fig.savefig(
        FIGURES / "fig_prefinding_conditionals.png",
        dpi=300, facecolor="white", bbox_inches="tight",
    )
    plt.close(fig)


def figure_august_case(results: dict) -> None:
    colors = {
        "band": "#56B4E9",
        "median": "#0072B2",
        "realized": "#111111",
        "history": "#666666",
        "event": "#D55E00",
    }
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), sharey=True)
    for ax, (key, title) in zip(axes, ASSETS.items()):
        case = results[key]["august_2026_case"]
        rows = case["forecast"]
        horizons = np.array([0] + [row["h"] for row in rows])
        p10 = np.array([0.0] + [row["p10_pct"] for row in rows])
        p50 = np.array([0.0] + [row["p50_pct"] for row in rows])
        p90 = np.array([0.0] + [row["p90_pct"] for row in rows])
        realized = np.array([0.0] + [row["realized_pct"] for row in rows])

        days = pd.read_csv(OUTPUT / f"days_{key}.csv", parse_dates=["date"])
        origin_pos = int(days.index[days["date"] == pd.Timestamp(case["origin"])][0])
        origin_close = float(days.loc[origin_pos, "close"])
        history_rows = days.iloc[max(0, origin_pos - 5):origin_pos + 1]
        history_x = np.arange(-len(history_rows) + 1, 1)
        history = (history_rows["close"].to_numpy(float) / origin_close - 1) * 100

        ax.fill_between(
            horizons, p10, p90, color=colors["band"], alpha=0.25,
            label="forecast P10–P90",
        )
        ax.plot(
            horizons, p50, color=colors["median"], linestyle="--",
            linewidth=1.8, label="forecast median",
        )
        ax.plot(
            history_x, history, color=colors["history"], linewidth=1.5,
            label="pre-origin close",
        )
        ax.plot(
            horizons, realized, color=colors["realized"], marker="o",
            linewidth=2.0, markersize=4, label="realized close",
        )
        ax.axvline(1, color=colors["event"], linestyle="-.", linewidth=1.2)
        ax.text(
            1.08, 24.5, "19 Aug.\nWhite House meeting",
            color=colors["event"], fontsize=8, va="top",
        )
        ax.axhline(0, color="#999999", linewidth=0.7)
        ax.set_title(f"{title}: forecast issued 18 Aug. 2026", fontsize=10, weight="bold")
        ax.set_xlim(history_x.min() - 0.2, 7.3)
        ax.set_ylim(-13, 26)
        ax.set_xlabel("sessions after origin", fontsize=9)
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("% from origin close", fontsize=9)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, legend_labels, loc="upper center", ncol=4,
        frameon=False, bbox_to_anchor=(0.5, 1.03), fontsize=8.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(FIGURES / "fig_prefinding_august_case.pdf", bbox_inches="tight")
    fig.savefig(
        FIGURES / "fig_prefinding_august_case.png",
        dpi=300, facecolor="white", bbox_inches="tight",
    )
    plt.close(fig)


def main() -> None:
    results = {key: analyse_asset(key) for key in ASSETS}
    result_path = OUTPUT / "arxiv_prefinding.json"
    result_path.write_text(json.dumps(results, indent=2))
    figure_conditionals(results)
    figure_august_case(results)
    print("written:", result_path)
    for key, result in results.items():
        news = result["headline_spike"]
        shock = result["large_realized_move"]
        print(
            key,
            "all accuracy", result["all_origins"]["directional_accuracy"]["mean"],
            "| news spike", news["event"]["directional_accuracy"]["mean"],
            "vs", news["comparison"]["directional_accuracy"]["mean"],
            "| large move", shock["event"]["directional_accuracy"]["mean"],
            "vs", shock["comparison"]["directional_accuracy"]["mean"],
        )


if __name__ == "__main__":
    main()
