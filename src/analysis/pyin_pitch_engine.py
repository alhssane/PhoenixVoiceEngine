import librosa
import numpy as np


class PyinPitchEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        file_path,
    ):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        frequencies, voiced_flag, voiced_probability = (
            librosa.pyin(
                audio,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
            )
        )

        frequencies = frequencies[
            ~np.isnan(
                frequencies
            )
        ]

        return {
            "status": "SUCCESS",
            "minimum_hz": round(
                float(
                    np.min(
                        frequencies
                    )
                ),
                2,
            ),
            "maximum_hz": round(
                float(
                    np.max(
                        frequencies
                    )
                ),
                2,
            ),
            "average_hz": round(
                float(
                    np.mean(
                        frequencies
                    )
                ),
                2,
            ),
            "samples": len(
                frequencies
            ),
        }