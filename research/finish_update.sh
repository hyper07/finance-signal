#!/usr/bin/env zsh
# Finish the paper update after integrate_findings.py was prepared (2026-09-06).
# Run from the repository root:   zsh research/finish_update.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY="$PWD/.venv/bin/python"      # absolute: step 1 runs inside research/

echo "== 1. integrate the new sections into PAPER.md (idempotent) =="
(cd research && $PY integrate_findings.py)

echo "== 2. regenerate LaTeX (main paper; companions unchanged) =="
$PY research/to_latex.py

echo "== 3. arXiv and Overleaf packages: flatten figure paths, copy the five new figures =="
$PY - <<'EOF'
import re
from pathlib import Path
src = Path("research/paper.tex").read_text()
for f in sorted(set(re.findall(r"\\includegraphics\[[^\]]*\]\{(output/figures/[^}]+)\}", src))):
    src = src.replace(f"{{{f}}}", f"{{{Path(f).name}}}")
Path("research/arxiv/paper.tex").write_text(src); Path("research/overleaf/main.tex").write_text(src)
print("figures referenced:", len(set(re.findall(r"includegraphics\[[^\]]*\]\{([^}]+)\}", src))))
EOF
for f in fig15_btc_declines_fan fig16_btc_prolonged_declines fig17_swing_legs_by_asset fig18_leg_anatomy fig19_band_ribbon; do
  cp research/output/figures/$f.png research/arxiv/ && cp research/output/figures/$f.png research/overleaf/
done

echo "== 4. compile check (tectonic; strip the pdfoutput line it rejects) =="
rm -rf /tmp/tc && mkdir -p /tmp/tc && cp research/arxiv/*.png /tmp/tc/ && grep -v '^\\pdfoutput=1$' research/arxiv/paper.tex > /tmp/tc/paper.tex
(cd /tmp/tc && /tmp/tectonic -X compile paper.tex --outfmt pdf --keep-logs 2>&1 | grep -iE "^error|fatal" || true
 echo "overfull: $(grep -c Overfull paper.log || true)")
PAGES=$($PY -c "from pypdf import PdfReader; print(len(PdfReader('/tmp/tc/paper.pdf').pages))")
FIGS=$(grep -c '^!\[Figure' research/PAPER.md); TABS=$(grep -c '^\*\*Table [0-9]' research/PAPER.md)
echo "pages: $PAGES | figures: $FIGS | tables: $TABS"
cp /tmp/tc/paper.pdf research/arxiv/paper_preview.pdf
sed -i '' -E "s/\*\*[0-9]+ pages, [0-9]+ figures/**$PAGES pages, $FIGS figures/; s/^[0-9]+ pages, [0-9]+ figures, [0-9]+ tables\./$PAGES pages, $FIGS figures, $TABS tables./" research/arxiv/ARXIV_SUBMISSION.md
(cd research/arxiv && tar -czf ../arxiv_submission.tar.gz paper.tex fig*.png)
(cd research/overleaf && rm -f ../overleaf_project.zip && zip -q ../overleaf_project.zip main.tex fig*.png)
$PY -c "
import re; from pathlib import Path
s = Path('research/PAPER.md').read_text(); a = re.search(r'## Abstract\n\n(.+?)\n', s).group(1)
Path('research/arxiv/abstract.txt').write_text(re.sub(r'\*([^*]+)\*', r'\1', a) + '\n')"

echo "== 5. public repository sync =="
DST=/Users/kibaek/Documents/Github/finance-signal-public/research
cp research/PAPER.md $DST/PAPER.md && cp research/papers/ijf_full/paper.md $DST/papers/ijf_full/paper.md
cp research/integrate_findings.py research/finish_update.sh $DST/
(cd /Users/kibaek/Documents/Github/finance-signal-public && git add -A && git -c user.name="Kibaek Kim" -c user.email="kibaek.kim2018@gmail.com" commit -q -m "Paper: band vs volatility formula (§4.1), Bitcoin decreases (§5.8), legs and horizons (§6.6-6.7), regime layer (§8.3)" && git log --oneline -1)
echo "done. Remaining by hand: republish the web page (see notes), push the public repo."
