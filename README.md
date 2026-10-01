# When Does AI Beam Prediction Save Radio Resources?

Companion code, manuscript, vector figures and verification records for the paper by Deepak Singh, Kyungpook National University.

## Paper and figures

- [Manuscript PDF](manuscript/beam_magazine.pdf)
- [LaTeX source](manuscript/beam_magazine.tex)
- [Editable architecture figure](manuscript/figures/accounting_architecture_vector.tex)
- [Reproduction instructions](AUTHOR_REPRODUCTION.md)
- [Computational reproduction report](submission_reproduction/REPRODUCTION_REPORT.md)

## Results and scope

The validation-selected conventional profile is prior-top-16 (T16). Evaluation success within 3 dB is 98.7512%. With 64 users and 50% AI adoption, UE measurements fall from 1,024 to 576, while top-4 audits at duty 0.5 save 1.0833 CSI-RS occurrences per refinement epoch. At full adoption, top-4 and top-16 audits at equal average UE measurement budget save 39.2667 and 55.3792 occurrences, respectively.

These are conditional resource-accounting results with ideal prediction, not measured deployed AI gains. Equal measurement budget does not imply equal monitoring reliability. See the manuscript for assumptions and limits.

## Reproduce the study

Use the complete `Beam_Prediction_LaTeX_and_Code.zip` attached to release `v1.0.0` once it has been uploaded, then follow `AUTHOR_REPRODUCTION.md` inside its `beam_magazine/` folder. The complete ZIP includes archived studies and large numerical outputs omitted from this browsable source tree. If the release is absent, deposition is still incomplete.

The repository also includes the three prior cohort/geometry NPZ inputs required by the current pipeline in `quality_revision/`. Raw and prepared third-party channel data are excluded from both distributions. Retrieve and prepare them using `data_pilot/README.md`; the required input SHA-256 is recorded in `AUTHOR_REPRODUCTION.md`. Do not resample the frozen historical cohorts.

The analysis uses Python 3.12, NumPy 2.3.5, SciPy 1.17.0 and Matplotlib 3.10.8. Data preparation has separate requirements. To compile the article, run pdfLaTeX twice on `beam_magazine.tex` from `manuscript/`.

## Complete package integrity

File: `Beam_Prediction_LaTeX_and_Code.zip`

SHA-256:
```
85752662835601ee9c37e0eb82e89807a439c5331356c3feda0c201dbbeb135b
```

`SOURCE_PACKAGE_MANIFEST.json` describes that complete ZIP; it is not a manifest of this smaller Git tree. `GITHUB_SOURCE_MANIFEST.json` records the files in this upload tree. `SNAPSHOT_README.md`, `DEPOSIT_README.md` and other dated records preserve the state when the verified snapshot was prepared. Their statements that deposition was pending are historical records, not evidence that a later upload failed.

## Provenance and citation

ChatGPT assisted with drafting, code, figures and executing the recorded computational checks. Those checks do not establish personal reproduction by the human author. The manuscript acknowledgment preserves the assistance disclosure.

After publishing, add the actual repository/release URL to `CITATION.cff` and the manuscript. No DOI or completed publication is claimed here. Dataset and third-party software rights remain separate; no blanket license has been assigned.
