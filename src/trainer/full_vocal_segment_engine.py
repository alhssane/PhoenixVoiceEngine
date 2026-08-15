import json
import re
from pathlib import Path

import librosa
import soundfile as sf


class FullVocalSegmentEngine:

    VERSION = "2.0.0"

    def build(
        self,
        audio_path,
    ):

        audio, sample_rate = librosa.load(
            audio_path,
            sr=None,
            mono=True,
        )

        with open(
            r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_full_words.json",
            "r",
            encoding="utf-8",
        ) as file:

            words = json.load(
                file
            )

        output_dir = Path(
            r"D:\PhoenixVoiceEngine\workspace\full_vocal_segments"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        count = 0

        for index, item in enumerate(words):

            word = item["word"].strip()

            start = int(
                item["start"]
                * sample_rate
            )

            end = int(
                item["end"]
                * sample_rate
            )

            segment = audio[start:end]

            if len(segment) == 0:

                continue

            safe_name = re.sub(
                r'[\\/:*?"<>|]',
                "_",
                word,
            )

            output_file = (
                output_dir
                / f"{index:04d}_{safe_name}.wav"
            )

            sf.write(
                output_file,
                segment,
                sample_rate,
            )

            count += 1

        return {

            "segments": count,

            "output_directory": str(
                output_dir
            ),

        }