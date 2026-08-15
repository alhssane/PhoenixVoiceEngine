import os
import json
import librosa
import soundfile as sf


class PhraseSegmentationEngine:

    VERSION = "2.0.0"

    def segment(
        self,
        audio_path,
        output_directory,
        segment_duration=3.0,
    ):

        os.makedirs(
            output_directory,
            exist_ok=True,
        )

        audio, sample_rate = librosa.load(
            audio_path,
            sr=None,
            mono=True,
        )

        total_duration = len(audio) / sample_rate

        database = []

        start_time = 0.0
        index = 0

        while start_time < total_duration:

            end_time = min(
                start_time + segment_duration,
                total_duration,
            )

            start_sample = int(
                start_time * sample_rate
            )

            end_sample = int(
                end_time * sample_rate
            )

            segment_audio = audio[
                start_sample:end_sample
            ]

            filename = (
                f"{index:04d}.wav"
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

            database.append(
                {
                    "segment": index,
                    "start": round(
                        start_time,
                        2,
                    ),
                    "end": round(
                        end_time,
                        2,
                    ),
                    "duration": round(
                        end_time - start_time,
                        2,
                    ),
                    "file": file_path,
                }
            )

            start_time += segment_duration

            index += 1

        return database