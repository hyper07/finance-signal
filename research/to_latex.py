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
    # multi-character sequences first (dict order matters)
    "p\u0302": r"$\hat p$", "q\u0302": r"$\hat q$", "\u03c3\u0302": r"$\hat\sigma$", "\u03bd\u0302": r"$\hat\nu$", "P\u0302": r"$\hat P$",
    "\u2011": "-",                       # non-breaking hyphen
    "\u2080": "$_0$", "\u2081": "$_1$", "\u2082": "$_2$", "\u2083": "$_3$", "\u2084": "$_4$",
    "\u2085": "$_5$", "\u2086": "$_6$", "\u2087": "$_7$", "\u2088": "$_8$", "\u2089": "$_9$",
    "→": r"$\to$", "≥": r"$\ge$", "≤": r"$\le$", "≈": r"$\approx$", "×": r"$\times$", "≫": r"$\gg$",
    "σ": r"$\sigma$", "Δ": r"$\Delta$", "ν": r"$\nu$", "Φ": r"$\Phi$", "Λ": r"$\Lambda$", "ρ": r"$\rho$",
    "𝟙": r"$\mathbf{1}$", "‖": r"$\|$", "∎": r"$\square$", "⁻⁵": r"$^{-5}$", "⁻⁴": r"$^{-4}$", "…": r"\ldots{}",
    "−": "-", "½": r"$\tfrac12$", "·": r"\textperiodcentered{}", "≠": r"$\ne$",
    "†": r"$\dagger$", "✓": r"$\checkmark$", "÷": r"$\div$", "α": r"$\alpha$", "β": r"$\beta$", "μ": r"$\mu$", "ε": r"$\varepsilon$", "τ": r"$\tau$", "ξ": r"$\xi$", "π": r"$\pi$", "θ": r"$\theta$", "χ": r"$\chi$", "λ": r"$\lambda$", "∈": r"$\in$", "∑": r"$\sum$", "√": r"$\surd$", "∞": r"$\infty$",
}
# pandoc drops $...$ when a digit follows the closing dollar ("0.49$\\to$0.68"), so
# math-mode replacements go in as raw LaTeX (raw_attribute extension)
TEXT_MAP.update({"č": r"\v{c}", "ć": r"\'{c}", "š": r"\v{s}", "ž": r"\v{z}", "ř": r"\v{r}", "ě": r"\v{e}", "ő": r"\H{o}", "ł": r"\l{}"})   # accents outside T1-safe set
TEXT_MAP = {k: (f"`{v}`{{=latex}}" if v.startswith("$") else v) for k, v in TEXT_MAP.items()}

MATH_SPLIT = re.compile(r"(\$\$.*?\$\$|\$[^$\n]+?\$)", re.S)


def sanitize(text: str) -> str:
    parts = MATH_SPLIT.split(text)
    for i in range(0, len(parts), 2):          # even indices are outside math
        for k, v in TEXT_MAP.items():
            parts[i] = parts[i].replace(k, v)
    return "".join(parts)


HEADER = (
    "\\usepackage{booktabs}\\usepackage{longtable}\\usepackage{graphicx}\\graphicspath{{./}}"
    "\\usepackage{fvextra}"
    "\\RecustomVerbatimEnvironment{verbatim}{Verbatim}{fontsize=\\footnotesize,breaklines=true,breakanywhere=true}"
    "\\usepackage[htt]{hyphenat}"                      # allow hyphenation inside \\texttt
    "\\usepackage{pdflscape}"                          # wide tables rotate to a landscape page
    "\\usepackage{caption}\\captionsetup[figure]{labelformat=empty}"   # captions already say "Figure N."
    "\\usepackage{float}"                              # [H] placement: figures stay where the text puts them
    "\\sloppy\\setlength{\\emergencystretch}{3em}"    # prefer loose lines to margin overflow
    "\\setlength{\\tabcolsep}{4pt}"
)


def polish(tex: str) -> str:
    """Post-process pandoc output (fixes that need the LaTeX, not the Markdown)."""
    # pandoc emits unanchored floats; with twenty figures they drift to the end of the
    # document (after the references). Anchor each one where its caption sits.
    tex = tex.replace("\\begin{figure}\n", "\\begin{figure}[H]\n")
    return tex


SPLIT = re.compile(r"(?<!\\)\|")
SEP_ROW = re.compile(r"\s*\|?[\s:|-]+\|?\s*")
# advance widths in Latin Modern, in units of one digit (0.5 em)
_W = {**{c: 1.4 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}, **{c: 0.6 for c in " .,:;'"}, "(": 0.8, ")": 0.8, "[": 0.6, "]": 0.6,
      "+": 1.55, "-": 0.7, "−": 1.0, "–": 1.0, "—": 2.0, "%": 1.65, "=": 1.55, "<": 1.55, ">": 1.55, "|": 0.55, "×": 1.55, "÷": 1.55,
      "≥": 1.55, "≤": 1.55, "≈": 1.55, "i": 0.55, "l": 0.55, "j": 0.6, "f": 0.6, "t": 0.75, "r": 0.8, "m": 1.6, "w": 1.45}
EM = {"small": 5.0, "footnotesize": 4.5, "scriptsize": 4.0}   # points per digit at 11pt base
PORTRAIT, LANDSCAPE = 452.0, 700.0                             # A4 text width/height with 1in margins
MARGIN = 1.06                                                  # safety on the width estimate


def _cells(line: str) -> list[str]:
    line = re.sub(r"\$[^$]*\$", lambda m: m.group(0).replace("|", "\x00"), line)   # pipes inside math are not separators
    parts = [c.replace("\x00", "|") for c in SPLIT.split(line.strip())]
    if parts and parts[0].strip() == "": parts = parts[1:]
    if parts and parts[-1].strip() == "": parts = parts[:-1]
    return [c.strip() for c in parts]


def _plain(c: str) -> str:
    c = re.sub(r"\$[^$]*\$", lambda m: "x" * max(3, len(m.group(0)) // 2), c)
    return re.sub(r"\*\*|__|`|\\", "", c)


def _vis_len(c: str) -> float:
    return sum(_W.get(ch, 1.0) for ch in _plain(c)) * (1.08 if "**" in c else 1.0)


def column_needs(block: list[str]) -> list[tuple[float, float]] | None:
    """Per column (minimum, natural) width in digit units. Short cells stay on one
    line; prose cells may wrap, so their minimum is the longest unbreakable token."""
    header, sep = _cells(block[0]), _cells(block[1]); rows = [_cells(l) for l in block[2:]]
    if len(sep) != len(header) or any(len(r) != len(header) for r in rows): return None
    needs = []
    for j in range(len(header)):
        col = [r[j] for r in rows]
        cell = max([_vis_len(c) for c in col] or [0.0])
        tok = max([_vis_len(t) for c in col for t in _plain(c).split()] or [0.0])
        hword = max([_vis_len(t) for t in _plain(header[j]).split()] or [0.0])
        minimum = max(4.0, cell if cell <= 20 else tok, hword)     # header words never overflow
        needs.append((minimum, max(minimum, min(cell, 44.0))))
    return needs


def layout(needs):
    """Largest font (then landscape) whose minimum widths fit; slack goes to wrappable columns."""
    ncol = len(needs); mins = sum(m for m, _ in needs) * MARGIN
    for land in (False, True):
        avail = (LANDSCAPE if land else PORTRAIT) - 8 * ncol
        for size, em in EM.items():
            if mins * em <= avail:
                slack = avail / em - mins
                flex = [n - m for m, n in needs]; tot = sum(flex)
                widths = [m * MARGIN + (slack * f / tot if tot else slack / ncol) for (m, n), f in zip(needs, flex)]
                return size, land, widths
    return "scriptsize", True, [m for m, _ in needs]


def iter_tables(md: str):
    lines = md.split("\n"); i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and SEP_ROW.fullmatch(lines[i + 1]):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"): j += 1
            yield lines[i:j], True; i = j
        else:
            yield [lines[i]], False; i += 1


def _separator(block, widths):
    sep = _cells(block[1])
    return "|" + "|".join((":" if s.startswith(":") else "") + "-" * max(3, round(w)) + (":" if s.endswith(":") else "") for s, w in zip(sep, widths)) + "|"


def proportional_separators(md: str) -> str:
    """Rewrite each table's separator row so pandoc's p{} widths follow content."""
    out = []
    for block, is_table in iter_tables(md):
        if is_table and (needs := column_needs(block)):
            block = [block[0], _separator(block, layout(needs)[2])] + block[2:]
        out.extend(block)
    return "\n".join(out)


def size_tables(md: str, report: bool = False) -> str:
    """Wrap each table in its font-size group (and a landscape page when needed),
    keeping the bold caption paragraph with the table."""
    out = []
    for block, is_table in iter_tables(md):
        if is_table and (needs := column_needs(block)):
            size, land, widths = layout(needs)
            if report:
                print(f"  {_cells(block[0])[0][:22]:22s} cols={len(needs):2d} {size:12s} {'landscape' if land else ''}")
            block = [block[0], _separator(block, widths)] + block[2:]
            while out and out[-1].strip() == "": out.pop()
            caption = [out.pop()] if out and out[-1].startswith("**Table") else []
            pre = [""] + (["\\landscape", ""] if land else []) + [f"\\begingroup\\{size}", ""]
            post = ["", "\\endgroup"] + (["", "\\endlandscape"] if land else []) + [""]
            block = pre + caption + [""] + block + post
        elif is_table and report:
            print("  ! skipped (ragged rows):", _cells(block[0])[:4])
        out.extend(block)
    return "\n".join(out)


def prepare(md: str, report: bool = False) -> str:
    return size_tables(md, report=report)


def main() -> None:
    md = prepare(SRC.read_text(), report=True)
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
                    "-V", "colorlinks=true", "-V", f"header-includes={HEADER}", "--columns=60"],
    )
    tex = polish(tex)
    # \pdfoutput=1 within the first few lines forces pdfLaTeX on arXiv's AutoTeX,
    # which is required because the figures are PNG (DVI routes cannot embed them)
    # and because the pdfLaTeX branch of the preamble is the one this source targets.
    tex = ("% Compiles with pdflatex (required: PNG figures). arXiv: \\pdfoutput=1 forces it.\n"
           "\\pdfoutput=1\n" + tex)
    OUT.write_text(tex)
    print(OUT, f"{OUT.stat().st_size/1e3:.0f} KB")


if __name__ == "__main__":
    main()
