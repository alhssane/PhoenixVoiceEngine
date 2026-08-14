import librosa
import numpy as np


class QuarterToneTimelineEngine:

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

        hop_length = 512

        timeline = []

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

            seconds = round(
                (
                    frame
                    * hop_length
                )
                / sample_rate,
                2,
            )

            note = self.NOTE_NAMES[
                nearest % 12
            ]

            timeline.append(
                {
                    "time": seconds,
                    "note": note,
                    "frequency": round(
                        float(
                            frequency
                        ),
                        2,
                    ),
                    "cents": round(
                        float(
                            cents
                        ),
                        2,
                    ),
                }
            )

        return timeline