import json
import os

import librosa
import soundfile as sf


class BreathAwarePhraseEngine:

    VERSION = "2.0.0"

    def build(
        self,
        audio_path,
        words_json_path,
        output_directory,
        gap_threshold=0.5,
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

            words = json.load(file)

        audio, sample_rate = librosa.load(
            audio_path,
            sr=None,
            mono=True,
        )

        phrases = []

        current_phrase = [
            words[0]
        ]

        for i in range(
            len(words) - 1
        ):

            current_word = words[i]

            next_word = words[i + 1]

            gap = (
                next_word["start"]
                - current_word["end"]
            )

            if gap >= gap_threshold:

                phrase_start = (
                    current_phrase[0]["start"]
                )

                phrase_end = (
                    current_phrase[-1]["end"]
                )

                phrases.append(
                    {
                        "start": phrase_start,
                        "end": phrase_end,
                        "words": current_phrase.copy(),
                    }
                )

                current_phrase = [
                    next_word
                ]

            else:

                if (
                    next_word
                    not in current_phrase
                ):

                    current_phrase.append(
                        next_word
                    )

        if current_phrase:

            phrases.append(
                {
                    "start": current_phrase[0]["start"],
                    "end": current_phrase[-1]["end"],
                    "words": current_phrase,
                }
            )

        results = []

        for index, phrase in enumerate(
            phrases
        ):

            start_sample = int(
                phrase["start"]
                * sample_rate
            )

            end_sample = int(
                phrase["end"]
                * sample_rate
            )

            segment = audio[
                start_sample:end_sample
            ]

            filename = (
                f"{index:04d}.wav"
            )

            path = os.path.join(
                output_directory,
                filename,
            )

            sf.write(
                path,
                segment,
                sample_rate,
            )

            results.append(
                {
                    "phrase": index,
                    "start": round(
                        phrase["start"],
                        2,
                    ),
                    "end": round(
                        phrase["end"],
                        2,
                    ),
                    "duration": round(
                        phrase["end"]
                        - phrase["start"],
                        2,
                    ),
                    "text": " ".join(
                        w["word"]
                        for w in phrase["words"]
                    ),
                    "file": path,
                }
            )

        return results