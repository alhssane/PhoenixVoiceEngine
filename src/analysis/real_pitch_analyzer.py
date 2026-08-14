import librosa
import numpy as np


class RealPitchAnalyzer:

    VERSION = "1.0.0"

    def analyze(self, file_path):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        pitches, magnitudes = librosa.piptrack(
            y=audio,
            sr=sample_rate,
        )

        detected_pitches = []

        for frame in range(
            pitches.shape[1]
        ):

            index = magnitudes[
                :,
                frame
            ].argmax()

            pitch = pitches[
                index,
                frame
            ]

            if pitch > 0:

                detected_pitches.append(
                    float(pitch)
                )

        if not detected_pitches:

            return {
                "status": "NO_PITCH",
            }

        detected_pitches = np.array(
            detected_pitches
        )

        return {
            "status": "SUCCESS",
            "minimum_pitch_hz": round(
                float(
                    np.min(
                        detected_pitches
                    )
                ),
                2,
            ),
            "maximum_pitch_hz": round(
                float(
                    np.max(
                        detected_pitches
                    )
                ),
                2,
            ),
            "average_pitch_hz": round(
                float(
                    np.mean(
                        detected_pitches
                    )
                ),
                2,
            ),
            "pitch_samples": len(
                detected_pitches
            ),
        }