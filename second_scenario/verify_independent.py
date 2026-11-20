from pathlib import Path
import argparse,hashlib,json
import numpy as np

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Independent second-scene quality and phase recomputation.')
parser.add_argument('--data',type=Path,default=ROOT/'prepared/beam_data.npz')
parser.add_argument('--results',type=Path,default=ROOT/'results')
parser.add_argument('--output',type=Path,default=ROOT/'INDEPENDENT_QA.json')
args=parser.parse_args()
DATA=args.data.resolve();RESULTS=args.results.resolve()
d={k:v for k,v in np.load(DATA,allow_pickle=False).items()}
power=d['power64'].astype(float)
db=10*np.log10(np.maximum(power,np.finfo(float).tiny))
prior=np.rint(db+np.random.default_rng(341993).normal(0,.5,db.shape))
now=np.rint(db+np.random.default_rng(341994).normal(0,.5,db.shape))
rank=np.argsort(-prior,axis=1,kind='stable')
indgroups={name:[] for name in ['L2x3','T16']}
for order in rank:
    a=int(order[0]);b=next(int(k) for k in order if min((int(k)-a)%64,(a-int(k))%64)>=3)
    indgroups['L2x3'].append(sorted([(a+j)%64 for j in (-1,0,1)]+[(b+j)%64 for j in (-1,0,1)]))
    indgroups['T16'].append(sorted(order[:16]))
indgroups={k:np.array(v) for k,v in indgroups.items()}
quality={}
for name,split in [('tracking_validation',1),('tracking_results',2)]:
    t={k:v for k,v in np.load(RESULTS/(name+'.npz'),allow_pickle=False).items()}
    mask=t['distance_m']==1
    c=t['current_index'][mask];p=t['previous_index'][mask]
    assert np.all(d['split'][c]==split)
    delta=np.array([[-1,0,0],[1,0,0],[0,-1,0],[0,1,0]])[t['direction'][mask]]
    err=np.linalg.norm(d['position'][c].astype(float)-delta-d['position'][p].astype(float),axis=1)
    assert np.all(err<=.001)
    assert np.array_equal(t['current_true_rank'][mask],np.argsort(-power[c],axis=1,kind='stable'))
    stats=json.loads((RESULTS/(name+'.json')).read_text())['by_distance']['1']
    quality[name]={}
    for profile in indgroups:
        g=indgroups[profile][p]
        assert np.array_equal(g,t['group_'+profile][mask])
        selected=np.array([ids[np.argmax(now[i,ids])] for i,ids in zip(c,g)])
        assert np.array_equal(selected,t['selected_'+profile][mask])
        loss=np.max(db[c],axis=1)-db[c,selected]
        good=loss<=3+1e-12
        assert np.array_equal(good,t['within3db_'+profile][mask])
        location={int(i):[] for i in c}
        for i,gval in zip(c,good):location[int(i)].append(float(gval))
        tile={}
        for i,vals in location.items():tile.setdefault(tuple(d['tile'][i]),[]).append(np.mean(vals))
        keys=sorted(tile)
        tile_count=np.array([len(tile[k]) for k in keys])
        tile_total=np.array([sum(tile[k]) for k in keys])
        draw=np.random.default_rng(341995).integers(len(keys),size=(2000,len(keys)))
        boot=np.array([sum(tile_total[row])/sum(tile_count[row]) for row in draw])
        mean=float(np.mean([np.mean(v) for v in location.values()]))
        ci=np.quantile(boot,[.025,.975])
        old=stats['methods'][profile]
        assert abs(mean-old['within_3db_fraction'])<1e-14
        assert np.max(np.abs(ci-old['within_3db_tile_bootstrap95']))<1e-14
        quality[name][profile]={'mean':mean,'ci':ci.tolist(),'pairs':len(c),'locations':len(location),'tiles':len(tile)}

t={k:v for k,v in np.load(RESULTS/'tracking_results.npz',allow_pickle=False).items()}
rng=np.random.default_rng(202609251)
cohorts={}
for distance in (1,2,5):
    rows=np.flatnonzero(t['distance_m']==distance)
    bycur={int(c):rows[t['current_index'][rows]==c] for c in np.unique(t['current_index'][rows])}
    for n in (8,16,32,64):
        for repeat in range(30):
            points=rng.choice(np.array(list(bycur)),size=n,replace=False)
            chosen=np.array([rng.choice(bycur[int(c)]) for c in points])
            order=rng.permutation(n)
            if distance==1 and n==64:cohorts[repeat]=(chosen,order)
headline={}
maxerr=0
for profile in ['L2x3','T16']:
    z={k:v for k,v in np.load(RESULTS/('phase_'+profile+'.npz'),allow_pickle=False).items()}
    sy=np.zeros((30,65,2));ip=np.zeros_like(sy)
    for rep in range(30):
        rows,order=cohorts[rep]
        assert np.array_equal(rows,z['cohort_tracking_rows'][rep])
        assert np.array_equal(order,z['capability_order'][rep])
        groups=[set(map(int,x)) for x in t['group_'+profile][rows]]
        base=len(set.union(*groups))
        for count in range(65):
            ai=set(order[:count].tolist())
            retained=set().union(*(g for i,g in enumerate(groups) if i not in ai))
            for j,(k,L) in enumerate([(4,2),(16,8)]):
                requests=[set(map(int,t['current_true_rank'][rows[i],:k])) for i in ai]
                combined=retained.union(*requests)
                sy[rep,count,j]=base-(len(retained)+(len(combined)-len(retained))/L)
                expected=len(retained)
                for b in range(64):
                    if b not in retained:
                        m=sum(b in a for a in requests)
                        expected+=1-(1-1/L)**m
                ip[rep,count,j]=base-expected
    err=max(np.max(abs(sy-z['synchronized_saved'])),np.max(abs(ip-z['independent_expected_saved'])))
    assert err<1e-12
    maxerr=max(maxerr,float(err))
    a=sy[:,64,1]-sy[:,64,0];b=ip[:,64,0]-ip[:,64,1]
    headline[profile]={'reversal_cohorts':int(np.sum((a>0)&(b>0))),
      'full_synchronized_top4_top16':sy[:,64,:].mean(axis=0).tolist(),
      'full_independent_top4_top16':ip[:,64,:].mean(axis=0).tolist(),
      'synchronized_advantage_min_max':[float(a.min()),float(a.max())],
      'independent_advantage_min_max':[float(b.min()),float(b.max())]}
report={'status':'passed','independent_quality':quality,'independent_phase':headline,
        'phase_cases':30*65*2*2,'max_absolute_phase_discrepancy':maxerr,
        'data_sha256':hashlib.sha256(DATA.read_bytes()).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'Independent recomputation from prepared channels and saved tracking arrays; original channel synthesizer not independently reimplemented.'}
args.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
