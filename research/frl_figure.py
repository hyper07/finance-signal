"""Create the single combined vector figure for the FRL submission."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
FIGURES = OUTPUT / "figures"
ASSETS = (("btc", "BTC/USD"), ("bito", "BITO"))


def condition_panel(ax, result: dict, title: str, show_legend: bool) -> None:
    labels = ["All", "Quiet\nnews", "Headline\nspike", "Large\nmove"]
    blocks = [
        result["all_origins"],
        result["headline_spike"]["comparison"],
        result["headline_spike"]["event"],
        result["large_realized_move"]["event"],
    ]
    accuracy = [row["directional_accuracy"]["mean"] for row in blocks]
    coverage = [row["interval_coverage"]["mean"] for row in blocks]
    counts = [row["n"] for row in blocks]
    x = np.arange(len(labels))
    width = 0.35
    ax.bar(
        x - width / 2, accuracy, width,
        color="#0072B2", edgecolor="black", linewidth=0.5,
        label="Directional accuracy",
    )
    ax.bar(
        x + width / 2, coverage, width,
        color="#E69F00", edgecolor="black", linewidth=0.5, hatch="//",
        label="P10-P90 coverage",
    )
    ax.axhline(0.5, color="#0072B2", linestyle=":", linewidth=1)
    ax.axhline(0.8, color="#E69F00", linestyle="--", linewidth=1)
    for pos, count in zip(x, counts):
        ax.text(pos, 1.015, f"n={count:,}", ha="center", fontsize=7)
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 1.08)
    ax.set_title(title, fontsize=10, weight="bold")
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=7.5)
    ax.spines[["top", "right"]].set_visible(False)
    if show_legend:
        ax.legend(loc="lower left", fontsize=7, frameon=False)


def case_panel(ax, key: str, result: dict, title: str,
               show_legend: bool) -> None:
    case = result["august_2026_case"]
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
        horizons, p10, p90, color="#56B4E9", alpha=0.28,
        label="Forecast P10-P90",
    )
    ax.plot(
        horizons, p50, color="#0072B2", linestyle="--",
        linewidth=1.6, label="Forecast median",
    )
    ax.plot(
        history_x, history, color="#666666", linewidth=1.3,
        label="Pre-origin close",
    )
    ax.plot(
        horizons, realized, color="#111111", marker="o",
        linewidth=1.8, markersize=3.5, label="Realized close",
    )
    ax.axvline(1, color="#D55E00", linestyle="-.", linewidth=1.1)
    ax.text(1.08, 24.7, "19 Aug.\npolicy meeting", color="#D55E00",
            fontsize=7, va="top")
    ax.axhline(0, color="#999999", linewidth=0.6)
    ax.set_xlim(history_x.min() - 0.2, 7.3)
    ax.set_ylim(-13, 26)
    ax.set_xlabel("Sessions after origin", fontsize=8)
    ax.set_title(title, fontsize=10, weight="bold")
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=7.5)
    ax.spines[["top", "right"]].set_visible(False)
    if show_legend:
        ax.legend(loc="upper left", fontsize=6.7, frameon=False, ncol=2)


def main() -> None:
    results = json.loads((OUTPUT / "arxiv_prefinding.json").read_text())
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.5))
    for column, (key, title) in enumerate(ASSETS):
        condition_panel(
            axes[0, column], results[key],
            f"{title}: conditional next-session scores",
            show_legend=column == 0,
        )
        case_panel(
            axes[1, column], key, results[key],
            f"{title}: forecast issued 18 August 2026",
            show_legend=column == 0,
        )
    axes[0, 0].set_ylabel("Share of forecasts", fontsize=8)
    axes[1, 0].set_ylabel("% from origin close", fontsize=8)
    for label, ax in zip(("A", "B", "C", "D"), axes.ravel()):
        ax.text(
            -0.11, 1.04, label, transform=ax.transAxes,
            fontsize=12, weight="bold", va="top",
        )
    fig.text(
        0.5, 0.01,
        "Headline spikes use licensed-archive counts; large moves are return-defined diagnostics.",
        ha="center", fontsize=7.5,
    )
    fig.tight_layout(rect=(0.02, 0.035, 1, 1), h_pad=2.0, w_pad=1.8)
    fig.savefig(FIGURES / "fig_frl_combined.pdf", bbox_inches="tight")
    fig.savefig(
        FIGURES / "fig_frl_combined.png",
        dpi=500, facecolor="white", bbox_inches="tight",
    )
    plt.close(fig)
    print("written:", FIGURES / "fig_frl_combined.pdf")


if __name__ == "__main__":
    main()
