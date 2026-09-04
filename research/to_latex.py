"""Convert PAPER.md to paper.tex with the pandoc bundled in pypandoc_binary.

Compile with xelatex or lualatex (the source uses Unicode); the first H1 and
the working-paper line become title metadata.  Text-mode Unicode symbols that
Latin Modern lacks are mapped to math macros; math segments are left alone.
"""
from __future__ import annotations

import re
from pathlib import Path

import pypandoc

HERE = Path(__file__).resolve().parent
SRC = HERE / "PAPER.md"
OUT = HERE / "paper.tex"

TEXT_MAP = {
    "→": r"$\to$", "≥": r"$\ge$", "≤": r"$\le$", "≈": r"$\approx$", "×": r"$\times$", "≫": r"$\gg$",
    "σ": r"$\sigma$", "Δ": r"$\Delta$", "ν": r"$\nu$", "Φ": r"$\Phi$", "Λ": r"$\Lambda$", "ρ": r"$\rho$",
    "𝟙": r"$\mathbf{1}$", "‖": r"$\|$", "∎": r"$\square$", "⁻⁵": r"$^{-5}$", "⁻⁴": r"$^{-4}$", "…": r"\ldots{}",
    "−": "-", "½": r"$\tfrac12$", "·": r"\textperiodcentered{}", "≠": r"$\ne$",
}
MATH_SPLIT = re.compile(r"(\$\$.*?\$\$|\$[^$\n]+?\$)", re.S)


def sanitize(text: str) -> str:
    parts = MATH_SPLIT.split(text)
    for i in range(0, len(parts), 2):          # even indices are outside math
        for k, v in TEXT_MAP.items():
            parts[i] = parts[i].replace(k, v)
    return "".join(parts)


def main() -> None:
    md = SRC.read_text()
    lines = md.splitlines()
    title = lines[0].lstrip("# ").strip()
    body = "\n".join(lines[1:])
    body = re.sub(r"^\*\*Working paper[^\n]*\n", "", body, flags=re.M)
    body = re.sub(r"^\*Kibaek Kim, Kiok Kim, Danielle Ahn[^\n]*\*\n", "", body, flags=re.M)
    body = body.replace("<<MULTIPLICITY_METHODS_END>>", "")
    body = sanitize(body)
    tex = pypandoc.convert_text(
        body, "latex", format="markdown+tex_math_dollars+pipe_tables",
        extra_args=["--standalone", "--wrap=none", "--shift-heading-level-by=-1", "-V", "geometry:margin=1in", "-V", "fontsize=11pt",
                    "-V", "documentclass=article", "-V", "papersize=a4",
                    "-M", f"title={title}", "-M", "author=Kibaek Kim, Kiok Kim, Danielle Ahn", "-M", "date=Working paper, draft v1.0 (2026-09-04)",
                    "-V", "colorlinks=true", "-V", "header-includes=\\usepackage{booktabs}\\usepackage{longtable}\\usepackage{graphicx}\\graphicspath{{./}}"],
    )
    tex = "% Compile with: xelatex paper.tex   (or lualatex; Unicode source)\n" + tex
    OUT.write_text(tex)
    print(OUT, f"{OUT.stat().st_size/1e3:.0f} KB")


if __name__ == "__main__":
    main()
