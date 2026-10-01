# Personal reproduction from a clean source checkout

These commands are for the author to execute. The computational runs already recorded in this package were executed by ChatGPT. Their records cannot establish that a named human author personally reproduced the study.

1. Extract the source ZIP into a new directory. Use Python 3.12 with NumPy 2.3.5, SciPy 1.17.0 and Matplotlib 3.10.8 for the analysis. The data generator has its own requirements in `data_pilot/requirements.txt`.
2. Follow `data_pilot/README.md` to retrieve and prepare the public scenario. The prepared `data_pilot/prepared/beam_data.npz` SHA256 must be:
   `f050003222407ea0d6466e064a288d37324397fc72f895894e0742b53473d25e`.
   Raw/prepared channels are not redistributed in this package. A differing digest needs investigation before comparing results.
3. From the extracted `beam_magazine/` directory, run:

```sh
python prior_revision/prior_baselines.py
python prior_revision/verify_baseline_independent.py
python prior_revision/accounting.py
python prior_revision/dense_curves.py
python prior_revision/verify_accounting_independent.py
python prior_revision/refresh_sensitivity.py
python prior_revision/write_manuscript_values.py
python prior_revision/make_figures.py
```

The verifiers independently reconstruct the results and run clean copied-directory replays. They do not only check that output files exist. Historical cohort inputs are included and must not be resampled.

Current Figure 1 is `manuscript/figures/accounting_architecture_vector.pdf`, with editable TikZ source of the same basename. It is conceptual vector artwork, not an experimental output. To regenerate it, run pdfLaTeX on `accounting_architecture_vector.tex` from that figures directory. The earlier raster and vector designs are historical material only.

4. Compile from `manuscript/`:

```sh
pdflatex -interaction=nonstopmode -halt-on-error beam_magazine.tex
pdflatex -interaction=nonstopmode -halt-on-error beam_magazine.tex
```

Expected primary outputs: T16 selected; evaluation success 0.9875118131497234;64-user half-adoption top4/top16 saved occurrences 1.0833333333/0.9666666667; full-adoption 39.2666666667/55.3791666667. Verifiers should pass, including C32 historical parity. PDF bytes may differ due to compiler/platform timestamps and do not determine scientific equality.

5. Retain your terminal logs, environment versions, input hash and verifier reports, and read the generated manuscript. Only after personally executing and checking the run is wording such as “the author independently reproduced the results” supported. Change the acknowledgment to describe the actual division of work while retaining applicable assistance disclosure.

The public-repository destination, final author approval and submission are not supplied or performed by these scripts.

## Final acknowledgment after your completed run

The current manuscript already discloses the AI system, its contributions and affected sections. After you personally complete the run, verify the outputs and approve the manuscript, you may add this factual sentence:

> The author independently reproduced all reported results from the companion package and takes responsibility for them.

Do not replace the existing disclosure with a narrower claim that ChatGPT was used only for grammar or coding; it also contributed manuscript text, plotting and computation. No sentence asserting your personal completion has been inserted automatically.

The current acknowledgment accurately reports the computational assistance and checks. It does not assert human-author reproduction or an existing public deposit. After those steps are complete, add only the corresponding truthful statement and real public DOI or repository URL. The fresh computational rerun is documented in `submission_reproduction/`; it regenerates outputs from the hash-verified prepared input and does not re-download or re-simulate the underlying ray-traced scene.
