"""Markup checks before building the PDF.

Markdown (PAPER.md): paragraphs with an odd number of `**`, an odd number of `*`
emphasis markers (outside math and code), an odd number of `$`, or a bold run longer
than 160 characters — the causes of "bold that makes no sense" after an editing pass.
LaTeX (paper.tex, if present): balance of \\begingroup/\\endgroup and
\\landscape/\\endlandscape, figures placed after the References heading, leftover
`{=latex}` or escaped-dollar math, and \\textbf runs longer than 200 characters.

Run from research/:  .venv/bin/python check_markup.py        (exit code 1 on problems)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+?\$", re.S)
CODE = re.compile(r"`[^`\n]+`")
problems = 0


def report(kind, where, text):
    global problems
    problems += 1
    print(f"[{kind}] {where}: {text[:160]}")


md = (HERE / "PAPER.md").read_text()
in_code = False
for n, para in enumerate(md.split("\n\n")):
    if para.count("```") % 2 == 1:
        in_code = not in_code
        continue
    if in_code or para.lstrip().startswith(("|", "```")):
        continue
    plain = CODE.sub("", MATH.sub("", para))
    if para.count("$") % 2 == 1:
        report("odd $", f"paragraph {n}", para)
    if plain.count("**") % 2 == 1:
        report("odd **", f"paragraph {n}", para)
    singles = re.sub(r"\*\*", "", plain)
    if len(re.findall(r"(?<![\w*])\*(?!\s)|(?<!\s)\*(?![\w*])", singles)) % 2 == 1:
        report("odd *", f"paragraph {n}", para)
    for m in re.finditer(r"\*\*(.+?)\*\*", plain, flags=re.S):
        if len(m.group(1)) > 160 and not m.group(1).startswith("Table"):
            report("long bold", f"paragraph {n}", m.group(1))

tex_path = HERE / "paper.tex"
if tex_path.exists():
    tex = tex_path.read_text().split("\n")
    def count(prefix): return sum(1 for l in tex if l.startswith(prefix))
    bg, eg, ls, le = count("\\begingroup"), count("\\endgroup"), count("\\landscape"), count("\\endlandscape")
    if bg != eg: report("group balance", "paper.tex", f"begingroup {bg} vs endgroup {eg}")
    if ls != le: report("landscape balance", "paper.tex", f"landscape {ls} vs endlandscape {le}")
    ref = next((i for i, l in enumerate(tex) if "{References}" in l and "section" in l), None)
    if ref is not None:
        late = [i + 1 for i, l in enumerate(tex) if i > ref and "includegraphics" in l]
        if late: report("figure after references", "paper.tex", f"lines {late}")
    joined = "\n".join(tex)
    if "{=latex}" in joined: report("raw leftover", "paper.tex", "{=latex} not consumed by pandoc")
    if re.search(r"\\\$\\[a-z]+\\\$", joined): report("escaped math", "paper.tex", "a $\\cmd$ symbol was escaped to text")
    for m in re.finditer(r"\\textbf\{((?:[^{}]|\{[^{}]*\})*)\}", joined):
        if len(m.group(1)) > 200 and not m.group(1).startswith("Table"):
            report("long textbf", "paper.tex", m.group(1))
    unanchored = sum(1 for l in tex if l.strip() == "\\begin{figure}")
    if unanchored: report("unanchored figure", "paper.tex", f"{unanchored} figure environments without [H]")

print("markup problems:", problems)
sys.exit(1 if problems else 0)
