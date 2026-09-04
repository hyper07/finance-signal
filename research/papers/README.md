# Submission package

Four manuscripts derived from one study, each aimed at a different venue. They share
code, data and the deposit manifest (`../DATA_DEPOSIT.md`); they do **not** share
text beyond the method summary, and no two are under review at the same venue.

| folder | manuscript | venue (first choice → fallback) | length | status |
|---|---|---|---|---|
| `ijf_full/` | *When the News Arrives* — the full audit (crypto, index, 50 stocks; propositions; sequential tests; calendar events; gap; gate experiment; action policies; entry‑delay rule) | **IJF special issue "The Future of Forecasting: Bridging Theory and Practice"** (deadline 15 Jan 2027) → *Quantitative Finance* → *Journal of Forecasting* → *EPJ Data Science* | ~14k words, 20 tables + Appendix E | **final draft v1.0** (`../PAPER.md`, `paper.tex`) |
| `frl_short/` | *Confidently wrong on the news* — crypto results only | *Finance Research Letters* (rolling) | ~2,600 words, 2 tables, 1 figure | **final draft v1.0** |
| `jbef_behavioral/` | *After the news: post‑shock drift, model latency and how users act on a multi‑day forecast* | *Journal of Behavioral and Experimental Finance* (rolling) → *Journal of Behavioral Finance* | ~5,600 words, 5 tables, 3 figures | **final draft v1.0** |
| `frontiers_perspective/` | *Why price‑pattern forecasters fail when people react* — the neuroeconomic agenda | *Frontiers in Behavioral Neuroscience* (Perspective) → *Frontiers in Neuroscience – Decision Neuroscience* | ~3,000 words, 1 schematic (to draw) | **final draft v1.0** |

## Rules that govern the package

1. **Exclusivity.** The IJF special issue requires that the full paper is not under
   consideration elsewhere. Submit the full paper to *one* venue at a time. The
   three companions are distinct papers (different question, different results
   emphasised, < 15% textual overlap) and may be submitted in parallel.
2. **Preprint first.** Post the full paper to arXiv (q‑fin.ST, cross‑list q‑fin.TR,
   cs.LG) and SSRN before any journal submission; cite the arXiv ID in the
   companions. All target journals permit preprints.
3. **Data.** Data deposit: Zenodo DOI 10.5281/zenodo.22308637 (inserted in every manuscript's data statement). Check Alpaca and
   Yahoo redistribution terms; if raw bars may not be redistributed, deposit the
   SHA‑256 manifest plus pull scripts (sufficient for verification).
4. **Conflict of interest.** Every manuscript carries the same disclosure: the
   author operates the audited service; rules were fixed before scoring; the model
   was not changed during the study.
5. **Attribution flags.** Two Microsoft event attributions (2010‑09‑13, 2011‑01‑06)
   rest on the event date only and are marked † wherever they appear.

## Build

```bash
.venv/bin/python research/to_latex.py                       # full paper -> research/paper.tex
.venv/bin/python research/papers/build_companions.py        # companions -> papers/*/paper.tex
```
Compile with xelatex/lualatex (Unicode). Journal templates: IJF/Elsevier `elsarticle`,
T&F `interact` (QF), Wiley (JoF), Frontiers LaTeX template — swap the preamble, keep the body.

## Submission plan (decided 2026-09-04)

| step | when | action |
|---|---|---|
| 1 | this week | Zenodo deposit: upload the bundle in `../deposit/` (own_inputs.zip, news_daily_counts.csv, derived_outputs.zip, RAW_INPUTS_MANIFEST.md, README_DEPOSIT.md; metadata in zenodo_metadata.json). Licensed raw bars and news text are **not** uploaded — only their SHA-256 and pull commands. DOI reserved: 10.5281/zenodo.22308637 — pasted into all four data statements; publish the record after uploading. |
| 2 | this week | compile `ijf_full/paper.tex` (xelatex), fix figure placement, one cold proofread; post to **arXiv q‑fin.ST** (cross‑list q‑fin.TR, cs.LG) and **SSRN** |
| 3 | after arXiv ID | submit **FRL short** (*Finance Research Letters*) and **Frontiers perspective** (*Frontiers in Behavioral Neuroscience*, Perspective) — both cite the arXiv ID |
| 4 | after arXiv ID | submit **JBEF behavioral** (*Journal of Behavioral and Experimental Finance*) |
| 5 | Oct–Dec 2026 | strengthen the full paper for the **IJF special issue** (deadline 15 Jan 2027): move Tables 2, 3, 10, 12, 13 to the online appendix; add BLS exact payroll dates; optional small‑cap / altcoin extension |
| 6 | 15 Jan 2027 | submit full paper to the IJF special issue; if declined (decisions Apr 2027) → *Quantitative Finance* → *Journal of Forecasting* → *EPJ Data Science* |
| alt | any time | if speed matters more than the IJF shot, submit the full paper to *Quantitative Finance* or *Journal of Financial Data Science* now instead of step 6 (not both — exclusivity) |
| opt | later | fifth note on the type‑dependent rebalancing bonus (needs a 1990s→ sample, AGG/IEF, Ledoit–Wolf test) for *Finance Research Letters* |

## Order of operations for the week (original)

| day | task |
|---|---|
| 1 | cross‑section (50 stocks) and gate experiment — done in this repo |
| 2 | fold results into the full paper (done: §5.7, §6.5; tables renumbered 1–18); optionally move Tables 2, 3, 10, 12, 13 to an online appendix for length; proofread voice |
| 3 | compile LaTeX for all four; fix figure placement; final numbers check against `output/*.json` |
| 4 | Zenodo deposit → DOI; arXiv + SSRN submission of the full paper |
| 5 | submit FRL short paper and Frontiers perspective; hold JBEF until arXiv ID is live; decide IJF‑SI vs QF for the full paper |
