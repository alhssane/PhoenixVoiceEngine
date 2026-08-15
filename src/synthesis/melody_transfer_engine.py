from pathlib import Path
import json

import librosa
import numpy as np


class MelodyTransferEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        audio_path,
        start_time,
        end_time,
    ):

        audio, sample_rate = librosa.load(
            audio_path,
            sr=None,
            mono=True,
        )

        start_sample = int(
            start_time
            * sample_rate
        )

        end_sample = int(
            end_time
            * sample_rate
        )

        segment = audio[
            start_sample:end_sample
        ]

        f0, voiced_flag, _ = librosa.pyin(
            segment,
            fmin=librosa.note_to_hz(
                "C2"
            ),
            fmax=librosa.note_to_hz(
                "C7"
            ),
        )

        pitches = []

        for value in f0:

            if np.isnan(value):

                continue

            pitches.append(
                round(
                    float(value),
                    2,
                )
            )

        return {
            "duration": round(
                len(segment)
                / sample_rate,
                3,
            ),
            "pitch_frames": len(
                pitches
            ),
            "pitch_curve": pitches,
            "status": (
                "MELODY_CAPTURED"
            ),
        }