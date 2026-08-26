from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any

import librosa
import numpy as np


AR_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]")


def install_epitran_hint() -> None:
    try:
        import epitran  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Missing Epitran. Install with: python -m pip install epitran") from exc


def normalize_arabic(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = text.replace("ـ", "")
    text = re.sub(r"\s+", " ", text)
    return text


def phonemize_word(epi: Any, word: str) -> list[str]:
    cleaned = normalize_arabic(word)
    if not cleaned or not AR_RE.search(cleaned):
        return []
    try:
        phones = epi.trans_list(cleaned)
    except Exception:
        ipa = epi.transliterate(cleaned)
        phones = [p for p in ipa.split() if p]
    return [str(p) for p in phones if str(p).strip()]


def load_manifest(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_words(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [x for x in data if isinstance(x, dict) and x.get("word") and x.get("end") is not None]


def nearest_note(midi_value: float) -> tuple[str, int, float]:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    midi = int(round(midi_value))
    return names[midi % 12], midi, round((midi_value - midi) * 100.0, 2)


def extract_pitch(audio_path: Path) -> dict[str, Any]:
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sr,
        frame_length=2048,
        hop_length=256,
    )
    times = librosa.times_like(f0, sr=sr, hop_length=256)
    rows: list[dict[str, Any]] = []
    valid = 0
    for t, hz, voiced, prob in zip(times, f0, voiced_flag, voiced_prob):
        if hz is None or not math.isfinite(float(hz)) or not bool(voiced):
            continue
        midi = float(librosa.hz_to_midi(float(hz)))
        note, midi_round, cents = nearest_note(midi)
        rows.append({
            "time": round(float(t), 4),
            "frequency_hz": round(float(hz), 3),
            "midi": round(midi, 3),
            "note": note,
            "midi_int": midi_round,
            "cents": cents,
            "voiced_probability": round(float(prob), 4),
        })
        valid += 1
    return {
        "sample_rate": int(sr),
        "frame_count": int(len(f0)),
        "valid_frames": int(valid),
        "coverage": round(valid / max(1, len(f0)), 4),
        "frames": rows,
    }


def attach_word_phonemes(words: list[dict[str, Any]], epi: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for word in words:
        text = normalize_arabic(str(word.get("word", "")))
        phones = phonemize_word(epi, text)
        start = float(word["start"])
        end = float(word["end"])
        duration = max(0.001, end - start)
        count = max(1, len(phones))
        phone_dur = duration / count
        phone_rows = []
        for i, phone in enumerate(phones):
            p0 = start + phone_dur * i
            p1 = end if i == len(phones) - 1 else start + phone_dur * (i + 1)
            phone_rows.append({"phone": phone, "start": round(p0, 4), "end": round(p1, 4), "duration": round(p1 - p0, 4)})
        result.append({
            "word": text,
            "start": round(start, 4),
            "end": round(end, 4),
            "phones": phones,
            "phone_alignment": phone_rows,
        })
    return result


def build_stage2(stage1: Path, output: Path) -> dict[str, Any]:
    install_epitran_hint()
    import epitran

    manifest_path = stage1 / "raw" / "segment_manifest.csv"
    words_path = next(stage1.parent.parent.glob("Projects/*/lyrics/original_words.json"), None)
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    if words_path is None or not words_path.is_file():
        raise FileNotFoundError("Could not locate original_words.json under Projects")

    segments = load_manifest(manifest_path)
    words = load_words(words_path)
    epi = epitran.Epitran("ara-Arab")

    aligned_words = attach_word_phonemes(words, epi)
    all_phones = sorted({p for w in aligned_words for p in w["phones"]})

    pitch_dir = output / "pitch"
    labels_dir = output / "labels"
    pitch_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for row in segments:
        name = row["name"]
        wav = stage1 / "raw" / "wavs" / f"{name}.wav"
        if not wav.is_file():
            continue
        pitch = extract_pitch(wav)
        (pitch_dir / f"{name}.json").write_text(json.dumps(pitch, ensure_ascii=False, indent=2), encoding="utf-8")

        start = float(row["start"])
        end = float(row["end"])
        seg_words = [w for w in aligned_words if float(w["end"]) > start and float(w["start"]) < end]
        local_words = []
        for w in seg_words:
            local_words.append({
                "word": w["word"],
                "start": round(max(0.0, float(w["start"]) - start), 4),
                "end": round(min(end, float(w["end"])) - start, 4),
                "phones": w["phones"],
                "phone_alignment": [
                    {
                        "phone": p["phone"],
                        "start": round(max(0.0, p["start"] - start), 4),
                        "end": round(min(end, p["end"]) - start, 4),
                        "duration": p["duration"],
                    }
                    for p in w["phone_alignment"]
                ],
            })

        coverage = pitch["coverage"]
        phone_count = sum(len(w["phones"]) for w in local_words)
        ready = bool(local_words) and phone_count > 0 and coverage >= 0.20
        label = {
            "name": name,
            "input_type": "phoneme",
            "phonemes": [p for w in local_words for p in w["phones"]],
            "words": local_words,
            "pitch_file": str(pitch_dir / f"{name}.json"),
            "pitch_coverage": coverage,
            "phoneme_source": "Epitran ara-Arab IPA; provisional phone durations distributed from ASR word boundaries",
            "alignment_status": "PROVISIONAL" if ready else "FAILED",
            "training_allowed": False,
        }
        (labels_dir / f"{name}.json").write_text(json.dumps(label, ensure_ascii=False, indent=2), encoding="utf-8")
        records.append({
            "name": name,
            "phoneme_count": phone_count,
            "pitch_coverage": coverage,
            "status": label["alignment_status"],
        })

    ready_count = sum(1 for r in records if r["status"] == "PROVISIONAL")
    report = {
        "schema_version": "0.2",
        "status": "STAGE2_PROVISIONAL_READY" if ready_count == len(records) and records else "STAGE2_INCOMPLETE",
        "segment_count": len(records),
        "segments_with_provisional_labels": ready_count,
        "phone_inventory_count": len(all_phones),
        "phone_inventory": all_phones,
        "phoneme_backend": "Epitran ara-Arab",
        "pitch_backend": "librosa.pyin",
        "training_allowed": False,
        "next_gate": "MFA_FORCED_ALIGNMENT_AND_DIFFSINGER_PHONESET_VALIDATION",
        "records": records,
    }
    (output / "dataset_stage2.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage1", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_stage2(Path(args.stage1), Path(args.output))
    print(json.dumps({k: report[k] for k in ("status", "segment_count", "segments_with_provisional_labels", "phone_inventory_count", "training_allowed", "next_gate")}, ensure_ascii=False, indent=2))
