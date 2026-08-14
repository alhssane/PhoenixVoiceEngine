from pathlib import Path

import librosa
import numpy as np


class RealSegmentQuarterToneAnalyzer:

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

            audio, sample_rate = librosa.load(
                str(file_path),
                sr=None,
                mono=True,
            )

            pitches, magnitudes = librosa.piptrack(
                y=audio,
                sr=sample_rate,
            )

            quarter_tones = 0

            total_pitches = 0

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

                total_pitches += 1

                midi = librosa.hz_to_midi(
                    frequency
                )

                cents = (
                    midi
                    - round(midi)
                ) * 100

                if (
                    35
                    <= abs(cents)
                    <= 65
                ):

                    quarter_tones += 1

            percentage = 0

            if total_pitches:

                percentage = round(
                    (
                        quarter_tones
                        / total_pitches
                    )
                    * 100,
                    2,
                )

            results.append(
                {
                    "file": file_path.name,
                    "quarter_tones": quarter_tones,
                    "samples": total_pitches,
                    "percentage": percentage,
                }
            )

        return results