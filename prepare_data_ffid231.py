import json
from pathlib import Path

import numpy as np


SUBPROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_SEGY = SUBPROJECT_DIR.parent / "2D_Land_vibro_data_2ms" / "Line_001.sgy"
OUTPUT_DIR = SUBPROJECT_DIR / "data" / "prepared"
TRACES_PER_SHOT = 284
FFID_FIRST = 231
TARGET_FFID = 231


def ibm_to_ieee32(trace_data):
    raw = np.frombuffer(trace_data, dtype=">u4")
    if raw.size == 0:
        return np.array([], dtype=np.float32)

    sign = np.where((raw >> 31) & 0x1, -1.0, 1.0)
    exponent = ((raw >> 24) & 0x7F).astype(np.int32) - 64
    fraction = (raw & 0x00FFFFFF).astype(np.float64) / float(0x01000000)
    samples = sign * fraction * np.power(16.0, exponent)
    samples[raw == 0] = 0.0
    return samples.astype(np.float32)


def read_segy_binary_header(segy_path: Path):
    with open(segy_path, "rb") as f:
        f.seek(3200)
        binhead = f.read(400)

    ns = int.from_bytes(binhead[20:22], byteorder="big", signed=False)
    dt_us = int.from_bytes(binhead[16:18], byteorder="big", signed=False)
    sample_format = int.from_bytes(binhead[24:26], byteorder="big", signed=False)
    return {"ns": ns, "dt_us": dt_us, "sample_format": sample_format}


def convert_segy_to_npy(segy_path: Path, out_dir: Path):
    header = read_segy_binary_header(segy_path)
    if header["sample_format"] != 1:
        raise ValueError("Only IBM float SEG-Y (sample format code 1) is supported.")

    ns = header["ns"]
    trace_size = 240 + ns * 4
    ntraces = (segy_path.stat().st_size - 3600) // trace_size

    data = np.empty((ntraces, ns), dtype=np.float32)
    ffids = np.empty(ntraces, dtype=np.int32)
    tracf = np.empty(ntraces, dtype=np.int32)

    with open(segy_path, "rb") as f:
        f.seek(3600)
        for i in range(ntraces):
            trace_header = f.read(240)
            ffids[i] = int.from_bytes(trace_header[8:12], byteorder="big", signed=True)
            tracf[i] = int.from_bytes(trace_header[12:16], byteorder="big", signed=True)
            trace_data = f.read(ns * 4)
            data[i] = ibm_to_ieee32(trace_data)

    twt_ms = np.arange(ns, dtype=np.float32) * (header["dt_us"] / 1000.0)

    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "Line_001.npy", data)
    np.save(out_dir / "Line_001_twt.npy", twt_ms)
    np.save(out_dir / "Line_001_ffid.npy", ffids)
    np.save(out_dir / "Line_001_tracf.npy", tracf)

    metadata = {
        "dataset_name": "Line_001",
        "segy_path": str(segy_path.resolve()),
        "ntraces": int(ntraces),
        "samples_per_trace": int(ns),
        "dt_ms": float(header["dt_us"] / 1000.0),
        "sample_format_code": int(header["sample_format"]),
        "npy_outputs": {
            "data": str((out_dir / "Line_001.npy").resolve()),
            "twt": str((out_dir / "Line_001_twt.npy").resolve()),
            "ffid": str((out_dir / "Line_001_ffid.npy").resolve()),
            "tracf": str((out_dir / "Line_001_tracf.npy").resolve()),
        },
    }
    with open(out_dir / "Line_001_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return data, twt_ms, ffids, tracf, metadata


def extract_ffid_231(data, twt_ms, ffids, tracf, out_dir: Path, traces_per_shot=TRACES_PER_SHOT, ffid_first=FFID_FIRST, target_ffid=TARGET_FFID):
    if data.shape[0] % traces_per_shot != 0:
        raise ValueError("Data does not reshape cleanly into regular shot gathers.")

    shot_index = target_ffid - ffid_first
    gathers = data.reshape((-1, traces_per_shot, data.shape[1]))
    ffid_gather = gathers[shot_index].astype(np.float32)

    ffid_mask = ffids == target_ffid
    ffid_tracf = tracf[ffid_mask]
    receiver_only = ffid_gather[ffid_tracf > 0].astype(np.float32)

    np.save(out_dir / "ffid_231_raw.npy", ffid_gather)
    np.save(out_dir / "ffid_231_receiver_only.npy", receiver_only)
    np.save(out_dir / "ffid_231_twt.npy", twt_ms)
    np.save(out_dir / "ffid_231_tracf.npy", ffid_tracf)

    metadata = {
        "target_ffid": int(target_ffid),
        "shot_index": int(shot_index),
        "traces_per_shot": int(traces_per_shot),
        "raw_shape": [int(v) for v in ffid_gather.shape],
        "receiver_only_shape": [int(v) for v in receiver_only.shape],
        "nonreceiver_trace_count": int(np.sum(ffid_tracf <= 0)),
        "receiver_trace_count": int(np.sum(ffid_tracf > 0)),
        "removed_tracf_values": [int(v) for v in ffid_tracf[ffid_tracf <= 0]],
    }
    with open(out_dir / "ffid_231_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


def main():
    data, twt_ms, ffids, tracf, line_meta = convert_segy_to_npy(DEFAULT_SEGY, OUTPUT_DIR)
    ffid_meta = extract_ffid_231(data, twt_ms, ffids, tracf, OUTPUT_DIR)

    print("SEG-Y to NPY complete")
    print("Prepared dir        :", OUTPUT_DIR)
    print("Full line shape     :", data.shape)
    print("FFID 231 raw shape  :", ffid_meta["raw_shape"])
    print("FFID 231 recv shape :", ffid_meta["receiver_only_shape"])


if __name__ == "__main__":
    main()
