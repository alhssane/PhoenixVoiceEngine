from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import soundfile as sf


DEFAULT_MIN_GAP_SEC = 0.5
DEFAULT_RMS_DB = -35.0
DEFAULT_MIN_VOICED_RATIO = 0.45
DEFAULT_F0_MIN = 65.0
DEFAULT_F0_MAX = 1100.0
DEFAULT_SHORT_INTER_WORD_GAP_SEC = 0.75
DEFAULT_SHORT_GAP_RMS_DB = -35.0
DEFAULT_SHORT_GAP_MIN_VOICED_RATIO = 0.70


def load_words(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("Transcript must be a JSON list.")
    out: list[dict[str, Any]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        word = str(item.get("word", "")).strip()
        if not word or not math.isfinite(start) or not math.isfinite(end):
            continue
        out.append({"index": i, "word": word, "start": start, "end": end})
    out.sort(key=lambda x: (x["start"], x["end"], x["index"]))
    return out


def analyze_region(audio: np.ndarray, sr: int, start: float, end: float) -> dict[str, float]:
    a = max(0, int(round(start * sr)))
    b = min(len(audio), int(round(end * sr)))
    seg = audio[a:b]
    if seg.size == 0:
        return {"duration_sec": max(0.0, end - start), "rms_db": -120.0, "voiced_ratio": 0.0, "median_f0_hz": 0.0}

    rms = float(np.sqrt(np.mean(seg.astype(np.float64) ** 2)))
    rms_db = 20.0 * math.log10(max(rms, 1e-8))

    try:
        f0, _, _ = librosa.pyin(
            seg.astype(np.float32),
            sr=sr,
            fmin=DEFAULT_F0_MIN,
            fmax=DEFAULT_F0_MAX,
            frame_length=2048,
            hop_length=512,
        )
        voiced = f0[~np.isnan(f0)]
        voiced_ratio = float(voiced.size / max(1, f0.size))
        median_f0 = float(np.median(voiced)) if voiced.size else 0.0
    except Exception:
        voiced_ratio = 0.0
        median_f0 = 0.0

    return {
        "duration_sec": max(0.0, end - start),
        "rms_db": rms_db,
        "voiced_ratio": voiced_ratio,
        "median_f0_hz": median_f0,
    }


def classify_gap(
    stats: dict[str, float],
    *,
    has_left_word: bool,
    has_right_word: bool,
    left_end: float,
    right_start: float,
    short_gap_sec: float,
    short_rms_db: float,
    short_voiced_ratio: float,
) -> tuple[bool, str]:
    duration = stats["duration_sec"]
    singing_signal = (
        stats["rms_db"] >= DEFAULT_RMS_DB
        and stats["voiced_ratio"] >= DEFAULT_MIN_VOICED_RATIO
    )
    inter_word_short_vocal = (
        has_left_word
        and has_right_word
        and duration <= short_gap_sec
        and stats["rms_db"] >= short_rms_db
        and stats["voiced_ratio"] >= short_voiced_ratio
    )
    if inter_word_short_vocal:
        return False, "SHORT_INTER_WORD_VOCAL_GAP"
    if singing_signal:
        return True, "MISSING_SINGING_TEXT"
    return False, "NON_SINGING_GAP"


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit whether untimed transcript gaps contain likely singing.")
    ap.add_argument("--source-wav", required=True)
    ap.add_argument("--words-json", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--min-gap-sec", type=float, default=DEFAULT_MIN_GAP_SEC)
    ap.add_argument("--rms-threshold-db", type=float, default=DEFAULT_RMS_DB)
    ap.add_argument("--min-voiced-ratio", type=float, default=DEFAULT_MIN_VOICED_RATIO)
    ap.add_argument("--short-inter-word-gap-sec", type=float, default=DEFAULT_SHORT_INTER_WORD_GAP_SEC)
    ap.add_argument("--short-gap-rms-threshold-db", type=float, default=DEFAULT_SHORT_GAP_RMS_DB)
    ap.add_argument("--short-gap-min-voiced-ratio", type=float, default=DEFAULT_SHORT_GAP_MIN_VOICED_RATIO)
    args = ap.parse_args()

    wav = Path(args.source_wav).resolve()
    words_path = Path(args.words_json).resolve()
    output = Path(args.output).resolve()

    info = sf.info(str(wav))
    audio, sr = sf.read(str(wav), dtype="float32")
    audio = np.asarray(audio).squeeze()
    if audio.ndim != 1:
        raise RuntimeError("Source WAV must be mono for coverage audit.")

    duration = len(audio) / sr
    words = load_words(words_path)

    gaps: list[dict[str, Any]] = []
    cursor = 0.0
    previous_item: dict[str, Any] | None = None
    for item in words:
        start = max(0.0, item["start"])
        end = min(duration, item["end"])
        gap_duration = start - cursor
        if gap_duration >= args.min_gap_sec:
            stats = analyze_region(audio, sr, cursor, start)
            likely_singing, classification = classify_gap(
                stats,
                has_left_word=previous_item is not None,
                has_right_word=True,
                left_end=float(previous_item["end"]) if previous_item else 0.0,
                right_start=start,
                short_gap_sec=args.short_inter_word_gap_sec,
                short_rms_db=args.short_gap_rms_threshold_db,
                short_voiced_ratio=args.short_gap_min_voiced_ratio,
            )
            gaps.append({
                "start_sec": cursor,
                "end_sec": start,
                **stats,
                "likely_singing": bool(likely_singing),
                "classification": classification,
                "left_word": previous_item["word"] if previous_item else None,
                "right_word": item["word"],
            })
        cursor = max(cursor, end)
        previous_item = item

    if duration - cursor >= args.min_gap_sec:
        stats = analyze_region(audio, sr, cursor, duration)
        singing_signal = (
            stats["rms_db"] >= args.rms_threshold_db
            and stats["voiced_ratio"] >= args.min_voiced_ratio
        )
        gaps.append({
            "start_sec": cursor,
            "end_sec": duration,
            **stats,
            "likely_singing": bool(singing_signal),
            "classification": "MISSING_SINGING_TEXT" if singing_signal else "NON_SINGING_GAP",
            "left_word": previous_item["word"] if previous_item else None,
            "right_word": None,
        })

    singing_gaps = [g for g in gaps if g["likely_singing"]]
    short_vocal_gaps = [g for g in gaps if g["classification"] == "SHORT_INTER_WORD_VOCAL_GAP"]
    result = {
        "status": "COVERAGE_REJECTED" if singing_gaps else "COVERAGE_CLEAN",
        "source_wav": str(wav),
        "words_json": str(words_path),
        "audio_duration_sec": duration,
        "transcript_word_count": len(words),
        "gap_count": len(gaps),
        "likely_singing_gap_count": len(singing_gaps),
        "likely_singing_gap_duration_sec": sum(g["duration_sec"] for g in singing_gaps),
        "short_inter_word_vocal_gap_count": len(short_vocal_gaps),
        "short_inter_word_vocal_gap_duration_sec": sum(g["duration_sec"] for g in short_vocal_gaps),
        "gaps": gaps,
        "training_allowed": not singing_gaps,
        "next_gate": "VERIFY_MISSING_SINGING_TEXT" if singing_gaps else "TRANSCRIPT_AND_COVERAGE_CLEAN",
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if singing_gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
