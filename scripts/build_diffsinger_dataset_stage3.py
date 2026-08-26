from __future__ import annotations

import argparse
import csv
import json
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

# Model vocabulary uses x for خ and th for ذ/ث in its Halabi-style scheme.
IPA_MAP = {
    "ʔ": "<", "ء": "<",
    "b": "b", "t": "t", "d": "d", "k": "k", "q": "q",
    "f": "f", "s": "s", "z": "z", "ʃ": "sh", "ʒ": "j",
    "x": "x", "χ": "x", "ɣ": "g", "ɢ": "g",
    "θ": "th", "ð": "th", "ħ": "H", "ʕ": "^",
    "h": "h", "m": "m", "n": "n", "r": "r", "ɾ": "r",
    "l": "l", "w": "w", "j": "y",
    "a": "a", "i": "i", "u": "u", "e": "e", "o": "o",
    "ː": ":", "ـ": "",
    "sˤ": "S", "dˤ": "D", "tˤ": "T", "zˤ": "Z",
    "S": "S", "D": "D", "T": "T", "Z": "Z",
}
MULTI_IPA = ["sˤ", "dˤ", "tˤ", "zˤ", "t͡ʃ", "d͡ʒ", "ʃ", "θ", "ð", "ɣ", "χ", "ħ", "ʕ"]
VALID_MODEL_TOKENS = {
    "<", "^", "S", "D", "T", "Z", "a", "aa", "b", "bb", "d", "dd", "f", "ff",
    "g", "gg", "h", "hh", "H", "i", "ii", "j", "jj", "k", "kk", "l", "ll", "m", "mm",
    "n", "nn", "p", "pp", "q", "qq", "r", "rr", "s", "sh", "sil", "ss", "t", "th", "tt",
    "u", "uu", "w", "ww", "x", "xx", "y", "yy", "z", "zz", "|", "A", "AA", "AH", "E", "EE",
    "I", "II", "U", "UU", "HH", "DD", "SS", "TT", "ZZ", "$", "$$", "*", "**", "<<"
}


def norm_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def epitran_to_model_tokens(text: str, epi) -> list[str]:
    tokens: list[str] = []
    for word in [w for w in norm_spaces(text).split(" ") if w]:
        ipa = epi.transliterate(word, normpunc=True)
        i = 0
        local: list[str] = []
        while i < len(ipa):
            if ipa[i].isspace() or ipa[i] in ",.!?؛،:;()[]{}'\"":
                i += 1
                continue
            matched = False
            for seq in MULTI_IPA:
                if ipa.startswith(seq, i):
                    mapped = IPA_MAP.get(seq)
                    if mapped:
                        local.append(mapped)
                    i += len(seq)
                    matched = True
                    break
            if matched:
                continue
            ch = ipa[i]
            if ch == "ː":
                if local:
                    prev = local[-1]
                    if prev in {"a", "i", "u", "e", "o"}:
                        local[-1] = prev + prev
                    elif prev and prev not in {"<", "|", ":"}:
                        local.append(prev)
                i += 1
                continue
            mapped = IPA_MAP.get(ch)
            if mapped:
                local.append(mapped)
            i += 1
        local = [x for x in local if x in VALID_MODEL_TOKENS]
        if local:
            if tokens:
                tokens.append("|")
            tokens.extend(local)
    return tokens


def load_stage1_manifest(stage1: Path) -> list[dict[str, str]]:
    manifest = stage1 / "raw" / "segment_manifest.csv"
    if not manifest.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest}")
    with manifest.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def token_vocabulary(processor) -> dict[str, int]:
    return {str(k): int(v) for k, v in processor.tokenizer.get_vocab().items()}


def ctc_forced_align(log_probs: torch.Tensor, target_ids: list[int], blank_id: int) -> list[tuple[int, int]]:
    if not target_ids:
        raise ValueError("Empty target sequence")
    t_steps, _ = log_probs.shape
    ext = [blank_id]
    for tok in target_ids:
        ext.extend([tok, blank_id])
    s_states = len(ext)
    neg_inf = -1e30
    dp = np.full((t_steps, s_states), neg_inf, dtype=np.float32)
    back = np.full((t_steps, s_states), -1, dtype=np.int16)
    dp[0, 0] = float(log_probs[0, blank_id].item())
    dp[0, 1] = float(log_probs[0, target_ids[0]].item())
    for t in range(1, t_steps):
        frame = log_probs[t]
        for s in range(s_states):
            best_prev = s
            best = dp[t - 1, s]
            if s - 1 >= 0 and dp[t - 1, s - 1] > best:
                best = dp[t - 1, s - 1]
                best_prev = s - 1
            if s - 2 >= 0 and ext[s] != blank_id and ext[s] != ext[s - 2] and dp[t - 1, s - 2] > best:
                best = dp[t - 1, s - 2]
                best_prev = s - 2
            dp[t, s] = best + float(frame[ext[s]].item())
            back[t, s] = best_prev
    end_state = max((s_states - 1, s_states - 2), key=lambda s: dp[-1, s])
    states = [end_state]
    s = end_state
    for t in range(t_steps - 1, 0, -1):
        s = int(back[t, s])
        if s < 0:
            raise RuntimeError("CTC backtrace failed")
        states.append(s)
    states.reverse()
    return [(state // 2, t) for t, state in enumerate(states) if ext[state] != blank_id]


def fit_token_sequence_to_frames(pairs: list[tuple[int, int]], token_count: int, hop_s: float, audio_duration: float) -> list[dict[str, float | int | bool]]:
    buckets: list[list[int]] = [[] for _ in range(token_count)]
    for idx, frame in pairs:
        if 0 <= idx < token_count:
            buckets[idx].append(frame)
    result = []
    previous_end = 0.0
    for idx, frames in enumerate(buckets):
        if not frames:
            result.append({"target_index": idx, "start": previous_end, "end": previous_end, "duration": 0.0, "aligned": False})
            continue
        start = max(previous_end, frames[0] * hop_s)
        end = min(audio_duration, (frames[-1] + 1) * hop_s)
        if end < start:
            end = start
        previous_end = end
        result.append({"target_index": idx, "start": float(start), "end": float(end), "duration": float(end - start), "aligned": True})
    return result


def build(stage1: Path, stage2: Path, output: Path) -> dict:
    from epitran import Epitran
    rows = load_stage1_manifest(stage1)
    output.mkdir(parents=True, exist_ok=True)
    phones_dir = output / "phones"
    phones_dir.mkdir(exist_ok=True)
    f0_dir = output / "f0"
    f0_dir.mkdir(exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForCTC.from_pretrained(MODEL_ID, dtype=dtype)
    model.to(device)
    model.eval()
    vocab = token_vocabulary(processor)
    blank_id = vocab.get(BLANK_TOKEN, int(getattr(model.config, "pad_token_id", 0)))
    epi = Epitran("ara-Arab")
    final_rows, diagnostics = [], []
    hop_s = 0.02
    for row in rows:
        name = row["name"]
        wav = stage1 / "raw" / "wavs" / f"{name}.wav"
        if not wav.exists():
            diagnostics.append({"name": name, "status": "MISSING_WAV"})
            continue
        text = norm_spaces(row.get("words", ""))
        target = epitran_to_model_tokens(text, epi)
        missing = [p for p in target if p != "|" and p not in vocab]
        if missing:
            diagnostics.append({"name": name, "status": "UNSUPPORTED_PHONEMES", "missing": sorted(set(missing))})
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
        except Exception as exc:
            diagnostics.append({"name": name, "status": "ALIGNMENT_FAILED", "error": str(exc)})
            continue
        aligned = fit_token_sequence_to_frames(pairs, len(target), hop_s, duration)
        coverage = sum(1 for x in aligned if x["aligned"]) / max(1, len(aligned))
        if coverage < 0.80:
            diagnostics.append({"name": name, "status": "LOW_COVERAGE", "coverage": coverage})
            continue
        f0, _, _ = librosa.pyin(audio, fmin=70.0, fmax=1200.0, sr=sr, frame_length=2048, hop_length=320)
        f0_path = f0_dir / f"{name}.npy"
        np.save(f0_path, np.nan_to_num(f0, nan=0.0).astype(np.float32))
        phone_path = phones_dir / f"{name}.json"
        phone_path.write_text(json.dumps({"name": name, "text": text, "phonemes": target, "alignment": aligned, "coverage": coverage, "f0": str(f0_path.relative_to(output))}, ensure_ascii=False, indent=2), encoding="utf-8")
        ph_durs = [max(0.001, float(x["duration"])) for x in aligned]
        final_rows.append({"name": name, "ph_seq": " ".join(target), "ph_dur": " ".join(f"{d:.4f}" for d in ph_durs)})
        diagnostics.append({"name": name, "status": "ALIGNED", "coverage": coverage, "phone_count": len(target)})
    csv_path = output / "transcriptions.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "ph_seq", "ph_dur"])
        writer.writeheader(); writer.writerows(final_rows)
    aligned_count = sum(1 for d in diagnostics if d["status"] == "ALIGNED")
    status = "STAGE3_ALIGNED" if aligned_count == len(rows) and aligned_count > 0 else "STAGE3_PARTIAL"
    report = {"schema_version": "0.2", "status": status, "model": MODEL_ID, "device": device, "source_stage1": str(stage1), "source_stage2": str(stage2), "segment_count": len(rows), "aligned_count": aligned_count, "phone_csv": str(csv_path), "diagnostics": diagnostics, "training_allowed": False, "next_gate": "DIFFSINGER_PHONESET_VALIDATION_AND_DATASET_BUILD", "note": "Arabic phoneme CTC forced alignment; token mapping follows the published model vocabulary."}
    (output / "dataset_stage3.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "segment_count", "aligned_count", "training_allowed", "next_gate")}, ensure_ascii=False, indent=2))
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage1", required=True)
    parser.add_argument("--stage2", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build(Path(args.stage1), Path(args.stage2), Path(args.output))