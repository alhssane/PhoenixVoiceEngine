from pathlib import Path

import librosa
import soundfile as sf


class RealSegmentExtractor:

    VERSION = "1.0.0"

    def extract(
        self,
        file_path,
        output_directory,
        segment_duration=5,
    ):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        duration = (
            len(audio)
            / sample_rate
        )

        output_path = Path(
            output_directory
        )

        output_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        segments = []

        start_time = 0
        segment_index = 1

        while start_time < duration:

            start_sample = int(
                start_time
                * sample_rate
            )

            end_time = min(
                start_time
                + segment_duration,
                duration,
            )

            end_sample = int(
                end_time
                * sample_rate
            )

            segment_audio = audio[
                start_sample:end_sample
            ]

            segment_name = (
                f"segment_"
                f"{segment_index:03d}.wav"
            )

            segment_file = (
                output_path
                / segment_name
            )

            sf.write(
                segment_file,
                segment_audio,
                sample_rate,
            )

            segments.append(
                {
                    "file": str(
                        segment_file
                    ),
                    "start": round(
                        start_time,
                        2,
                    ),
                    "end": round(
                        end_time,
                        2,
                    ),
                }
            )

            start_time += (
                segment_duration
            )

            segment_index += 1

        return segments