import librosa
import numpy as np


class RealTonicAnalyzer:

    VERSION = "1.0.0"

    def analyze(self, file_path):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        f0 = librosa.yin(
            audio,
            fmin=80,
            fmax=1000,
            sr=sample_rate,
        )

        f0 = f0[
            np.isfinite(f0)
        ]

        f0 = f0[
            (f0 >= 80)
            & (f0 <= 1000)
        ]

        if len(f0) == 0:

            return {
                "status": "NO_TONIC",
            }

        tonic = float(
            np.median(f0)
        )

        return {
            "status": "SUCCESS",
            "tonic_hz": round(
                tonic,
                2,
            ),
            "minimum_hz": round(
                float(np.min(f0)),
                2,
            ),
            "maximum_hz": round(
                float(np.max(f0)),
                2,
            ),
            "average_hz": round(
                float(np.mean(f0)),
                2,
            ),
            "samples": len(f0),
        }