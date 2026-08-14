import librosa
import numpy as np
import math


class QuarterToneMapEngine:

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

    def hz_to_midi(
        self,
        frequency,
    ):

        return (
            69
            + 12
            * math.log2(
                frequency
                / 440.0
            )
        )

    def cents_offset(
        self,
        frequency,
    ):

        midi = self.hz_to_midi(
            frequency
        )

        nearest = round(
            midi
        )

        return (
            midi
            - nearest
        ) * 100

    def analyze(
        self,
        file_path,
    ):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        frequencies = librosa.yin(
            audio,
            fmin=80,
            fmax=1000,
            sr=sample_rate,
        )

        frequencies = frequencies[
            np.isfinite(
                frequencies
            )
        ]

        frequencies = frequencies[
            frequencies > 0
        ]

        results = []

        for frequency in frequencies:

            midi = self.hz_to_midi(
                frequency
            )

            note_index = (
                round(
                    midi
                )
                % 12
            )

            note_name = (
                self.NOTE_NAMES[
                    note_index
                ]
            )

            cents = round(
                self.cents_offset(
                    frequency
                ),
                2,
            )

            if abs(
                cents
            ) >= 40:

                results.append(
                    {
                        "note": note_name,
                        "frequency": round(
                            frequency,
                            2,
                        ),
                        "cents": cents,
                    }
                )

        return results