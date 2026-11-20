#!/usr/bin/env python3
"""Exact audit-phase sensitivity on saved, frozen T16 cohorts.

Usage: python audit_phase_sensitivity.py --source PATH/TO/prior_revision --output DIR
Requires Python 3 and numpy. No channel regeneration, training, or Monte Carlo.
For each fixed endpoint/cohort, every AI UE audits once each L epochs. In the
synchronized arm all phases coincide. In the independent-phase arm each UE's
phase is uniformly and independently selected from 0..L-1. Its interval remains
L epochs. Results are expectations over phase assignments and one full period;
they are NOT a time-varying channel or a detection-performance experiment.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def union(rows):
    return set(int(x) for row in rows for x in row)


def expected_count(retained, audit_lists, period):
    """A resource with m consumers is needed with probability 1-(1-1/L)^m."""
    multiplicity = np.zeros(64, dtype=int)
    for row in audit_lists:
        for b in set(map(int, row)):
            multiplicity[b] += 1
    eligible = np.ones(64, dtype=bool)
    eligible[list(retained)] = False
    q = 1.0 / period
    extra = float(np.sum(1-(1-q)**multiplicity[eligible]))
    return len(retained)+extra, multiplicity


def enumerated_expectation(retained, audit_lists, period):
    counts=[]
    for phases in itertools.product(range(period), repeat=len(audit_lists)):
        per_epoch=[]
        for epoch in range(period):
            per_epoch.append(len(retained | union([a for a,p in zip(audit_lists,phases) if p==epoch])))
        counts.append(sum(per_epoch)/period)
    return sum(counts)/len(counts)


def describe(x):
    return {'mean':float(np.mean(x)), 'p05':float(np.quantile(x,.05)),
            'p95':float(np.quantile(x,.95)), 'min':float(np.min(x)), 'max':float(np.max(x))}


def run(source, output):
    output.mkdir(parents=True,exist_ok=True)
    tp=source/'tracking_results.npz'; ep=source/'accounting_endpoints.npz'
    t=np.load(tp,allow_pickle=False); e=np.load(ep,allow_pickle=False)
    di=list(e['distances_m']).index(1); ni=list(e['population_sizes']).index(64)
    pi=list(e['conventional_profiles']).index('T16')
    metric=list(e['metric_names']).index('csi_beams')
    smetric=list(e['metric_names']).index('csi_saved')
    fixture_results=[]
    for retained,lists in [(set(), [[1,2],[1,3],[1,4]]),({1},[[1,2],[1,3],[1,4]])]:
        for period in (2,8):
            calculated,_=expected_count(retained,lists,period)
            enumerated=enumerated_expectation(retained,lists,period)
            assert abs(calculated-enumerated)<1e-12
            fixture_results.append({'retained':sorted(retained),'lists':lists,'period':period,
                                    'analytic':calculated,'enumerated':enumerated})
    cases=[]; parity_errors=[]
    for n_ai in (32,64):
        ai=list(e['adoption_fractions']).index(n_ai/64)
        for k,period in ((4,2),(16,8)):
            q=1/period; ji=list(e['design_names']).index(f'topk{k}')
            records=[]
            for ri in range(30):
                rows=e['cohort_tracking_rows'][di,ni,ri,:64]
                order=e['capability_order'][di,ni,ri,:64]
                assert len(np.unique(t['current_index'][rows]))==64
                assert np.all(t['distance_m'][rows]==1)
                is_ai=np.zeros(64,dtype=bool); is_ai[order[:n_ai]]=True
                groups=t['group_T16'][rows]; audit=t['current_true_rank'][rows[is_ai],:k]
                base=union(groups); retained=union(groups[~is_ai]); all_audit=union(audit)
                sync=len(retained)+q*len(all_audit-retained)
                independent,multiplicity=expected_count(retained,audit,period)
                endpoint=e['endpoints'][di,ni,ri,pi,ai,ji]
                expected=(1-q)*endpoint[0,metric]+q*endpoint[1,metric]
                esaved=(1-q)*endpoint[0,smetric]+q*endpoint[1,smetric]
                parity_errors += [abs(sync-expected),abs(len(base)-sync-esaved)]
                assert abs(sync-expected)<1e-12
                assert abs(len(base)-sync-esaved)<1e-12
                assert independent+1e-12>=sync
                # The union bound also provides an independent sanity bound.
                assert independent<=len(retained)+q*sum(len(set(map(int,row))-retained) for row in audit)+1e-12
                records.append({'cohort':ri,'baseline_occurrences':len(base),'retained_occurrences':len(retained),
                    'synchronized_occurrences':sync,'independent_phase_expected_occurrences':independent,
                    'synchronized_saved':len(base)-sync,'independent_phase_expected_saved':len(base)-independent,
                    'phase_penalty_occurrences':independent-sync,
                    'synchronized_saving_percent':100*(len(base)-sync)/len(base),
                    'independent_phase_expected_saving_percent':100*(len(base)-independent)/len(base),
                    'retained_beams':sorted(retained),'audit_consumer_multiplicity':multiplicity.tolist()})
            keys=['baseline_occurrences','retained_occurrences','synchronized_occurrences',
                'independent_phase_expected_occurrences','synchronized_saved','independent_phase_expected_saved',
                'phase_penalty_occurrences','synchronized_saving_percent','independent_phase_expected_saving_percent']
            cases.append({'population':64,'AI_users':n_ai,'adoption':n_ai/64,'audit_K':k,'audit_period_epochs':period,
                'audit_duty':q,'average_observations_per_AI_UE':k*q,'total_UE_observations_per_epoch':(64-n_ai)*16+n_ai*k*q,
                'summary':{key:describe([r[key] for r in records]) for key in keys},'cohorts':records})
    result={'status':'executed','analysis_date':'2026-11-16','type':'post hoc accounting sensitivity on frozen endpoints',
        'source_files':{str(p):sha(p) for p in (tp,ep)},'script_sha256':sha(__file__),
        'assumptions':['T16 conventional profile; 1 m endpoints; 64 users; original 30 cohorts and capability ordering.',
            'Ideal current rankings determine fixed audit lists, unchanged between timing arms.',
            'Every AI UE measures K candidates once every L epochs; phases independently uniform for the independent arm.',
            'Retained demand, audit demand, and physical sharing eligibility stay fixed over the accounting period.',
            'A resource already required by conventional UEs has no incremental audit transmission cost.',
            'Results are exact expectations over phases, not observed trajectories, detected errors, energy, or scheduler conformance.'],
        'formula':'Expected occurrence count = |R| + sum over b not in R of [1-(1-1/L)^m_b], where m_b counts AI audit consumers.',
        'validation':{'small_fixture_full_phase_enumeration':fixture_results,
            'original_synchronized_count_and_saved_max_abs_error':max(parity_errors),'matched_cohort_cases':120,
            'nonnegative_phase_penalty_all_cases':True,'union_bound_all_cases':True},'cases':cases}
    (output/'audit_phase_results.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Exact audit-phase accounting sensitivity','',
        'Executed on the original T16 cohorts (1 m, 64 users, 30 cohorts). This is a post hoc sensitivity, not a new channel experiment. Each UE retains the same periodic audit interval; only its phase is randomized independently. Expectations are calculated exactly, without Monte Carlo.','',
        '| AI users | Audit | Synchronized occupied | Independent-phase occupied | Synchronized saved | Independent-phase saved |',
        '|---:|---|---:|---:|---:|---:|']
    for c in cases:
        s=c['summary']; vals=[s[key]['mean'] for key in ['synchronized_occurrences','independent_phase_expected_occurrences','synchronized_saved','independent_phase_expected_saved']]
        lines.append(f"| {c['AI_users']} | top-{c['audit_K']} / {c['audit_period_epochs']} epochs | "+' | '.join(f'{v:.6f}' for v in vals)+' |')
    lines += ['', 'Synchronized values reproduce all 120 corresponding original cohort cases exactly (zero count/saving error). Two small fixtures at periods 2 and 8 match exhaustive enumeration of all phase assignments. Phase randomization never lowers occupancy for the fixed audit demands.', '',
        'Interpretation: synchronized audits materially reduce transmission demand near full adoption. At half adoption, the conventional demand floor leaves little extra demand and the phase penalty is smaller. Per-UE average observation counts and intervals are unchanged; error-detection effectiveness is not evaluated. These results must not be described as a trajectory simulation or a measured hardware saving.','',
        'Reproduce: `python audit_phase_sensitivity.py --source PATH/TO/prior_revision --output OUTPUT_DIR`','',
        'The source NPZ files are required; their SHA-256 hashes are recorded in the JSON. Per-cohort retained beam sets and audit-consumer multiplicities are also saved, permitting independent recomputation of the new expectations without channel data.']
    (output/'AUDIT_PHASE_FINDINGS.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--source',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); run(a.source.resolve(),a.output.resolve())
