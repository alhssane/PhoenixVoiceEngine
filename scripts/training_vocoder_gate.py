from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

import librosa
import numpy as np
import torch


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Project-wide Phoenix ground-truth vocoder validation gate."
    )
    ap.add_argument("--diffsinger", required=True, type=pathlib.Path)
    ap.add_argument("--config", required=True, type=pathlib.Path)
    ap.add_argument("--input-wav", required=True, type=pathlib.Path)
    ap.add_argument("--output-wav", required=True, type=pathlib.Path)
    ap.add_argument("--report", required=True, type=pathlib.Path)
    args = ap.parse_args()

    root = args.diffsinger.resolve()
    config = args.config.resolve()
    input_wav = args.input_wav.resolve()
    output_wav = args.output_wav.resolve()
    report_path = args.report.resolve()

    required = (root, config, input_wav)
    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)

    os.environ["PYTHONPATH"] = str(root)
    sys.path.insert(0, str(root))
    sys.argv = [sys.argv[0], "--config", str(config)]

    from utils.hparams import hparams, set_hparams

    set_hparams(print_hparams=False)

    from modules.vocoders.nsf_hifigan import NsfHifiGAN
    from utils.binarizer_utils import get_mel_torch, get_pitch_parselmouth
    from utils.infer_utils import save_wav

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sample_rate = int(hparams["audio_sample_rate"])
    mel_bins = int(hparams["audio_num_mel_bins"])
    hop_size = int(hparams["hop_size"])
    win_size = int(hparams["win_size"])
    fft_size = int(hparams["fft_size"])

    wav, actual_sr = librosa.load(str(input_wav), sr=sample_rate, mono=True)
    if wav.size == 0:
        raise RuntimeError(f"Empty waveform: {input_wav}")

    mel = get_mel_torch(
        wav,
        sample_rate,
        num_mel_bins=mel_bins,
        hop_size=hop_size,
        win_size=win_size,
        fft_size=fft_size,
        fmin=float(hparams["fmin"]),
        fmax=float(hparams["fmax"]),
        device=device,
    )

    f0, _ = get_pitch_parselmouth(
        wav,
        samplerate=sample_rate,
        length=len(mel),
        hop_size=hop_size,
        f0_min=float(hparams.get("f0_min", 40.0)),
        f0_max=float(hparams.get("f0_max", 1100.0)),
    )

    vocoder = NsfHifiGAN()
    reconstructed = vocoder.spec2wav(mel, f0=f0)
    reconstructed = np.asarray(reconstructed, dtype=np.float32).reshape(-1)

    if reconstructed.size == 0:
        raise RuntimeError("Vocoder produced an empty waveform.")
    if not np.isfinite(reconstructed).all():
        raise RuntimeError("Vocoder produced non-finite audio samples.")
    if not torch.isfinite(mel).all():
        raise RuntimeError("Ground-truth Mel contains non-finite values.")
    if not np.isfinite(np.asarray(f0)).all():
        raise RuntimeError("Ground-truth F0 contains non-finite values.")

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    save_wav(reconstructed, output_wav, sample_rate)

    result = {
        "status": "TRAINING_VOCODER_GATE_PASSED",
        "gate": "GROUND_TRUTH_MEL_F0_VOCODER_RECONSTRUCTION",
        "input_wav": str(input_wav),
        "output_wav": str(output_wav),
        "config": str(config),
        "vocoder_checkpoint": hparams.get("vocoder_ckpt"),
        "sample_rate": sample_rate,
        "input_source_sample_rate": int(actual_sr),
        "mel_frames": int(len(mel)),
        "mel_bins": mel_bins,
        "hop_size": hop_size,
        "f0_frames": int(len(f0)),
        "device": str(device),
        "reconstructed_duration_sec": round(reconstructed.size / sample_rate, 6),
        "training_allowed": True,
        "note": "This gate validates the feature/vocoder path only; it does not certify acoustic-model quality.",
    }
    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
