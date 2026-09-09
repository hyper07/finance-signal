from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "research" / "papers" / "frl_submission"
OUTPUT = ROOT / "research" / "output"


class FrlSubmissionTests(unittest.TestCase):
    def test_manuscript_limits(self) -> None:
        text = (PAPER / "paper.md").read_text()
        abstract = re.search(r"\*\*Abstract\.\*\* (.+)", text)
        self.assertIsNotNone(abstract)
        abstract_words = re.findall(r"\b[\w'-]+\b", abstract.group(1))
        self.assertLessEqual(len(abstract_words), 100)

        body = text.split("## 1. Introduction", 1)[1].split(
            "## References", 1
        )[0]
        body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
        body = re.sub(r"^\|.*\|$", "", body, flags=re.MULTILINE)
        body = re.sub(r"\$\$.*?\$\$", "", body, flags=re.DOTALL)
        self.assertLess(len(re.findall(r"\b[\w'-]+\b", body)), 2_500)

    def test_highlights_meet_frl_limit(self) -> None:
        highlights = [
            line.removeprefix("• ").strip()
            for line in (PAPER / "Highlights.txt").read_text().splitlines()
            if line.startswith("• ")
        ]
        self.assertGreaterEqual(len(highlights), 3)
        self.assertLessEqual(len(highlights), 5)
        self.assertTrue(all(len(line) <= 85 for line in highlights))

    def test_required_disclosures_are_present(self) -> None:
        text = (PAPER / "paper.md").read_text()
        for heading in (
            "## Data availability",
            "## Declaration of competing interest",
            "## Declaration of generative AI",
        ):
            self.assertIn(heading, text)
        self.assertIn("proprietary forecast-generation engine is not included", text)
        self.assertIn("authors operate the forecasting service", text.lower())

    def test_combined_figure_is_vector_and_resolves(self) -> None:
        text = (PAPER / "paper.md").read_text()
        figures = re.findall(r"!\[[^\]]+\]\(([^)]+)\)", text)
        self.assertEqual(figures, ["../../output/figures/fig_frl_combined.pdf"])
        path = (PAPER / figures[0]).resolve()
        self.assertTrue(path.exists())
        self.assertEqual(path.suffix, ".pdf")
        self.assertGreater(path.stat().st_size, 10_000)

    def test_robustness_grid_is_complete(self) -> None:
        result = json.loads((OUTPUT / "frl_robustness.json").read_text())
        for key in ("btc", "bito"):
            self.assertEqual(
                set(result[key]["block_length"]), {"3", "7", "14", "21"}
            )
            self.assertEqual(
                set(result[key]["large_move_threshold"]), {"2.0", "2.5", "3.0"}
            )
            self.assertEqual(
                set(result[key]["headline_ratio_threshold"]),
                {"1.5", "2.0", "2.5", "3.0"},
            )

    def test_compiled_review_pdf_is_within_page_limit(self) -> None:
        pdf = PAPER / "paper.pdf"
        self.assertTrue(pdf.exists())
        self.assertLessEqual(len(PdfReader(pdf).pages), 14)


if __name__ == "__main__":
    unittest.main()
