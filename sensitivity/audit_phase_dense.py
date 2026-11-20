#!/usr/bin/env python3
"""Exact phase expectations at every integer adoption on the original cohorts.

Usage: python audit_phase_dense.py --source inputs --output .
No sampling, channel regeneration, learning, or trajectory experiment is done.
The 30 cohorts and nested capability order are read from dense_curves.npz.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_phase_sensitivity import sha, union, expected_count, enumerated_expectation, describe


def run(source, output):
    output.mkdir(parents=True, exist_ok=True)
    dp = source / 'dense_curves.npz'
    tp = source / 'tracking_results.npz'
    ep = source / 'accounting_endpoints.npz'
    # Materialize each required NPZ member once; repeated NPZ indexing otherwise
    # decompresses the large saved curve array at every adoption count.
    with np.load(dp, allow_pickle=False) as archive:
        d = {key: archive[key] for key in archive.files}
    with np.load(tp, allow_pickle=False) as archive:
        t = {key: archive[key] for key in ['current_index', 'distance_m', 'group_T16', 'current_true_rank']}
    with np.load(ep, allow_pickle=False) as archive:
        e = {key: archive[key] for key in ['population_sizes', 'distances_m', 'cohort_tracking_rows', 'capability_order']}
    ni = list(d['population_sizes']).index(64)
    pi = list(d['conventional_profiles']).index('T16')
    mi = list(d['metric_names']).index('csi_saved')
    eni = list(e['population_sizes']).index(64)
    edi = list(e['distances_m']).index(1)
    assert np.array_equal(d['cohort_tracking_rows'][ni], e['cohort_tracking_rows'][edi, eni])
    assert np.array_equal(d['capability_order'][ni], e['capability_order'][edi, eni])
    assert np.array_equal(d['AI_counts'], np.arange(65))

    # A small exhaustive check guards the analytic multiplicity expression.
    fixture_errors = []
    for retained in (set(), {1}):
        for period in (2, 8):
            lists = [[1, 2], [1, 3], [1, 4]]
            analytical, _ = expected_count(retained, lists, period)
            exhaustive = enumerated_expectation(retained, lists, period)
            fixture_errors.append(abs(analytical - exhaustive))
    assert max(fixture_errors) < 1e-12

    designs = [('topk4', 4, 2), ('topk16', 16, 8)]
    synchronized = np.zeros((30, 65, 2))
    independent = np.zeros_like(synchronized)
    baseline = np.zeros(30, dtype=int)
    retained_counts = np.zeros((30, 65), dtype=int)
    parity_errors = []
    for ri in range(30):
        rows = d['cohort_tracking_rows'][ni, ri]
        order = d['capability_order'][ni, ri]
        assert len(np.unique(t['current_index'][rows])) == 64
        assert np.all(t['distance_m'][rows] == 1)
        groups = t['group_T16'][rows]
        baseline[ri] = len(union(groups))
        for n_ai in range(65):
            is_ai = np.zeros(64, dtype=bool)
            is_ai[order[:n_ai]] = True
            retained = union(groups[~is_ai])
            retained_counts[ri, n_ai] = len(retained)
            # Reconstruct each retained mask independently from source rows.
            mask = sum(1 << b for b in retained)
            assert mask == int(d['ordinary_masks'][ni, ri, pi, n_ai])
            for ji, (name, k, period) in enumerate(designs):
                dji = list(d['design_names']).index(name)
                assert d['design_q'][dji] == 1 / period
                audit = t['current_true_rank'][rows[is_ai], :k]
                audit_union = union(audit)
                # Saved audit_masks include retained demand in an audit update.
                audit_mask = sum(1 << b for b in (audit_union | retained))
                assert audit_mask == int(d['audit_masks'][ni, ri, pi, n_ai, dji])
                sync = len(retained) + len(audit_union - retained) / period
                indep, _ = expected_count(retained, audit, period)
                synchronized[ri, n_ai, ji] = baseline[ri] - sync
                independent[ri, n_ai, ji] = baseline[ri] - indep
                saved = d['per_cohort'][ni, ri, pi, n_ai, dji, mi]
                parity_errors.append(abs(synchronized[ri, n_ai, ji] - saved))
                assert parity_errors[-1] < 1e-12
                assert indep + 1e-12 >= sync
                assert indep <= len(retained) + sum(len(set(map(int, row)) - retained) for row in audit) / period + 1e-12

    sync_advantage = synchronized[:, -1, 1] - synchronized[:, -1, 0]
    independent_advantage = independent[:, -1, 0] - independent[:, -1, 1]
    reversal = (sync_advantage > 0) & (independent_advantage > 0)
    np.savez_compressed(output / 'audit_phase_dense_results.npz',
        AI_counts=np.arange(65), design_names=np.array([x[0] for x in designs]),
        audit_K=np.array([x[1] for x in designs]), audit_periods=np.array([x[2] for x in designs]),
        synchronized_saved=synchronized, independent_expected_saved=independent,
        baseline_occurrences=baseline, retained_occurrences=retained_counts,
        cohort_tracking_rows=d['cohort_tracking_rows'][ni], capability_order=d['capability_order'][ni])

    result = {
        'analysis_date': '2026-11-17',
        'type': 'Exact phase-accounting extension on the existing frozen cohorts; no new channel experiment.',
        'source_files': {str(p): sha(p) for p in (dp, tp, ep)},
        'script_sha256': sha(__file__),
        'formula': '|R| + sum over b outside R of [1-(1-1/L)^m_b]; phases independent uniform, one audit per UE per L updates.',
        'population': 64, 'profile': 'T16', 'distance_m': 1, 'cohorts': 30,
        'counts': list(range(65)),
        'spread_definition': 'Linear-interpolated 5th and 95th percentiles across 30 fixed cohorts; descriptive spread, not a confidence interval.',
        'validation': {
            'original_synchronized_cohort_adoption_design_cases': len(parity_errors),
            'original_synchronized_max_abs_error': max(parity_errors),
            'small_fixture_exhaustive_phase_max_abs_error': max(fixture_errors),
            'retained_and_audit_bitmasks_match_original_all_cases': True,
            'cohorts_and_capability_order_match_original_endpoints': True,
            'independent_occupancy_ge_synchronized_all_cases': True,
            'independent_occupancy_union_bound_all_cases': True,
        },
        'full_adoption': {
            'ranking_reversal_cohorts': int(reversal.sum()), 'total_cohorts': 30,
            'synchronized_top16_minus_top4_saved': describe(sync_advantage),
            'independent_top4_minus_top16_expected_saved': describe(independent_advantage),
        },
        'curves': {},
    }
    for ji, (name, k, period) in enumerate(designs):
        result['curves'][name] = {'K': k, 'period': period}
        for timing, data in [('synchronized', synchronized), ('independent', independent)]:
            result['curves'][name][timing] = {
                'mean': np.mean(data[:, :, ji], axis=0).tolist(),
                'p05': np.quantile(data[:, :, ji], .05, axis=0).tolist(),
                'p95': np.quantile(data[:, :, ji], .95, axis=0).tolist(),
            }
    (output / 'audit_phase_dense_summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'validation': result['validation'], 'full_adoption': result['full_adoption']}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    run(args.source.resolve(), args.output.resolve())
