# When Does AI Beam Prediction Save Radio Resources?

Final LaTeX delivery after venue and layout checks, 28 September 2026.

`FINAL_LATEX_README.md` explains the current main export. `export_final_latex.py` creates `main.tex` with the bibliography embedded and all four vector figures, including editable TikZ source for Figure 1. Its caption defines C and A. The truthful acknowledgment and factual author biography are restored. The paper contains four figures and two tables. Fresh computational reproduction is recorded in `submission_reproduction/`; it is not a claim of personal reproduction by the human author. Public deposition is not yet completed.

## Current result

Validation selects prior-top-16 (T16) across 22 conventional candidates using the same prior full-bank information. Evaluation succeeds 98.7512% within 3 dB, with tile interval 97.9268–99.4572%. This halves measurements relative to the previous contiguous C32 baseline.

Positive partial-adoption savings replace the previous C32-specific84% threshold. For 64 users at50% adoption, measurements fall 1,024→576 (43.75%), but top4q=.5 saves only 1.0833 CSI-RS occurrences. Top16q=.125 saves 0.9667 at the same average measurement budget. At full adoption the ordering reverses:39.2667 versus55.3792 occurrences. These are conditional per-update accounting results with ideal prediction, not measured deployed AI gains.

Read `RESEARCH_STATUS.md` for results and limitations, `AUTHOR_REPRODUCTION.md` for clean reproduction commands, and `manuscript/beam_magazine.pdf` for the article.

The scientific results are final and unchanged. The acknowledgment identifies the assistance actually performed; it does not imply personal reproduction or completed public deposition.

## Current source and evidence

- `prior_revision/BASELINE_PROTOCOL.json`: amendment frozen before new profile outcomes; earlier scene/results known.
- `prior_revision/prior_baselines.py`: same observations, geometry, corrected weighting and validation selection across 22 candidates.
- `prior_revision/baseline_selection.json`: selection saved before evaluation.
- `prior_revision/qualified_baseline.json`: canonical current baseline/quality record.
- `prior_revision/tracking_validation.*`, `tracking_results.*`: complete1/2/5m evidence.
- `prior_revision/accounting.py`, `ACCOUNTING_PROTOCOL.json`: all resource and activity accounts; historical cohorts preserved.
- `prior_revision/dense_curves.py`: all integer AI counts for 8/16/32/64 users, 30 cohorts, T16/C32 and three equal-budget monitors.
- `prior_revision/verify_baseline_independent.py`, `verify_accounting_independent.py`: independent reconstruction and clean-directory replays.
- `prior_revision/independent_baseline_reconstruction.json`, `independent_accounting_verification.json`: verification records.
- `prior_revision/refresh_sensitivity.py`, `refresh_sensitivity.json`, `REFRESH_SENSITIVITY.md`: explicit replacement-refresh cost sensitivity; no sustained-quality claim.
- `prior_revision/C32_PARITY.json`: unchanged C32 diagnostic outputs.
- `prior_revision/write_manuscript_values.py`, `make_figures.py`: regenerate numerical prose and figures.
- `manuscript/figures/accounting_architecture_vector.pdf` and `.tex`: current vector Figure 1 and its editable TikZ source.
- `prior_revision/make_architecture.py`: regenerate the superseded vector architecture; retained as historical material and not used by the current paper.
- `quality_revision/STANDARDS_CHECK.md`: primary standards/source audit; the conditional 16-resource claim and CFP were rechecked28September.

Analysis runtime: Python 3.12, NumPy 2.3.5, SciPy 1.17.0, Matplotlib 3.10.8. Prepared input data must match SHA256 `f050003222407ea0d6466e064a288d37324397fc72f895894e0742b53473d25e`. See data-pilot documentation for retrieval and its separate environment. Previous cohort and geometry inputs required by the current scripts are included. Do not replace them with new favorable draws.

## Interpret the comparisons

Quality averages current locations uniformly and then eligible previous directions uniformly, matching accounting. The profile selection criterion minimizes per-UE measurements among tested qualifiers, not cell union or global tracker cost. The evaluation gate is the point rate; the full tile interval is also reported.

The primary ledger is one refinement after 1 m displacement, conditioned on an available prior full-bank measurement. Initialization and sustained refresh costs are outside the ledger. Static endpoint pairs cannot establish time-consistent tracking, Doppler or inter-update performance. The optional 80 ms grid represents45km/h through T=D/v and keeps four fixed 20 ms SSB bursts:26,560activeRE and5,160,960 totalgridRE.

EqualKq fixes mean UE measurements, not detection coverage, delay or reliability. Ideal prediction and monitoring rankings are perfect-current-information counterfactuals. Control signaling, uplink scheduling, RX beams, model compute and watts are not evaluated.

At 64users/fulladoption/top4q=.5, sparse CSI-bearing slots change31.9333→13.05; packed 5→2.05. The 16 SSB-bearing slots are unchanged and additional. At half adoption packing releases symbols but no whole CSI-bearing slots. These are fixed-map sensitivities, not validated hardware energy savings.

## Provenance and distribution

`archive/c32_draft/` preserves the preceding manuscript and figures. `quality_revision/`, `revision/`, `archive/tracking_draft/`, `archive/acquisition_draft/`, `experiment/` and `results/` retain earlier studies and amendments. Their claims are historical where superseded here. Original pair-weighted results remain archived; current quality always uses the corrected population weighting.

The source bundle includes current code, results and independent checks. It excludes raw scenario files, prepared channel arrays, third-party packages, model caches, standards PDFs and retrieval snapshots. The old regenerable `revision/accounting_sweep.npz` may be omitted; its endpoint evidence and code are included. Dataset and software licenses remain distinct.

The computational reproductions were executed here by ChatGPT; personal author reproduction and final author approval are not asserted. No public repository was created and no manuscript submitted.
