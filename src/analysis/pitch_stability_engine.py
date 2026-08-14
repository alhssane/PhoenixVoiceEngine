import librosa
import numpy as np


class PitchStabilityEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        file_path,
        window_size=50,
    ):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        pitches, magnitudes = librosa.piptrack(
            y=audio,
            sr=sample_rate,
        )

        values = []

        for frame in range(
            pitches.shape[1]
        ):

            index = np.argmax(
                magnitudes[:, frame]
            )

            frequency = pitches[
                index,
                frame,
            ]

            if frequency < 80:

                continue

            midi = librosa.hz_to_midi(
                frequency
            )

            nearest = round(
                midi
            )

            cents = (
                midi - nearest
            ) * 100

            values.append(
                float(cents)
            )

        results = []

        for index in range(
            0,
            len(values),
            window_size,
        ):

            window = values[
                index:index
                + window_size
            ]

            if len(window) < 5:

                continue

            average = np.mean(
                window
            )

            deviation = np.std(
                window
            )

            if deviation < 10:

                status = (
                    "STABLE"
                )

            elif deviation < 25:

                status = (
                    "SEMI-STABLE"
                )

            else:

                status = (
                    "TRANSITION"
                )

            results.append(
                {
                    "average": round(
                        float(
                            average
                        ),
                        2,
                    ),
                    "deviation": round(
                        float(
                            deviation
                        ),
                        2,
                    ),
                    "status": status,
                }
            )

        return results