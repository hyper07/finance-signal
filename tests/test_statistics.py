from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

RESEARCH = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH))

from event_study import (  # noqa: E402
    block_bootstrap_diff,
    block_bootstrap_group_diff,
    block_bootstrap_mean,
)


class BlockBootstrapTests(unittest.TestCase):
    def test_paired_identical_inputs_have_zero_interval(self) -> None:
        values = np.linspace(-2.0, 3.0, 40)
        result = block_bootstrap_diff(
            values, values, paired=True, draws=300, seed=7
        )

        self.assertEqual(result["difference"], 0.0)
        self.assertEqual(result["ci95"], [0.0, 0.0])
        self.assertEqual(result["p_two_sided"], 1.0)

    def test_paired_constant_difference_is_preserved(self) -> None:
        baseline = np.arange(50, dtype=float)
        treatment = baseline - 0.25
        result = block_bootstrap_diff(
            treatment, baseline, paired=True, draws=300, seed=7
        )

        self.assertEqual(result["difference"], -0.25)
        self.assertEqual(result["ci95"], [-0.25, -0.25])
        self.assertLessEqual(result["p_two_sided"], 1 / 301)

    def test_paired_inputs_require_equal_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "equal lengths"):
            block_bootstrap_diff(
                np.arange(3), np.arange(4), paired=True, draws=20
            )

    def test_group_bootstrap_preserves_event_labels_and_order(self) -> None:
        values = np.tile([0.0, 0.0, 1.0, 1.0], 40)
        group = np.tile([False, False, True, True], 40)
        result = block_bootstrap_group_diff(
            values, group, block=8, draws=300, seed=9
        )

        self.assertEqual(result["difference"], 1.0)
        self.assertEqual(result["n_event"], 80)
        self.assertEqual(result["n_comparison"], 80)
        self.assertLessEqual(result["p_two_sided"], 1 / 301)

    def test_mean_bootstrap_reports_degenerate_constant_interval(self) -> None:
        result = block_bootstrap_mean(
            np.full(40, 0.75), block=7, draws=300, seed=4, null=0.5
        )

        self.assertEqual(result["mean"], 0.75)
        self.assertEqual(result["ci95"], [0.75, 0.75])
        self.assertLessEqual(result["p_two_sided"], 1 / 301)


if __name__ == "__main__":
    unittest.main()
