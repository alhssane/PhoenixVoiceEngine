import json
import os

import librosa
import soundfile as sf


class MusicalPhraseEngine:

    VERSION = "1.0.0"

    def build(
        self,
        audio_path,
        words_json_path,
        output_directory,
        min_words=4,
        max_words=8,
        min_duration=3.0,
        max_duration=6.0,
    ):

        os.makedirs(
            output_directory,
            exist_ok=True,
        )

        with open(
            words_json_path,
            "r",
            encoding="utf-8",
        ) as file:

            words = json.load(
                file
            )

        audio, sample_rate = librosa.load(
            audio_path,
            sr=None,
            mono=True,
        )

        phrases = []

        index = 0
        phrase_id = 0

        while index < len(words):

            start_index = index

            phrase_words = []

            while index < len(words):

                phrase_words.append(
                    words[index]
                )

                duration = (
                    phrase_words[-1]["end"]
                    - phrase_words[0]["start"]
                )

                word_count = len(
                    phrase_words
                )

                index += 1

                if (
                    word_count >= min_words
                    and duration >= min_duration
                ):

                    break

                if (
                    word_count >= max_words
                    or duration >= max_duration
                ):

                    break

            phrase_start = (
                phrase_words[0]["start"]
            )

            phrase_end = (
                phrase_words[-1]["end"]
            )

            start_sample = int(
                phrase_start
                * sample_rate
            )

            end_sample = int(
                phrase_end
                * sample_rate
            )

            phrase_audio = audio[
                start_sample:end_sample
            ]

            filename = (
                f"{phrase_id:04d}.wav"
            )

            file_path = os.path.join(
                output_directory,
                filename,
            )

            sf.write(
                file_path,
                phrase_audio,
                sample_rate,
            )

            phrases.append(
                {
                    "phrase": phrase_id,
                    "start": round(
                        phrase_start,
                        2,
                    ),
                    "end": round(
                        phrase_end,
                        2,
                    ),
                    "duration": round(
                        phrase_end
                        - phrase_start,
                        2,
                    ),
                    "words": [
                        w["word"]
                        for w in phrase_words
                    ],
                    "text": " ".join(
                        w["word"]
                        for w in phrase_words
                    ),
                    "file": file_path,
                }
            )

            phrase_id += 1

        return phrases