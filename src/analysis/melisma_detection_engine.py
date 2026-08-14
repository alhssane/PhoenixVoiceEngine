import librosa
import numpy as np


class MelismaDetectionEngine:

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
        min_notes=3,
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

        times = librosa.times_like(
            frequencies,
            sr=sample_rate,
        )

        frames = []

        for index, frequency in enumerate(
            frequencies
        ):

            if np.isnan(
                frequency
            ):

                continue

            midi = round(
                librosa.hz_to_midi(
                    frequency
                )
            )

            note = self.NOTE_NAMES[
                midi % 12
            ]

            frames.append(
                {
                    "time": float(
                        times[index]
                    ),
                    "note": note,
                }
            )

        melismas = []

        current = []

        for frame in frames:

            if not current:

                current.append(
                    frame
                )

                continue

            previous_note = current[
                -1
            ]["note"]

            current_note = frame[
                "note"
            ]

            if current_note != previous_note:

                current.append(
                    frame
                )

            else:

                if (
                    len(
                        current
                    )
                    >= min_notes
                ):

                    melismas.append(
                        current.copy()
                    )

                current = [
                    frame
                ]

        if (
            len(current)
            >= min_notes
        ):

            melismas.append(
                current
            )

        return melismas