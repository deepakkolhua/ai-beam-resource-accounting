#!/usr/bin/env python3
"""Download the frozen official second scene and verify its exact bytes.

Usage: python download_losangeles.py --output ./source_data
The source archive and extracted raw files remain outside this code package.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

SCENARIO = "city_1_losangeles_28"
EXPECTED_BYTES = 33633360
EXPECTED_SHA256 = "3eb62ebc424a4008bc14e286672adec55010809c5024424b0384134a3f6928d7"
BASE_URL = "https://deepmimo.net"
HEADERS = {"User-Agent": "DeepMIMO-Python/4.0", "Accept": "*/*"}


def download(output):
    output.mkdir(parents=True, exist_ok=True)
    archive = output / (SCENARIO + ".zip")
    if not archive.exists():
        request = urllib.request.Request(
            BASE_URL + "/api/download/secure?filename=" + archive.name,
            headers=HEADERS)
        with urllib.request.urlopen(request, timeout=45) as response:
            receipt = json.load(response)
        if int(receipt["fileSize"]) != EXPECTED_BYTES:
            raise RuntimeError("Upstream size changed; inspect the version before replacing inputs")
        redirect = receipt["redirectUrl"]
        redirect = BASE_URL + redirect if redirect.startswith("/") else redirect
        if not redirect.startswith("https://"):
            raise RuntimeError("Expected an HTTPS download route")
        partial = output / (SCENARIO + ".partial")
        request = urllib.request.Request(redirect, headers=HEADERS)
        with urllib.request.urlopen(request, timeout=45) as response, partial.open("wb") as stream:
            count = 0
            while chunk := response.read(1 << 20):
                count += len(chunk)
                if count > EXPECTED_BYTES:
                    raise RuntimeError("Download exceeded declared source size")
                stream.write(chunk)
        partial.rename(archive)
    if archive.stat().st_size != EXPECTED_BYTES:
        raise RuntimeError("Source archive size mismatch")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise RuntimeError("Source archive SHA256 mismatch")
    raw = output / "raw"
    raw.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        if source.testzip() is not None:
            raise RuntimeError("Source archive failed CRC verification")
        for item in source.infolist():
            if not (raw / item.filename).resolve().is_relative_to(raw.resolve()):
                raise RuntimeError("Unsafe ZIP extraction path")
        source.extractall(raw)
    print(f"Verified {SCENARIO}: {EXPECTED_BYTES} bytes; raw files at {raw.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    download(parser.parse_args().output.resolve())
