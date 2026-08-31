from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

NORMALIZE = {"aa": "a", "ii": "i", "uu": "u", "|": None}
EPS = 1e-8


def parse_seq(value: str) -> list[str]:
    return [x for x in str(value or "").split() if x]


def parse_durs(value: str) -> list[float]:
    return [float(x) for x in str(value or "").split() if x]


def norm_phone(phone: str) -> str | None:
    return NORMALIZE.get(phone, phone)


def load_stage3(stage3: Path, name: str) -> tuple[list[str], list[dict[str, Any]]]:
    path = stage3 / "phones" / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    phones = [str(x) for x in payload.get("phonemes", [])]
    alignment = list(payload.get("alignment", []))
    if len(phones) != len(alignment):
        raise RuntimeError(f"{name}: Stage3 phoneme/alignment count mismatch")
    return phones, alignment


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    audio, sr = sf.read(str(path), dtype="float32", always_2d=True)
    x = audio.mean(axis=1)
    return x, int(sr)


def frame_rms(x: np.ndarray, sr: int, frame_sec: float = 0.020, hop_sec: float = 0.010) -> tuple[np.ndarray, np.ndarray]:
    frame = max(16, int(round(frame_sec * sr)))
    hop = max(8, int(round(hop_sec * sr)))
    if len(x) < frame:
        xp = np.pad(x, (0, frame - len(x)))
    else:
        xp = x
    starts = np.arange(0, max(1, len(xp) - frame + 1), hop, dtype=np.int64)
    vals = np.empty(len(starts), dtype=np.float32)
    for j, s in enumerate(starts):
        z = xp[int(s):int(s) + frame]
        vals[j] = float(np.sqrt(np.mean(z * z) + EPS))
    times = (starts + frame / 2) / sr
    return times, vals


def local_audio_stats(rms_times: np.ndarray, rms_vals: np.ndarray, start: float, end: float, floor: float) -> dict[str, float]:
    m = (rms_times >= start) & (rms_times < end)
    vals = rms_vals[m]
    if vals.size == 0:
        return {"rms_median": 0.0, "rms_p90": 0.0, "silence_fraction": 1.0}
    med = float(np.median(vals))
    p90 = float(np.percentile(vals, 90))
    silence_fraction = float(np.mean(vals <= floor))
    return {"rms_median": med, "rms_p90": p90, "silence_fraction": silence_fraction}


def main() -> int:
    ap = argparse.ArgumentParser(description="Audio-grounded Stage5 alignment audit; read-only.")
    ap.add_argument("--stage5-csv", type=Path, required=True)
    ap.add_argument("--stage5-wavs", type=Path, required=True)
    ap.add_argument("--stage3", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--output-csv", type=Path, required=True)
    ap.add_argument("--duration-delta-warn", type=float, default=0.035)
    ap.add_argument("--short-sec", type=float, default=0.030)
    ap.add_argument("--long-sec", type=float, default=0.400)
    ap.add_argument("--rms-silence-fraction-warn", type=float, default=0.60)
    args = ap.parse_args()

    rows = list(csv.DictReader(args.stage5_csv.open("r", encoding="utf-8-sig", newline="")))
    if not rows:
        raise RuntimeError("Stage5 CSV is empty")

    details: list[dict[str, Any]] = []
    phone_stats: dict[str, list[float]] = defaultdict(list)
    critical = 0
    warnings = 0
    missing = 0
    coverage_errors: list[float] = []

    for row_i, row in enumerate(rows):
        name = str(row.get("name") or f"row_{row_i}")
        phones = parse_seq(row.get("ph_seq", ""))
        durs = parse_durs(row.get("ph_dur", ""))
        if len(phones) != len(durs) or not phones:
            critical += 1
            details.append({"name": name, "row_index": row_i, "status": "CRITICAL_PHONE_DURATION_MISMATCH"})
            continue

        wav = args.stage5_wavs / f"{name}.wav"
        if not wav.is_file():
            missing += 1
            details.append({"name": name, "row_index": row_i, "status": "MISSING_WAV", "wav": str(wav)})
            continue

        s3_phones, s3_items = load_stage3(args.stage3, name)
        usable = []
        for p, item in zip(s3_phones, s3_items):
            q = norm_phone(p)
            if q is None or not item.get("aligned"):
                continue
            dur = float(item.get("duration", 0.0))
            if dur <= 0:
                continue
            usable.append((q, float(item.get("start", 0.0)), float(item.get("end", 0.0)), dur))

        if len(usable) != len(phones):
            warnings += 1
            details.append({"name": name, "row_index": row_i, "status": "ALIGNMENT_PHONE_COUNT_DIFFERENCE", "stage5_phone_count": len(phones), "stage3_usable_phone_count": len(usable)})
            continue

        audio, sr = read_wav(wav)
        audio_duration = len(audio) / sr
        if not usable:
            critical += 1
            continue
        crop_start = usable[0][1]
        crop_end = usable[-1][2]
        crop_duration = max(0.0, crop_end - crop_start)
        phone_total = float(sum(durs))
        coverage_error = abs(crop_duration - phone_total)
        coverage_errors.append(coverage_error)

        rms_times, rms_vals = frame_rms(audio, sr)
        floor = float(np.percentile(rms_vals, 20)) * 0.35
        cumulative = 0.0
        for i, (phone, st5_dur) in enumerate(zip(phones, durs)):
            s5_start = cumulative
            s5_end = cumulative + st5_dur
            cumulative = s5_end
            if i >= len(usable):
                break
            s3_phone, s3_start, s3_end, s3_dur = usable[i]
            local_start = max(0.0, s3_start - crop_start)
            local_end = max(local_start, s3_end - crop_start)
            feat = local_audio_stats(rms_times, rms_vals, local_start, local_end, floor)
            dur_delta = abs(st5_dur - s3_dur)
            duration_flag = dur_delta > args.duration_delta_warn
            plausibility_flag = st5_dur < args.short_sec or st5_dur > args.long_sec
            silence_flag = feat["silence_fraction"] >= args.rms_silence_fraction_warn
            severity = "ok"
            reasons: list[str] = []
            if duration_flag:
                severity = "warning"
                reasons.append("STAGE5_VS_STAGE3_DURATION_DELTA")
            if plausibility_flag:
                severity = "warning"
                reasons.append("DURATION_OUTSIDE_THRESHOLD")
            if silence_flag and norm_phone(phone) not in {"SP", "AP", "|"}:
                severity = "warning"
                reasons.append("HIGH_AUDIO_SILENCE_FRACTION")
            if coverage_error > 0.05:
                severity = "critical"
                reasons.append("ROW_COVERAGE_ERROR")
            if reasons:
                warnings += int(severity == "warning")
                critical += int(severity == "critical")
            phone_stats[phone].append(float(st5_dur))
            details.append({
                "name": name,
                "row_index": row_i,
                "phone_index": i,
                "phone": phone,
                "stage5_duration_sec": st5_dur,
                "stage3_duration_sec": s3_dur,
                "duration_delta_sec": dur_delta,
                "stage3_start_sec": s3_start,
                "stage3_end_sec": s3_end,
                "crop_relative_start_sec": local_start,
                "crop_relative_end_sec": local_end,
                **feat,
                "severity": severity,
                "reasons": reasons,
            })

    duration_summary = {}
    for p, vals in sorted(phone_stats.items()):
        duration_summary[p] = {
            "count": len(vals),
            "median_sec": statistics.median(vals),
            "p10_sec": float(np.percentile(vals, 10)),
            "p90_sec": float(np.percentile(vals, 90)),
            "min_sec": min(vals),
            "max_sec": max(vals),
        }

    result = {
        "status": "STAGE5_AUDIO_GROUNDED_ALIGNMENT_AUDIT_V1",
        "scope": "FINAL_STAGE5_ONLY",
        "stage5_csv": str(args.stage5_csv.resolve()),
        "stage5_wavs": str(args.stage5_wavs.resolve()),
        "stage3": str(args.stage3.resolve()),
        "summary": {
            "rows": len(rows),
            "critical": critical,
            "warnings": warnings,
            "missing_wavs": missing,
            "mean_coverage_error_sec": statistics.fmean(coverage_errors) if coverage_errors else None,
            "max_coverage_error_sec": max(coverage_errors) if coverage_errors else None,
        },
        "phone_duration_summary": duration_summary,
        "flagged": [x for x in details if x.get("severity") in {"warning", "critical"} or x.get("status")],
        "details": details,
        "notes": [
            "This audit compares Stage5 phone durations against the Stage3 CTC alignment actually used to crop the Stage5 WAVs.",
            "Audio RMS silence fraction is a screening signal, not an automatic assertion that an alignment is wrong.",
            "No files are modified by this tool.",
        ],
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["name", "row_index", "phone_index", "phone", "stage5_duration_sec", "stage3_duration_sec", "duration_delta_sec", "stage3_start_sec", "stage3_end_sec", "crop_relative_start_sec", "crop_relative_end_sec", "rms_median", "rms_p90", "silence_fraction", "severity", "reasons"]
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for item in details:
            if isinstance(item.get("reasons"), list):
                item = dict(item)
                item["reasons"] = ";".join(item["reasons"])
            w.writerow(item)

    print(json.dumps({
        "status": result["status"],
        "summary": result["summary"],
        "flagged_count": len(result["flagged"]),
        "top_flagged": result["flagged"][:20],
        "output_json": str(args.output_json.resolve()),
        "output_csv": str(args.output_csv.resolve()),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
