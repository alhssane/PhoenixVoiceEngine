import json
from pathlib import Path

import librosa
import numpy as np


class VoiceEmbeddingEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        audio_path,
    ):

        audio, sample_rate = librosa.load(
            audio_path,
            sr=None,
            mono=True,
        )

        spectral_centroid = librosa.feature.spectral_centroid(
            y=audio,
            sr=sample_rate,
        )

        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=audio,
            sr=sample_rate,
        )

        zero_crossing_rate = librosa.feature.zero_crossing_rate(
            audio,
        )

        rms = librosa.feature.rms(
            y=audio,
        )

        profile = {
            "duration": round(
                len(audio) / sample_rate,
                2,
            ),
            "sample_rate": sample_rate,
            "timbre_centroid": round(
                float(
                    np.mean(
                        spectral_centroid
                    )
                ),
                2,
            ),
            "timbre_bandwidth": round(
                float(
                    np.mean(
                        spectral_bandwidth
                    )
                ),
                2,
            ),
            "energy": round(
                float(
                    np.mean(
                        rms
                    )
                ),
                4,
            ),
            "voice_activity": round(
                float(
                    np.mean(
                        zero_crossing_rate
                    )
                ),
                4,
            ),
        }

        return profile

    def save(
        self,
        profile,
        output_path,
    ):

        Path(
            output_path
        ).write_text(
            json.dumps(
                profile,
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )