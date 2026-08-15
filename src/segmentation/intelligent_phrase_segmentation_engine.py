import json
import os

import librosa
import soundfile as sf


class IntelligentPhraseSegmentationEngine:

    VERSION = "1.1.0"

    def segment(
        self,
        audio_path,
        words_json_path,
        output_directory,
        target_duration=3.0,
        start_padding=0.15,
        end_padding=0.25,
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

        audio_duration = (
            len(audio) / sample_rate
        )

        segments = []

        current_start = 0.0

        segment_index = 0

        while current_start < audio_duration:

            target_end = (
                current_start
                + target_duration
            )

            included_words = []

            for word in words:

                if (
                    word["start"]
                    >= current_start
                    and word["end"]
                    <= target_end
                ):

                    included_words.append(
                        word
                    )

            if not included_words:

                next_words = [
                    w
                    for w in words
                    if w["start"]
                    >= current_start
                ]

                if not next_words:

                    break

                included_words.append(
                    next_words[0]
                )

            segment_end = (
                included_words[-1]["end"]
            )

            real_start = max(
                0,
                current_start
                - start_padding,
            )

            real_end = min(
                audio_duration,
                segment_end
                + end_padding,
            )

            start_sample = int(
                real_start
                * sample_rate
            )

            end_sample = int(
                real_end
                * sample_rate
            )

            segment_audio = audio[
                start_sample:end_sample
            ]

            filename = (
                f"{segment_index:04d}.wav"
            )

            file_path = os.path.join(
                output_directory,
                filename,
            )

            sf.write(
                file_path,
                segment_audio,
                sample_rate,
            )

            segments.append(
                {
                    "segment": segment_index,
                    "start": round(
                        real_start,
                        2,
                    ),
                    "end": round(
                        real_end,
                        2,
                    ),
                    "duration": round(
                        real_end
                        - real_start,
                        2,
                    ),
                    "words": [
                        w["word"]
                        for w in included_words
                    ],
                    "file": file_path,
                }
            )

            current_start = (
                segment_end
            )

            segment_index += 1

        return segments