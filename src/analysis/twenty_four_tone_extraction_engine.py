import librosa
import numpy as np


class TwentyFourToneExtractionEngine:

    VERSION = "1.0.0"

    NOTES = [
        "C",
        "C(+50)",
        "C#",
        "C#(+50)",
        "D",
        "D(+50)",
        "D#",
        "D#(+50)",
        "E",
        "E(+50)",
        "F",
        "F(+50)",
        "F#",
        "F#(+50)",
        "G",
        "G(+50)",
        "G#",
        "G#(+50)",
        "A",
        "A(+50)",
        "A#",
        "A#(+50)",
        "B",
        "B(+50)",
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

        detected_notes = []

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

            note_index = (
                nearest % 12
            )

            note_name = [
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
            ][note_index]

            if abs(cents) >= 35:

                note_name = (
                    f"{note_name}(+50)"
                )

            detected_notes.append(
                note_name
            )

        counts = {}

        for note in detected_notes:

            counts[note] = (
                counts.get(
                    note,
                    0,
                )
                + 1
            )

        total = len(
            detected_notes
        )

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