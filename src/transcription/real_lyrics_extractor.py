import json
from pathlib import Path

from faster_whisper import WhisperModel


class RealLyricsExtractor:

    def __init__(self):

        self.model = WhisperModel(
            "small",
            compute_type="int8"
        )

    def extract(
        self,
        audio_path
    ):

        segments, info = self.model.transcribe(
            str(audio_path),
            language="ar",
            word_timestamps=True
        )

        results = []

        for segment in segments:

            segment_data = {
                "text": segment.text,
                "start_time": round(
                    segment.start,
                    2
                ),
                "end_time": round(
                    segment.end,
                    2
                ),
                "words": []
            }

            if segment.words:

                for word in segment.words:

                    segment_data["words"].append(
                        {
                            "text": word.word,
                            "start_time": round(
                                word.start,
                                2
                            ),
                            "end_time": round(
                                word.end,
                                2
                            )
                        }
                    )

            results.append(
                segment_data
            )

        return {
            "language": info.language,
            "duration": info.duration,
            "segments": results
        }

    def save(
        self,
        data,
        output_path
    ):

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )