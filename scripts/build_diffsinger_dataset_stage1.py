from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import soundfile as sf

MIN_SEGMENT_SEC = 2.0
MAX_SEGMENT_SEC = 9.0
PRE_ROLL_SEC = 0.08
POST_ROLL_SEC = 0.12


def load_words(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("original_words.json must contain a non-empty JSON list")
    result: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        word = str(item.get("word", "")).strip()
        if not word:
            continue
        start = float(item["start"])
        end = float(item["end"])
        if not (math.isfinite(start) and math.isfinite(end)) or end <= start:
            continue
        result.append({"word": word, "start": start, "end": end})
    if not result:
        raise ValueError("No usable timed words were found")
    return result


def group_words(words: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for word in words:
        if not current:
            current = [word]
            continue
        duration = word["end"] - current[0]["start"]
        gap = word["start"] - current[-1]["end"]
        if duration <= MAX_SEGMENT_SEC and (duration <= 5.0 or gap < 1.0):
            current.append(word)
        else:
            groups.append(current)
            current = [word]
    if current:
        groups.append(current)

    merged: list[list[dict[str, Any]]] = []
    for group in groups:
        duration = group[-1]["end"] - group[0]["start"]
        if merged and duration < MIN_SEGMENT_SEC:
            previous = merged[-1]
            combined = previous + group
            if combined[-1]["end"] - combined[0]["start"] <= MAX_SEGMENT_SEC:
                merged[-1] = combined
                continue
        merged.append(group)
    return merged


def build_dataset(project: Path, output: Path) -> dict[str, Any]:
    audio_files = sorted((project / "audio").glob("*.wav"))
    if not audio_files:
        raise FileNotFoundError(f"No WAV found in {project / 'audio'}")
    audio = audio_files[0]
    words_path = project / "lyrics" / "original_words.json"
    words = load_words(words_path)
    groups = group_words(words)

    samples, sr = sf.read(str(audio), always_2d=True, dtype="float32")
    total = samples.shape[0]
    duration = total / sr

    raw_wavs = output / "raw" / "wavs"
    raw_wavs.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for index, group in enumerate(groups):
        start = max(0.0, group[0]["start"] - PRE_ROLL_SEC)
        end = min(duration, group[-1]["end"] + POST_ROLL_SEC)
        if end - start < MIN_SEGMENT_SEC:
            continue
        i0 = max(0, int(round(start * sr)))
        i1 = min(total, int(round(end * sr)))
        segment = samples[i0:i1]
        if len(segment) == 0:
            continue
        name = f"freed_joud_{index:04d}"
        wav_path = raw_wavs / f"{name}.wav"
        sf.write(str(wav_path), segment, sr, subtype="PCM_16")
        rows.append({
            "name": name,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
            "words": " ".join(w["word"] for w in group),
            "word_count": len(group),
            "phonemes_ready": False,
            "pitch_ready": False,
            "status": "STAGING_ONLY",
        })

    if not rows:
        raise RuntimeError("No usable segments were produced")

    csv_path = output / "raw" / "segment_manifest.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "schema_version": "0.1",
        "status": "STAGING_READY",
        "source_project": str(project),
        "source_audio": str(audio),
        "sample_rate": int(sr),
        "channels": int(samples.shape[1]) if samples.ndim > 1 else 1,
        "source_duration": round(duration, 3),
        "source_word_count": len(words),
        "segment_count": len(rows),
        "segments": rows,
        "next_gate": "PHONEME_ALIGNMENT_AND_PITCH",
        "training_allowed": False,
    }
    (output / "dataset_stage1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Phoenix DiffSinger dataset staging segments")
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_dataset(Path(args.project), Path(args.output))
    print(json.dumps({k: report[k] for k in ("status", "source_word_count", "segment_count", "next_gate", "training_allowed")}, ensure_ascii=False, indent=2))
