# arXiv submission notes

## Build

From the repository root:

```bash
uv venv --python 3.12
uv pip install --python .venv/bin/python -r research/requirements-publish.txt
MPLCONFIGDIR=/tmp/mplconfig .venv/bin/python research/arxiv_prefinding.py
MPLCONFIGDIR=/tmp/mplconfig .venv/bin/python research/btc_decline_fans.py
.venv/bin/python research/build_arxiv_prefinding.py
```

Outputs:

- `dist/arxiv_prefinding/preprint.pdf` — local preview
- `dist/arxiv_prefinding_source.tar.gz` — upload this source archive

The source archive contains only `main.tex`, `figure1.pdf`, `figure2.pdf`, and
`figure3.pdf` (the twelve-decline fan chart, set on a landscape page).
At arXiv, select **XeLaTeX** and TeX Live 2025.

## Proposed metadata

- **Primary category:** `q-fin.ST` (Statistical Finance)
- **Title:** *When information breaks the historical pattern: preliminary evidence from a deployed Bitcoin forecaster*
- **Comments:** Preliminary exploratory study; 1 table, 3 figures. The proprietary forecast-generation engine is not included.

Copy the abstract from `paper.md`; it is kept below 100 words so the same draft
can later be adapted for *Finance Research Letters*.

## Required human checks before upload

- [ ] Confirm author names, order, affiliations, and corresponding email.
- [ ] Confirm all authors approve public posting.
- [ ] Rotate the credentials that were present in the local `.env`.
- [ ] Verify or replace the existing Zenodo deposit before adding its DOI.
- [ ] Decide how to remove licensed headline text from prior public Git history;
      the current working tree is scrubbed, but earlier commits may retain it.
- [ ] Push a reviewed, rights-safe commit and use its immutable URL in the paper.
- [ ] Open `preprint.pdf` and inspect every page at 100% zoom.
- [ ] Upload the source archive and confirm arXiv reproduces the local PDF.
- [ ] Review arXiv's generated metadata and select an appropriate distribution
      licence only after confirming rights.
