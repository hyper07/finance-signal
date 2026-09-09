"""Validate and assemble the draft Finance Research Letters submission."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from pypdf import PdfReader

REPO = Path(__file__).resolve().parent.parent
RESEARCH = REPO / "research"
PAPER = RESEARCH / "papers" / "frl_submission"
OUTPUT = RESEARCH / "output"
DIST = PAPER / "dist"


def run(*parts: str, env: dict[str, str] | None = None) -> None:
    subprocess.run(parts, cwd=REPO, check=True, env=env)


def word_counts() -> tuple[int, int]:
    text = (PAPER / "paper.md").read_text()
    abstract = re.search(r"\*\*Abstract\.\*\* (.+)", text)
    if abstract is None:
        raise ValueError("Abstract not found")
    body = text.split("## 1. Introduction", 1)[1].split("## References", 1)[0]
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
    body = re.sub(r"^\|.*\|$", "", body, flags=re.MULTILINE)
    body = re.sub(r"\$\$.*?\$\$", "", body, flags=re.DOTALL)
    token = re.compile(r"\b[\w'-]+\b")
    return len(token.findall(abstract.group(1))), len(token.findall(body))


def validate() -> None:
    abstract_words, body_words = word_counts()
    if body_words >= 2_500:
        raise ValueError(f"FRL body limit exceeded: {body_words} words")

    highlights = [
        line.removeprefix("• ").strip()
        for line in (PAPER / "Highlights.txt").read_text().splitlines()
        if line.startswith("• ")
    ]
    if not 3 <= len(highlights) <= 5:
        raise ValueError(f"FRL requires 3-5 highlights, found {len(highlights)}")
    overlong = [(len(line), line) for line in highlights if len(line) > 85]
    if overlong:
        raise ValueError(f"Highlights exceed 85 characters: {overlong}")

    pdf = PAPER / "paper.pdf"
    pages = len(PdfReader(pdf).pages)
    if pages > 14:
        raise ValueError(f"FRL page limit exceeded: {pages} pages")

    robustness = OUTPUT / "frl_robustness.json"
    figure = OUTPUT / "figures" / "fig_frl_combined.pdf"
    for path in (robustness, figure):
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(path)

    print(f"abstract: {abstract_words} words")
    print(f"body (conservative count): {body_words} words")
    print(f"review PDF: {pages} pages")
    print("highlights:", ", ".join(str(len(line)) for line in highlights), "characters")


def package() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    files = {
        PAPER / "paper.md": "manuscript.md",
        PAPER / "paper.tex": "manuscript.tex",
        PAPER / "paper.pdf": "manuscript.pdf",
        PAPER / "Title_Page.md": "Title_Page.md",
        PAPER / "Highlights.txt": "Highlights.txt",
        PAPER / "Cover_Letter.md": "Cover_Letter.md",
        PAPER / "Author_Confirmation_Form.md": "Author_Confirmation_Form.md",
        PAPER / "SUBMISSION_METADATA.md": "SUBMISSION_METADATA.md",
        PAPER / "SUBMISSION_CHECKLIST.md": "SUBMISSION_CHECKLIST.md",
        OUTPUT / "figures" / "fig_frl_combined.pdf": "fig_frl_combined.pdf",
        OUTPUT / "frl_robustness.json": "frl_robustness.json",
    }
    for source, name in files.items():
        shutil.copy2(source, DIST / name)

    archive = PAPER / "frl_submission_DRAFT.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(DIST.iterdir()):
            bundle.write(path, path.name)
    print("draft package:", archive)


def main() -> None:
    env = dict(__import__("os").environ)
    env.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
    run(sys.executable, "research/frl_robustness.py", env=env)
    run(sys.executable, "research/frl_figure.py", env=env)
    run(
        sys.executable,
        "research/papers/build_companions.py",
        "frl_submission",
    )
    compiler = shutil.which("tectonic")
    if compiler:
        run(compiler, "research/papers/frl_submission/paper.tex")
    else:
        raise RuntimeError("Install Tectonic or compile paper.tex with XeLaTeX")
    validate()
    package()
    print("DRAFT ONLY: author, rights, data-release, and fee actions remain.")


if __name__ == "__main__":
    main()
