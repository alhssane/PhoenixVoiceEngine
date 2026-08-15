import json
from pathlib import Path

import librosa
import numpy as np


class SingingStyleTrainerV2:

    VERSION = "2.0.0"

    def analyze(
        self,
        audio_file,
    ):

        audio, sample_rate = librosa.load(
            audio_file,
            sr=None,
            mono=True,
        )

        f0, _, _ = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
        )

        pitches = f0[
            ~np.isnan(f0)
        ]

        rms = librosa.feature.rms(
            y=audio
        )[0]

        result = {

            "average_pitch": round(
                float(
                    np.mean(
                        pitches
                    )
                ),
                2,
            ),

            "pitch_std": round(
                float(
                    np.std(
                        pitches
                    )
                ),
                2,
            ),

            "minimum_pitch": round(
                float(
                    np.min(
                        pitches
                    )
                ),
                2,
            ),

            "maximum_pitch": round(
                float(
                    np.max(
                        pitches
                    )
                ),
                2,
            ),

            "average_energy": round(
                float(
                    np.mean(
                        rms
                    )
                ),
                6,
            ),

            "vibrato_strength": round(
                float(
                    np.std(
                        pitches
                    )
                    /
                    np.mean(
                        pitches
                    )
                ),
                4,
            ),

            "style_status": "LEARNED",
        }

        output = Path(
            r"D:\PhoenixVoiceEngine\workspace\trained_artists\fareed_singing_style_v2.json"
        )

        with open(
            output,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=4,
            )

        return result