"""Create a side-effect-free arXiv source archive and local PDF preview."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESEARCH = REPO / "research"
PAPER_DIR = RESEARCH / "papers" / "arxiv_prefinding"
FIGURE_DIR = RESEARCH / "output" / "figures"
DIST = REPO / "dist" / "arxiv_prefinding"
SOURCE_ARCHIVE = REPO / "dist" / "arxiv_prefinding_source.tar.gz"
FIGURES = {
    "../../output/figures/fig_prefinding_conditionals.pdf": "figure1.pdf",
    "../../output/figures/fig_prefinding_august_case.pdf": "figure2.pdf",
    "../../output/figures/fig15_btc_declines_fan.pdf": "figure3.pdf",
}


def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def build_tex() -> str:
    run([
        sys.executable,
        str(RESEARCH / "papers" / "build_companions.py"),
        "arxiv_prefinding",
    ])
    source = (PAPER_DIR / "paper.tex").read_text()
    for old, new in FIGURES.items():
        source = source.replace(old, new)
    if "../../" in source:
        raise ValueError("submission source still contains parent-directory paths")
    if "\\pdfoutput" in source:
        raise ValueError("submission source must not set \\pdfoutput")
    return source


def compile_preview() -> None:
    tectonic = shutil.which("tectonic")
    if tectonic is None and Path("/tmp/tectonic").is_file():
        tectonic = "/tmp/tectonic"
    if tectonic is None:
        print("tectonic not found; source package built without a PDF preview")
        return
    run([
        tectonic, "-X", "compile", "main.tex",
        "--outfmt", "pdf", "--keep-logs",
    ], cwd=DIST)
    (DIST / "main.pdf").replace(DIST / "preprint.pdf")


def validate_source() -> None:
    tex = (DIST / "main.tex").read_text()
    included = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
    missing = [name for name in included if not (DIST / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing submission figures: {missing}")
    unexpected = sorted(
        path.name for path in DIST.iterdir()
        if path.name.startswith(".env") or path.suffix in {".csv", ".jsonl", ".pkl"}
    )
    if unexpected:
        raise ValueError(f"unsafe files in submission directory: {unexpected}")


def package_source() -> None:
    with tarfile.open(SOURCE_ARCHIVE, "w:gz") as archive:
        for name in ("main.tex", *FIGURES.values()):
            archive.add(DIST / name, arcname=name)


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    for path in DIST.iterdir():
        if path.is_file():
            path.unlink()
    (DIST / "main.tex").write_text(build_tex())
    for source_name, target_name in FIGURES.items():
        source = FIGURE_DIR / Path(source_name).name
        shutil.copy2(source, DIST / target_name)
    validate_source()
    compile_preview()
    package_source()
    print("source archive:", SOURCE_ARCHIVE)
    print("preview:", DIST / "preprint.pdf")
    print("arXiv compiler: select XeLaTeX")


if __name__ == "__main__":
    main()
