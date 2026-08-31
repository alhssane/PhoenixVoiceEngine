from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

NORMALIZE = {"aa": "a", "ii": "i", "uu": "u", "|": None}
EPS = 1e-8


def seq(v: str) -> list[str]:
    return [x for x in str(v or "").split() if x]


def durs(v: str) -> list[float]:
    return [float(x) for x in str(v or "").split() if x]


def norm_phone(p: str) -> str | None:
    return NORMALIZE.get(p, p)


def load_stage3(stage3: Path, name: str) -> list[tuple[str, float, float, float]]:
    path = stage3 / "phones" / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    phones = [str(x) for x in payload.get("phonemes", [])]
    alignment = list(payload.get("alignment", []))
    if len(phones) != len(alignment):
        raise RuntimeError(f"{name}: Stage3 phoneme/alignment count mismatch")

    usable = []
    for p, item in zip(phones, alignment):
        q = norm_phone(p)
        if q is None:
            continue
        duration = float(item.get("duration", 0.0))
        start = float(item.get("start", 0.0))
        end = float(item.get("end", start + duration))
        # Stage3 v1.4 alignment records do not require an explicit `aligned` flag.
        # A positive duration with valid start/end is an actual alignment record.
        if duration <= 0 or end <= start:
            continue
        usable.append((q, start, end, duration))
    return usable


def rms_features(x: np.ndarray, sr: int, start: float, end: float) -> dict[str, float]:
    frame = max(16, int(round(0.020 * sr)))
    hop = max(8, int(round(0.010 * sr)))
    if len(x) < frame:
        x = np.pad(x, (0, frame - len(x)))
    starts = np.arange(0, max(1, len(x) - frame + 1), hop, dtype=np.int64)
    vals = np.asarray(
        [np.sqrt(np.mean(x[int(s):int(s) + frame] ** 2) + EPS) for s in starts],
        dtype=np.float32,
    )
    times = (starts + frame / 2) / sr
    mask = (times >= start) & (times < end)
    chosen = vals[mask]
    if chosen.size == 0:
        return {"rms_median": 0.0, "rms_p90": 0.0, "silence_fraction": 1.0}
    floor = float(np.percentile(vals, 20)) * 0.35
    return {
        "rms_median": float(np.median(chosen)),
        "rms_p90": float(np.percentile(chosen, 90)),
        "silence_fraction": float(np.mean(chosen <= floor)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Audio-grounded Stage5 alignment audit v2.")
    ap.add_argument("--stage5-csv", type=Path, required=True)
    ap.add_argument("--stage5-wavs", type=Path, required=True)
    ap.add_argument("--stage3", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--output-csv", type=Path, required=True)
    ap.add_argument("--duration-delta-warn", type=float, default=0.035)
    ap.add_argument("--silence-fraction-warn", type=float, default=0.60)
    args = ap.parse_args()

    with args.stage5_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("Stage5 CSV is empty")

    details: list[dict[str, Any]] = []
    counts = defaultdict(int)
    coverage_errors: list[float] = []

    for row_i, row in enumerate(rows):
        name = str(row.get("name") or f"row_{row_i}")
        phones = seq(row.get("ph_seq", ""))
        stage5_durs = durs(row.get("ph_dur", ""))
        if len(phones) != len(stage5_durs):
            counts["critical"] += 1
            details.append({"name": name, "row_index": row_i, "status": "CRITICAL_PHONE_DURATION_MISMATCH"})
            continue

        wav = args.stage5_wavs / f"{name}.wav"
        if not wav.is_file():
            counts["missing_wav"] += 1
            details.append({"name": name, "row_index": row_i, "status": "MISSING_WAV"})
            continue

        s3 = load_stage3(args.stage3, name)
        if len(s3) != len(phones):
            counts["warning"] += 1
            details.append({
                "name": name,
                "row_index": row_i,
                "status": "ALIGNMENT_PHONE_COUNT_DIFFERENCE",
                "stage5_phone_count": len(phones),
                "stage3_usable_phone_count": len(s3),
            })
            continue

        audio, sr = sf.read(str(wav), dtype="float32", always_2d=True)
        x = audio.mean(axis=1)
        crop_start = s3[0][1]
        crop_end = s3[-1][2]
        stage3_span = crop_end - crop_start
        stage5_total = float(sum(stage5_durs))
        coverage_error = abs(stage3_span - stage5_total)
        coverage_errors.append(coverage_error)
        counts["rows_compared"] += 1

        for i, (phone, st5_dur) in enumerate(zip(phones, stage5_durs)):
            s3_phone, s3_start, s3_end, s3_dur = s3[i]
            local_start = max(0.0, s3_start - crop_start)
            local_end = max(local_start, s3_end - crop_start)
            feat = rms_features(x, sr, local_start, local_end)
            delta = abs(st5_dur - s3_dur)
            reasons: list[str] = []
            if delta > args.duration_delta_warn:
                reasons.append("STAGE5_VS_STAGE3_DURATION_DELTA")
            if feat["silence_fraction"] >= args.silence_fraction_warn and phone not in {"SP", "AP"}:
                reasons.append("HIGH_AUDIO_SILENCE_FRACTION")
            if coverage_error > 0.05:
                reasons.append("ROW_COVERAGE_ERROR")
            severity = "warning" if reasons else "ok"
            counts[severity] += int(bool(reasons))
            details.append({
                "name": name,
                "row_index": row_i,
                "phone_index": i,
                "phone": phone,
                "stage5_duration_sec": st5_dur,
                "stage3_duration_sec": s3_dur,
                "duration_delta_sec": delta,
                "stage3_start_sec": s3_start,
                "stage3_end_sec": s3_end,
                "crop_relative_start_sec": local_start,
                "crop_relative_end_sec": local_end,
                **feat,
                "coverage_error_sec": coverage_error,
                "severity": severity,
                "reasons": reasons,
            })

    result = {
        "status": "STAGE5_AUDIO_GROUNDED_ALIGNMENT_AUDIT_V2",
        "scope": "FINAL_STAGE5_ONLY",
        "stage5_csv": str(args.stage5_csv.resolve()),
        "stage5_wavs": str(args.stage5_wavs.resolve()),
        "stage3": str(args.stage3.resolve()),
        "stage3_alignment_policy": "positive_duration_and_valid_start_end; explicit aligned flag is optional",
        "summary": {
            "rows": len(rows),
            "rows_compared": counts["rows_compared"],
            "critical": counts["critical"],
            "warnings": counts["warning"],
            "missing_wavs": counts["missing_wav"],
            "mean_coverage_error_sec": statistics.fmean(coverage_errors) if coverage_errors else None,
            "max_coverage_error_sec": max(coverage_errors) if coverage_errors else None,
        },
        "flagged": [x for x in details if x.get("severity") == "warning" or x.get("status")],
        "details": details,
        "notes": [
            "Stage3 v1.4 records contain start/end/duration but no explicit aligned boolean; therefore positive-duration records are treated as usable alignments.",
            "RMS silence fraction is only a screening signal.",
            "This tool is read-only and does not modify training data.",
        ],
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "name", "row_index", "phone_index", "phone", "stage5_duration_sec",
        "stage3_duration_sec", "duration_delta_sec", "stage3_start_sec",
        "stage3_end_sec", "crop_relative_start_sec", "crop_relative_end_sec",
        "rms_median", "rms_p90", "silence_fraction", "coverage_error_sec",
        "severity", "reasons"
    ]
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in details:
            out = dict(item)
            if isinstance(out.get("reasons"), list):
                out["reasons"] = ";".join(out["reasons"])
            writer.writerow(out)

    print(json.dumps({
        "status": result["status"],
        "summary": result["summary"],
        "flagged_count": len(result["flagged"]),
        "output_json": str(args.output_json.resolve()),
        "output_csv": str(args.output_csv.resolve()),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
