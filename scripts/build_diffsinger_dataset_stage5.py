from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

import numpy as np
import soundfile as sf


def load_stage3_alignment(stage4: Path, name: str) -> tuple[float, float]:
    stage3 = stage4.parent / "freed_joud_diffsinger_stage3"
    path = stage3 / "phones" / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing Stage3 alignment: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    aligned = [x for x in payload.get("alignment", []) if x.get("aligned") and float(x.get("duration", 0.0)) > 0]
    if not aligned:
        raise RuntimeError(f"No aligned span available for {name}")
    start = min(float(x["start"]) for x in aligned)
    end = max(float(x["end"]) for x in aligned)
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
    args = ap.parse_args()

    stage4 = Path(args.stage4).resolve()
    output = Path(args.output).resolve()
    raw = output / "raw"
    wavs = raw / "wavs"
    wavs.mkdir(parents=True, exist_ok=True)

    report = json.loads((stage4 / "dataset_stage4_ar.json").read_text(encoding="utf-8"))
    if report.get("status") != "ARABIC_PHONESET_READY" or report.get("segment_count") != 11:
        raise RuntimeError("Stage4 Arabic phone-set dataset is not ready for bake.")

    src_csv = stage4 / "raw" / "transcriptions.csv"
    src_wavs = stage4 / "raw" / "wavs"
    rows = list(csv.DictReader(src_csv.open("r", encoding="utf-8-sig", newline="")))
    if len(rows) != report["segment_count"]:
        raise RuntimeError("transcriptions.csv count does not match Stage4 report.")

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

        start, end = load_stage3_alignment(stage4, name)
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

    max_error = max(x["coverage_error"] for x in durations_report)
    result = {
        "schema_version": "0.5",
        "status": "RAW_DATASET_VALIDATED",
        "segment_count": len(rows),
        "wav_count": len(list(wavs.glob("*.wav"))),
        "phone_csv": str(dst_csv),
        "phonemes": str(output / "phonemes.txt"),
        "max_duration_coverage_error_sec": max_error,
        "segments": durations_report,
        "training_allowed": False,
        "next_gate": "DIFFSINGER_BINARIZE_CONFIG_AND_PREPROCESS",
        "note": "Each WAV is cropped to the Stage3 CTC-aligned phoneme span before validating ph_dur coverage.",
    }
    (output / "dataset_stage5.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "segment_count", "wav_count", "max_duration_coverage_error_sec", "training_allowed", "next_gate")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
