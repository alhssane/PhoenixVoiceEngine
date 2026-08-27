from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import librosa
import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
HOP_LENGTH = 512


def midi_to_name(midi: float) -> str:
    n = int(round(float(midi)))
    n = max(24, min(96, n))
    return f"{NOTE_NAMES[n % 12]}{n // 12 - 1}"


def f0_to_midi(f0: np.ndarray) -> np.ndarray:
    return 69.0 + 12.0 * np.log2(np.maximum(f0, 1e-6) / 440.0)


def load_training_f0(
    wav: np.ndarray,
    sr: int,
    config: Path,
    diffsinger_root: Path,
) -> tuple[np.ndarray, int]:
    root = diffsinger_root.resolve()
    config = config.resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    if not config.is_file():
        raise FileNotFoundError(config)

    # Do not depend on the caller's current working directory.
    os.environ["PYTHONPATH"] = str(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    sys.argv = [sys.argv[0], "--config", str(config)]

    from utils.hparams import set_hparams, hparams
    from utils.binarizer_utils import get_mel_torch, get_pitch_parselmouth

    set_hparams(print_hparams=False)
    mel = get_mel_torch(
        wav,
        sr,
        num_mel_bins=int(hparams["audio_num_mel_bins"]),
        hop_size=int(hparams["hop_size"]),
        win_size=int(hparams["win_size"]),
        fft_size=int(hparams["fft_size"]),
        fmin=float(hparams["fmin"]),
        fmax=float(hparams["fmax"]),
        device="cpu",
    )
    f0, _ = get_pitch_parselmouth(
        wav,
        samplerate=sr,
        length=len(mel),
        hop_size=int(hparams["hop_size"]),
        f0_min=float(hparams.get("f0_min", 40.0)),
        f0_max=float(hparams.get("f0_max", 1100.0)),
    )
    return np.asarray(f0, dtype=np.float32), int(len(mel))


def note_for_interval(f0: np.ndarray, sr: int, start: float, dur: float) -> str:
    i0 = max(0, int(round(start * sr / HOP_LENGTH)))
    i1 = min(len(f0), int(round((start + dur) * sr / HOP_LENGTH)) + 1)
    vals = f0[i0:i1]
    vals = vals[vals > 0]
    if vals.size < 2:
        return "rest"
    return midi_to_name(float(np.median(f0_to_midi(vals))))


def build_groups(ph_seq: list[str], ph_dur: list[float], notes: list[str]):
    groups = []
    for phone, dur, note in zip(ph_seq, ph_dur, notes):
        if not groups or groups[-1]["note"] != note:
            groups.append({"note": note, "ph_num": 1, "duration": float(dur)})
        else:
            groups[-1]["ph_num"] += 1
            groups[-1]["duration"] += float(dur)
    return groups


def main() -> int:
    ap = argparse.ArgumentParser(description="Phoenix Stage10 V4: exact training F0 backend")
    ap.add_argument("--diffsinger", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    diffsinger = Path(args.diffsinger).resolve()
    raw = Path(args.raw).resolve()
    config = Path(args.config).resolve()
    out = Path(args.out).resolve()
    csv_path = raw / "transcriptions.csv"
    wav_dir = raw / "wavs"
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)
    if not config.exists():
        raise FileNotFoundError(config)

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

    f0, mel_len = load_training_f0(y, sr, config, diffsinger)
    notes_per_phone = []
    t = 0.0
    for phone, dur in zip(ph_seq, ph_dur):
        note = "rest" if phone in {"SP", "AP"} else note_for_interval(f0, sr, t, dur)
        notes_per_phone.append(note)
        t += dur

    groups = build_groups(ph_seq, ph_dur, notes_per_phone)
    note_seq = [g["note"] for g in groups]
    note_dur = [g["duration"] for g in groups]
    ph_num = [g["ph_num"] for g in groups]

    if sum(ph_num) != len(ph_seq):
        raise RuntimeError("ph_num coverage invariant failed")
    if abs(sum(note_dur) - sum(ph_dur)) > 0.01:
        raise RuntimeError("note duration coverage invariant failed")
    if len(f0) != mel_len:
        raise RuntimeError(f"F0/Mel length mismatch: f0={len(f0)}, mel={mel_len}")

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
        "f0_backend": "parselmouth_exact_training_backend",
    }]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "STAGE10_V4_EXACT_F0_DS_READY",
        "source": name,
        "phones": len(ph_seq),
        "notes": len(note_seq),
        "compression_ratio": round(len(ph_seq) / max(1, len(note_seq)), 3),
        "f0_values": len(f0),
        "voiced_frames": int(np.count_nonzero(f0 > 0)),
        "mel_frames": mel_len,
        "f0_backend": "parselmouth_exact_training_backend",
        "ds_file": str(out),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
