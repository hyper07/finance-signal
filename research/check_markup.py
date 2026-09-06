"""Markup checks before building the PDF.

Catches the three defect classes that have actually reached the typeset paper:

1. **Unbalanced delimiters.** An odd number of unescaped `$` on a line (a currency
   amount such as `$19bn` that pandoc reads as a math delimiter, swallowing the rest
   of the table), or an odd number of `**` / `*` in a paragraph (a stray emphasis
   marker left by an editing pass, which turns the rest of the paragraph bold).
   Table rows are checked too — that is where the currency amounts live.
2. **Mid-word insertions.** `in$t$ervals`, `s$p$lits`, `stat*is*tic` — math or
   emphasis spans dropped inside a word by the Grammarly merge.
3. **LaTeX-side breakage.** Unbalanced `\\begingroup`/`\\endgroup` or
   `\\landscape`/`\\endlandscape`, figures floated past the References heading,
   leftover `{=latex}` raw markers, escaped-dollar math, over-long `\\textbf` runs.

Run from research/:  .venv/bin/python check_markup.py     (exit 1 if anything found)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+?\$", re.S)
CODE = re.compile(r"`[^`\n]+`")
UNESCAPED_DOLLAR = re.compile(r"(?<!\\)\$")
MIDWORD = re.compile(r"[A-Za-z]\$[^$\s]{1,10}\$[a-z]|[a-z]\*[a-z]{1,4}\*[a-z]")   # no spaces inside: a gap between two math spans is not a defect
problems = 0


def report(kind: str, where: str, text: str) -> None:
    global problems
    problems += 1
    print(f"[{kind}] {where}: {text.strip()[:150]}")


# ---------- Markdown sources ----------
SOURCES = [HERE / "PAPER.md"] + sorted((HERE / "papers").glob("*/paper.md"))
REPORTS = [HERE / n for n in ("BTC_DECLINES.md", "SWING_LEGS.md", "STOCK_EVENTS.md", "IMPLEMENTATION_GUIDE.md")]

for src in SOURCES + [p for p in REPORTS if p.exists()]:
    md = src.read_text()
    where = src.relative_to(HERE)

    # per line: delimiter balance (tables included) and mid-word insertions
    in_fence = False
    for n, line in enumerate(md.split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if len(UNESCAPED_DOLLAR.findall(line)) % 2 == 1:
            report("odd $", f"{where}:{n}", line)
        for m in MIDWORD.finditer(line):
            report("mid-word insertion", f"{where}:{n}", line[max(0, m.start() - 40):m.end() + 40])

    # per paragraph: emphasis balance and runaway bold
    in_fence = False
    for n, para in enumerate(md.split("\n\n")):
        if para.count("```") % 2 == 1:
            in_fence = not in_fence
            continue
        if in_fence or para.lstrip().startswith(("|", "```")):
            continue
        plain = re.sub(r"!?\[[^\]]*\]\([^)]*\)", "", CODE.sub("", MATH.sub("", para)))   # drop link/image targets: underscores in filenames are not math
        if plain.count("**") % 2 == 1:
            report("odd **", f"{where} para {n}", para)
        singles = plain.replace("**", "")
        if len(re.findall(r"(?<![\w*\\])\*(?!\s)|(?<!\s)\*(?![\w*\\])", singles)) % 2 == 1:
            report("odd *", f"{where} para {n}", para)
        prose = re.sub(r"\S*[/.]\S*", "", plain)   # filenames and paths carry underscores that are not math
        if re.search(r"[A-Za-zα-ωΑ-Ω\*]_[\{A-Za-z0-9]", prose):
            report("pseudo-math", f"{where} para {n}", para)
        for m in re.finditer(r"\*\*(.+?)\*\*", plain, flags=re.S):
            if len(m.group(1)) > 260 and not m.group(1).startswith("Table"):
                report("long bold", f"{where} para {n}", m.group(1))

# ---------- generated LaTeX ----------
tex_path = HERE / "paper.tex"
if tex_path.exists():
    lines = tex_path.read_text().split("\n")
    joined = "\n".join(lines)
    count = lambda p: sum(1 for l in lines if l.startswith(p))
    if count("\\begingroup") != count("\\endgroup"):
        report("group balance", "paper.tex", f"begingroup {count('\\begingroup')} vs endgroup {count('\\endgroup')}")
    if count("\\landscape") != count("\\endlandscape"):
        report("landscape balance", "paper.tex", f"landscape {count('\\landscape')} vs endlandscape {count('\\endlandscape')}")
    ref = next((i for i, l in enumerate(lines) if "{References}" in l and "section" in l), None)
    appendix = next((i for i, l in enumerate(lines) if "section" in l and "Appendix" in l), len(lines))
    if ref is not None:   # a figure between References and the appendices has floated out of its section
        late = [i + 1 for i, l in enumerate(lines) if ref < i < appendix and "includegraphics" in l]
        if late:
            report("figure after references", "paper.tex", f"lines {late}")
    if "{=latex}" in joined:
        report("raw leftover", "paper.tex", "{=latex} not consumed by pandoc")
    if re.search(r"\\\$\\[a-z]+\\\$", joined):
        report("escaped math", "paper.tex", "a $\\cmd$ symbol was escaped to literal text")
    for m in re.finditer(r"\\textbf\{((?:[^{}]|\{[^{}]*\})*)\}", joined):
        if len(m.group(1)) > 200 and not m.group(1).startswith("Table"):
            report("long textbf", "paper.tex", m.group(1))
    # a table row that lost its cells to a swallowed math span
    for i, l in enumerate(lines, 1):
        if l.rstrip().endswith("|") and "&" in l and "\\\\" not in l:
            report("broken table row", f"paper.tex:{i}", l)

print("markup problems:", problems)
sys.exit(1 if problems else 0)
