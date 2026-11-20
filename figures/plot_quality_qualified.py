#!/usr/bin/env python3
"""Single validation-selection panel extracted from saved prior_revision results.

No fitting, profile selection or experimental recomputation is performed.
Usage: python plot_quality_qualified.py --source ../sensitivity/inputs --output .
"""
from pathlib import Path
import argparse
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(source, output):
    output.mkdir(parents=True,exist_ok=True)
    sources = {n:source/n for n in ['BASELINE_PROTOCOL.json','qualified_baseline.json','tracking_validation.json']}
    protocol=json.loads(sources['BASELINE_PROTOCOL.json'].read_text())
    qualified=json.loads(sources['qualified_baseline.json'].read_text())
    selected=qualified['selected_profile']
    profiles=protocol['candidate_profiles']
    validation=json.loads(sources['tracking_validation.json'].read_text())['by_distance']['1']['methods']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,
        'axes.labelsize':9,'xtick.labelsize':8.5,'ytick.labelsize':8.5,
        'legend.fontsize':8.5,'axes.spines.top':False,'axes.spines.right':False,
        'axes.linewidth':.7,'pdf.fonttype':42,'ps.fonttype':42})
    fig,ax=plt.subplots(figsize=(3.5,2.5))
    fig.subplots_adjust(left=.20,right=.975,bottom=.23,top=.97)
    values={}
    for family,label,color,marker in [
        ('topk','Prior top-K','#0072B2','o'),
        ('lobes','Separated peaks','#009E73','^'),
        ('contiguous','Contiguous','#D55E00','s')]:
        rows=[p for p in profiles if p['family']==family]
        counts=[p['measurements'] for p in rows]
        lower=[100*validation[p['id']]['within_3db_tile_bootstrap95'][0] for p in rows]
        ax.plot(counts,lower,color=color,marker=marker,markersize=3.5,label=label,
            markerfacecolor='white',markeredgewidth=.9,lw=1.4)
        values[family]=[{'profile':p['id'],'measurements':c,'lower_95_percent':v} for p,c,v in zip(rows,counts,lower)]
    ax.axhline(95,color='.35',linestyle=(0,(3,2)),linewidth=.8,zorder=0)
    ax.set_xscale('log',base=2)
    ax.set(xticks=[2,4,8,16,32,64],xlim=(1.8,71),ylim=(76,101),yticks=[80,85,90,95,100],
        xlabel='Measurements per conventional UE',ylabel='Validation lower 95%\nendpoint (%)')
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.grid(axis='y',color='.9',linewidth=.6);ax.set_axisbelow(True)
    ax.legend(loc='lower right',frameon=False,borderpad=.1,handlelength=1.5,labelspacing=.25)
    chosen=next(p for p in profiles if p['id']==selected)
    cy=100*validation[selected]['within_3db_tile_bootstrap95'][0]
    ax.scatter([chosen['measurements']],[cy],s=75,facecolors='none',edgecolors='.1',linewidths=1,zorder=5)
    ax.annotate(f'Selected: {selected}',xy=(chosen['measurements'],cy),xytext=(.02,.95),
        textcoords='axes fraction',va='top',fontsize=8.5,color='.1',
        arrowprops={'arrowstyle':'-','color':'.3','lw':.7})
    fig.savefig(output/'quality_qualified.pdf',bbox_inches='tight',pad_inches=.04)
    fig.savefig(output/'quality_qualified.png',dpi=240,bbox_inches='tight',pad_inches=.04)
    plt.close(fig)
    (output/'quality_qualified_provenance.json').write_text(json.dumps({
        'source_files':{n:{'path':str(p.resolve()),'sha256':sha(p)} for n,p in sources.items()},
        'script_sha256':sha(__file__),'selected_profile':selected,'displacement_m':1,
        'scope':'Validation selection panel only. Original evaluation panel omitted; no values altered.',
        'interval_semantics':'Lower endpoint of geographic-tile bootstrap 95% interval; conditional on this scene.',
        'size_inches':[3.5,2.5],'values':values},indent=2)+'\n')
    print(output/'quality_qualified.pdf')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run(a.source,a.output)
