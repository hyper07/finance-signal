"""Sentence-level merge of Grammarly's edits (Grammer_PAPER.md, flattened export) into
the structured PAPER.md. Structure, tables, figures, captions, code and references come
from the original; each prose sentence takes Grammarly's wording when the sentence
aligns and carries the same formulas (restored verbatim), otherwise stays original."""
import re, sys, difflib
from collections import Counter
from pathlib import Path

ORIG = Path("PAPER.md").read_text(); GRAM = Path("Grammer_PAPER.md").read_text()
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else None
MATH = re.compile(r"\$\$.*?\$\$|\$[^$\n]+?\$", re.S); CODE = re.compile(r"`[^`\n]+`")
LIST_LINE = re.compile(r"^(\s*)([-*]|\d+\.)\s+")
STRUCT_PREFIX = ("#", "|", "![", "```", "---", "**Table", "<<", "**Working paper", "*Kibaek", "**Keywords")

def orig_units(text):
    units = []
    for b in re.split(r"\n\s*\n", text):
        s = b.strip("\n")
        if not s.strip(): continue
        first = s.lstrip()
        if first.startswith(STRUCT_PREFIX) or "```" in s: units.append(("struct", s)); continue
        lines = s.split("\n")
        if all(LIST_LINE.match(l) or (l.startswith("  ") and l.strip()) for l in lines):
            item = None
            for l in lines:
                if LIST_LINE.match(l):
                    if item: units.append(("item", item))
                    item = l
                else: item += "\n" + l
            if item: units.append(("item", item))
            continue
        units.append(("prose", s))
    return units

def gram_units(text):
    units = []
    for b in re.split(r"\n\s*\n", text):
        s = b.strip("\n")
        if not s.strip() or "\t" in s or s.strip() == "---": continue
        lines = [l for l in s.split("\n") if l.strip()]
        units.extend(lines) if all(LIST_LINE.match(l) for l in lines) else units.append(s)
    return units

def words(t):
    t = MATH.sub(" MATH ", t); t = re.sub(r"[`*_#>|]", " ", t)
    return re.sub(r"[^\w\s%]", " ", t.lower()).split()

def ratio(a, b):
    wa, wb = words(a), words(b)
    if not wa or not wb: return 0.0
    sa, sb = set(wa), set(wb)
    if len(sa & sb) / len(sa | sb) < 0.15: return 0.0
    return difflib.SequenceMatcher(None, wa, wb, autojunk=False).ratio()

# ---- paragraph alignment (monotonic DP) ----
O, G = orig_units(ORIG), gram_units(GRAM)
pi = [i for i, (k, _) in enumerate(O) if k != "struct"]
n, m = len(pi), len(G)
sim = [[(r if (r := ratio(O[i][1], G[j])) >= 0.30 else 0.0) for j in range(m)] for i in pi]
best = [[0.0] * (m + 1) for _ in range(n + 1)]; back = [[None] * (m + 1) for _ in range(n + 1)]
for a in range(1, n + 1):
    for j in range(1, m + 1):
        cand = [(best[a - 1][j], "up"), (best[a][j - 1], "left")]
        if sim[a - 1][j - 1] > 0: cand.append((best[a - 1][j - 1] + sim[a - 1][j - 1], "diag"))
        best[a][j], back[a][j] = max(cand)
match = {}; a, j = n, m
while a > 0 and j > 0:
    mv = back[a][j]
    if mv == "diag": match[pi[a - 1]] = j - 1; a -= 1; j -= 1
    elif mv == "up": a -= 1
    else: j -= 1
used = set(match.values())

# ---- sentences ----
ABBR = re.compile(r"(?:\b(?:e\.g|i\.e|vs|cf|Fig|Figs|Sec|Secs|No|Nos|Tab|Prop|Eq|Eqs|Ref|Refs|approx|et al|St|Inc|Ltd|Co|U\.S|a\.m|p\.m|resp)|\b[A-Z])\.$")
def sentences(text):
    stash = []
    def keep(m): stash.append(m.group(0)); return f"\x02{len(stash) - 1}\x03"
    t = CODE.sub(keep, MATH.sub(keep, text))
    out, start = [], 0
    for mm in re.finditer(r"[.!?][\"”’)\]]*\s+(?=[\"“(\[A-Z0-9\x02])", t):
        pre = t[start:mm.end()].rstrip()
        if ABBR.search(pre.split()[-1] if pre.split() else ""): continue
        out.append(pre); start = mm.end()
    if t[start:].strip(): out.append(t[start:].strip())
    return [re.sub(r"\x02(\d+)\x03", lambda m: stash[int(m.group(1))], s) for s in out]

SUSPECT = re.compile(r"[a-z]{2,}[A-Z][a-z]{2,}")
PROPER = ("iShares", "PayPal", "GitHub", "YouTube", "MicroStrategy", "BlackRock", "JPMorgan", "FedEx", "McKinsey", "OpenAI", "LaTeX", "eBay", "iPhone")
def suspicious(t):
    for p in PROPER: t = t.replace(p, "")
    return SUSPECT.search(t) is not None
def clean_gram(g):
    return re.sub(r"\b([A-Z])\1([a-z])", r"\1\2", g)            # "TThe" -> "The"

PLAIN = [(r"\\%", "%"), (r"\\ge", "≥"), (r"\\le", "≤"), (r"\\approx", "≈"), (r"\\times", "×"), (r"\\pm", "±"), (r"\\to", "→"),
         (r"\\sigma", "σ"), (r"\\alpha", "α"), (r"\\nu", "ν"), (r"\\hat ", ""), (r"\\hat", ""), (r"\\mathrm|\\text|\\operatorname", ""),
         (r"[{}]", ""), (r"\\,|\\;|\\ ", " "), (r"\\", "")]
WORDS = {"≥": "greater than or equal to", "≤": "less than or equal to", "≈": "approximately", "×": "by", "→": "to"}

def plain_regex(span):
    p = span.strip("$")
    for a, b in PLAIN: p = re.sub(a, b, p)
    p = re.sub(r"\s+", "", p)
    if not p or len(p) > 40: return None
    pieces = []
    for ch in p:
        if ch in "≥≤≈×→=+<>/": pieces.append(r"\s*(?:" + re.escape(ch) + (("|" + WORDS[ch]) if ch in WORDS else "") + (r"|>=" if ch == "≥" else r"|<=" if ch == "≤" else "") + r")\s*")
        elif ch == "-": pieces.append(r"\s*[-–−]\s*")
        else: pieces.append(re.escape(ch))
    return re.compile("".join(pieces))

def remath(o_sent, g_sent):
    """Put the original math spans back where Grammarly wrote them as plain text."""
    g = re.sub(r"\$([^$\n]{1,60}?)\$", r"\1", g_sent)              # drop Grammarly's own short delimiters
    if "$" in g: return None                                         # stray dollar (currency) would pair with a formula
    for span in MATH.findall(o_sent):
        rx = plain_regex(span)
        if rx is None: return None
        m = rx.search(g)
        if not m: return None
        hit = m.group(0); lead = hit[:len(hit) - len(hit.lstrip())]; trail = hit[len(hit.rstrip()):]
        g = g[:m.start()] + lead + span + trail + g[m.end():]
    return g

TERMS = ("origin", "horizon", "coverage", "consensus", "quantile", "brier", "calibrat", "interval", "band", "shock", "spike",
         "drift", "analog", "base rate", "hit rate", "winkler", "bootstrap", "walk-forward", "point-in-time", "look-ahead",
         "leverage", "volatility", "surprise", "headline", "earnings", "fomc", "payroll", "climatolog", "gate", "kernel",
         "filtration", "exogen", "tautolog", "latency", "continuation", "reversion", "revert", "contrarian", "sharpe", "drawdown",
         "rebalanc", "session", "vote", "signal", "forecast", "bitcoin", "crypto", "index", "stock")
TERM_REJECTS = []

def terms_kept(o_sent, g_sent):
    """Grammarly must not rename technical terms (it turned 'origins' into 'sources')."""
    lo, lg = o_sent.lower(), g_sent.lower()
    missing = [t for t in TERMS if t in lo and t not in lg]
    if missing: TERM_REJECTS.append((missing, o_sent[:90], g_sent[:90]))
    return not missing

def adopt(o_sent, g_sent):
    """Grammarly sentence with the original's math/code/emphasis restored, or None."""
    if not terms_kept(o_sent, g_sent): return None
    om, gm = MATH.findall(o_sent), MATH.findall(g_sent)
    if len(om) != len(gm):
        g_sent = remath(o_sent, g_sent)
        if g_sent is None: return None
        gm = MATH.findall(g_sent)
        if len(om) != len(gm): return None
    if suspicious(MATH.sub("", g_sent)): return None
    outside = MATH.sub("", g_sent)
    if "\\" in outside or "^{" in outside or "_{" in outside: return None
    it = iter(om); g = MATH.sub(lambda m: next(it), g_sent)
    if MATH.findall(g) != om or "$" in MATH.sub("", g): return None
    for c in CODE.findall(o_sent):                                   # backticks
        bare = c.strip("`")
        if c not in g:
            if bare not in g: return None
            g = re.sub(r"(?<![`\w])" + re.escape(bare) + r"(?![`\w])", c, g, count=1)
    for mark in ("**", "*"):                                         # emphasis spans
        for em in re.findall(re.escape(mark) + r"([^*\n]+?)" + re.escape(mark), o_sent):
            if f"{mark}{em}{mark}" in g: continue
            core = em.rstrip(".").rstrip()
            idx = g.lower().find(core.lower())
            if idx < 0: return None
            end = idx + len(core)
            if g[end:end + 1] == ".": end += 1
            g = g[:idx] + f"{mark}{g[idx:end].rstrip('.') if em.endswith('.') else g[idx:end]}{'.' if em.endswith('.') and not g[idx:end].endswith('.') else ''}{mark}" + g[end:]
            g = g.replace(f"{mark}{g[idx+len(mark):end+len(mark)]}{mark}", f"{mark}{em}{mark}") if False else g
    return g

def merge_paragraph(orig, g):
    g = clean_gram(g)
    os_, gs = sentences(orig), sentences(LIST_LINE.sub("", g, count=1))
    lm = LIST_LINE.match(orig); prefix = lm.group(0) if lm else ""
    body = orig[len(prefix):] if prefix else orig
    os_ = sentences(body)
    out, taken, k, j = [], 0, 0, 0
    while k < len(os_):
        o = os_[k]
        # best Grammarly candidate near the cursor
        cands = [(ratio(o, gs[jj]), jj) for jj in range(j, min(j + 3, len(gs)))]
        r, jj = max(cands) if cands else (0.0, None)
        if jj is not None and 0.25 <= r < 0.35: NEAR.append((round(r, 2), o[:110], gs[jj][:110]))
        if jj is None or r < 0.35:
            out.append(o); k += 1; continue
        gsent = gs[jj]
        # Grammarly joined this sentence with the next original one
        if k + 1 < len(os_) and set(words(os_[k + 1])) and len(set(words(os_[k + 1])) & set(words(gsent))) / len(set(words(os_[k + 1]))) >= 0.6 and ratio(os_[k + 1], gsent) < 0.35:
            pair = o + " " + os_[k + 1]
            fixed = adopt(pair, gsent)
            if fixed: out.append(fixed); taken += 2
            else: out.extend([o, os_[k + 1]])
            k += 2; j = jj + 1; continue
        # Grammarly split this sentence in two
        if jj + 1 < len(gs) and set(words(gs[jj + 1])) and len(set(words(gs[jj + 1])) & set(words(o))) / len(set(words(gs[jj + 1]))) >= 0.6 and (k + 1 >= len(os_) or ratio(os_[k + 1], gs[jj + 1]) < 0.35):
            gsent = gsent + " " + gs[jj + 1]; j = jj + 2
        else:
            j = jj + 1
        fixed = adopt(o, gsent)
        if fixed: out.append(fixed); taken += 1
        else: out.append(o)
        k += 1
    return prefix + " ".join(out), taken, len(os_)

NEAR = []
out, stats = [], Counter()
for i, (kind, text) in enumerate(O):
    if kind == "struct" or i not in match:
        out.append(text); stats["struct" if kind == "struct" else "unmatched"] += 1; continue
    g = G[match[i]]; j = match[i] + 1
    if j < m and j not in used and set(words(G[j])) and len(set(words(G[j])) & set(words(text))) / len(set(words(G[j]))) >= 0.6 and not LIST_LINE.match(G[j]):
        g = g + " " + G[j]; used.add(j)
    merged, taken, total = merge_paragraph(text, g)
    ow, mw = len(words(text)), len(words(merged))
    if ow >= 15 and not (0.7 * ow <= mw <= 1.5 * ow):
        out.append(text); stats["length-guard"] += 1; continue
    out.append(merged); stats["sent_taken"] += taken; stats["sent_total"] += total
    stats["para_changed" if merged != text else "para_same"] += 1

merged = "\n\n".join(out) + "\n"
mo, mm = Counter(MATH.findall(ORIG)), Counter(MATH.findall(merged))
co, cm = Counter(CODE.findall(ORIG)), Counter(CODE.findall(merged))
print("stats:", dict(stats))
print("math preserved:", mo == mm, "| code preserved:", co == cm, "| headings:", merged.count("\n#") == ORIG.count("\n#"), "| table rows equal:", sum(l.startswith('|') for l in merged.splitlines()) == sum(l.startswith('|') for l in ORIG.splitlines()), "| figures:", merged.count("\n![") == ORIG.count("\n!["))
if mo != mm: print("  math diff:", (mo - mm).most_common(3), (mm - mo).most_common(3))
if co != cm: print("  code diff:", (co - cm).most_common(3), (cm - co).most_common(3))
new_susp = sorted({t for t in re.findall(r"\w*[a-z]{2,}[A-Z][a-z]{2,}\w*", MATH.sub("", merged))} - {t for t in re.findall(r"\w*[a-z]{2,}[A-Z][a-z]{2,}\w*", ORIG)})
print("new merged-word tokens:", new_susp[:15])
print("term-guard rejections:", len(TERM_REJECTS))
for miss, o, g in TERM_REJECTS[:14]: print(f"  {miss} | O: {o}\n{' '*8}G: {g}")
print("near-miss sentence pairs:", len(NEAR))
for r, o, g in NEAR[:12]: print(f"  {r} | O: {o}\n        G: {g}")
if OUT: OUT.write_text(merged); print("written", OUT)
