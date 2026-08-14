from pathlib import Path
import wave


class RealAudioAnalyzer:

    VERSION = "1.0.0"

    def analyze(self, file_path):

        path = Path(file_path)

        if not path.exists():

            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        with wave.open(
            str(path),
            "rb",
        ) as audio:

            channels = audio.getnchannels()

            sample_rate = audio.getframerate()

            total_frames = audio.getnframes()

            sample_width = (
                audio.getsampwidth()
            )

            duration = (
                total_frames
                / sample_rate
            )

        return {
            "file_name": path.name,
            "channels": channels,
            "sample_rate": sample_rate,
            "sample_width_bytes": sample_width,
            "duration_seconds": round(
                duration,
                2,
            ),
        }