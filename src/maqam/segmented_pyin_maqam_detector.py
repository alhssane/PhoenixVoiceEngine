import os
import tempfile

import librosa
import soundfile as sf

from src.maqam.pyin_maqam_detector_v2 import (
    PyinMaqamDetector,
)


class SegmentedPyinMaqamDetector:

    VERSION = "3.0.0"

    def analyze(
        self,
        file_path,
        segment_seconds=5,
    ):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        duration = librosa.get_duration(
            y=audio,
            sr=sample_rate,
        )

        detector = PyinMaqamDetector()

        timeline = []

        start = 0

        while start < duration:

            end = min(
                start + segment_seconds,
                duration,
            )

            start_sample = int(
                start * sample_rate
            )

            end_sample = int(
                end * sample_rate
            )

            segment = audio[
                start_sample:end_sample
            ]

            temp_path = os.path.join(
                tempfile.gettempdir(),
                f"segment_{int(start)}.wav",
            )

            sf.write(
                temp_path,
                segment,
                sample_rate,
            )

            results = detector.analyze(
                temp_path
            )

            try:

                os.remove(
                    temp_path
                )

            except PermissionError:

                pass

            maqam = max(
                results,
                key=results.get,
            )

            confidence = results[
                maqam
            ]

            timeline.append(
                {
                    "start": round(
                        start,
                        2,
                    ),
                    "end": round(
                        end,
                        2,
                    ),
                    "maqam": maqam,
                    "confidence": confidence,
                }
            )

            start += segment_seconds

        return timeline