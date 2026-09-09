# Finance Research Letters submission handoff

This folder is the focused journal package. The manuscript reports a
reliability-boundary finding; it does not claim that headline volume causes
returns or that investor behavior was measured.

## Files

- `paper.md`, `paper.tex`, `paper.pdf` — review manuscript
- `Title_Page.md` — contact, affiliation, conflict, and funding template
- `Highlights.txt` — mandatory separate highlights file
- `Cover_Letter.md` — journal-specific cover letter
- `Author_Confirmation_Form.md` — authorship and CRediT decisions
- `SUBMISSION_METADATA.md` — copy-ready Editorial Manager fields
- `SUBMISSION_CHECKLIST.md` — final upload sequence
- `fig_frl_combined.pdf` — journal-ready vector figure
- `frl_robustness.json` — complete block-length and threshold checks

## Confirmed journal requirements on 8 September 2026

- Body text: fewer than 2,500 words.
- Complete paper: no more than 14 pages.
- Review manuscript: double-spaced, with figures and tables near their citations.
- Highlights: a separate editable file with 3–5 bullets, each at most 85 characters.
- New submissions may use one Word or PDF file under “Your Paper Your Way.”
- Submission fee: USD 200, non-refundable, including for a desk rejection.
- Submission site: <https://www.editorialmanager.com/frl/default.aspx>.
- Preprints are permitted and do not count as prior publication.

Source: the official *Finance Research Letters* Guide for Authors,
<https://www.sciencedirect.com/journal/finance-research-letters/publish/guide-for-authors>.

## Build

From the repository root:

```bash
.venv/bin/python research/build_frl_submission.py
```

The builder requires Tectonic on `PATH`; it reruns the analyses and figure,
compiles the manuscript, validates the journal limits, and writes
`frl_submission_DRAFT.zip`.

The package is not upload-ready until all bracketed author fields are replaced,
all authors approve, and the data/repository rights checks in
`SUBMISSION_CHECKLIST.md` are complete.
