from pathlib import Path

import librosa
import numpy as np


class ArtistPhonemeBank:

    VERSION = "1.0.0"

    def __init__(self):

        self.sample_rate = 22050

    def load_audio(self, audio_path):

        audio, sr = librosa.load(
            audio_path,
            sr=self.sample_rate,
            mono=True,
        )

        return audio, sr

    def detect_voice_regions(self, audio):

        intervals = librosa.effects.split(
            audio,
            top_db=25,
        )

        return intervals

    def build_bank(self, audio_path):

        audio, sr = self.load_audio(
            audio_path
        )

        intervals = self.detect_voice_regions(
            audio
        )

        phoneme_bank = []

        for index, interval in enumerate(intervals):

            start = interval[0]

            end = interval[1]

            duration = (
                end - start
            ) / sr

            phoneme_bank.append(
                {
                    "id": index + 1,
                    "start": round(
                        start / sr,
                        2,
                    ),
                    "end": round(
                        end / sr,
                        2,
                    ),
                    "duration": round(
                        duration,
                        2,
                    ),
                }
            )

        return phoneme_bank