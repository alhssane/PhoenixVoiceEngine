"""
Phoenix Voice Studio
Audio Converter

Provides safe, reusable audio conversion utilities.
The original audio file is never modified.
"""

from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf


class AudioConverter:
    """Core audio conversion utilities."""

    @staticmethod
    def load(audio_path: str):
        """
        Load an audio file.

        Returns:
            audio_data: NumPy audio array
            sample_rate: Sample rate in Hz
        """

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Audio path is not a file: {audio_path}"
            )

        audio_data, sample_rate = sf.read(
            str(path),
            always_2d=False,
        )

        return audio_data, sample_rate

    @staticmethod
    def convert_to_mono(audio_data: np.ndarray) -> np.ndarray:
        """
        Convert audio to mono.

        Mono audio is returned unchanged.
        Stereo/multi-channel audio is averaged across channels.
        """

        if audio_data.ndim == 1:
            return audio_data

        if audio_data.ndim == 2:
            return np.mean(audio_data, axis=1)

        raise ValueError(
            f"Unsupported audio dimensions: {audio_data.ndim}"
        )

    @staticmethod
    def resample(
        audio_data: np.ndarray,
        source_rate: int,
        target_rate: int,
    ) -> np.ndarray:
        """
        Resample audio using linear interpolation.

        This first implementation is intentionally dependency-light.
        A higher-quality resampler can be introduced later.
        """

        if source_rate <= 0:
            raise ValueError("source_rate must be greater than zero.")

        if target_rate <= 0:
            raise ValueError("target_rate must be greater than zero.")

        if source_rate == target_rate:
            return audio_data

        if len(audio_data) == 0:
            return audio_data

        duration = len(audio_data) / source_rate

        target_length = max(
            1,
            int(round(duration * target_rate)),
        )

        source_positions = np.linspace(
            0,
            len(audio_data) - 1,
            num=len(audio_data),
        )

        target_positions = np.linspace(
            0,
            len(audio_data) - 1,
            num=target_length,
        )

        if audio_data.ndim == 1:

            return np.interp(
                target_positions,
                source_positions,
                audio_data,
            )

        if audio_data.ndim == 2:

            channels = []

            for channel in range(audio_data.shape[1]):

                converted = np.interp(
                    target_positions,
                    source_positions,
                    audio_data[:, channel],
                )

                channels.append(converted)

            return np.stack(channels, axis=1)

        raise ValueError(
            f"Unsupported audio dimensions: {audio_data.ndim}"
        )

    @staticmethod
    def normalize(
        audio_data: np.ndarray,
        peak: float = 0.95,
    ) -> np.ndarray:
        """
        Normalize audio peak level.

        The default peak is 0.95, leaving a small safety margin
        below digital full scale.
        """

        if not 0 < peak <= 1:
            raise ValueError(
                "peak must be greater than 0 and less than or equal to 1."
            )

        if len(audio_data) == 0:
            return audio_data

        max_value = np.max(np.abs(audio_data))

        if max_value == 0:
            return audio_data

        gain = peak / max_value

        normalized = audio_data * gain

        return normalized

    @staticmethod
    def save(
        audio_data: np.ndarray,
        sample_rate: int,
        output_path: str,
        subtype: Optional[str] = "PCM_24",
    ) -> str:
        """
        Save processed audio to a new file.

        The output path must be different from the source path
        when used by the Auto-Fix pipeline.
        """

        output = Path(output_path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        sf.write(
            str(output),
            audio_data,
            sample_rate,
            subtype=subtype,
        )

        return str(output)

    @classmethod
    def convert_file_to_mono(
        cls,
        input_path: str,
        output_path: str,
        normalize: bool = False,
    ) -> str:
        """
        Load an audio file, convert it to mono,
        optionally normalize it, and save a new file.
        """

        audio_data, sample_rate = cls.load(input_path)

        mono_audio = cls.convert_to_mono(audio_data)

        if normalize:
            mono_audio = cls.normalize(mono_audio)

        return cls.save(
            mono_audio,
            sample_rate,
            output_path,
        )