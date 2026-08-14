from pathlib import Path

import librosa
import numpy as np


class RealNoteExtractionEngine:

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

        notes = []

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

            midi = int(
                round(
                    librosa.hz_to_midi(
                        frequency
                    )
                )
            )

            note = self.NOTE_NAMES[
                midi % 12
            ]

            notes.append(
                note
            )

        counts = {}

        for note in notes:

            counts[note] = (
                counts.get(
                    note,
                    0,
                )
                + 1
            )

        total = len(notes)

        distribution = {}

        for note, count in sorted(
            counts.items()
        ):

            distribution[note] = round(
                (
                    count
                    / total
                )
                * 100,
                2,
            )

        return distribution