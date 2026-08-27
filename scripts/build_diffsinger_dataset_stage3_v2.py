from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch
from transformers import AutoModelForCTC, AutoProcessor

MODEL_ID = "MostafaMaroof/wav2vec2-arabic-phoneme-asr"
SAMPLE_RATE = 16000
BLANK_TOKEN = "[PAD]"

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.phoneme_contract import normalize_arabic_for_phonemization, phonemize_arabic_text
from src.arabic.transcript_contract import repair_mojibake


def load_stage1_manifest(stage1: Path) -> list[dict[str, str]]:
    path = stage1 / "raw" / "segment_manifest.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing Stage1 manifest: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def token_vocabulary(processor) -> dict[str, int]:
    return {str(k): int(v) for k, v in processor.tokenizer.get_vocab().items()}


def ctc_forced_align(log_probs: torch.Tensor, target_ids: list[int], blank_id: int) -> list[tuple[int, int]]:
    if not target_ids:
        raise ValueError("Empty target sequence")
    t_steps, _ = log_probs.shape
    ext = [blank_id]
    for token in target_ids:
        ext.extend([token, blank_id])
    states = len(ext)
    neg_inf = -1e30
    dp = np.full((t_steps, states), neg_inf, dtype=np.float32)
    back = np.full((t_steps, states), -1, dtype=np.int16)
    dp[0, 0] = float(log_probs[0, blank_id].item())
    dp[0, 1] = float(log_probs[0, target_ids[0]].item())
    for t in range(1, t_steps):
        frame = log_probs[t]
        for s in range(states):
            best_prev = s
            best = dp[t - 1, s]
            if s > 0 and dp[t - 1, s - 1] > best:
                best = dp[t - 1, s - 1]
                best_prev = s - 1
            if s > 1 and ext[s] != blank_id and ext[s] != ext[s - 2] and dp[t - 1, s - 2] > best:
                best = dp[t - 1, s - 2]
                best_prev = s - 2
            dp[t, s] = best + float(frame[ext[s]].item())
            back[t, s] = best_prev
    end_state = max((states - 1, states - 2), key=lambda s: dp[-1, s])
    trace = [end_state]
    current = end_state
    for t in range(t_steps - 1, 0, -1):
        current = int(back[t, current])
        if current < 0:
            raise RuntimeError("CTC backtrace failed")
        trace.append(current)
    trace.reverse()
    return [(state // 2, t) for t, state in enumerate(trace) if ext[state] != blank_id]


def fit_token_sequence_to_frames(pairs: list[tuple[int, int]], token_count: int, hop_s: float, duration: float) -> list[dict[str, float | int | bool]]:
    by_token: list[list[int]] = [[] for _ in range(token_count)]
    for index, frame in pairs:
        if 0 <= index < token_count:
            by_token[index].append(frame)

    centers: list[float | None] = []
    for frames in by_token:
        if frames:
            centers.append(((frames[0] + frames[-1] + 1) * 0.5) * hop_s)
        else:
            centers.append(None)

    valid = [(i, c) for i, c in enumerate(centers) if c is not None]
    if not valid:
        return [{"target_index": i, "start": 0.0, "end": 0.0, "duration": 0.0, "aligned": False} for i in range(token_count)]

    aligned_frames = [frame for frames in by_token for frame in frames]
    first_center = max(0.0, min(duration, (min(aligned_frames) + 0.5) * hop_s))
    last_center = max(first_center, min(duration, (max(aligned_frames) + 0.5) * hop_s))
    valid_indices = [i for i, _ in valid]
    valid_centers = [float(c) for _, c in valid]

    starts: dict[int, float] = {}
    ends: dict[int, float] = {}
    for pos, index in enumerate(valid_indices):
        center = valid_centers[pos]
        start = first_center if pos == 0 else (valid_centers[pos - 1] + center) * 0.5
        end = last_center if pos == len(valid_indices) - 1 else (center + valid_centers[pos + 1]) * 0.5
        starts[index] = max(0.0, min(start, duration))
        ends[index] = max(starts[index], min(end, duration))

    result: list[dict[str, float | int | bool]] = []
    previous_end = first_center
    for index in range(token_count):
        if index not in starts:
            result.append({"target_index": index, "start": previous_end, "end": previous_end, "duration": 0.0, "aligned": False})
            continue
        start = max(previous_end, starts[index])
        end = max(start, ends[index])
        result.append({"target_index": index, "start": float(start), "end": float(end), "duration": float(end - start), "aligned": True})
        previous_end = end
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Phoenix canonical Arabic Stage3: forced alignment + F0")
    ap.add_argument("--stage1", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    stage1 = Path(args.stage1).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    phones_dir = output / "phones"
    f0_dir = output / "f0"
    phones_dir.mkdir(parents=True, exist_ok=True)
    f0_dir.mkdir(parents=True, exist_ok=True)

    rows = load_stage1_manifest(stage1)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForCTC.from_pretrained(MODEL_ID, torch_dtype=dtype)
    model.to(device)
    model.eval()
    vocab = token_vocabulary(processor)
    blank_id = vocab.get(BLANK_TOKEN, int(getattr(model.config, "pad_token_id", 0)))

    from epitran import Epitran
    epi = Epitran("ara-Arab")
    final_rows: list[dict[str, str]] = []
    diagnostics: list[dict] = []

    for row in rows:
        name = row["name"]
        wav = stage1 / "raw" / "wavs" / f"{name}.wav"
        if not wav.exists():
            diagnostics.append({"name": name, "status": "MISSING_WAV"})
            continue

        text = normalize_arabic_for_phonemization(repair_mojibake(row.get("words", "")))
        try:
            target = phonemize_arabic_text(epi, text)
        except Exception as exc:
            diagnostics.append({"name": name, "status": "PHONEME_CONVERSION_FAILED", "error": str(exc)})
            continue

        if not target:
            diagnostics.append({"name": name, "status": "EMPTY_PHONEME_SEQUENCE"})
            continue

        missing = sorted({phone for phone in target if phone != "|" and phone not in vocab})
        if missing:
            diagnostics.append({"name": name, "status": "UNSUPPORTED_CTC_PHONEMES", "missing": missing})
            continue

        audio, sr = sf.read(str(wav), dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        if sr != SAMPLE_RATE:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)
            sr = SAMPLE_RATE
        duration = len(audio) / sr
        inputs = processor(audio, sampling_rate=sr, return_tensors="pt")
        input_values = inputs.input_values.to(device=device, dtype=dtype)
        with torch.inference_mode():
            logits = model(input_values).logits[0].float().log_softmax(-1).cpu()
        target_ids = [vocab[p] for p in target]
        try:
            pairs = ctc_forced_align(logits, target_ids, blank_id)
            aligned = fit_token_sequence_to_frames(pairs, len(target), 0.02, duration)
        except Exception as exc:
            diagnostics.append({"name": name, "status": "ALIGNMENT_FAILED", "error": str(exc)})
            continue

        coverage = sum(1 for item in aligned if item["aligned"]) / max(1, len(aligned))
        if coverage < 0.80:
            diagnostics.append({"name": name, "status": "LOW_COVERAGE", "coverage": coverage})
            continue

        f0, _, _ = librosa.pyin(audio, fmin=70.0, fmax=1200.0, sr=sr, frame_length=2048, hop_length=320)
        f0_path = f0_dir / f"{name}.npy"
        np.save(f0_path, np.nan_to_num(f0, nan=0.0).astype(np.float32))
        phone_path = phones_dir / f"{name}.json"
        phone_path.write_text(
            json.dumps({
                "name": name,
                "text": text,
                "phonemes": target,
                "alignment": aligned,
                "coverage": coverage,
                "f0": str(f0_path.relative_to(output)),
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        ph_durs = [max(0.001, float(item["duration"])) for item in aligned]
        final_rows.append({"name": name, "ph_seq": " ".join(target), "ph_dur": " ".join(f"{d:.4f}" for d in ph_durs)})
        diagnostics.append({"name": name, "status": "ALIGNED", "coverage": coverage, "phone_count": len(target)})

    csv_path = output / "transcriptions.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "ph_seq", "ph_dur"])
        writer.writeheader()
        writer.writerows(final_rows)

    aligned_count = sum(1 for item in diagnostics if item["status"] == "ALIGNED")
    status = "STAGE3_CANONICAL_ALIGNED" if aligned_count == len(rows) and aligned_count > 0 else "STAGE3_CANONICAL_PARTIAL"
    report = {
        "schema_version": "1.0",
        "status": status,
        "model": MODEL_ID,
        "device": device,
        "source_stage1": str(stage1),
        "segment_count": len(rows),
        "aligned_count": aligned_count,
        "phone_csv": str(csv_path),
        "diagnostics": diagnostics,
        "training_allowed": False,
        "next_gate": "DIFFSINGER_PHONESET_VALIDATION_AND_DATASET_BUILD",
        "note": "Stage3 consumes the canonical UTF-8 Stage1 words and the shared Phoenix Arabic phoneme contract. It never re-reads legacy original_words.json or Stage2 text.",
    }
    (output / "dataset_stage3.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "segment_count", "aligned_count", "training_allowed", "next_gate")}, ensure_ascii=False, indent=2))
    return 0 if aligned_count == len(rows) and aligned_count > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
