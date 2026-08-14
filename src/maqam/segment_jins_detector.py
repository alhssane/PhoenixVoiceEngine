from pathlib import Path

import librosa
import numpy as np

from src.maqam.arabic_jins_engine import (
    ArabicJinsEngine,
)


class SegmentJinsDetector:

    VERSION = "1.0.0"

    def analyze(
        self,
        segments_directory,
    ):

        jins_engine = (
            ArabicJinsEngine()
        )

        jins_database = (
            jins_engine.get_ajnas()
        )

        results = []

        directory = Path(
            segments_directory
        )

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

            if not detected:

                continue

            average_pitch = (
                sum(detected)
                / len(detected)
            )

            best_match = (
                "unknown"
            )

            best_distance = (
                float("inf")
            )

            for jins_name, jins_data in (
                jins_database.items()
            ):

                expected = (
                    len(
                        jins_data[
                            "intervals"
                        ]
                    )
                    * 150
                )

                distance = abs(
                    average_pitch
                    - expected
                )

                if (
                    distance
                    < best_distance
                ):

                    best_distance = (
                        distance
                    )

                    best_match = (
                        jins_name
                    )

            results.append(
                {
                    "segment": (
                        file_path.name
                    ),
                    "jins": (
                        best_match
                    ),
                    "average_pitch": round(
                        average_pitch,
                        2,
                    ),
                }
            )

        return results