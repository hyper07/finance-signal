from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RESEARCH = REPO / "research"
PAPER = RESEARCH / "papers" / "arxiv_prefinding" / "paper.md"
OUTPUT = RESEARCH / "output"


class PrefindingReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paper = PAPER.read_text()
        cls.results = json.loads((OUTPUT / "arxiv_prefinding.json").read_text())

    def test_abstract_remains_within_frl_limit(self) -> None:
        abstract = re.search(
            r"\*\*Abstract\.\*\* (.+?)\n", self.paper
        )
        self.assertIsNotNone(abstract)
        words = re.findall(r"\b[\w'-]+\b", abstract.group(1))
        self.assertLessEqual(len(words), 100)

    def test_abstract_accuracy_matches_results(self) -> None:
        btc = self.results["btc"]["all_origins"]["directional_accuracy"]["mean"]
        bito = self.results["bito"]["all_origins"]["directional_accuracy"]["mean"]
        self.assertIn(f"{btc:.1%}", self.paper)
        self.assertIn(f"{bito:.1%}", self.paper)

    def test_paper_embeds_existing_vector_figures(self) -> None:
        paths = re.findall(r"!\[[^\]]+\]\(([^)]+\.pdf)\)", self.paper)
        self.assertEqual(len(paths), 2)
        for relative in paths:
            self.assertTrue((PAPER.parent / relative).resolve().is_file())

    def test_public_catalogues_do_not_redistribute_headline_text(self) -> None:
        for stem in ("btc_declines_catalogue", "stock_events_catalogue"):
            records = json.loads((OUTPUT / f"{stem}.json").read_text())
            self.assertTrue(records)
            self.assertNotIn("headlines", records[0])
            self.assertIn("headline_sha256", records[0])
            frame = pd.read_csv(OUTPUT / f"{stem}.csv", nrows=1)
            self.assertNotIn("headlines", frame.columns)
            self.assertIn("headline_sha256", frame.columns)

    def test_preliminary_interpretation_is_explicit(self) -> None:
        self.assertIn("do not measure investor behavior", self.paper)
        self.assertIn("not preregistered", self.paper)
        self.assertIn("cannot be independently", self.paper)


if __name__ == "__main__":
    unittest.main()
