# Exact audit-phase accounting sensitivity

Executed on the original T16 cohorts (1 m, 64 users, 30 cohorts). This is a post hoc sensitivity, not a new channel experiment. Each UE retains the same periodic audit interval; only its phase is randomized independently. Expectations are calculated exactly, without Monte Carlo.

| AI users | Audit | Synchronized occupied | Independent-phase occupied | Synchronized saved | Independent-phase saved |
|---:|---|---:|---:|---:|---:|
| 32 | top-4 / 2 epochs | 62.183333 | 62.191667 | 1.083333 | 1.075000 |
| 32 | top-16 / 8 epochs | 62.300000 | 62.419615 | 0.966667 | 0.847052 |
| 64 | top-4 / 2 epochs | 24.000000 | 41.496341 | 39.266667 | 21.770325 |
| 64 | top-16 / 8 epochs | 7.887500 | 50.776746 | 55.379167 | 12.489921 |

Synchronized values reproduce all 120 corresponding original cohort cases exactly (zero count/saving error). Two small fixtures at periods 2 and 8 match exhaustive enumeration of all phase assignments. Phase randomization never lowers occupancy for the fixed audit demands.

Interpretation: synchronized audits materially reduce transmission demand near full adoption. At half adoption, the conventional demand floor leaves little extra demand and the phase penalty is smaller. Per-UE average observation counts and intervals are unchanged; error-detection effectiveness is not evaluated. These results must not be described as a trajectory simulation or a measured hardware saving.

Reproduce: `python audit_phase_sensitivity.py --source PATH/TO/prior_revision --output OUTPUT_DIR`

The source NPZ files are required; their SHA-256 hashes are recorded in the JSON. Per-cohort retained beam sets and audit-consumer multiplicities are also saved, permitting independent recomputation of the new expectations without channel data.


## Full adoption-curve extension (17 November 2026)

`audit_phase_dense.py` extends the same exact phase calculation to every integer AI population from 0 to 64 on the original 30 frozen cohorts and nested capability order. It saves per-cohort arrays in `audit_phase_dense_results.npz` and descriptive summaries in `audit_phase_dense_summary.json`. This is additional accounting on existing endpoint data, not a new channel, predictor, or trajectory experiment.

All 3,900 reconstructed synchronized cohort/adoption/design results match the original `dense_curves.npz` values exactly. Retained and audit-update bitmasks match in every case. All 120 independently phased cohort/design cases previously reported at half/full adoption are also reproduced exactly. Four exhaustive small phase fixtures match the analytical expression with zero error.

At full adoption, the ranking reversal occurs in **30 of 30 cohorts**. The synchronized top-sixteen minus top-four savings advantage ranges from 13.50 to 18.875 occurrences/update (mean 16.1125; 5th–95th cohort percentiles 14.225–17.6375). The independent-phase expected top-four minus top-sixteen advantage ranges from 6.386559 to 13.801529 (mean 9.280404; 5th–95th percentiles 6.488540–11.785716). These are paired cohort differences. Cohort spread is descriptive and is not a confidence interval or random-phase simulation interval.

Figure 3 now plots the two headline audit designs under both timing arrangements. Solid lines denote synchronized audits and dashed lines exact independent-phase expectations; shaded regions show the 5th–95th cohort percentiles. The geometric-four synchronized data remain in the original bundled `inputs/dense_curves.npz`.

Reproduce from the package root:

```bash
python sensitivity/audit_phase_dense.py --source sensitivity/inputs --output sensitivity
python figures/plot_equal_budget.py --source sensitivity --output figures
```
