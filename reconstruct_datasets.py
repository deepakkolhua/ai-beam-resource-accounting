#!/usr/bin/env python3
"""Reconstruct four research NPZ files split for GitHub upload. Python 3.8+."""
from pathlib import Path
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "RECONSTRUCTION_MANIFEST.json").read_text())
for name, expected in manifest.items():
    target = ROOT / name
    pieces = [Path(str(target) + f".part{i:02d}") for i in range(expected["parts"])]
    missing = [str(p) for p in pieces if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing parts for {name}: {missing}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(str(target) + ".reconstructing")
    digest = hashlib.sha256()
    count = 0
    try:
        with temp.open("wb") as out:
            for piece in pieces:
                with piece.open("rb") as inp:
                    while True:
                        block = inp.read(1024 * 1024)
                        if not block:
                            break
                        out.write(block)
                        digest.update(block)
                        count += len(block)
        if count != expected["bytes"] or digest.hexdigest() != expected["sha256"]:
            raise ValueError(f"Integrity check failed: {name}; size={count}; SHA256={digest.hexdigest()}")
        os.replace(temp, target)
        print(f"Verified {name} ({count:,} bytes, SHA-256 {digest.hexdigest()})")
    finally:
        if temp.exists():
            temp.unlink()
print("All four split datasets reconstructed and verified.")
