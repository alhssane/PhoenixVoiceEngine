import librosa
import numpy as np


class PyinNoteExtractor:

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

    def analyze(self, file_path):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        frequencies, _, _ = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
        )

        frequencies = frequencies[
            ~np.isnan(frequencies)
        ]

        notes = []

        for frequency in frequencies:

            midi = round(
                librosa.hz_to_midi(
                    frequency
                )
            )

            note = self.NOTE_NAMES[
                midi % 12
            ]

            notes.append(note)

        total = len(notes)

        distribution = {}

        for note in self.NOTE_NAMES:

            count = notes.count(note)

            if count == 0:

                continue

            distribution[note] = round(
                (count / total) * 100,
                2,
            )

        return distribution