from pathlib import Path
import json

import librosa
import numpy as np
import soundfile as sf


class SongReconstructionEngine:

    VERSION = "3.0.0"

    def generate(
        self,
        words,
    ):

        timeline_file = (
            r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_words.json"
        )

        with open(
            timeline_file,
            "r",
            encoding="utf-8",
        ) as file:

            timeline = json.load(
                file
            )

        duration = max(
            item["end"]
            for item in timeline
        )

        sample_rate = 44100

        output = np.zeros(
            int(
                duration
                * sample_rate
            )
        )

        database = Path(
            r"D:\PhoenixVoiceEngine\workspace\vocal_segments"
        )

        for index, word in enumerate(words):

            if index >= len(timeline):

                break

            candidates = list(
                database.glob(
                    f"*_{word}.wav"
                )
            )

            if not candidates:

                continue

            audio, sample_rate = sf.read(
                candidates[0]
            )

            if len(audio.shape) > 1:

                audio = np.mean(
                    audio,
                    axis=1,
                )

            start_sample = int(
                timeline[index]["start"]
                * sample_rate
            )

            end_sample = (
                start_sample
                + len(audio)
            )

            if end_sample > len(output):

                end_sample = len(
                    output
                )

                audio = audio[
                    : end_sample
                    - start_sample
                ]

            output[
                start_sample:end_sample
            ] = audio

        output_path = (
            r"D:\PhoenixVoiceEngine\outputs\reconstructed_song.wav"
        )

        sf.write(
            output_path,
            output,
            sample_rate,
        )

        return {

            "output": output_path,

            "duration": round(
                len(output)
                / sample_rate,
                2,
            ),

            "words": len(
                words
            ),

        }