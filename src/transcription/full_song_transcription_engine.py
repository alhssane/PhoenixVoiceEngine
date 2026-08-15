import json
from pathlib import Path

from faster_whisper import WhisperModel


class FullSongTranscriptionEngine:

    VERSION = "1.0.0"

    def transcribe(
        self,
        audio_path,
    ):

        model = WhisperModel(

            r"D:\PhoenixVoiceEngine\models\faster-whisper-large-v3",

            device="cpu",

            compute_type="int8",

        )

        segments, info = model.transcribe(

            audio_path,

            language="ar",

            word_timestamps=True,

            vad_filter=True,

        )

        words = []

        for segment in segments:

            if not segment.words:

                continue

            for word in segment.words:

                if word.word is None:

                    continue

                text = word.word.strip()

                if not text:

                    continue

                start = round(

                    float(word.start),

                    2,

                )

                end = round(

                    float(word.end),

                    2,

                )

                words.append(

                    {

                        "word": text,

                        "start": start,

                        "end": end,

                        "duration": round(

                            end - start,

                            2,

                        ),

                    }

                )

        output_dir = Path(

            r"D:\PhoenixVoiceEngine\outputs\lyrics"

        )

        output_dir.mkdir(

            parents=True,

            exist_ok=True,

        )

        output_file = (

            output_dir

            / "fareed_full_words.json"

        )

        with open(

            output_file,

            "w",

            encoding="utf-8",

        ) as file:

            json.dump(

                words,

                file,

                ensure_ascii=False,

                indent=4,

            )

        return {

            "words": len(words),

            "language": info.language,

            "duration": round(

                info.duration,

                2,

            ),

            "output": str(output_file),

        }