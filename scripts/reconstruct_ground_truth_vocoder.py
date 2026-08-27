import argparse
import os
import pathlib
import sys

import librosa
import torch


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconstruct a real training WAV through DiffSinger's exact mel/F0/vocoder path."
    )
    parser.add_argument("--diffsinger", required=True, type=pathlib.Path)
    parser.add_argument("--config", required=True, type=pathlib.Path)
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()

    root = args.diffsinger.resolve()
    config = args.config.resolve()
    input_wav = args.input.resolve()
    output_wav = args.output.resolve()

    for path in (root, config, input_wav):
        if not path.exists():
            raise FileNotFoundError(path)

    os.environ["PYTHONPATH"] = str(root)
    sys.path.insert(0, str(root))
    sys.argv = [sys.argv[0], "--config", str(config)]

    from utils.hparams import set_hparams, hparams

    set_hparams(print_hparams=False)

    from modules.vocoders.nsf_hifigan import NsfHifiGAN
    from utils.binarizer_utils import get_mel_torch, get_pitch_parselmouth
    from utils.infer_utils import save_wav

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sample_rate = int(hparams["audio_sample_rate"])

    wav, _ = librosa.load(str(input_wav), sr=sample_rate, mono=True)
    if wav.size == 0:
        raise RuntimeError(f"Empty waveform: {input_wav}")

    mel = get_mel_torch(
        wav,
        sample_rate,
        num_mel_bins=int(hparams["audio_num_mel_bins"]),
        hop_size=int(hparams["hop_size"]),
        win_size=int(hparams["win_size"]),
        fft_size=int(hparams["fft_size"]),
        fmin=float(hparams["fmin"]),
        fmax=float(hparams["fmax"]),
        device=device,
    )

    f0, _ = get_pitch_parselmouth(
        wav,
        samplerate=sample_rate,
        length=len(mel),
        hop_size=int(hparams["hop_size"]),
        f0_min=float(hparams.get("f0_min", 40.0)),
        f0_max=float(hparams.get("f0_max", 1100.0)),
    )

    vocoder = NsfHifiGAN()
    reconstructed = vocoder.spec2wav(mel, f0=f0)

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    save_wav(reconstructed, output_wav, sample_rate)

    print("GROUND_TRUTH_VOCODER_RECONSTRUCTION_OK")
    print(f"INPUT={input_wav}")
    print(f"OUTPUT={output_wav}")
    print(f"SAMPLE_RATE={sample_rate}")
    print(f"MEL_FRAMES={len(mel)}")
    print(f"MEL_BINS={mel.shape[-1]}")
    print(f"F0_FRAMES={len(f0)}")
    print(f"DEVICE={device}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
