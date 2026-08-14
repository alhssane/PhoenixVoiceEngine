import librosa
import numpy as np


class SyllableDetectionEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        file_path,
    ):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        onset_frames = librosa.onset.onset_detect(
            y=audio,
            sr=sample_rate,
            units="time",
        )

        duration = librosa.get_duration(
            y=audio,
            sr=sample_rate,
        )

        syllables = []

        if len(onset_frames) == 0:

            return syllables

        for index, start in enumerate(
            onset_frames
        ):

            if index + 1 < len(
                onset_frames
            ):

                end = onset_frames[
                    index + 1
                ]

            else:

                end = duration

            syllables.append(
                {
                    "start": round(
                        float(start),
                        2,
                    ),
                    "end": round(
                        float(end),
                        2,
                    ),
                    "duration": round(
                        float(end - start),
                        2,
                    ),
                }
            )

        return syllables