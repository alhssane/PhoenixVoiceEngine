"""
Phoenix Voice Studio
Auto-Fix Engine

Analyzes an audio file and applies safe automatic
preparation steps without modifying the original file.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from src.audio.audio_converter import AudioConverter


@dataclass
class AudioFixReport:
    """Result of the automatic audio preparation."""

    source_path: str
    output_path: str

    original_channels: int
    final_channels: int

    original_sample_rate: int
    final_sample_rate: int

    mono_converted: bool
    normalized: bool


class AutoFixEngine:
    """
    Automatically prepares audio for the next processing stage.

    The original source file is never modified.
    """

    def __init__(self, target_sample_rate: int = 44100):

        if target_sample_rate <= 0:
            raise ValueError(
                "target_sample_rate must be greater than zero."
            )

        self.target_sample_rate = target_sample_rate

    def inspect(self, audio_path: str) -> dict:
        """Inspect basic properties of an audio file."""

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        audio_data, sample_rate = sf.read(
            str(path),
            always_2d=False,
        )

        if audio_data.ndim == 1:
            channels = 1
        elif audio_data.ndim == 2:
            channels = audio_data.shape[1]
        else:
            raise ValueError(
                f"Unsupported audio dimensions: {audio_data.ndim}"
            )

        return {
            "channels": channels,
            "sample_rate": sample_rate,
            "duration": len(audio_data) / sample_rate,
        }

    def process(
        self,
        input_path: str,
        output_path: str,
        convert_stereo: bool = True,
        normalize: bool = False,
    ) -> AudioFixReport:
        """
        Prepare an audio file.

        The original file is never modified.

        Args:
            input_path:
                Original audio file.

            output_path:
                New processed audio file.

            convert_stereo:
                Convert multi-channel audio to mono.

            normalize:
                Normalize peak level if requested.
        """

        source = Path(input_path)
        output = Path(output_path)

        if not source.exists():
            raise FileNotFoundError(
                f"Audio file not found: {input_path}"
            )

        if source.resolve() == output.resolve():
            raise ValueError(
                "Output file must be different from the source file."
            )

        audio_data, sample_rate = AudioConverter.load(
            str(source)
        )

        if audio_data.ndim == 1:
            original_channels = 1
        else:
            original_channels = audio_data.shape[1]

        original_sample_rate = sample_rate

        mono_converted = False
        normalized = False

        # -----------------------------------------
        # Stereo / multi-channel handling
        # -----------------------------------------

        if convert_stereo and audio_data.ndim == 2:

            audio_data = AudioConverter.convert_to_mono(
                audio_data
            )

            mono_converted = True

        # -----------------------------------------
        # Optional normalization
        # -----------------------------------------

        if normalize:

            audio_data = AudioConverter.normalize(
                audio_data
            )

            normalized = True

        # -----------------------------------------
        # Save processed audio
        # -----------------------------------------

        AudioConverter.save(
            audio_data,
            sample_rate,
            str(output),
        )

        final_channels = 1 if audio_data.ndim == 1 else audio_data.shape[1]

        return AudioFixReport(
            source_path=str(source),
            output_path=str(output),
            original_channels=original_channels,
            final_channels=final_channels,
            original_sample_rate=original_sample_rate,
            final_sample_rate=sample_rate,
            mono_converted=mono_converted,
            normalized=normalized,
        )