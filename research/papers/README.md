# Submission package

**Authors:** Kibaek Kim, Kiok Kim, Danielle Ahn (dotori.ai). Confirm the author
order, affiliations, correspondence email, and unanimous approval before upload.

## Current publication path

| folder | purpose | status |
|---|---|---|
| `frl_submission/` | Focused *Finance Research Letters* package | **Draft package prepared; external actions remain** |
| `arxiv_prefinding/` | Preprint version of the same narrow paper | **Prepared for author and rights review** |
| `ijf_full/` | Legacy full audit | **Not submission-ready** |
| `frl_short/` | Legacy short journal draft | **Superseded by `frl_submission/`** |
| `jbef_behavioral/` | Behavioral interpretation | **Parked; behavior was not measured** |
| `frontiers_perspective/` | Future research agenda | **Parked and incomplete** |

Do not submit the legacy manuscripts in parallel. Their overlap, statistical
methods, claims, figures, and metadata require separate revision.

## Build the FRL package

Install Tectonic, then run:

```bash
.venv/bin/python research/build_frl_submission.py
```

The build reruns the block-length and threshold checks, generates one combined
vector figure, compiles the double-spaced nine-page manuscript, validates the
2,500-word, 14-page, and highlight limits, and writes
`frl_submission/frl_submission_DRAFT.zip`.

See [`frl_submission/README_SUBMISSION.md`](frl_submission/README_SUBMISSION.md)
and [`frl_submission/SUBMISSION_CHECKLIST.md`](frl_submission/SUBMISSION_CHECKLIST.md).

## Build the preliminary preprint

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r research/requirements-publish.txt
MPLCONFIGDIR=/tmp/mplconfig .venv/bin/python research/arxiv_prefinding.py
.venv/bin/python research/build_arxiv_prefinding.py
```

The build creates:

- `dist/arxiv_prefinding/preprint.pdf`
- `dist/arxiv_prefinding_source.tar.gz`

See [`arxiv_prefinding/README_SUBMISSION.md`](arxiv_prefinding/README_SUBMISSION.md)
for the upload checklist. Select XeLaTeX at arXiv.

## Claims allowed in this version

- This one deployed historical-pattern forecaster has little next-session
  directional separation on average.
- Its forecast distribution fails conditionally on outcome-defined large moves.
- Headline-count spikes are associated with larger standardized errors, but the
  directional relationship is not replicated across BTC and BITO.
- The results motivate prospective research into news content and direct measures
  of investor behavior.

Do not claim that all news breaks predictions, that information events are
exogenous, that human behavior was observed, or that the results establish a
universal accuracy ceiling.

## External blockers before arXiv upload

1. Rotate the credentials that were present in the local `.env`.
2. Confirm rights for the existing Zenodo deposit and earlier Git history.
   Current catalogue outputs contain counts and hashes rather than licensed
   headline text, but prior public versions may retain that text.
3. Publish or identify an immutable, rights-safe code commit.
4. Confirm all author and affiliation metadata.
