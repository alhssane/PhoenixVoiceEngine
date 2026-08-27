from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

import numpy as np
import soundfile as sf

NORMALIZE = {"aa": "a", "ii": "i", "uu": "u", "|": None}


def resolve_stage3_dir(stage4: Path, explicit: str | None) -> Path:
    """Resolve the Stage3 directory without relying on legacy fixed names."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).resolve())

    dataset_root = stage4.parent
    candidates.extend(
        [
            dataset_root / "stage3_full_v4",
            dataset_root / "stage3_full_v3",
            dataset_root / "freed_joud_diffsinger_stage3",
            dataset_root / "stage3",
        ]
    )

    for candidate in candidates:
        if (candidate / "phones").is_dir():
            return candidate

    raise FileNotFoundError(
        "Could not locate Stage3 alignment directory. Expected a sibling "
        "stage3_full_v4/phones, stage3_full_v3/phones, or pass --stage3 explicitly."
    )


def load_stage3_alignment(stage3: Path, name: str) -> tuple[float, float]:
    path = stage3 / "phones" / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing Stage3 alignment: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    phonemes = payload.get("phonemes", [])
    alignment = payload.get("alignment", [])
    if len(phonemes) != len(alignment):
        raise RuntimeError(f"Stage3 phoneme/alignment mismatch for {name}")

    kept = []
    for phone, item in zip(phonemes, alignment):
        normalized = NORMALIZE.get(phone, phone)
        if normalized is None:
            continue
        if not item.get("aligned"):
            continue
        if float(item.get("duration", 0.0)) <= 0:
            continue
        kept.append(item)

    if not kept:
        raise RuntimeError(f"No usable aligned phoneme span available for {name}")
    start = min(float(x["start"]) for x in kept)
    end = max(float(x["end"]) for x in kept)
    if end <= start:
        raise RuntimeError(f"Invalid aligned span for {name}: {start}..{end}")
    return start, end


def crop_wav(src: Path, dst: Path, start: float, end: float) -> tuple[int, int, float]:
    audio, sr = sf.read(str(src), dtype="float32", always_2d=True)
    total = audio.shape[0] / sr
    start = max(0.0, min(start, total))
    end = max(start, min(end, total))
    a = int(round(start * sr))
    b = int(round(end * sr))
    if b <= a:
        raise RuntimeError(f"Empty crop for {src.name}")
    cropped = audio[a:b]
    sf.write(str(dst), cropped, sr, subtype="PCM_16")
    return sr, cropped.shape[1], cropped.shape[0] / sr


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage4", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--stage3", required=False, default=None)
    args = ap.parse_args()

    stage4 = Path(args.stage4).resolve()
    output = Path(args.output).resolve()
    raw = output / "raw"
    wavs = raw / "wavs"
    wavs.mkdir(parents=True, exist_ok=True)

    report_path = stage4 / "dataset_stage4_ar.json"
    if not report_path.exists():
        raise FileNotFoundError(f"Missing Stage4 report: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    accepted_statuses = {
        "ARABIC_PHONESET_READY",
        "ARABIC_CANONICAL_PHONESET_READY",
    }
    if report.get("status") not in accepted_statuses:
        raise RuntimeError(
            f"Stage4 Arabic phone-set dataset is not ready for bake: "
            f"status={report.get('status')!r}"
        )

    src_csv = stage4 / "raw" / "transcriptions.csv"
    src_wavs = stage4 / "raw" / "wavs"
    if not src_csv.exists():
        raise FileNotFoundError(f"Missing Stage4 transcription CSV: {src_csv}")
    if not src_wavs.is_dir():
        raise FileNotFoundError(f"Missing Stage4 WAV directory: {src_wavs}")

    rows = list(csv.DictReader(src_csv.open("r", encoding="utf-8-sig", newline="")))
    expected_count = int(report.get("segment_count", len(rows)))
    if expected_count != len(rows):
        raise RuntimeError(
            f"transcriptions.csv count does not match Stage4 report: "
            f"rows={len(rows)} report={expected_count}"
        )

    stage3 = resolve_stage3_dir(stage4, args.stage3)

    durations_report = []
    for row in rows:
        name = row["name"]
        phones = [x for x in row["ph_seq"].split() if x]
        durs = [float(x) for x in row["ph_dur"].split() if x]
        if len(phones) != len(durs):
            raise RuntimeError(f"Phone/duration mismatch: {name}: {len(phones)} != {len(durs)}")
        if not phones or any(d <= 0 for d in durs):
            raise RuntimeError(f"Invalid phone durations: {name}")

        src = src_wavs / f"{name}.wav"
        if not src.exists():
            raise FileNotFoundError(src)

        start, end = load_stage3_alignment(stage3, name)
        dst = wavs / src.name
        sample_rate, channels, audio_duration = crop_wav(src, dst, start, end)
        phone_duration = float(sum(durs))
        error = abs(audio_duration - phone_duration)
        if error > 0.05:
            raise RuntimeError(
                f"Duration coverage still too far after aligned crop for {name}: "
                f"audio={audio_duration:.3f}s phones={phone_duration:.3f}s error={error:.3f}s"
            )

        durations_report.append({
            "name": name,
            "sample_rate": int(sample_rate),
            "channels": int(channels),
            "crop_start_sec": start,
            "crop_end_sec": end,
            "audio_duration": audio_duration,
            "phone_duration": phone_duration,
            "coverage_error": error,
        })

    dst_csv = raw / "transcriptions.csv"
    with dst_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "ph_seq", "ph_dur"])
        writer.writeheader()
        writer.writerows(rows)

    shutil.copy2(stage4 / "phonemes.txt", output / "phonemes.txt")
    shutil.copy2(stage4 / "phone_set.json", output / "phone_set.json")

    max_error = max(x["coverage_error"] for x in durations_report) if durations_report else 0.0
    result = {
        "schema_version": "0.8",
        "status": "RAW_DATASET_VALIDATED",
        "segment_count": len(rows),
        "wav_count": len(list(wavs.glob("*.wav"))),
        "phone_csv": str(dst_csv),
        "phonemes": str(output / "phonemes.txt"),
        "stage3_dir": str(stage3),
        "stage4_status": report.get("status"),
        "max_duration_coverage_error_sec": max_error,
        "segments": durations_report,
        "training_allowed": False,
        "next_gate": "DIFFSINGER_BINARIZE_CONFIG_AND_PREPROCESS",
        "note": "Each WAV is cropped to the Stage3 CTC-aligned span of non-separator phonemes before validating ph_dur coverage.",
    }
    (output / "dataset_stage5.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "segment_count", "wav_count", "max_duration_coverage_error_sec", "training_allowed", "next_gate")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
