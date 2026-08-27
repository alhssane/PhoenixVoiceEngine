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


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit whether untimed transcript gaps contain likely singing.")
    ap.add_argument("--source-wav", required=True)
    ap.add_argument("--words-json", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--min-gap-sec", type=float, default=DEFAULT_MIN_GAP_SEC)
    ap.add_argument("--rms-threshold-db", type=float, default=DEFAULT_RMS_DB)
    ap.add_argument("--min-voiced-ratio", type=float, default=DEFAULT_MIN_VOICED_RATIO)
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
    for item in words:
        start = max(0.0, item["start"])
        end = min(duration, item["end"])
        if start - cursor >= args.min_gap_sec:
            stats = analyze_region(audio, sr, cursor, start)
            likely_singing = (
                stats["rms_db"] >= args.rms_threshold_db
                and stats["voiced_ratio"] >= args.min_voiced_ratio
            )
            gaps.append({
                "start_sec": cursor,
                "end_sec": start,
                **stats,
                "likely_singing": bool(likely_singing),
            })
        cursor = max(cursor, end)

    if duration - cursor >= args.min_gap_sec:
        stats = analyze_region(audio, sr, cursor, duration)
        likely_singing = (
            stats["rms_db"] >= args.rms_threshold_db
            and stats["voiced_ratio"] >= args.min_voiced_ratio
        )
        gaps.append({
            "start_sec": cursor,
            "end_sec": duration,
            **stats,
            "likely_singing": bool(likely_singing),
        })

    singing_gaps = [g for g in gaps if g["likely_singing"]]
    result = {
        "status": "COVERAGE_REJECTED" if singing_gaps else "COVERAGE_CLEAN",
        "source_wav": str(wav),
        "words_json": str(words_path),
        "audio_duration_sec": duration,
        "transcript_word_count": len(words),
        "gap_count": len(gaps),
        "likely_singing_gap_count": len(singing_gaps),
        "likely_singing_gap_duration_sec": sum(g["duration_sec"] for g in singing_gaps),
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
