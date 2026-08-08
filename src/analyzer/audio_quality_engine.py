"""
Phoenix Voice Studio
Audio Quality Engine

Analyzes the technical and signal characteristics of an audio file
and estimates its suitability for voice-training preparation.

This engine does not modify the original audio.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

import numpy as np
import soundfile as sf


@dataclass
class AudioQualityReport:
    """Complete quality analysis result."""

    file_name: str
    duration: float
    sample_rate: int
    channels: int
    subtype: str

    peak_dbfs: float
    rms_dbfs: float

    clipping_ratio: float
    silence_ratio: float
    dynamic_range_db: float

    technical_score: float
    signal_score: float
    training_suitability: float

    status: str
    recommendations: list[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the report to a dictionary."""

        return asdict(self)


class AudioQualityEngine:
    """
    Analyzes audio quality without changing the source file.

    The engine focuses on measurable characteristics and does not
    assume that a lower-quality recording should automatically be rejected.
    """

    def __init__(self):

        self.min_training_duration = 10.0
        self.max_reasonable_silence_ratio = 0.50

    def analyze(self, audio_path: str) -> AudioQualityReport:
        """Analyze an audio file and return a quality report."""

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Audio path is not a file: {audio_path}"
            )

        audio, sample_rate = sf.read(
            str(path),
            always_2d=False,
        )

        if audio.size == 0:
            raise ValueError(
                "The audio file contains no audio samples."
            )

        channels = self._get_channels(audio)

        mono_audio = self._to_mono(audio)

        duration = len(mono_audio) / sample_rate

        peak = float(np.max(np.abs(mono_audio)))

        rms = float(
            np.sqrt(
                np.mean(
                    np.square(mono_audio.astype(np.float64))
                )
            )
        )

        peak_dbfs = self._to_dbfs(peak)
        rms_dbfs = self._to_dbfs(rms)

        clipping_ratio = self._calculate_clipping_ratio(
            mono_audio
        )

        silence_ratio = self._calculate_silence_ratio(
            mono_audio
        )

        dynamic_range_db = self._calculate_dynamic_range(
            mono_audio
        )

        technical_score = self._technical_score(
            sample_rate=sample_rate,
            channels=channels,
            duration=duration,
        )

        signal_score = self._signal_score(
            rms_dbfs=rms_dbfs,
            peak_dbfs=peak_dbfs,
            clipping_ratio=clipping_ratio,
            silence_ratio=silence_ratio,
            dynamic_range_db=dynamic_range_db,
        )

        training_suitability = round(
            (technical_score * 0.35)
            + (signal_score * 0.65),
            1,
        )

        status = self._get_status(
            training_suitability,
            duration,
        )

        recommendations = self._get_recommendations(
            sample_rate=sample_rate,
            channels=channels,
            duration=duration,
            peak_dbfs=peak_dbfs,
            rms_dbfs=rms_dbfs,
            clipping_ratio=clipping_ratio,
            silence_ratio=silence_ratio,
            dynamic_range_db=dynamic_range_db,
        )

        return AudioQualityReport(
            file_name=path.name,
            duration=round(duration, 2),
            sample_rate=sample_rate,
            channels=channels,
            subtype=self._get_subtype(path),
            peak_dbfs=round(peak_dbfs, 2),
            rms_dbfs=round(rms_dbfs, 2),
            clipping_ratio=round(clipping_ratio, 6),
            silence_ratio=round(silence_ratio, 4),
            dynamic_range_db=round(dynamic_range_db, 2),
            technical_score=round(technical_score, 1),
            signal_score=round(signal_score, 1),
            training_suitability=training_suitability,
            status=status,
            recommendations=recommendations,
        )

    @staticmethod
    def _get_channels(audio: np.ndarray) -> int:
        """Return the number of audio channels."""

        if audio.ndim == 1:
            return 1

        if audio.ndim == 2:
            return int(audio.shape[1])

        raise ValueError(
            f"Unsupported audio dimensions: {audio.ndim}"
        )

    @staticmethod
    def _to_mono(audio: np.ndarray) -> np.ndarray:
        """Create a mono analysis signal."""

        if audio.ndim == 1:
            return audio.astype(np.float64)

        if audio.ndim == 2:
            return np.mean(
                audio.astype(np.float64),
                axis=1,
            )

        raise ValueError(
            f"Unsupported audio dimensions: {audio.ndim}"
        )

    @staticmethod
    def _to_dbfs(value: float) -> float:
        """Convert linear amplitude to dBFS."""

        if value <= 1e-12:
            return -120.0

        return 20.0 * np.log10(value)

    @staticmethod
    def _calculate_clipping_ratio(
        audio: np.ndarray,
    ) -> float:
        """Estimate the proportion of samples at digital full scale."""

        if audio.size == 0:
            return 0.0

        clipped = np.abs(audio) >= 0.999

        return float(
            np.mean(clipped)
        )

    @staticmethod
    def _calculate_silence_ratio(
        audio: np.ndarray,
        threshold_dbfs: float = -55.0,
    ) -> float:
        """
        Estimate the proportion of samples below the silence threshold.

        This is a silence estimate, not a dedicated noise measurement.
        """

        if audio.size == 0:
            return 1.0

        threshold = 10 ** (threshold_dbfs / 20.0)

        silent = np.abs(audio) < threshold

        return float(
            np.mean(silent)
        )

    @staticmethod
    def _calculate_dynamic_range(
        audio: np.ndarray,
    ) -> float:
        """
        Estimate dynamic range using robust amplitude percentiles.

        This is intentionally not presented as a mastering-grade
        dynamic-range measurement.
        """

        absolute = np.abs(audio)

        if absolute.size == 0:
            return 0.0

        high = np.percentile(
            absolute,
            95,
        )

        low = np.percentile(
            absolute,
            10,
        )

        if low <= 1e-12:
            low = 1e-12

        return max(
            0.0,
            20.0 * np.log10(high / low),
        )

    def _technical_score(
        self,
        sample_rate: int,
        channels: int,
        duration: float,
    ) -> float:
        """Calculate technical recording score."""

        score = 100.0

        if sample_rate < 16000:
            score -= 35
        elif sample_rate < 22050:
            score -= 20
        elif sample_rate < 32000:
            score -= 10
        elif sample_rate < 44100:
            score -= 5

        if channels <= 0:
            score -= 40

        if duration < self.min_training_duration:
            score -= 25

        return max(
            0.0,
            min(100.0, score),
        )

    def _signal_score(
        self,
        rms_dbfs: float,
        peak_dbfs: float,
        clipping_ratio: float,
        silence_ratio: float,
        dynamic_range_db: float,
    ) -> float:
        """Calculate signal suitability score."""

        score = 100.0

        # Very weak signal.
        if rms_dbfs < -45:
            score -= 30
        elif rms_dbfs < -35:
            score -= 15

        # Excessive clipping.
        if clipping_ratio > 0.01:
            score -= 30
        elif clipping_ratio > 0.001:
            score -= 15

        # Excessive silence.
        if silence_ratio > 0.80:
            score -= 30
        elif silence_ratio > 0.50:
            score -= 15

        # Extremely compressed / narrow signal.
        if dynamic_range_db < 3:
            score -= 10

        # Peak should generally remain inside digital full scale.
        if peak_dbfs > -0.1:
            score -= 5

        return max(
            0.0,
            min(100.0, score),
        )

    def _get_status(
        self,
        suitability: float,
        duration: float,
    ) -> str:
        """Convert score into a practical training status."""

        if duration < self.min_training_duration:
            return "NOT_SUITABLE"

        if suitability >= 85:
            return "READY"

        if suitability >= 70:
            return "READY_WITH_PROCESSING"

        if suitability >= 50:
            return "NEEDS_PROCESSING"

        return "LOW_QUALITY"

    def _get_recommendations(
        self,
        sample_rate: int,
        channels: int,
        duration: float,
        peak_dbfs: float,
        rms_dbfs: float,
        clipping_ratio: float,
        silence_ratio: float,
        dynamic_range_db: float,
    ) -> list[str]:
        """Generate practical processing recommendations."""

        recommendations = []

        if channels > 1:
            recommendations.append(
                "Consider converting multi-channel audio to mono."
            )

        if sample_rate < 44100:
            recommendations.append(
                "Consider resampling to 44100 Hz."
            )

        if rms_dbfs < -35:
            recommendations.append(
                "Signal level is low; inspect and consider careful normalization."
            )

        if clipping_ratio > 0.001:
            recommendations.append(
                "Clipping detected; inspect the original recording before training."
            )

        if silence_ratio > 0.50:
            recommendations.append(
                "Large amount of silence detected; inspect and trim unnecessary silence."
            )

        if dynamic_range_db < 3:
            recommendations.append(
                "Very limited dynamic range detected."
            )

        if duration < self.min_training_duration:
            recommendations.append(
                "Audio is very short for reliable training."
            )

        if not recommendations:
            recommendations.append(
                "No major technical preparation is currently required."
            )

        return recommendations

    @staticmethod
    def _get_subtype(audio_path: Path) -> str:
        """Read the audio subtype from the file."""

        try:
            info = sf.info(str(audio_path))
            return info.subtype
        except Exception:
            return "UNKNOWN"