import json
from pathlib import Path

import librosa
import numpy as np


class VocalDatasetBuilder:

    VERSION = "1.0.0"

    def analyze(
        self,
        audio_file,
    ):

        audio, sample_rate = librosa.load(
            audio_file,
            sr=None,
            mono=True,
        )

        duration = len(audio) / sample_rate

        rms = librosa.feature.rms(
            y=audio
        )[0]

        zcr = librosa.feature.zero_crossing_rate(
            audio
        )[0]

        spectral_centroid = librosa.feature.spectral_centroid(
            y=audio,
            sr=sample_rate,
        )[0]

        dataset = {
            "duration": round(
                duration,
                2,
            ),
            "sample_rate": sample_rate,
            "samples": len(audio),
            "mean_energy": round(
                float(
                    np.mean(rms)
                ),
                6,
            ),
            "mean_zero_crossing_rate": round(
                float(
                    np.mean(zcr)
                ),
                6,
            ),
            "mean_spectral_centroid": round(
                float(
                    np.mean(
                        spectral_centroid
                    )
                ),
                2,
            ),
        }

        output = Path(
            r"D:\PhoenixVoiceEngine\workspace\trained_artists\fareed_dataset.json"
        )

        with open(
            output,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                dataset,
                file,
                ensure_ascii=False,
                indent=4,
            )

        return dataset