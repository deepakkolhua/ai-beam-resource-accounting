#!/usr/bin/env python3
"""Single-panel N=64/T16 synchronized and independent audit-phase curves.

First run sensitivity/audit_phase_dense.py on its bundled inputs.
Usage: python plot_equal_budget.py --source ../sensitivity --output .
Plots all integer adoption counts, with descriptive 5th–95th cohort bands.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(source, output):
    output.mkdir(parents=True, exist_ok=True)
    path = source / 'audit_phase_dense_results.npz'
    z = np.load(path, allow_pickle=False)
    counts = z['AI_counts']
    assert np.array_equal(counts, np.arange(65))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
        'axes.labelsize': 9, 'xtick.labelsize': 9, 'ytick.labelsize': 9,
        'legend.fontsize': 7.5, 'axes.spines.top': False, 'axes.spines.right': False,
        'axes.linewidth': .7, 'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, ax = plt.subplots(figsize=(3.5, 2.65))
    fig.subplots_adjust(left=.20, right=.985, bottom=.205, top=.98)
    values = {}
    for timing, field, ls in [('synchronized', 'synchronized_saved', '-'),
                              ('independent', 'independent_expected_saved', '--')]:
        for design, k, period, color, marker in [
            ('topk4', 4, 2, '#0072B2', 'o'),
            ('topk16', 16, 8, '#D55E00', 's')]:
            ji = list(z['design_names']).index(design)
            cohort = z[field][:, :, ji]
            assert cohort.shape == (30, 65) and np.isfinite(cohort).all()
            mean = np.mean(cohort, axis=0)
            lo, hi = np.quantile(cohort, [.05, .95], axis=0)
            ax.fill_between(counts / 64 * 100, lo, hi, color=color, alpha=.13,
                            linewidth=0, zorder=1)
            ax.plot(counts / 64 * 100, mean, color=color, marker=marker,
                markevery=8, linestyle=ls, lw=1.45, markersize=3.4,
                markerfacecolor='white', markeredgewidth=.85, zorder=3,
                label=f'Top-{k} / {period}, {timing}')
            values[f'{design}_{timing}'] = {'AI_counts': counts.tolist(),
                'mean_saved': mean.tolist(), 'p05_saved': lo.tolist(), 'p95_saved': hi.tolist()}
    ax.set(xlim=(-1, 101), ylim=(-1, 62), xticks=[0, 25, 50, 75, 100],
           yticks=[0, 15, 30, 45, 60], xlabel='AI adoption (%)',
           ylabel='CSI-RS occurrences saved\nper refinement update')
    ax.grid(axis='y', color='.88', lw=.6)
    ax.set_axisbelow(True)
    ax.axhline(0, color='.5', lw=.7)
    ax.legend(loc='upper left', frameon=False, borderpad=.1,
              handlelength=2.1, labelspacing=.45, handletextpad=.55)
    fig.savefig(output / 'equal_budget.pdf', bbox_inches='tight', pad_inches=.04)
    fig.savefig(output / 'equal_budget.png', dpi=260, bbox_inches='tight', pad_inches=.04)
    plt.close(fig)
    (output / 'equal_budget_provenance.json').write_text(json.dumps({
        'source_file': str(path.resolve()), 'source_sha256': sha(path), 'script_sha256': sha(__file__),
        'population': 64, 'profile': 'T16', 'cohorts': 30,
        'timing': 'Synchronized periodic audits and exact independent uniform phase expectations.',
        'data': 'Every integer adoption count; mean and linear-interpolated 5th–95th percentiles across the same 30 frozen cohorts.',
        'spread': 'Descriptive cohort spread, not confidence intervals or random-phase simulation intervals.',
        'design_scope': 'Two audit designs central to the reversal; original geometric-4 data remain in inputs/dense_curves.npz.',
        'values': values}, indent=2) + '\n')
    print(output / 'equal_budget.pdf')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    run(args.source.resolve(), args.output.resolve())
