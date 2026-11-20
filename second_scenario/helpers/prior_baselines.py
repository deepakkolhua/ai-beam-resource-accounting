#!/usr/bin/env python3
"""Frozen prior-evidence candidate families for an exploratory endpoint study.

Run from any directory. No models are fitted and no candidate uses current true
power. Prior full-bank information is identical for all conventional families.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2) + '\n')


def observations(data, protocol):
    power = data['power64'].astype(float)
    if power.shape[1] != 64 or not np.isfinite(power).all() or np.any(power < 0) or np.any(power.max(axis=1) <= 0):
        raise ValueError('Expected positive finite64-beam power rows.')
    db = 10 * np.log10(np.maximum(power, np.finfo(float).tiny))
    conf = protocol['observations']
    def noisy(seed):
        x = db + np.random.default_rng(seed).normal(0, conf['noise_std_db'], size=db.shape)
        q = conf['quantization_db']
        return np.rint(x/q)*q
    return db, noisy(conf['prior_noise_seed']), noisy(conf['current_noise_seed'])


def contiguous(prior, k):
    center = prior.argmax(axis=1)
    if k == 64:
        return np.broadcast_to(np.arange(64, dtype=np.int16), (len(prior),64)).copy()
    half = k//2
    left, right = (center-half)%64, (center+half)%64
    rows = np.arange(len(prior))
    edge = np.where(prior[rows,left]>=prior[rows,right],left,right)
    inside = (center[:,None]+np.arange(-(half-1),half)[None,:])%64
    return np.sort(np.column_stack([inside,edge]),axis=1).astype(np.int16)


def groups_from_prior(prior, profiles):
    rank = np.argsort(-prior, axis=1, kind='stable')
    output = {}
    for profile in profiles:
        name, family = profile['id'], profile['family']
        if family == 'topk':
            group = np.sort(rank[:,:profile['k']],axis=1).astype(np.int16)
        elif family == 'contiguous':
            group = contiguous(prior,profile['k'])
        else:
            width, ncenters = profile['width'],profile['centers']
            half = width//2
            group = np.empty((len(prior),width*ncenters),dtype=np.int16)
            for row, ordered in enumerate(rank):
                accepted=[]
                for beam in ordered:
                    if all(min((int(beam)-c)%64,(c-int(beam))%64)>=width for c in accepted):
                        accepted.append(int(beam))
                        if len(accepted)==ncenters:
                            break
                if len(accepted)!=ncenters:
                    raise AssertionError('Could not form fixed-cardinality disjoint blocks.')
                group[row] = np.sort(np.concatenate([(c+np.arange(-half,half+1))%64 for c in accepted]))
        assert group.shape[1] == profile['measurements']
        assert np.all(np.diff(group,axis=1)>0)
        output[name]=group
    return output


def summarize_population(outputs, protocol):
    summaries={}
    conf=protocol['quality']['bootstrap']
    names=['HOLD']+[p['id'] for p in protocol['candidate_profiles']]
    for distance in [1,2,5]:
        rows=np.flatnonzero(outputs['distance_m']==distance)
        current,first,inverse=np.unique(outputs['current_index'][rows],return_index=True,return_inverse=True)
        counts=np.bincount(inverse)
        point_tiles=outputs['current_tile'][rows[first]]
        assert np.array_equal(outputs['current_tile'][rows],point_tiles[inverse])
        tiles,cluster=np.unique(point_tiles,axis=0,return_inverse=True)
        tile_n=np.bincount(cluster)
        sampled=np.random.default_rng(conf['seed']).integers(len(tiles),size=(conf['replicates'],len(tiles)))
        methods={}
        for name in names:
            good=outputs[f'within3db_{name}'][rows].astype(float)
            point_probability=np.bincount(inverse,weights=good)/counts
            tile_sum=np.bincount(cluster,weights=point_probability)
            bootstrap=tile_sum[sampled].sum(axis=1)/tile_n[sampled].sum(axis=1)
            losses=outputs[f'loss_db_{name}'][rows]
            point_mean_loss=np.bincount(inverse,weights=losses)/counts
            methods[name]={
                'within_3db_fraction':float(point_probability.mean()),
                'within_3db_tile_bootstrap95':np.quantile(bootstrap,[.025,.975]).tolist(),
                'pair_weighted_within_3db_fraction':float(good.mean()),
                'mean_loss_db':float(point_mean_loss.mean()),
            }
        summaries[str(distance)]={
            'pairs':int(len(rows)), 'distinct_current_locations':int(len(current)), 'current_tiles':int(len(tiles)),
            'eligible_previous_count_distribution':{str(k):int(np.sum(counts==k)) for k in np.unique(counts)},
            'methods':methods,
        }
    return summaries


def run_population(parent, output, data, db, prior, current_obs, profile_groups, protocol, split):
    stem='tracking_validation' if split==1 else 'tracking_results'
    parent_path=parent/f'{stem}.npz'
    expected=protocol['parent_validation_arrays_sha256' if split==1 else 'parent_test_arrays_sha256']
    if sha(parent_path)!=expected:
        raise ValueError('Original geometry source hash mismatch.')
    geometry=['current_index','previous_index','current_original_row','previous_original_row',
              'current_position','previous_position','current_tile','previous_split','distance_m','direction',
              'coordinate_match_error_m','prior_selected','true_current_best','current_true_rank']
    with np.load(parent_path) as z:
        outputs={key:z[key] for key in geometry}
    current=outputs['current_index']; previous=outputs['previous_index']; rows=np.arange(len(current))
    assert np.array_equal(outputs['prior_selected'],prior[previous].argmax(axis=1))
    assert np.array_equal(outputs['true_current_best'],data['power64'][current].argmax(axis=1))
    outputs['selected_HOLD']=outputs['prior_selected'].copy()
    for profile in protocol['candidate_profiles']:
        name=profile['id']; group=profile_groups[name][previous]
        obs=np.take_along_axis(current_obs[current],group,axis=1)
        selected=group[rows,obs.argmax(axis=1)]
        outputs[f'group_{name}']=group
        outputs[f'selected_{name}']=selected
    best=db[current,outputs['true_current_best']]
    for name in ['HOLD']+[p['id'] for p in protocol['candidate_profiles']]:
        selected=outputs[f'selected_{name}']
        loss=best-db[current,selected]
        assert np.all(loss>=-1e-10)
        outputs[f'loss_db_{name}']=loss
        outputs[f'within3db_{name}']=loss<=3.0+protocol['quality']['tolerance_db']
    path=output/f'{stem}.npz'
    np.savez_compressed(path,**outputs)
    report={
        'population':'validation' if split==1 else 'test',
        'population_split':split,
        'protocol_sha256':sha(output/'BASELINE_PROTOCOL.json'),
        'script_sha256':sha(__file__),
        'results_npz_sha256':sha(path),
        'parent_npz_sha256':sha(parent_path),
        'data_sha256':protocol['data_sha256'],
        'estimand':protocol['quality']['estimand'],
        'bootstrap':protocol['quality']['bootstrap'],
        'profiles':protocol['candidate_profiles'],
        'by_distance':summarize_population(outputs,protocol),
    }
    write_json(output/f'{stem}.json',report)
    return report


def run(data_path, parent, output):
    protocol_path=output/'BASELINE_PROTOCOL.json'
    protocol=json.loads(protocol_path.read_text())
    if sha(data_path)!=protocol['data_sha256']:
        raise ValueError('Prepared data differs from frozen protocol.')
    with np.load(data_path) as z:
        data={key:z[key] for key in z.files}
    db,prior,current_obs=observations(data,protocol)
    group_table=groups_from_prior(prior,protocol['candidate_profiles'])
    validation=run_population(parent,output,data,db,prior,current_obs,group_table,protocol,1)
    methods=validation['by_distance'][str(protocol['selection']['distance_m'])]['methods']
    qualified=[p for p in protocol['candidate_profiles'] if methods[p['id']]['within_3db_tile_bootstrap95'][0]>=protocol['selection']['target']]
    # Candidate order was frozen as count, family, profile label in protocol.
    selected=qualified[0] if qualified else None
    selection={
        'protocol_sha256':sha(protocol_path),
        'validation_results_sha256':sha(output/'tracking_validation.json'),
        'selection_uses_test_results':False,
        'selected_profile':selected['id'] if selected else None,
        'selected_measurements':selected['measurements'] if selected else None,
        'selected_profile_definition':selected,
        'validation_selected':methods[selected['id']] if selected else None,
        'validation_candidates':methods,
        'validation_qualifying_profiles':[p['id'] for p in qualified],
        'selection_rule':protocol['selection'],
        'status':'selected' if selected else 'no_qualified_baseline',
    }
    selection_path=output/'baseline_selection.json'
    write_json(selection_path,selection)
    selection_hash=sha(selection_path)
    print('VALIDATION SELECTION WRITTEN:',json.dumps({k:selection[k] for k in ['selected_profile','selected_measurements','validation_selected']}),flush=True)
    # No evaluation arrays were accessed above except hash verification recorded
    # before computation. Evaluation is now evaluated without revising selection.
    evaluation=run_population(parent,output,data,db,prior,current_obs,group_table,protocol,2)
    assert sha(selection_path)==selection_hash
    result=dict(selection)
    result['selection_file_sha256']=selection_hash
    result['evaluation_results_sha256']=sha(output/'tracking_results.json')
    result['evaluation_selected']=evaluation['by_distance'][str(protocol['selection']['distance_m'])]['methods'][selected['id']] if selected else None
    result['evaluation_point_passes']=bool(result['evaluation_selected']['within_3db_fraction']>=protocol['selection']['target']) if selected else False
    result['evaluation_lower95_passes']=bool(result['evaluation_selected']['within_3db_tile_bootstrap95'][0]>=protocol['selection']['target']) if selected else False
    result['scope']=protocol['quality']['scope']
    write_json(output/'qualified_baseline.json',result)
    print('EVALUATION:',json.dumps({k:result[k] for k in ['selected_profile','selected_measurements','evaluation_selected','evaluation_point_passes','evaluation_lower95_passes']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    project=Path(__file__).resolve().parents[1]
    p.add_argument('--data',type=Path,default=project/'data_pilot/prepared/beam_data.npz')
    p.add_argument('--parent-dir',type=Path,default=project/'quality_revision')
    p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
    a=p.parse_args()
    run(a.data,a.parent_dir,a.output_dir)
