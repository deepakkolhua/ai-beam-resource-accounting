#!/usr/bin/env python3
"""Frozen second-scene qualification and exact phase-accounting extension.

Reuses the original candidate and corrected geographic-bootstrap functions.
Reports failures without switching scenes, seeds, profiles or quality gates.
"""
import argparse, hashlib, json, sys
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'helpers'))
from prior_baselines import observations,groups_from_prior,summarize_population
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,x:Path(p).write_text(json.dumps(x,indent=2)+'\n')

def geometry(data,conf,split):
    pos=data['position'].astype(float);current_population=np.flatnonzero(data['split']==split);tree=cKDTree(pos)
    parts=[[],[],[],[],[]]
    for distance in conf['geometry']['distances_m']:
        for direction,(axis,sign) in enumerate(conf['geometry']['directions']):
            offset=np.zeros(3);offset[axis]=sign*distance
            error,previous=tree.query(pos[current_population]-offset);ok=error<=conf['geometry']['tolerance_m']
            for target,val in zip(parts,[current_population[ok],previous[ok],np.full(ok.sum(),distance,dtype=np.int16),np.full(ok.sum(),direction,dtype=np.int8),error[ok]]):target.append(val)
    current,previous,distance,direction,error=map(np.concatenate,parts)
    for d in conf['geometry']['distances_m']:
        if not np.any(distance==d):raise ValueError(f'No eligible {d}m pairs in split{split}; protocol will not be altered.')
    return dict(current_index=current,previous_index=previous,current_original_row=data['original_row'][current],previous_original_row=data['original_row'][previous],current_position=pos[current],previous_position=pos[previous],current_tile=data['tile'][current],previous_split=data['split'][previous],distance_m=distance,direction=direction,coordinate_match_error_m=error)

def population(data,db,prior,current_obs,groups,conf,geom):
    out=dict(geom);current=out['current_index'];previous=out['previous_index'];row=np.arange(len(current))
    out['prior_selected']=prior[previous].argmax(axis=1).astype(np.int16)
    out['true_current_best']=data['power64'][current].argmax(axis=1).astype(np.int16)
    out['current_true_rank']=np.argsort(-data['power64'][current],axis=1,kind='stable').astype(np.int16)
    out['selected_HOLD']=out['prior_selected'].copy()
    for p in conf['candidate_profiles']:
        name=p['id'];g=groups[name][previous];observed=np.take_along_axis(current_obs[current],g,axis=1)
        out['group_'+name]=g;out['selected_'+name]=g[row,observed.argmax(axis=1)]
    best=db[current,out['true_current_best']]
    for name in ['HOLD']+[p['id'] for p in conf['candidate_profiles']]:
        loss=best-db[current,out['selected_'+name]];assert np.all(loss>=-1e-10)
        out['loss_db_'+name]=loss;out['within3db_'+name]=loss<=3+conf['quality']['tolerance_db']
    return out,summarize_population(out,conf)

def choose_cohorts(t,conf):
    rng=np.random.default_rng(conf['cohorts']['seed']);result={}
    for distance in conf['geometry']['distances_m']:
        eligible=np.flatnonzero(t['distance_m']==distance);current=np.unique(t['current_index'][eligible])
        rows={int(c):eligible[t['current_index'][eligible]==c] for c in current}
        for n in conf['cohorts']['populations']:
            if len(current)<n:raise ValueError(f'Only{len(current)} distinct {distance}m current points for N={n}; no replacement.')
            for repeat in range(conf['cohorts']['repeats']):
                cs=rng.choice(current,size=n,replace=False);pairs=np.array([rng.choice(rows[int(c)]) for c in cs]);order=rng.permutation(n)
                result[distance,n,repeat]=(pairs,order)
    return result

def describe(x):
    return dict(mean=float(np.mean(x)),p05=float(np.quantile(x,.05)),p95=float(np.quantile(x,.95)),min=float(np.min(x)),max=float(np.max(x)))

def phase(t,cohorts,profile,conf,out):
    sync=np.zeros((30,65,2));indep=np.zeros_like(sync);base=np.zeros(30);cohortrows=[];orders=[]
    for rep in range(30):
        rows,order=cohorts[1,64,rep];cohortrows.append(rows);orders.append(order)
        groups=t['group_'+profile][rows];base[rep]=len(np.unique(groups))
        for count in range(65):
            ai=np.zeros(64,dtype=bool);ai[order[:count]]=True
            retained=np.unique(groups[~ai]);retained_mask=np.zeros(64,dtype=bool);retained_mask[retained]=True
            for j,(_,k,period) in enumerate(conf['phase']['designs']):
                audits=t['current_true_rank'][rows[ai],:k];m=np.bincount(audits.ravel(),minlength=64)
                s=len(retained)+np.count_nonzero((m>0)&~retained_mask)/period
                i=len(retained)+np.sum((1-(1-1/period)**m)[~retained_mask])
                assert i+1e-12>=s
                sync[rep,count,j]=base[rep]-s;indep[rep,count,j]=base[rep]-i
    result={'profile':profile,'baseline_occurrences':describe(base),'population':64,'cohorts':30,'designs':conf['phase']['designs'],'adoption':{}}
    for count in (32,64):
        result['adoption'][str(count/64)]={name:{'synchronized_saved':describe(sync[:,count,j]),'independent_expected_saved':describe(indep[:,count,j])} for j,(name,_,_) in enumerate(conf['phase']['designs'])}
    sd=sync[:,-1,1]-sync[:,-1,0];id=indep[:,-1,0]-indep[:,-1,1]
    result['full_adoption_reversal']={'count':int(np.sum((sd>0)&(id>0))),'total':30,'synchronized_top16_advantage':describe(sd),'independent_top4_advantage':describe(id)}
    np.savez_compressed(out/f'phase_{profile}.npz',AI_counts=np.arange(65),synchronized_saved=sync,independent_expected_saved=indep,baseline_occurrences=base,cohort_tracking_rows=np.array(cohortrows),capability_order=np.array(orders))
    write(out/f'phase_{profile}.json',result);return result

def run(datafile,out):
    out.mkdir(parents=True,exist_ok=True);conf=json.loads((ROOT/'SECOND_SCENARIO_PROTOCOL.json').read_text())
    record={'created_utc':datetime.now(timezone.utc).isoformat(),'scenario':conf['scenario'],'data_sha256':sha(datafile),'protocol_sha256':sha(ROOT/'SECOND_SCENARIO_PROTOCOL.json'),'script_sha256':sha(__file__),'original_helper_sha256':sha(ROOT/'helpers/prior_baselines.py'),'status':'written before quality/accounting calculation; internal record, not external preregistration'}
    write(out/'RUN_MANIFEST.json',record)
    with np.load(datafile,allow_pickle=False) as z:data={k:z[k] for k in z.files}
    geoms={split:geometry(data,conf,split) for split in (1,2)}
    for split,g in geoms.items():np.savez_compressed(out/f'geometry_split{split}.npz',**g)
    db,prior,current=observations(data,conf);groups=groups_from_prior(prior,conf['candidate_profiles'])
    v,vs=population(data,db,prior,current,groups,conf,geoms[1]);np.savez_compressed(out/'tracking_validation.npz',**v);write(out/'tracking_validation.json',{'by_distance':vs})
    methods=vs['1']['methods'];qualified=[p for p in conf['candidate_profiles'] if methods[p['id']]['within_3db_tile_bootstrap95'][0]>=conf['selection']['target']]
    selected=qualified[0]['id'] if qualified else None
    selection={'selected_profile':selected,'selected_measurements':qualified[0]['measurements'] if qualified else None,'validation_qualifying_profiles':[p['id'] for p in qualified],'selection_uses_test_results':False,'validation_selected':methods[selected] if selected else None,'fixed_T16_validation':methods['T16']}
    write(out/'baseline_selection.json',selection);selection_hash=sha(out/'baseline_selection.json');print('VALIDATION:',json.dumps(selection),flush=True)
    t,ts=population(data,db,prior,current,groups,conf,geoms[2]);np.savez_compressed(out/'tracking_results.npz',**t);write(out/'tracking_results.json',{'by_distance':ts})
    assert sha(out/'baseline_selection.json')==selection_hash
    result=dict(selection);result.update(evaluation_selected=ts['1']['methods'][selected] if selected else None,fixed_T16_evaluation=ts['1']['methods']['T16'],evaluation_point_passes=bool(selected and ts['1']['methods'][selected]['within_3db_fraction']>=.95),fixed_T16_point_passes=bool(ts['1']['methods']['T16']['within_3db_fraction']>=.95),pairs=ts['1']['pairs'],distinct_current_locations=ts['1']['distinct_current_locations'],current_tiles=ts['1']['current_tiles'])
    write(out/'qualified_baseline.json',result);cohorts=choose_cohorts(t,conf)
    profiles=list(dict.fromkeys(([selected] if selected else [])+['T16']))
    result['phase']={p:phase(t,cohorts,p,conf,out) for p in profiles}
    result['scope']='Same fixed pipeline on second static scene; oracle only. Quality failures remain failures. Phase results conditional on saved channel endpoint demands.'
    write(out/'SECOND_SCENARIO_RESULTS.json',result);print('RESULT:',json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();run(a.data.resolve(),a.output.resolve())
