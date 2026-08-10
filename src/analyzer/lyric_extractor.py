"""
Phoenix Voice Studio
Real Lyric Extractor

Stage:
    Clean vocal audio
        ->
    ASR transcription
        ->
    Word-level lyric timestamps

The extractor uses faster-whisper when installed.
It does not perform musical-note alignment yet.
That will be handled by the next pipeline stage.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional


@dataclass
class LyricWordResult:
    index: int
    text: str
    start_time: float
    end_time: float
    duration: float
    confidence: float = 0.0

    def to_dict(self):
        return {
            "index": self.index,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "confidence": self.confidence,
        }


@dataclass
class LyricSegmentResult:
    index: int
    text: str
    start_time: float
    end_time: float
    duration: float
    confidence: float = 0.0
    words: List[LyricWordResult] = field(default_factory=list)

    def to_dict(self):
        return {
            "index": self.index,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "confidence": self.confidence,
            "words": [
                word.to_dict()
                for word in self.words
            ],
        }


@dataclass
class LyricExtractionReport:
    file_name: str
    duration: float
    language: str
    language_probability: float

    text: str
    segment_count: int
    word_count: int

    voiced_coverage: float
    average_word_confidence: float

    segments: List[LyricSegmentResult] = field(
        default_factory=list
    )
    words: List[LyricWordResult] = field(
        default_factory=list
    )

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "duration": self.duration,
            "language": self.language,
            "language_probability": self.language_probability,
            "text": self.text,
            "segment_count": self.segment_count,
            "word_count": self.word_count,
            "voiced_coverage": self.voiced_coverage,
            "average_word_confidence": (
                self.average_word_confidence
            ),
            "segments": [
                segment.to_dict()
                for segment in self.segments
            ],
            "words": [
                word.to_dict()
                for word in self.words
            ],
        }


class LyricExtractor:
    """
    Extract real lyrics from audio using faster-whisper.

    Defaults are chosen for a clean Arabic vocal track:
        model_size = large-v3
        language = ar
        task = transcribe
        word_timestamps = True
        vad_filter = True
        model_path = optional local CTranslate2 model directory

    If model_path is omitted, the extractor automatically uses
    the PhoenixVoiceEngine local large-v3 model when available:

        <project_root>/models/faster-whisper-large-v3

    The faster-whisper dependency is imported lazily so the
    Phoenix project can still import/test its data structures
    without loading the ASR model.
    """

    def __init__(
        self,
        model_size: str = "large-v3",
        language: str = "ar",
        device: str = "cuda",
        compute_type: str = "float16",
        beam_size: int = 5,
        vad_filter: bool = True,
        min_silence_duration_ms: int = 500,
        model_path: Optional[str] = None,
    ):
        if not model_size:
            raise ValueError("model_size cannot be empty.")

        if not language:
            raise ValueError("language cannot be empty.")

        if beam_size < 1:
            raise ValueError(
                "beam_size must be at least 1."
            )

        if min_silence_duration_ms < 0:
            raise ValueError(
                "min_silence_duration_ms cannot be negative."
            )

        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.beam_size = int(beam_size)
        self.vad_filter = bool(vad_filter)
        self.min_silence_duration_ms = int(
            min_silence_duration_ms
        )

        # PhoenixVoiceEngine local model.
        #
        # When model_path is not supplied, look for the
        # downloaded CTranslate2 model inside:
        #
        #   <project_root>/models/faster-whisper-large-v3
        #
        # This prevents the real extractor from trying to
        # download large-v3 from Hugging Face on every run.
        if model_path:
            self.model_path = Path(model_path)
        else:
            project_root = (
                Path(__file__).resolve().parents[2]
            )
            local_model = (
                project_root
                / "models"
                / "faster-whisper-large-v3"
            )

            self.model_path = (
                local_model
                if local_model.is_dir()
                else None
            )

        self._model = None

    # ========================================================
    # MODEL
    # ========================================================

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. "
                "Install it before running real lyric extraction."
            ) from exc

        # Prefer the local PhoenixVoiceEngine model when it
        # exists. Otherwise fall back to model_size, which
        # preserves the original public API.
        model_source = (
            str(self.model_path)
            if self.model_path is not None
            else self.model_size
        )

        if self.model_path is not None:
            required_files = (
                "model.bin",
                "config.json",
                "tokenizer.json",
                "preprocessor_config.json",
                "vocabulary.json",
            )

            missing = [
                name
                for name in required_files
                if not (
                    self.model_path / name
                ).is_file()
            ]

            if missing:
                raise RuntimeError(
                    "Local faster-whisper model is incomplete. "
                    "Missing files: "
                    + ", ".join(missing)
                    + f"\nModel path: {self.model_path}"
                )

        self._model = WhisperModel(
            model_source,
            device=self.device,
            compute_type=self.compute_type,
        )

        return self._model

    # ========================================================
    # PUBLIC API
    # ========================================================

    def extract(
        self,
        audio_path: str,
        model: Optional[Any] = None,
    ) -> LyricExtractionReport:

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found:\n{path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Audio path is not a file:\n{path}"
            )

        whisper_model = (
            model
            if model is not None
            else self._load_model()
        )

        vad_parameters = {
            "min_silence_duration_ms": (
                self.min_silence_duration_ms
            )
        }

        segments_iter, info = whisper_model.transcribe(
            str(path),
            language=self.language,
            task="transcribe",
            beam_size=self.beam_size,
            word_timestamps=True,
            vad_filter=self.vad_filter,
            vad_parameters=vad_parameters,
            condition_on_previous_text=False,
        )

        # faster-whisper returns a generator. Materialize it
        # before building the report.
        raw_segments = list(segments_iter)

        return self._build_report(
            path=path,
            raw_segments=raw_segments,
            info=info,
        )

    # ========================================================
    # REPORT
    # ========================================================

    def _build_report(
        self,
        path: Path,
        raw_segments,
        info,
    ) -> LyricExtractionReport:

        segments: List[LyricSegmentResult] = []
        all_words: List[LyricWordResult] = []

        segment_index = 1
        word_index = 1

        for raw_segment in raw_segments:
            segment_start = self._safe_float(
                getattr(raw_segment, "start", 0.0)
            )

            segment_end = self._safe_float(
                getattr(raw_segment, "end", segment_start)
            )

            segment_start = max(0.0, segment_start)
            segment_end = max(
                segment_start,
                segment_end,
            )

            segment_text = str(
                getattr(raw_segment, "text", "")
            ).strip()

            segment_confidence = self._segment_confidence(
                raw_segment
            )

            segment_words = []

            raw_words = getattr(
                raw_segment,
                "words",
                None,
            ) or []

            for raw_word in raw_words:
                word_text = str(
                    getattr(raw_word, "word", "")
                ).strip()

                if not word_text:
                    continue

                word_start = self._safe_float(
                    getattr(
                        raw_word,
                        "start",
                        segment_start,
                    )
                )

                word_end = self._safe_float(
                    getattr(
                        raw_word,
                        "end",
                        word_start,
                    )
                )

                word_start = max(
                    segment_start,
                    word_start,
                )

                word_end = min(
                    segment_end,
                    max(word_start, word_end),
                )

                word_confidence = self._word_confidence(
                    raw_word
                )

                word_result = LyricWordResult(
                    index=word_index,
                    text=word_text,
                    start_time=round(
                        word_start,
                        6,
                    ),
                    end_time=round(
                        word_end,
                        6,
                    ),
                    duration=round(
                        max(
                            0.0,
                            word_end - word_start,
                        ),
                        6,
                    ),
                    confidence=round(
                        word_confidence,
                        2,
                    ),
                )

                segment_words.append(
                    word_result
                )

                all_words.append(
                    word_result
                )

                word_index += 1

            segments.append(
                LyricSegmentResult(
                    index=segment_index,
                    text=segment_text,
                    start_time=round(
                        segment_start,
                        6,
                    ),
                    end_time=round(
                        segment_end,
                        6,
                    ),
                    duration=round(
                        max(
                            0.0,
                            segment_end - segment_start,
                        ),
                        6,
                    ),
                    confidence=round(
                        segment_confidence,
                        2,
                    ),
                    words=segment_words,
                )
            )

            segment_index += 1

        duration = self._info_duration(
            info,
            segments,
        )

        language = str(
            getattr(
                info,
                "language",
                self.language,
            )
            or self.language
        )

        language_probability = self._safe_float(
            getattr(
                info,
                "language_probability",
                0.0,
            )
        )

        language_probability = self._normalize_percent(
            language_probability
        )

        text = " ".join(
            segment.text
            for segment in segments
            if segment.text
        ).strip()

        average_word_confidence = (
            sum(
                word.confidence
                for word in all_words
            )
            / len(all_words)
            if all_words
            else 0.0
        )

        voiced_end = max(
            (
                segment.end_time
                for segment in segments
            ),
            default=0.0,
        )

        voiced_coverage = (
            voiced_end
            / duration
            * 100.0
            if duration > 0
            else 0.0
        )

        voiced_coverage = min(
            100.0,
            max(0.0, voiced_coverage),
        )

        return LyricExtractionReport(
            file_name=path.name,
            duration=round(
                duration,
                6,
            ),
            language=language,
            language_probability=round(
                language_probability,
                2,
            ),
            text=text,
            segment_count=len(segments),
            word_count=len(all_words),
            voiced_coverage=round(
                voiced_coverage,
                2,
            ),
            average_word_confidence=round(
                average_word_confidence,
                2,
            ),
            segments=segments,
            words=all_words,
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    @classmethod
    def _word_confidence(cls, word):
        for name in (
            "probability",
            "confidence",
        ):
            value = getattr(
                word,
                name,
                None,
            )

            if value is not None:
                return cls._normalize_percent(
                    cls._safe_float(value)
                )

        return 0.0

    @classmethod
    def _segment_confidence(cls, segment):
        value = getattr(
            segment,
            "avg_logprob",
            None,
        )

        if value is not None:
            logprob = cls._safe_float(value)

            # Keep this as a bounded diagnostic score.
            # It is not claimed to be a calibrated probability.
            if logprob <= 0:
                score = 100.0 * (
                    1.0 - min(
                        1.0,
                        abs(logprob) / 5.0,
                    )
                )
                return max(0.0, min(100.0, score))

        value = getattr(
            segment,
            "confidence",
            None,
        )

        if value is not None:
            return cls._normalize_percent(
                cls._safe_float(value)
            )

        return 0.0

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _safe_float(value, default=0.0):
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return float(default)

    @staticmethod
    def _normalize_percent(value):
        if 0.0 <= value <= 1.0:
            return value * 100.0

        return max(
            0.0,
            min(100.0, value),
        )

    @classmethod
    def _info_duration(
        cls,
        info,
        segments,
    ):
        duration = cls._safe_float(
            getattr(
                info,
                "duration",
                0.0,
            )
        )

        if duration > 0:
            return duration

        return max(
            (
                segment.end_time
                for segment in segments
            ),
            default=0.0,
        )