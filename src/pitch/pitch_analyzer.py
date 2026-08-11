from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import librosa
import numpy as np


class PitchAnalyzer:
    """
    PhoenixVoiceEngine
    Pitch Analyzer V1.0

    Extracts fundamental frequency (F0) from an audio file.

    This component does NOT:
    - modify audio
    - modify lyrics
    - perform voice conversion
    - perform melody correction
    - perform automatic lyric correction

    It only analyzes the pitch curve of the input audio.
    """

    VERSION = "1.0.0"

    DEFAULT_SAMPLE_RATE = 16000
    DEFAULT_HOP_LENGTH = 160
    DEFAULT_FRAME_LENGTH = 2048

    DEFAULT_FMIN = 65.41
    DEFAULT_FMAX = 1046.50

    def __init__(
        self,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        hop_length: int = DEFAULT_HOP_LENGTH,
        frame_length: int = DEFAULT_FRAME_LENGTH,
        fmin: float = DEFAULT_FMIN,
        fmax: float = DEFAULT_FMAX,
    ) -> None:

        if sample_rate <= 0:
            raise ValueError(
                "sample_rate must be positive."
            )

        if hop_length <= 0:
            raise ValueError(
                "hop_length must be positive."
            )

        if frame_length <= 0:
            raise ValueError(
                "frame_length must be positive."
            )

        if fmin <= 0:
            raise ValueError(
                "fmin must be positive."
            )

        if fmax <= fmin:
            raise ValueError(
                "fmax must be greater than fmin."
            )

        self.sample_rate = int(sample_rate)
        self.hop_length = int(hop_length)
        self.frame_length = int(frame_length)
        self.fmin = float(fmin)
        self.fmax = float(fmax)

    # ============================================================
    # Audio Loading
    # ============================================================

    def load_audio(
        self,
        audio_path: str | Path,
    ) -> tuple[np.ndarray, int]:

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {path}"
            )

        y, sr = librosa.load(
            str(path),
            sr=self.sample_rate,
            mono=True,
        )

        if y is None or len(y) == 0:
            raise ValueError(
                "Audio file contains no samples."
            )

        y = np.asarray(
            y,
            dtype=np.float32,
        )

        return y, sr

    # ============================================================
    # Audio Statistics
    # ============================================================

    def _audio_statistics(
        self,
        y: np.ndarray,
        sr: int,
    ) -> Dict[str, Any]:

        duration = float(len(y) / sr)

        peak = float(
            np.max(
                np.abs(y)
            )
        )

        rms = float(
            np.sqrt(
                np.mean(
                    np.square(y)
                )
            )
        )

        return {
            "sample_rate": int(sr),
            "sample_count": int(len(y)),
            "duration": round(
                duration,
                6,
            ),
            "peak": round(
                peak,
                6,
            ),
            "rms": round(
                rms,
                6,
            ),
        }

    # ============================================================
    # Pitch Extraction
    # ============================================================

    def extract_pitch(
        self,
        y: np.ndarray,
        sr: int,
    ) -> Dict[str, Any]:

        if len(y) == 0:
            raise ValueError(
                "Cannot extract pitch from empty audio."
            )

        f0, voiced_flag, voiced_prob = (
            librosa.pyin(
                y,
                fmin=self.fmin,
                fmax=self.fmax,
                sr=sr,
                frame_length=self.frame_length,
                hop_length=self.hop_length,
            )
        )

        times = librosa.times_like(
            f0,
            sr=sr,
            hop_length=self.hop_length,
        )

        frames: List[
            Dict[str, Any]
        ] = []

        for index in range(
            len(f0)
        ):

            pitch = f0[index]

            if np.isnan(pitch):
                pitch_value: Optional[
                    float
                ] = None
            else:
                pitch_value = float(
                    pitch
                )

            if voiced_flag is None:
                voiced = (
                    pitch_value is not None
                )
            else:
                voiced = bool(
                    voiced_flag[index]
                )

            if voiced_prob is None:
                probability = (
                    1.0
                    if voiced
                    else 0.0
                )
            else:
                probability = float(
                    voiced_prob[index]
                )

            frames.append(
                {
                    "frame_index": int(index),
                    "time": round(
                        float(times[index]),
                        6,
                    ),
                    "f0_hz": (
                        round(
                            pitch_value,
                            4,
                        )
                        if pitch_value is not None
                        else None
                    ),
                    "voiced": voiced,
                    "voiced_probability": round(
                        probability,
                        6,
                    ),
                }
            )

        return {
            "frame_count": len(frames),
            "frames": frames,
        }

    # ============================================================
    # Pitch Statistics
    # ============================================================

    def _pitch_statistics(
        self,
        frames: List[
            Dict[str, Any]
        ],
    ) -> Dict[str, Any]:

        pitches = [
            float(
                frame["f0_hz"]
            )
            for frame in frames
            if frame.get("f0_hz") is not None
        ]

        voiced_frames = sum(
            1
            for frame in frames
            if frame.get("voiced") is True
        )

        total_frames = len(frames)

        if pitches:

            pitch_array = np.asarray(
                pitches,
                dtype=np.float64,
            )

            f0_min = float(
                np.min(pitch_array)
            )

            f0_max = float(
                np.max(pitch_array)
            )

            f0_mean = float(
                np.mean(pitch_array)
            )

            f0_median = float(
                np.median(pitch_array)
            )

        else:

            f0_min = None
            f0_max = None
            f0_mean = None
            f0_median = None

        voiced_ratio = (
            float(
                voiced_frames / total_frames
            )
            if total_frames
            else 0.0
        )

        return {
            "voiced_frame_count": int(
                voiced_frames
            ),
            "unvoiced_frame_count": int(
                total_frames - voiced_frames
            ),
            "voiced_ratio": round(
                voiced_ratio,
                6,
            ),
            "f0_min_hz": (
                round(
                    f0_min,
                    4,
                )
                if f0_min is not None
                else None
            ),
            "f0_max_hz": (
                round(
                    f0_max,
                    4,
                )
                if f0_max is not None
                else None
            ),
            "f0_mean_hz": (
                round(
                    f0_mean,
                    4,
                )
                if f0_mean is not None
                else None
            ),
            "f0_median_hz": (
                round(
                    f0_median,
                    4,
                )
                if f0_median is not None
                else None
            ),
        }

    # ============================================================
    # Full Analysis
    # ============================================================

    def analyze(
        self,
        y: np.ndarray,
        sr: int,
        source_path: str | Path | None = None,
    ) -> Dict[str, Any]:

        audio_stats = self._audio_statistics(
            y,
            sr,
        )

        pitch_data = self.extract_pitch(
            y,
            sr,
        )

        statistics = self._pitch_statistics(
            pitch_data["frames"]
        )

        return {
            "version": self.VERSION,
            "source": (
                str(source_path)
                if source_path is not None
                else None
            ),
            "analysis": {
                "sample_rate": self.sample_rate,
                "hop_length": self.hop_length,
                "frame_length": self.frame_length,
                "fmin_hz": self.fmin,
                "fmax_hz": self.fmax,
            },
            "audio": audio_stats,
            "pitch": {
                "frame_count": pitch_data[
                    "frame_count"
                ],
                "statistics": statistics,
                "frames": pitch_data[
                    "frames"
                ],
            },
        }

    # ============================================================
    # File Analysis
    # ============================================================

    def analyze_file(
        self,
        audio_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:

        y, sr = self.load_audio(
            audio_path
        )

        result = self.analyze(
            y,
            sr,
            source_path=audio_path,
        )

        output = Path(
            output_path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return result