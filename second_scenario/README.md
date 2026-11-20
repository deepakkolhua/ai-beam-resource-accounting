# Second-scene check: Los Angeles

This directory runs the existing quality-qualification and cell-union accounting
method on the public `city_1_losangeles_28` DeepMIMO scenario. The scene was chosen
as the next numbered distinct city in the same 28-GHz scenario family, before
examining its channel-quality or accounting results. No second-scene tuning,
candidate-family addition, seed search or scenario replacement was performed.
The dated protocol and provenance files are internal records, not an external
preregistration.

## Result

The unchanged 22-profile validation rule selects **L2x3**, two separated
three-beam neighborhoods (six measurements). Validation success within 3 dB is
97.095%, with a tile-bootstrap 95% interval of 95.175–98.572%. The unchanged
profile attains 95.877% on evaluation, interval 92.878–97.997%. It passes the
original evaluation **point-estimate** gate of 95%; its evaluation interval
does not lie wholly above 95%. Fixed T16, retained as a separate sensitivity,
attains 98.417% on evaluation, interval 97.471–99.230%.

The evaluation population contains 9,102 one-metre directional pairs, 2,496
distinct current locations and 14 geographic tiles. For 30 cohorts of 64 UEs,
the selected baseline transmits a mean of 52.7 shared occurrences per update.

| Adoption | Audit design | Synchronized savings | Independent-phase expected savings |
|---|---|---:|---:|
| 50% | Top-four / two updates | 5.466667 | 5.227083 |
| 50% | Top-sixteen / eight updates | 5.470833 | 0.497051 |
| 100% | Top-four / two updates | 30.900000 | 17.573225 |
| 100% | Top-sixteen / eight updates | 44.750000 | 5.251303 |

At full adoption, the expected ranking reverses in all 30 cohorts. The paired
synchronized top-sixteen advantage ranges from 10.5 to 17.5 occurrences; the
independent-phase top-four advantage ranges from 9.315290 to 15.613353.
Independent-phase top-sixteen savings are negative in 3 of 30 cohorts (minimum
−4.437413), despite the positive mean. These are expectations over independent
uniform audit phases conditional on each saved cohort, not statements about
every possible realized phase assignment.

## Reproduce

Use Python 3.12 with the pinned dependencies in `requirements.txt`. From the
revision package root, install into a separate environment and run:

```bash
python -m pip install -r second_scenario/requirements.txt
python second_scenario/download_losangeles.py --output work/losangeles
python second_scenario/prepare_scenario.py --raw work/losangeles/raw --archive work/losangeles/city_1_losangeles_28.zip --output work/losangeles/prepared
python second_scenario/run_pipeline.py --data work/losangeles/prepared/beam_data.npz --output work/losangeles/results
```

To rerun only qualification and accounting using the bundled prepared arrays:

```bash
python second_scenario/run_pipeline.py --data second_scenario/prepared/beam_data.npz --output work/losangeles_rerun
```

The official 33,633,360-byte ZIP has SHA-256
`3eb62ebc424a4008bc14e286672adec55010809c5024424b0384134a3f6928d7`.
Raw source files remain unchanged. The prepared `beam_data.npz` has SHA-256
`5f86ccfaf431441b12309d833115d3b09ec7b184445f12247976b7efde8a3fb8`.
ZIP timestamps can change across regeneration; compare numerical arrays rather
than requiring an NPZ container byte hash to remain identical.

## Controls preserved

- First numerical TX set/index and RX set: TX set 1, TX index 0, RX set 0.
- One 64-element half-wavelength ULA, 64 DFT beams, one receive antenna,
  up to 25 paths, and one OFDM frequency sample with the original 512-subcarrier
  and 10-MHz generator parameters.
- Original 20-m tiles, 2-m boundary guards and SHA256 geographic split.
- Original 0.5-dB noise, 1-dB quantization and seeds 341993/341994.
- Identical 22 candidate profiles, prior-only candidate construction, low-index
  tie rules, 2,000-replicate geographic bootstrap and seed 341995.
- The validation selection is written before evaluation outcomes; the original
  95% lower-bound selection gate and 95% evaluation point gate are unchanged.
- Exact x/y endpoint displacement checks at 1, 2 and 5 m, tolerance 0.001 m.
- Cohort seed 202609251 and the original sampling loop over distances 1/2/5 m,
  population sizes 8/16/32/64 and 30 replicates. Each UE has one uniformly chosen
  eligible prior point; adoption is nested through a random capability order.
- Top-four every second update and top-sixteen every eighth update, each costing
  two average observations per AI UE. The phase ledger covers every integer
  adoption count without further sampling.

`helpers/prior_baselines.py` and `helpers/original_prepare_data.py` are unmodified
copies of the original analysis/preparation modules. The wrappers remove the
original New-York-specific filenames and parent-result hash dependencies; they
retain the underlying split, channel, candidate, noise and bootstrap algorithms.

## Scope

The second scene adds a distinct simulated propagation environment. It is still
an error-free oracle with ideal audit rankings, static endpoint demands, one
base station per scene and one receive antenna. It does not supply a learned
predictor, dynamic channel trajectories, measured RF performance or practical
resource-control validation. The two scene-specific selected baselines differ
(New York T16; Los Angeles L2x3), so their absolute savings should not be presented
as an identical-baseline cross-city performance comparison. Fixed-T16 results
are retained separately for that sensitivity.

The original source data and DeepMIMO software retain their respective terms;
this package does not assign a new license to them. The downloader records the
official API and archive provenance.

## Independent numerical check

Run `python second_scenario/verify_independent.py` from the package root.
The included INDEPENDENT_QA.json records reconstruction of candidate sets,
quality intervals, cohort sampling and 7,800 phase values (maximum difference
3.55e-14). The DeepMIMO channel synthesizer was not independently reimplemented.
