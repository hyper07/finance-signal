"""Convert each companion manuscript (papers/*/paper.md) to LaTeX with the bundled
pandoc, using the same Unicode sanitizing as research/to_latex.py."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pypandoc

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from to_latex import HEADER, polish, prepare, sanitize  # noqa: E402

META = {
    "frl_short": ("Confidently wrong on the news: a live Bitcoin forecaster around information shocks", "Finance Research Letters — short article"),
    "jbef_behavioral": ("After the news: post-shock drift, model latency and how users act on a multi-day forecast", "Journal of Behavioral and Experimental Finance"),
    "frontiers_perspective": ("Why price-pattern forecasters fail when people react: a neuroeconomic research agenda for news and social media in markets", "Frontiers in Behavioral Neuroscience — Perspective"),
}


def build(folder: str) -> None:
    src = HERE / folder / "paper.md"
    if not src.exists():
        print("missing", src); return
    title, venue = META[folder]
    lines = src.read_text().splitlines()
    body = "\n".join(l for l in lines[1:] if not l.startswith("**Target:") and not l.startswith("*Kibaek Kim, Kiok Kim"))
    body = sanitize(prepare(body))
    tex = pypandoc.convert_text(
        body, "latex", format="markdown+tex_math_dollars+pipe_tables",
        extra_args=["--standalone", "--wrap=none", "--shift-heading-level-by=-1", "-V", "geometry:margin=1in", "-V", "fontsize=11pt",
                    "-V", "documentclass=article", "-M", f"title={title}", "-M", "author=Kibaek Kim, Kiok Kim, Danielle Ahn", "-M", f"date={venue} — draft 2026-09-04",
                    "-V", "colorlinks=true", "-V", f"header-includes={HEADER}", "--columns=60"],
    )
    tex = polish(tex)
    out = HERE / folder / "paper.tex"
    out.write_text("% Compile with xelatex or lualatex (Unicode source)\n" + tex)
    print(out, f"{out.stat().st_size/1e3:.0f} KB")


if __name__ == "__main__":
    for folder in (sys.argv[1:] or list(META)):
        build(folder)
