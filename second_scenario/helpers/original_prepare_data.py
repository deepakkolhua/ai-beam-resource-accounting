"""Prepare a reproducible, geographically split DeepMIMO spatial beam pilot.

Run with Python plus deepmimo==4.0.5, numpy, scipy. No model is trained here.
Downloaded source files remain unmodified. This script writes the split before
generating or examining channel/beam quality.
"""
from pathlib import Path
import hashlib
import json
import sys
from datetime import datetime, timezone

import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parent
if (ROOT / "vendor").exists():
    sys.path.insert(0, str(ROOT / "vendor"))
import deepmimo as dm


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def geographic_split(pos):
    """20 m geographic tiles; remove points within 2 m of every tile edge.

    Deterministic SHA256 tile assignment: first 64-bit integer modulo 10,
    0..5 train, 6..7 validation, 8..9 test. Location only; no label balancing.
    All retained points in a tile share a split. Boundary guards create at
    least 4 m separation between points across adjacent tiles.
    """
    origin = np.floor(pos[:, :2].min(axis=0) / 20.0) * 20.0
    rel = pos[:, :2].astype(np.float64) - origin
    tile = np.floor(rel / 20.0).astype(int)
    within = np.mod(rel, 20.0)
    guard = np.any((within < 2.0) | (within > 18.0), axis=1)
    split = np.full(len(pos), -1, dtype=np.int8)
    for key in np.unique(tile, axis=0):
        val = int.from_bytes(hashlib.sha256(
            f"beam-pilot-20260925:{key[0]}:{key[1]}".encode()).digest()[:8], "big") % 10
        label = 0 if val < 6 else 1 if val < 8 else 2
        mask = np.all(tile == key, axis=1) & ~guard
        split[mask] = label
    return split, tile, origin


def dft_weights(n_ant, active, n_beams):
    """Unit-total-power ULA steering weights, inactive tail entries zero.

    Spatial frequencies lie in [-1,1), uniformly in direction cosine.
    A broad codeword uses only the first active contiguous elements; its
    lower array gain is preserved. No artificial normalization of powers.
    """
    u = -1 + 2 * np.arange(n_beams) / n_beams
    w = np.zeros((n_ant, n_beams), dtype=np.complex128)
    w[:active] = np.exp(-1j * np.pi * np.arange(active)[:, None] * u[None]) / np.sqrt(active)
    return w, u


def main():
    out = ROOT / "prepared"
    out.mkdir(exist_ok=True)
    raw = ROOT / "raw"
    pos = loadmat(raw / "rx_pos_t001_tx000_r000.mat")["rx_pos"]
    split, tiles, origin = geographic_split(pos)
    np.savez(out / "split_before_channels.npz", position=pos, split=split, tile=tiles)
    protocol = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "data preparation only; no predictor or quality results examined",
        "scenario": "city_0_newyork_28", "tx_set": 1, "tx_index": 0, "rx_set": 0,
        "tx_selection": "first numerical TX set; not selected by channel quality",
        "array": "64 horizontal isotropic half-wavelength ULA; one isotropic UE antenna",
        "frequency_hz": 28e9, "max_paths": 25,
        "frequency_samples": [0], "ofdm_subcarriers": 512, "ofdm_bandwidth_hz": 10e6,
        "channel_scope": "single frequency, coherent ray phases, static, noiseless powers",
        "narrow_codebook": {"antennas": 64, "beams": 64, "unit_total_power": True},
        "coarse_codebooks": [{"active_contiguous_antennas": k, "beams": k} for k in (4,8)],
        "split": {"tile_m":20, "guard_each_edge_m":2, "origin_xy":origin.tolist(),
                  "algorithm":"SHA256 beam-pilot-20260925:tile_x:tile_y; first64bits mod10; train<6,val<8,test otherwise",
                  "labels":{"excluded":-1,"train":0,"validation":1,"test":2}},
        "eligibility": "geographic guard plus finite nonzero generated channel; no SNR or best-beam filter",
        "source_zip_sha256": sha(ROOT / "city_0_newyork_28.zip"),
        "source_params_sha256": sha(raw / "params.json"),
        "split_sha256": sha(out / "split_before_channels.npz"),
        "script_sha256": sha(__file__),
    }
    (out / "DATA_PROTOCOL.json").write_text(json.dumps(protocol, indent=2))
    # Absolute scenarios_folder avoids changing the original scenario contents.
    dm.config.set("scenarios_folder", str(ROOT))
    dataset = dm.load("raw", tx_sets={1:[0]}, rx_sets=[0], max_paths=25)
    assert np.array_equal(np.asarray(dataset.rx_pos), pos)
    params = dm.ChannelParameters(bs_antenna={"shape":[64,1], "spacing":0.5,"rotation":[0,0,0]},
                                  ue_antenna={"shape":[1,1]}, num_paths=25,
                                  ofdm={"subcarriers":512,"selected_subcarriers":[0],"bandwidth":10e6})
    channels = dataset.compute_channels(params)[:,0,:,0]
    valid = np.isfinite(channels).all(axis=1) & (np.linalg.norm(channels,axis=1)>0) & (split>=0)
    row = np.flatnonzero(valid)
    h = channels[row]
    wn, un = dft_weights(64,64,64)
    w8,u8 = dft_weights(64,8,8)
    w4,u4 = dft_weights(64,4,4)
    # DeepMIMO downlink H multiplies TX column precoder: scalar received H @ w.
    powers = np.abs(h.astype(np.complex128) @ wn)**2
    coarse8 = np.abs(h.astype(np.complex128) @ w8)**2
    coarse4 = np.abs(h.astype(np.complex128) @ w4)**2
    np.savez_compressed(out / "beam_data.npz", original_row=row, position=pos[row],
        split=split[row], tile=tiles[row], channel=h, power64=powers,
        coarse8=coarse8, coarse4=coarse4, weights64=wn, weights8=w8, weights4=w4,
        direction_cosine64=un, direction_cosine8=u8, direction_cosine4=u4,
        tx_position=np.asarray(dataset.tx_pos))
    # Basic physics checks: DFT Parseval, unit precoder norms, finite powers.
    energy = np.sum(np.abs(h.astype(np.complex128))**2,axis=1)
    parseval = np.max(np.abs(powers.sum(axis=1)-energy)/energy)
    assert parseval < 1e-10
    assert all(np.allclose(np.linalg.norm(w,axis=0),1) for w in [wn,w8,w4])
    summary = {
        "scenario_grid_points":len(pos), "geographic_guard_removed":int((split<0).sum()),
        "channel_zero_or_nonfinite":int((~(np.isfinite(channels).all(axis=1)&(np.linalg.norm(channels,axis=1)>0))).sum()),
        "retained_users":int(len(row)),
        "split_counts":{name:int((split[row]==k).sum()) for k,name in enumerate(["train","validation","test"])},
        "channel_shape":list(h.shape), "narrow_power_shape":list(powers.shape),
        "parseval_max_relative_error":float(parseval),
        "beam_data_sha256":sha(out / "beam_data.npz"),
        "channel_dtype":str(h.dtype), "power_dtype":str(powers.dtype),
        "no_model_trained":True,
    }
    (out / "DATA_SUMMARY.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
