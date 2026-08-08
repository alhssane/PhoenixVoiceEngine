"""
Phoenix Voice Studio
Vocal Candidate Detector

Estimates how likely an active audio segment is to contain
a vocal/performance signal.

IMPORTANT:
This is a candidate detector, not a vocal separator.
It does not remove music or guarantee that a segment contains vocals.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


@dataclass
class VocalCandidate:
    """Vocal candidate analysis for one audio segment."""

    index: int
    start: float
    end: float
    duration: float

    energy_score: float
    spectral_score: float
    harmonic_score: float
    stability_score: float

    confidence: float
    classification: str

    def to_dict(self) -> dict[str, Any]:
        """Convert candidate to a dictionary."""

        return asdict(self)


@dataclass
class VocalCandidateReport:
    """Complete vocal candidate detection report."""

    file_name: str
    total_duration: float

    candidate_count: int
    high_confidence_duration: float
    medium_confidence_duration: float

    high_confidence_coverage: float
    medium_confidence_coverage: float

    candidates: list[VocalCandidate]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to a dictionary."""

        data = asdict(self)

        data["candidates"] = [
            candidate.to_dict()
            for candidate in self.candidates
        ]

        return data


class VocalCandidateDetector:
    """
    Estimates vocal likelihood for detected active segments.

    This version intentionally uses signal-analysis heuristics.
    It is not a machine-learning vocal separator.
    """

    def __init__(
        self,
        high_confidence_threshold: float = 70.0,
        medium_confidence_threshold: float = 45.0,
        frame_duration: float = 0.05,
    ):

        if not 0 <= medium_confidence_threshold <= 100:
            raise ValueError(
                "medium_confidence_threshold must be between 0 and 100."
            )

        if not 0 <= high_confidence_threshold <= 100:
            raise ValueError(
                "high_confidence_threshold must be between 0 and 100."
            )

        if (
            high_confidence_threshold
            < medium_confidence_threshold
        ):
            raise ValueError(
                "high_confidence_threshold must be "
                "greater than or equal to "
                "medium_confidence_threshold."
            )

        if frame_duration <= 0:
            raise ValueError(
                "frame_duration must be greater than zero."
            )

        self.high_confidence_threshold = (
            high_confidence_threshold
        )

        self.medium_confidence_threshold = (
            medium_confidence_threshold
        )

        self.frame_duration = frame_duration

    # =========================================================
    # PUBLIC API
    # =========================================================

    def analyze(
        self,
        audio_path: str,
        segments: list[Any],
    ) -> VocalCandidateReport:
        """
        Analyze previously detected active segments.

        Args:
            audio_path:
                Source audio file.

            segments:
                Segments returned by VocalActivityAnalyzer.

        Returns:
            VocalCandidateReport
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

        audio, sample_rate = sf.read(
            str(path),
            always_2d=False,
        )

        if audio.size == 0:
            raise ValueError(
                "The audio file contains no samples."
            )

        mono_audio = self._to_mono(audio)

        total_duration = (
            len(mono_audio) / sample_rate
        )

        candidates = []

        for index, segment in enumerate(
            segments,
            start=1,
        ):

            start = float(
                self._segment_value(
                    segment,
                    "start",
                )
            )

            end = float(
                self._segment_value(
                    segment,
                    "end",
                )
            )

            if end <= start:
                continue

            segment_audio = self._extract_segment(
                mono_audio,
                sample_rate,
                start,
                end,
            )

            if segment_audio.size == 0:
                continue

            energy_score = self._energy_score(
                segment_audio
            )

            spectral_score = self._spectral_score(
                segment_audio,
                sample_rate,
            )

            harmonic_score = self._harmonic_score(
                segment_audio,
                sample_rate,
            )

            stability_score = self._stability_score(
                segment_audio,
                sample_rate,
            )

            confidence = self._calculate_confidence(
                energy_score=energy_score,
                spectral_score=spectral_score,
                harmonic_score=harmonic_score,
                stability_score=stability_score,
            )

            classification = self._classify(
                confidence
            )

            candidates.append(
                VocalCandidate(
                    index=index,
                    start=round(
                        start,
                        3,
                    ),
                    end=round(
                        end,
                        3,
                    ),
                    duration=round(
                        end - start,
                        3,
                    ),
                    energy_score=round(
                        energy_score,
                        1,
                    ),
                    spectral_score=round(
                        spectral_score,
                        1,
                    ),
                    harmonic_score=round(
                        harmonic_score,
                        1,
                    ),
                    stability_score=round(
                        stability_score,
                        1,
                    ),
                    confidence=round(
                        confidence,
                        1,
                    ),
                    classification=classification,
                )
            )

        high_duration = sum(
            candidate.duration
            for candidate in candidates
            if candidate.classification
            == "HIGH_CONFIDENCE"
        )

        medium_duration = sum(
            candidate.duration
            for candidate in candidates
            if candidate.classification
            in {
                "HIGH_CONFIDENCE",
                "MEDIUM_CONFIDENCE",
            }
        )

        high_coverage = (
            high_duration / total_duration * 100
            if total_duration > 0
            else 0.0
        )

        medium_coverage = (
            medium_duration / total_duration * 100
            if total_duration > 0
            else 0.0
        )

        return VocalCandidateReport(
            file_name=path.name,
            total_duration=round(
                total_duration,
                2,
            ),
            candidate_count=len(candidates),
            high_confidence_duration=round(
                high_duration,
                2,
            ),
            medium_confidence_duration=round(
                medium_duration,
                2,
            ),
            high_confidence_coverage=round(
                high_coverage,
                2,
            ),
            medium_confidence_coverage=round(
                medium_coverage,
                2,
            ),
            candidates=candidates,
        )

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _segment_value(
        segment: Any,
        key: str,
    ) -> Any:
        """Read a value from a dataclass or dictionary."""

        if isinstance(segment, dict):
            return segment[key]

        return getattr(
            segment,
            key,
        )

    @staticmethod
    def _to_mono(
        audio: np.ndarray,
    ) -> np.ndarray:
        """Convert audio to mono."""

        if audio.ndim == 1:
            return audio.astype(
                np.float64
            )

        if audio.ndim == 2:
            return np.mean(
                audio.astype(np.float64),
                axis=1,
            )

        raise ValueError(
            f"Unsupported audio dimensions: "
            f"{audio.ndim}"
        )

    @staticmethod
    def _extract_segment(
        audio: np.ndarray,
        sample_rate: int,
        start: float,
        end: float,
    ) -> np.ndarray:
        """Extract a segment safely."""

        start_sample = max(
            0,
            int(round(start * sample_rate)),
        )

        end_sample = min(
            len(audio),
            int(round(end * sample_rate)),
        )

        if end_sample <= start_sample:
            return np.array(
                [],
                dtype=np.float64,
            )

        return audio[
            start_sample:end_sample
        ]

    # =========================================================
    # ENERGY
    # =========================================================

    @staticmethod
    def _energy_score(
        audio: np.ndarray,
    ) -> float:
        """
        Estimate whether the segment has a usable signal level.

        This does not mean louder = more vocal.
        """

        rms = np.sqrt(
            np.mean(
                np.square(audio)
            )
        )

        if rms <= 1e-12:
            return 0.0

        rms_db = 20 * np.log10(rms)

        if rms_db <= -50:
            return 0.0

        if rms_db >= -12:
            return 100.0

        return float(
            np.interp(
                rms_db,
                [-50, -12],
                [0, 100],
            )
        )

    # =========================================================
    # SPECTRAL ANALYSIS
    # =========================================================

    @staticmethod
    def _spectral_score(
        audio: np.ndarray,
        sample_rate: int,
    ) -> float:
        """
        Estimate spectral concentration in a broad
        vocal-relevant frequency range.

        This is a heuristic and is NOT a vocal classifier.
        """

        if len(audio) < 1024:
            return 50.0

        window_size = min(
            4096,
            len(audio),
        )

        window = np.hanning(
            window_size
        )

        frame = audio[:window_size] * window

        spectrum = np.abs(
            np.fft.rfft(frame)
        )

        frequencies = np.fft.rfftfreq(
            window_size,
            d=1.0 / sample_rate,
        )

        total_energy = np.sum(
            spectrum
        )

        if total_energy <= 1e-12:
            return 0.0

        band = (
            (frequencies >= 80)
            & (frequencies <= 5000)
        )

        band_energy = np.sum(
            spectrum[band]
        )

        ratio = (
            band_energy / total_energy
        )

        return float(
            np.clip(
                ratio * 100,
                0,
                100,
            )
        )

    # =========================================================
    # HARMONIC ANALYSIS
    # =========================================================

    @staticmethod
    def _harmonic_score(
        audio: np.ndarray,
        sample_rate: int,
    ) -> float:
        """
        Estimate harmonic structure using short frames.

        IMPORTANT:
        This function deliberately does NOT run autocorrelation
        over the complete audio segment.

        Instead, it:
            1. Splits the segment into short frames.
            2. Selects a limited number of representative frames.
            3. Uses FFT-based autocorrelation for each frame.
            4. Averages the resulting scores.

        This keeps analysis practical for long recordings.
        """

        if len(audio) < 1024:
            return 50.0

        # -----------------------------------------------------
        # 0.5 second analysis frames
        # -----------------------------------------------------

        frame_duration = 0.5

        frame_size = int(
            sample_rate * frame_duration
        )

        if frame_size < 1024:
            return 50.0

        # -----------------------------------------------------
        # Build frames
        # -----------------------------------------------------

        frames = []

        if len(audio) <= frame_size:

            frames.append(audio)

        else:

            for start in range(
                0,
                len(audio) - frame_size + 1,
                frame_size,
            ):

                frames.append(
                    audio[
                        start:start + frame_size
                    ]
                )

        if not frames:
            return 50.0

        # -----------------------------------------------------
        # Limit processing for very long segments.
        # -----------------------------------------------------

        max_frames = 20

        if len(frames) > max_frames:

            indexes = np.linspace(
                0,
                len(frames) - 1,
                max_frames,
                dtype=int,
            )

            frames = [
                frames[index]
                for index in indexes
            ]

        # -----------------------------------------------------
        # Frequency range.
        # -----------------------------------------------------

        min_frequency = 70.0
        max_frequency = 1000.0

        min_lag = max(
            1,
            int(
                sample_rate
                / max_frequency
            ),
        )

        max_lag = min(
            frame_size // 2,
            int(
                sample_rate
                / min_frequency
            ),
        )

        if max_lag <= min_lag:
            return 50.0

        scores = []

        # -----------------------------------------------------
        # Analyze frames
        # -----------------------------------------------------

        for frame in frames:

            if len(frame) < 1024:
                continue

            centered = (
                frame
                - np.mean(frame)
            )

            energy = np.sum(
                centered ** 2
            )

            if energy <= 1e-12:
                continue

            # -------------------------------------------------
            # Windowing improves spectral analysis.
            # -------------------------------------------------

            window = np.hanning(
                len(centered)
            )

            windowed = (
                centered * window
            )

            # -------------------------------------------------
            # FFT-based autocorrelation.
            # -------------------------------------------------

            fft_size = 1

            target_size = (
                len(windowed) * 2
            )

            while fft_size < target_size:
                fft_size *= 2

            spectrum = np.fft.rfft(
                windowed,
                n=fft_size,
            )

            autocorrelation = np.fft.irfft(
                np.abs(spectrum) ** 2,
                n=fft_size,
            )

            zero_lag = (
                autocorrelation[0]
            )

            if zero_lag <= 1e-12:
                continue

            autocorrelation = (
                autocorrelation
                / zero_lag
            )

            region = autocorrelation[
                min_lag:max_lag
            ]

            if region.size == 0:
                continue

            peak = float(
                np.max(region)
            )

            score = np.clip(
                peak * 100.0,
                0.0,
                100.0,
            )

            scores.append(
                score
            )

        if not scores:
            return 50.0

        return float(
            np.mean(scores)
        )

    # =========================================================
    # STABILITY
    # =========================================================

    def _stability_score(
        self,
        audio: np.ndarray,
        sample_rate: int,
    ) -> float:
        """
        Estimate short-term stability of the signal.

        Stable voiced regions generally show more consistent
        frame-level energy than highly irregular noise.
        """

        frame_size = max(
            1,
            int(
                self.frame_duration
                * sample_rate
            ),
        )

        if len(audio) < frame_size * 2:
            return 50.0

        frame_rms = []

        for start in range(
            0,
            len(audio),
            frame_size,
        ):

            frame = audio[
                start:start + frame_size
            ]

            if len(frame) == 0:
                continue

            rms = np.sqrt(
                np.mean(
                    frame ** 2
                )
            )

            frame_rms.append(
                rms
            )

        if len(frame_rms) < 2:
            return 50.0

        frame_rms = np.asarray(
            frame_rms,
            dtype=np.float64,
        )

        mean = np.mean(
            frame_rms
        )

        if mean <= 1e-12:
            return 0.0

        coefficient = (
            np.std(frame_rms)
            / mean
        )

        # Lower variation = higher stability.
        score = 100.0 - (
            coefficient * 100.0
        )

        return float(
            np.clip(
                score,
                0,
                100,
            )
        )

    # =========================================================
    # CONFIDENCE
    # =========================================================

    @staticmethod
    def _calculate_confidence(
        energy_score: float,
        spectral_score: float,
        harmonic_score: float,
        stability_score: float,
    ) -> float:
        """
        Combine heuristic features into candidate confidence.

        This is a heuristic score, NOT a probability.
        """

        confidence = (
            energy_score * 0.15
            + spectral_score * 0.20
            + harmonic_score * 0.45
            + stability_score * 0.20
        )

        return float(
            np.clip(
                confidence,
                0,
                100,
            )
        )

    # =========================================================
    # CLASSIFICATION
    # =========================================================

    def _classify(
        self,
        confidence: float,
    ) -> str:
        """Classify a confidence score."""

        if (
            confidence
            >= self.high_confidence_threshold
        ):
            return "HIGH_CONFIDENCE"

        if (
            confidence
            >= self.medium_confidence_threshold
        ):
            return "MEDIUM_CONFIDENCE"

        return "LOW_CONFIDENCE"