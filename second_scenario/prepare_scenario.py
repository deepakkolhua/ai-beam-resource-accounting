#!/usr/bin/env python3
"""Parametric preparation using the original split, channel and precoder code.

The frozen scenario is city_1_losangeles_28. Source files are read unchanged.
No predictor is trained. The split is written before channel power computation.
"""
import argparse, hashlib, importlib.util, json, re, sys
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from scipy.io import loadmat
import deepmimo as dm

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('original_prepare',ROOT/'helpers/original_prepare_data.py')
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(raw,archive,out):
    conf=json.loads((ROOT/'SECOND_SCENARIO_PROTOCOL.json').read_text())
    out.mkdir(parents=True,exist_ok=True)
    choices=[]
    for path in raw.glob('rx_pos_t*_tx*_r*.mat'):
        m=re.fullmatch(r'rx_pos_t(\d+)_tx(\d+)_r(\d+)\.mat',path.name)
        if m:choices.append((tuple(map(int,m.groups())),path))
    if not choices:raise ValueError('No v4receiverpositionfiles')
    (txset,txindex,rxset),posfile=sorted(choices)[0]
    pos=loadmat(posfile)['rx_pos']
    split,tiles,origin=original.geographic_split(pos)
    np.savez_compressed(out/'split_before_channels.npz',position=pos,split=split,tile=tiles)
    record={'scenario':conf['scenario'],'created_utc':datetime.now(timezone.utc).isoformat(),
        'tx_set':txset,'tx_index':txindex,'rx_set':rxset,'selection':'first numerical tuple before channel quality',
        'source_archive_sha256':sha(archive),'source_archive_bytes':archive.stat().st_size,
        'source_params_sha256':sha(raw/'params.json'),'source_positions_sha256':sha(posfile),
        'frozen_protocol_sha256':sha(ROOT/'SECOND_SCENARIO_PROTOCOL.json'),
        'split_sha256':sha(out/'split_before_channels.npz'),'split_origin_xy':origin.tolist(),
        'script_sha256':sha(__file__),'original_helper_sha256':sha(ROOT/'helpers/original_prepare_data.py'),
        'deepmimo_version':dm.__version__,'numpy_version':np.__version__}
    (out/'DATA_PROTOCOL.json').write_text(json.dumps(record,indent=2)+'\n')
    dm.config.set('scenarios_folder',str(raw.parent))
    dataset=dm.load(raw.name,tx_sets={txset:[txindex]},rx_sets=[rxset],max_paths=25)
    assert np.array_equal(np.asarray(dataset.rx_pos),pos)
    params=dm.ChannelParameters(bs_antenna=conf['preparation']['bs_antenna'],
        ue_antenna=conf['preparation']['ue_antenna'],num_paths=25,ofdm=conf['preparation']['ofdm'])
    channels=dataset.compute_channels(params)[:,0,:,0]
    valid=np.isfinite(channels).all(axis=1)&(np.linalg.norm(channels,axis=1)>0)&(split>=0)
    row=np.flatnonzero(valid);h=channels[row]
    w64,u64=original.dft_weights(64,64,64);w8,u8=original.dft_weights(64,8,8);w4,u4=original.dft_weights(64,4,4)
    power=np.abs(h.astype(np.complex128)@w64)**2
    coarse8=np.abs(h.astype(np.complex128)@w8)**2;coarse4=np.abs(h.astype(np.complex128)@w4)**2
    energy=np.sum(np.abs(h.astype(np.complex128))**2,axis=1)
    error=float(np.max(np.abs(power.sum(axis=1)-energy)/energy))
    assert error<1e-10
    np.savez_compressed(out/'beam_data.npz',original_row=row,position=pos[row],split=split[row],tile=tiles[row],
        channel=h,power64=power,coarse8=coarse8,coarse4=coarse4,weights64=w64,weights8=w8,weights4=w4,
        direction_cosine64=u64,direction_cosine8=u8,direction_cosine4=u4,tx_position=np.asarray(dataset.tx_pos))
    summary={'scenario':conf['scenario'],'retained_users':len(row),'source_grid_points':len(pos),
        'split_counts':{str(k):int((split[row]==k).sum()) for k in (0,1,2)},
        'parseval_max_relative_error':error,'beam_data_sha256':sha(out/'beam_data.npz')}
    (out/'DATA_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',required=True,type=Path);p.add_argument('--archive',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run(a.raw.resolve(),a.archive.resolve(),a.output.resolve())
