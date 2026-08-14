from pathlib import Path

import librosa
import numpy as np


class RealSegmentPitchAnalyzer:

    VERSION = "1.0.0"

    def analyze(
        self,
        segments_directory,
    ):

        directory = Path(
            segments_directory
        )

        results = []

        for file_path in sorted(
            directory.glob(
                "*.wav"
            )
        ):

            audio, sample_rate = (
                librosa.load(
                    str(file_path),
                    sr=None,
                    mono=True,
                )
            )

            pitches, magnitudes = (
                librosa.piptrack(
                    y=audio,
                    sr=sample_rate,
                )
            )

            detected = []

            for frame in range(
                pitches.shape[1]
            ):

                index = np.argmax(
                    magnitudes[:, frame]
                )

                pitch = pitches[
                    index,
                    frame,
                ]

                if pitch > 80:

                    detected.append(
                        float(pitch)
                    )

            if detected:

                average_pitch = round(
                    sum(detected)
                    / len(detected),
                    2,
                )

            else:

                average_pitch = 0

            results.append(
                {
                    "file": file_path.name,
                    "samples": len(
                        detected
                    ),
                    "average_pitch": (
                        average_pitch
                    ),
                }
            )

        return results