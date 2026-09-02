from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import librosa
import soundfile as sf

from src.analyzer.audio_quality_engine import AudioQualityEngine
from src.analyzer.vocal_activity_analyzer import VocalActivityAnalyzer
from src.analyzer.lyric_extractor import LyricExtractor
from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend

VERSION = "1.1.0"
TARGET_PHONES = {"Z", "aa", "ii", "uu", "w", "y", "<", "D", "S", "T", "H", "^", "g", "j", "sh", "th"}


def normalize_arabic(text: str) -> str:
    text = str(text or "")
    text = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", text)
    text = re.sub(r"[\u200f\u200e\u061C]", "", text)
    return re.sub(r"[\W_]+", "", text, flags=re.UNICODE)


def load_v11(path: Path) -> tuple[set[str], Counter[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames is None:
            raise RuntimeError("V11 master has no header.")
        expected = ["ID", "SESSION", "PATTERN", "WORD", "TASHKEEL", "PHONES", "TARGETS"]
        if reader.fieldnames != expected:
            raise RuntimeError(f"V11 header mismatch: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != 1000:
        raise RuntimeError(f"V11 master must contain 1000 records, got {len(rows)}.")
    words = {normalize_arabic(r["WORD"]) for r in rows if r.get("WORD")}
    phones = Counter()
    for row in rows:
        for phone in (row.get("TARGETS") or "").split(","):
            if phone in TARGET_PHONES:
                phones[phone] += 1
    return words, phones


def safe_name(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z_\-]+", "_", text).strip("_") or "segment"


def extract_clip(audio, sr: int, out_path: Path, start: float, end: float, pad_start: float, pad_end: float) -> float:
    duration = len(audio) / sr
    a = max(0.0, float(start) - pad_start)
    b = min(duration, float(end) + pad_end)
    if b <= a:
        raise RuntimeError(f"Invalid clip interval {start}..{end}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), audio[int(round(a * sr)):int(round(b * sr))], sr, subtype="PCM_16")
    return b - a


def group_words(words: list[dict[str, Any]], max_duration: float, max_gap: float) -> list[list[dict[str, Any]]]:
    if max_duration <= 0 or max_gap < 0:
        raise ValueError("Invalid phrase grouping limits.")
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for word in words:
        if not current:
            current = [word]
            continue
        gap = float(word["start"]) - float(current[-1]["end"])
        proposed = float(word["end"]) - float(current[0]["start"])
        if gap <= max_gap and proposed <= max_duration:
            current.append(word)
        else:
            groups.append(current)
            current = [word]
    if current:
        groups.append(current)
    return groups


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="PhoenixVoiceEngine V12 full-audio Zaffa corpus miner.")
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--v11", default=r"D:\PhoenixVoiceEngine\diagnostics\arabic_recording_pack_v11\recording_master_v11.tsv")
    ap.add_argument("--model-path", default=None)
    ap.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    ap.add_argument("--compute-type", default="float16")
    ap.add_argument("--max-phrase-sec", type=float, default=8.0)
    ap.add_argument("--max-interword-gap-sec", type=float, default=1.0)
    ap.add_argument("--word-padding", type=float, default=0.08)
    ap.add_argument("--phrase-padding", type=float, default=0.15)
    args = ap.parse_args()

    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    v11 = Path(args.v11).resolve()
    output.mkdir(parents=True, exist_ok=True)

    if not source.is_file():
        raise FileNotFoundError(source)
    if not v11.is_file():
        raise FileNotFoundError(v11)

    print("=== PHOENIXVOICEENGINE ZAFFA CORPUS MINER V12 ===")
    print("VERSION:", VERSION)
    print("SOURCE:", source)
    print("V11:", v11)

    quality = AudioQualityEngine().analyze(str(source))
    print("\nAUDIO QUALITY:", quality.status, f"{quality.training_suitability}/100")
    if quality.status not in {"READY", "READY_WITH_PROCESSING"}:
        raise RuntimeError(f"V12 rejected source audio: {quality.status}")
    (output / "audio_quality_v12.json").write_text(
        json.dumps(quality.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    activity = VocalActivityAnalyzer().analyze(str(source))
    (output / "activity_v12.json").write_text(
        json.dumps(activity.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("Loading audio once for candidate extraction...")
    audio, sr = librosa.load(str(source), sr=None, mono=True)
    if audio.size == 0 or sr <= 0:
        raise RuntimeError("Source audio contains no usable samples.")

    extractor = LyricExtractor(
        model_size="large-v3",
        language="ar",
        device=args.device,
        compute_type=args.compute_type,
        beam_size=5,
        vad_filter=True,
        min_silence_duration_ms=350,
        model_path=args.model_path,
    )
    report = extractor.extract(str(source))
    (output / "transcript_v12.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    v11_words, v11_phone_targets = load_v11(v11)
    transcript_words = [
        {
            "index": w.index,
            "text": w.text,
            "normalized": normalize_arabic(w.text),
            "start": float(w.start_time),
            "end": float(w.end_time),
            "duration": float(w.duration),
            "confidence": float(w.confidence),
        }
        for w in report.words
        if w.text.strip() and w.end_time > w.start_time
    ]

    candidates_dir = output / "candidates"
    word_rows: list[dict[str, Any]] = []
    found_words: set[str] = set()
    phone_counts: Counter[str] = Counter()
    g2p_failures: list[dict[str, str]] = []
    g2p = PhoenixArabicG2PFrontend()

    for idx, word in enumerate(transcript_words, 1):
        normalized = word["normalized"]
        is_target = normalized in v11_words
        if is_target:
            found_words.add(normalized)

        phones: list[str] = []
        try:
            conversion = g2p.convert_word(word["text"])
            phones = list(conversion.phones)
            phone_counts.update(p for p in phones if p in TARGET_PHONES)
        except Exception as exc:
            g2p_failures.append({"word": word["text"], "error": str(exc)})

        path = candidates_dir / "words" / f"word_{idx:06d}_{safe_name(word['text'])}.wav"
        duration = extract_clip(audio, sr, path, word["start"], word["end"], args.word_padding, args.word_padding)
        word_rows.append({
            "id": f"w{idx:06d}",
            "source": source.name,
            "source_start": word["start"],
            "source_end": word["end"],
            "clip_duration": round(duration, 6),
            "word": word["text"],
            "normalized_word": normalized,
            "confidence": word["confidence"],
            "phones": " ".join(phones),
            "candidate_status": "TARGET_WORD_MATCH" if is_target else "NON_TARGET_WORD",
            "audio": str(path),
        })

    phrase_rows: list[dict[str, Any]] = []
    groups = group_words(transcript_words, args.max_phrase_sec, args.max_interword_gap_sec)
    for idx, group in enumerate(groups, 1):
        start = float(group[0]["start"])
        end = float(group[-1]["end"])
        text_value = " ".join(w["text"] for w in group)
        path = candidates_dir / "phrases" / f"phrase_{idx:05d}.wav"
        duration = extract_clip(audio, sr, path, start, end, args.phrase_padding, args.phrase_padding)
        phrase_rows.append({
            "id": f"p{idx:05d}",
            "source": source.name,
            "source_start": start,
            "source_end": end,
            "clip_duration": round(duration, 6),
            "text": text_value,
            "word_count": len(group),
            "audio": str(path),
            "candidate_status": "ALIGNMENT_REQUIRED",
        })

    write_tsv(output / "word_candidates_v12.tsv", word_rows)
    write_tsv(output / "phrase_candidates_v12.tsv", phrase_rows)

    coverage = {
        "v11_target_word_count": len(v11_words),
        "transcript_word_count": len(transcript_words),
        "v11_target_words_found": len(found_words),
        "v11_target_word_coverage_percent": round(100.0 * len(found_words) / max(1, len(v11_words)), 2),
        "missing_v11_words": sorted(v11_words - found_words),
        "v11_target_phone_reference_counts": dict(v11_phone_targets),
        "observed_target_phone_counts": dict(phone_counts),
        "g2p_failure_count": len(g2p_failures),
        "g2p_failures": g2p_failures[:100],
    }
    (output / "coverage_v12.json").write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary = {
        "schema_version": "v12.1",
        "status": "CANDIDATES_READY_ALIGNMENT_REQUIRED",
        "source": str(source),
        "audio_quality_status": quality.status,
        "audio_training_suitability": quality.training_suitability,
        "duration_sec": quality.duration,
        "transcript_words": len(transcript_words),
        "word_candidates": len(word_rows),
        "phrase_candidates": len(phrase_rows),
        "target_words_found": len(found_words),
        "target_word_coverage_percent": coverage["v11_target_word_coverage_percent"],
        "target_phone_observations": dict(phone_counts),
        "activity_segments": activity.segment_count,
        "training_allowed": False,
        "next_gate": "PHONEME_FORCED_ALIGNMENT_AND_SEGMENT_QC",
        "note": "ASR timestamps are candidate boundaries only. Candidates are not training-approved until phoneme-level alignment and QC pass.",
    }
    (output / "summary_v12.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n=== V12 COMPLETE ===")
    print("STATUS:", summary["status"])
    print("TRANSCRIPT_WORDS:", len(transcript_words))
    print("WORD_CANDIDATES:", len(word_rows))
    print("PHRASE_CANDIDATES:", len(phrase_rows))
    print("TARGET_WORD_COVERAGE:", coverage["v11_target_word_coverage_percent"], "%")
    print("OUTPUT:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
