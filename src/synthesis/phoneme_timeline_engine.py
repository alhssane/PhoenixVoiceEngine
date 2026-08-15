import json


class PhonemeTimelineEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        generation_data,
    ):

        phonemes = generation_data[
            "phonemes"
        ]

        duration = generation_data[
            "duration"
        ]

        phoneme_duration = (
            duration
            / len(phonemes)
        )

        timeline = []

        current_time = 0.0

        for phoneme in phonemes:

            start = current_time

            end = (
                current_time
                + phoneme_duration
            )

            timeline.append(
                {
                    "phoneme": phoneme,
                    "start": round(
                        start,
                        3,
                    ),
                    "end": round(
                        end,
                        3,
                    ),
                    "duration": round(
                        phoneme_duration,
                        3,
                    ),
                }
            )

            current_time = end

        return {
            "artist": generation_data[
                "artist"
            ],
            "word": generation_data[
                "word"
            ],
            "timeline": timeline,
            "duration": duration,
            "maqam": generation_data[
                "maqam"
            ],
            "status": (
                "TIMELINE_GENERATED"
            ),
        }