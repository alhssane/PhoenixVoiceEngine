from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import Any

import librosa
import numpy as np
import torch


def squeeze_mel(x: torch.Tensor | np.ndarray) -> np.ndarray:
    if torch.is_tensor(x):
        x = x.detach().cpu().numpy()
    x = np.asarray(x, dtype=np.float32)
    while x.ndim > 2 and x.shape[0] == 1:
        x = x[0]
    if x.ndim != 2:
        raise ValueError(f"Expected 2-D mel after squeeze, got shape={x.shape}")
    # DiffSinger convention is [frames, mel_bins].
    if x.shape[0] in (80, 100, 128) and x.shape[1] > x.shape[0]:
        x = x.T
    return x


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    aa = a.reshape(-1).astype(np.float64)
    bb = b.reshape(-1).astype(np.float64)
    if aa.size < 2 or np.std(aa) == 0 or np.std(bb) == 0:
        return 0.0
    return float(np.corrcoef(aa, bb)[0, 1])


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare DiffSinger predicted MEL with ground-truth MEL from the same source WAV.")
    ap.add_argument("--diffsinger", required=True, type=pathlib.Path)
    ap.add_argument("--config", required=True, type=pathlib.Path)
    ap.add_argument("--source-wav", required=True, type=pathlib.Path)
    ap.add_argument("--pred-mel", required=True, type=pathlib.Path)
    ap.add_argument("--output", required=True, type=pathlib.Path)
    args = ap.parse_args()

    root = args.diffsinger.resolve()
    config = args.config.resolve()
    source = args.source_wav.resolve()
    pred_path = args.pred_mel.resolve()
    for p in (root, config, source, pred_path):
        if not p.exists():
            raise FileNotFoundError(p)

    os.environ["PYTHONPATH"] = str(root)
    sys.path.insert(0, str(root))
    sys.argv = [sys.argv[0], "--config", str(config)]

    from utils.hparams import set_hparams, hparams
    from utils.binarizer_utils import get_mel_torch
    set_hparams(print_hparams=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sr = int(hparams["audio_sample_rate"])
    y, loaded_sr = librosa.load(str(source), sr=sr, mono=True)
    if loaded_sr != sr:
        raise RuntimeError(f"Unexpected sample rate after load: {loaded_sr}")

    gt = get_mel_torch(
        y, sr,
        num_mel_bins=int(hparams["audio_num_mel_bins"]),
        hop_size=int(hparams["hop_size"]),
        win_size=int(hparams["win_size"]),
        fft_size=int(hparams["fft_size"]),
        fmin=float(hparams["fmin"]),
        fmax=float(hparams["fmax"]),
        device=device,
    )
    gt = squeeze_mel(gt)

    payload: Any = torch.load(pred_path, map_location="cpu", weights_only=False)
    if not isinstance(payload, list) or not payload:
        raise RuntimeError(f"Unsupported predicted MEL container: {type(payload).__name__}")
    pred = squeeze_mel(payload[0]["mel"])

    t = min(len(gt), len(pred))
    bins = min(gt.shape[1], pred.shape[1])
    gt = gt[:t, :bins]
    pred = pred[:t, :bins]

    diff = pred - gt
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff * diff)))
    corr = pearson(gt, pred)
    frame_energy_gt = np.mean(gt, axis=1)
    frame_energy_pred = np.mean(pred, axis=1)
    energy_corr = pearson(frame_energy_gt, frame_energy_pred)

    report = {
        "status": "ACOUSTIC_MEL_COMPARISON_COMPLETE",
        "source_wav": str(source),
        "predicted_mel": str(pred_path),
        "sample_rate": sr,
        "target_shape": [int(gt.shape[0]), int(gt.shape[1])],
        "predicted_shape": [int(pred.shape[0]), int(pred.shape[1])],
        "aligned_frames_compared": int(t),
        "mel_bins_compared": int(bins),
        "mae": mae,
        "rmse": rmse,
        "global_pearson": corr,
        "frame_energy_pearson": energy_corr,
        "ground_truth_range": [float(np.min(gt)), float(np.max(gt))],
        "predicted_range": [float(np.min(pred)), float(np.max(pred))],
        "device": str(device),
        "interpretation": {
            "high_correlation_low_error": "Acoustic model is reproducing the target spectral shape relatively well; inspect vocoder/input and fine-grained timing next.",
            "low_correlation_high_error": "Acoustic model is not reproducing the target spectrum; focus on acoustic training/conditioning/alignment rather than vocoder.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
