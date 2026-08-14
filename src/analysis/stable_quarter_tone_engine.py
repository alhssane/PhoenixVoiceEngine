import librosa
import numpy as np


class StableQuarterToneEngine:

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
        minimum_duration=0.30,
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

        hop_length = 512

        detected = []

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

            if (
                abs(cents) < 35
                or abs(cents) > 65
            ):

                continue

            note = self.NOTE_NAMES[
                nearest % 12
            ]

            time_position = (
                frame
                * hop_length
            ) / sample_rate

            detected.append(
                (
                    note,
                    time_position,
                    cents,
                )
            )

        grouped = {}

        for note, time_value, cents in detected:

            grouped.setdefault(
                note,
                []
            ).append(
                (
                    time_value,
                    cents,
                )
            )

        results = []

        for note, values in grouped.items():

            start = values[0][0]

            end = values[-1][0]

            duration = (
                end - start
            )

            if (
                duration
                < minimum_duration
            ):

                continue

            average_cents = np.mean(
                [
                    value[1]
                    for value in values
                ]
            )

            results.append(
                {
                    "note": note,
                    "occurrences": len(
                        values
                    ),
                    "duration": round(
                        duration,
                        2,
                    ),
                    "average_cents": round(
                        float(
                            average_cents
                        ),
                        2,
                    ),
                }
            )

        return results