from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import librosa
import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
F0_MIN = 65.0
F0_MAX = 1100.0
HOP_LENGTH = 512


def midi_to_name(midi: float) -> str:
    n = int(round(float(midi)))
    n = max(24, min(96, n))
    return f"{NOTE_NAMES[n % 12]}{n // 12 - 1}"


def f0_to_midi(f0: np.ndarray) -> np.ndarray:
    return 69.0 + 12.0 * np.log2(np.maximum(f0, 1e-6) / 440.0)


def extract_f0(y: np.ndarray, sr: int) -> np.ndarray:
    f0, _, _ = librosa.pyin(
        y,
        fmin=F0_MIN,
        fmax=F0_MAX,
        sr=sr,
        frame_length=2048,
        hop_length=HOP_LENGTH,
    )
    f0 = np.asarray(f0, dtype=np.float32)
    return np.nan_to_num(f0, nan=0.0, posinf=0.0, neginf=0.0)


def note_for_interval(f0: np.ndarray, sr: int, start: float, dur: float) -> str:
    i0 = max(0, int(round(start * sr / HOP_LENGTH)))
    i1 = min(len(f0), int(round((start + dur) * sr / HOP_LENGTH)) + 1)
    values = f0[i0:i1]
    values = values[values > 0]
    if values.size < 2:
        return "rest"
    return midi_to_name(float(np.median(f0_to_midi(values))))


def build_note_groups(ph_seq: list[str], ph_dur: list[float], notes: list[str]):
    groups = []
    current = None
    for phone, dur, note in zip(ph_seq, ph_dur, notes):
        key = note
        if current is None or current["note"] != key:
            current = {"note": note, "ph_num": 1, "duration": float(dur)}
            groups.append(current)
        else:
            current["ph_num"] += 1
            current["duration"] += float(dur)
    return groups


def main() -> int:
    ap = argparse.ArgumentParser(description="Phoenix Stage10 V3 note-grouped DS preparation")
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    raw = Path(args.raw).resolve()
    out = Path(args.out).resolve()
    csv_path = raw / "transcriptions.csv"
    wav_dir = raw / "wavs"
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8-sig")))
    if not rows:
        raise RuntimeError("transcriptions.csv is empty")

    row = next((r for r in rows if "<" not in r.get("ph_seq", "").split()), rows[0])
    name = row["name"]
    ph_seq = row["ph_seq"].split()
    ph_dur = [float(x) for x in row["ph_dur"].split()]
    if len(ph_seq) != len(ph_dur):
        raise RuntimeError(f"{name}: ph_seq/ph_dur mismatch")

    wav = wav_dir / f"{name}.wav"
    if not wav.exists():
        raise FileNotFoundError(wav)

    y, sr = librosa.load(wav, sr=None, mono=True)
    f0 = extract_f0(y, sr)

    notes_per_phone = []
    t = 0.0
    for phone, dur in zip(ph_seq, ph_dur):
        note = "rest" if phone in {"SP", "AP"} else note_for_interval(f0, sr, t, dur)
        notes_per_phone.append(note)
        t += dur

    groups = build_note_groups(ph_seq, ph_dur, notes_per_phone)
    note_seq = [g["note"] for g in groups]
    note_dur = [g["duration"] for g in groups]
    ph_num = [g["ph_num"] for g in groups]

    if sum(ph_num) != len(ph_seq):
        raise RuntimeError("Internal V3 invariant failed: ph_num does not cover ph_seq")
    if abs(sum(note_dur) - sum(ph_dur)) > 0.01:
        raise RuntimeError("Internal V3 invariant failed: note durations do not cover phone durations")

    payload = [{
        "offset": 0.0,
        "text": name,
        "ph_seq": " ".join(ph_seq),
        "ph_dur": " ".join(f"{x:.6f}" for x in ph_dur),
        "ph_num": " ".join(str(x) for x in ph_num),
        "note_seq": " ".join(note_seq),
        "note_dur": " ".join(f"{x:.6f}" for x in note_dur),
        "note_slur": " ".join("0" for _ in note_seq),
        "f0_seq": " ".join(f"{float(x):.6f}" for x in f0),
        "f0_timestep": HOP_LENGTH / float(sr),
    }]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": "STAGE10_V3_DS_READY",
        "source": name,
        "phones": len(ph_seq),
        "notes": len(note_seq),
        "compression_ratio": round(len(ph_seq) / max(1, len(note_seq)), 3),
        "f0_values": len(f0),
        "voiced_frames": int(np.count_nonzero(f0 > 0)),
        "ds_file": str(out),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
