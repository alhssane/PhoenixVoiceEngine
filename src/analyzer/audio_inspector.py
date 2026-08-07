"""
Phoenix Voice Studio
Audio Inspector Engine
"""

from pathlib import Path
import soundfile as sf
from mutagen import File


class AudioInspector:

    SUPPORTED_FORMATS = [
        ".wav",
        ".mp3",
        ".flac",
        ".ogg",
        ".m4a",
    ]

    def inspect(self, file_path: str):

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {path}"
            )

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {path.suffix}"
            )

        info = sf.info(str(path))
        metadata = File(str(path))

        duration = round(info.duration, 2)

        return {

            "file_name": path.name,

            "format": path.suffix.upper(),

            "duration": duration,

            "sample_rate": info.samplerate,

            "channels": info.channels,

            "subtype": info.subtype,

            "frames": info.frames,

            "ready_for_training":
                info.channels == 1
                and info.samplerate >= 44100,

            "metadata":
                metadata.pprint()
                if metadata
                else "No Metadata",

        }