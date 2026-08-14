import librosa
import numpy as np


class PyinQuarterToneDistribution:

    VERSION = "1.0.0"

    NOTE_NAMES = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    ]

    def analyze(
        self,
        file_path,
        threshold=35,
    ):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        frequencies, _, _ = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz(
                "C2"
            ),
            fmax=librosa.note_to_hz(
                "C7"
            ),
        )

        frequencies = frequencies[
            ~np.isnan(
                frequencies
            )
        ]

        detected = []

        for frequency in frequencies:

            midi = librosa.hz_to_midi(
                frequency
            )

            nearest = round(
                midi
            )

            cents = (
                midi - nearest
            ) * 100

            if abs(cents) < threshold:

                continue

            note = self.NOTE_NAMES[
                nearest % 12
            ]

            if cents > 0:

                label = (
                    f"{note}(+50)"
                )

            else:

                label = (
                    f"{note}(-50)"
                )

            detected.append(
                label
            )

        total = len(
            detected
        )

        distribution = {}

        for label in sorted(
            set(detected)
        ):

            count = detected.count(
                label
            )

            distribution[
                label
            ] = round(
                (
                    count
                    / total
                )
                * 100,
                2,
            )

        return distribution