import librosa
import numpy as np


class PitchDistributionEngine:

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

        if len(
            frequencies
        ) == 0:

            return {}

        midi_notes = librosa.hz_to_midi(
            frequencies
        )

        pitch_classes = (
            np.round(
                midi_notes
            ).astype(
                int
            )
            % 12
        )

        distribution = {}

        total = len(
            pitch_classes
        )

        for index, name in enumerate(
            self.NOTE_NAMES
        ):

            count = np.sum(
                pitch_classes
                == index
            )

            percentage = (
                count
                / total
            ) * 100

            distribution[
                name
            ] = round(
                percentage,
                2,
            )

        return distribution