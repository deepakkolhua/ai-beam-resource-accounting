# When Does AI Beam Prediction Save Radio Resources?
**Cell-Level Accounting for AI-Native 6G — Version 7 research companion**

This public repository contains the version 7 manuscript and scientific materials for Deepak Singh's research on cell-level AI-beam resource accounting. Results are computational research scenarios, **not** claims of deployment-tested energy savings or a formally published journal article.


The final standalone PDF is used here rather than the older PDF copy present inside the revision archive. The version 7 TeX source and supporting figures are included separately.

## Reproduction materials
- [Scientific plotting source, vector figures and provenance](figures/)
- [Audit-phase sensitivity scripts, prepared accounting inputs and saved results](sensitivity/)
- [Second-scene preparation, independent checks, run protocols and outputs](second_scenario/)
- [Validation summary](Validation_Summary.json)

Four NPZ files are stored as numbered binary parts to avoid connector transfer limits; they can be losslessly reconstructed and SHA-256 verified. Run once from the repository root:

```bash
python3 reconstruct_datasets.py
```

The script uses only the Python standard library. It rebuilds the original files and verifies their byte sizes and hashes using [RECONSTRUCTION_MANIFEST.json](RECONSTRUCTION_MANIFEST.json). Then follow [the second-scenario instructions](second_scenario/README.md) and the relevant scripts. To compile the manuscript, use a TeX installation with `pdflatex` and compile `ComMag_Beam_Accounting.tex` twice from the repository root.

## Publication scope and research limits
Research files only: manuscript, figures, code, protocols, prepared inputs, reproducibility metadata and scientific results. Submission correspondence, cover letter, peer-review replies and revision diffs are deliberately excluded from this deposit.

The study uses model-based accounting and conditional oracle-style analysis; realizable signaling, robustness, energy metrology, controller support and practical model computation warrant further validation. Refer to the manuscript's limitations and the protocol records before generalizing the findings.

Some older root-level documents describe earlier repository snapshots and upload plans, and may reference historical paths or archives. **Use this version 7 manifest and the links above for the present scientific deposit.** No DOI, publisher acceptance, or journal publication is asserted here.

Data and third-party components retain their respective rights; no blanket redistributive license is implied. Computational-assistance disclosures appear in the manuscript acknowledgment.
