"""
PhoenixVoiceEngine - Lyric Candidate Generator V1.1

Generates alternative ASR candidates for suspicious lyric words by
re-decoding the corresponding audio region with faster-whisper.

V1.1 fixes the V1 alignment problem:
- candidates are taken from word-level timestamps;
- only words overlapping the target timestamp are accepted;
- multi-word segments are never split and assigned wholesale to one target;
- common ASR boilerplate is filtered;
- the original ASR word is always preserved as a candidate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence
import json
import re


ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

BOILERPLATE = {
    "اشتركوا",
    "اشترك",
    "القناة",
    "قناتي",
    "ترجمة",
    "موسيقى",
    "نانسي",
    "youtube",
    "subscribe",
    "channel",
}


def normalize_token(text: str) -> str:
    text = str(text or "").strip()
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.replace("ـ", "")
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي")
    return text


def is_boilerplate(text: str) -> bool:
    normalized = normalize_token(text).lower()
    return normalized in {normalize_token(x).lower() for x in BOILERPLATE}


@dataclass
class Candidate:
    text: str
    confidence: float
    source: str
    pass_name: str
    start_time: float
    end_time: float


@dataclass
class CandidateReport:
    word_index: int
    original_text: str
    original_confidence: float
    start_time: float
    end_time: float
    suspicious: bool
    candidates: List[Candidate]
    selected_candidate: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["candidates"] = [asdict(c) for c in self.candidates]
        return data


class LyricCandidateGenerator:
    """Generate timestamp-aligned candidates for suspicious ASR words."""

    DEFAULT_MODEL = r"D:\PhoenixVoiceEngine\models\faster-whisper-large-v3"

    def __init__(
        self,
        model_path: Optional[str] = None,
        language: str = "ar",
        device: str = "cuda",
        compute_type: str = "float16",
        suspicious_confidence: float = 82.0,
        context_padding: float = 1.25,
        beam_sizes: Sequence[int] = (5, 10),
        max_candidates: int = 8,
        transcriber: Optional[Callable[..., Iterable[Any]]] = None,
    ) -> None:
        self.model_path = str(model_path or self.DEFAULT_MODEL)
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.suspicious_confidence = float(suspicious_confidence)
        self.context_padding = float(context_padding)
        self.beam_sizes = tuple(int(x) for x in beam_sizes)
        self.max_candidates = int(max_candidates)
        self._model = None
        self._transcriber = transcriber

    def _load_model(self) -> Any:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_path,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    @staticmethod
    def _words(report: Dict[str, Any]) -> List[Dict[str, Any]]:
        words: List[Dict[str, Any]] = []
        for segment in report.get("segments", []):
            words.extend(segment.get("words", []))
        words.sort(key=lambda w: float(w.get("start_time", 0.0) or 0.0))
        return words

    def suspicious_words(
        self,
        report: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return [
            word
            for word in self._words(report)
            if str(word.get("text", "")).strip()
            and float(word.get("confidence", 0.0) or 0.0)
            < self.suspicious_confidence
        ]

    @staticmethod
    def _get(item: Any, name: str, default: Any = None) -> Any:
        if isinstance(item, dict):
            return item.get(name, default)
        return getattr(item, name, default)

    @classmethod
    def _confidence(cls, item: Any) -> float:
        value = cls._get(item, "confidence", None)
        if value is None:
            value = cls._get(item, "probability", None)
        if value is None:
            value = cls._get(item, "avg_logprob", 0.0)

        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.0

        # faster-whisper word probability is normally 0..1.
        if 0.0 <= value <= 1.0:
            value *= 100.0
        elif value < 0.0:
            # Only used as a fallback for avg_logprob.
            value = max(0.0, min(100.0, 100.0 + value * 20.0))

        return max(0.0, min(100.0, value))

    @classmethod
    def _extract_aligned_words(
        cls,
        result: Any,
        target_start: float,
        target_end: float,
        tolerance: float = 0.12,
    ) -> List[tuple[str, float, float, float]]:
        """
        Extract only word-level results that overlap the target interval.

        Returns:
            (text, confidence_percent, start, end)
        """
        if result is None:
            return []

        items = result.segments if hasattr(result, "segments") else result
        output: List[tuple[str, float, float, float]] = []

        for segment in items:
            word_items = cls._get(segment, "words", None)

            # We require actual word timestamps when the decoder supplies
            # multiple words. This prevents the V1 multi-word contamination.
            if word_items:
                for word in word_items:
                    text = str(
                        cls._get(
                            word,
                            "word",
                            cls._get(word, "text", ""),
                        )
                    ).strip()

                    if not text or is_boilerplate(text):
                        continue

                    start = cls._get(word, "start", None)
                    end = cls._get(word, "end", None)

                    try:
                        start = float(start)
                        end = float(end)
                    except (TypeError, ValueError):
                        continue

                    if end < target_start - tolerance:
                        continue
                    if start > target_end + tolerance:
                        continue

                    output.append(
                        (
                            text,
                            round(cls._confidence(word), 2),
                            start,
                            end,
                        )
                    )
                continue

            # Fallback is deliberately restricted to a single-token segment.
            text = str(cls._get(segment, "text", "")).strip()
            tokens = cls._split_tokens(text)

            if len(tokens) != 1 or is_boilerplate(tokens[0]):
                continue

            start = cls._get(segment, "start", target_start)
            end = cls._get(segment, "end", target_end)

            try:
                start = float(start)
                end = float(end)
            except (TypeError, ValueError):
                start, end = target_start, target_end

            if end < target_start - tolerance:
                continue
            if start > target_end + tolerance:
                continue

            output.append(
                (
                    tokens[0],
                    round(cls._confidence(segment), 2),
                    start,
                    end,
                )
            )

        return output

    @staticmethod
    def _split_tokens(text: str) -> List[str]:
        punctuation = ".,،؛:!?؟()[]{}\"'«»"
        return [
            token.strip(punctuation)
            for token in str(text).split()
            if token.strip(punctuation)
        ]

    def _call_real_transcriber(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        beam_size: int,
    ) -> Iterable[Any]:
        model = self._load_model()

        clip_start = max(0.0, start_time - self.context_padding)
        clip_end = max(clip_start + 0.10, end_time + self.context_padding)

        segments, _info = model.transcribe(
            audio_path,
            language=self.language,
            beam_size=beam_size,
            word_timestamps=True,
            condition_on_previous_text=False,
            vad_filter=False,
            clip_timestamps=[clip_start, clip_end],
        )
        return list(segments)

    def _transcribe(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        beam_size: int,
    ) -> Iterable[Any]:
        if self._transcriber is not None:
            return self._transcriber(
                audio_path=audio_path,
                start_time=start_time,
                end_time=end_time,
                beam_size=beam_size,
                language=self.language,
            )

        return self._call_real_transcriber(
            audio_path,
            start_time,
            end_time,
            beam_size,
        )

    def generate_for_word(
        self,
        audio_path: str,
        word: Dict[str, Any],
        word_index: int,
    ) -> CandidateReport:
        original = str(word.get("text", "")).strip()
        confidence = float(word.get("confidence", 0.0) or 0.0)
        start = float(word.get("start_time", 0.0) or 0.0)
        end = float(word.get("end_time", start) or start)

        suspicious = confidence < self.suspicious_confidence

        if not suspicious:
            return CandidateReport(
                word_index=word_index,
                original_text=original,
                original_confidence=confidence,
                start_time=start,
                end_time=end,
                suspicious=False,
                candidates=[],
            )

        candidates: Dict[str, Candidate] = {}

        for beam_size in self.beam_sizes:
            raw = self._transcribe(
                audio_path,
                start,
                end,
                beam_size,
            )

            aligned = self._extract_aligned_words(
                raw,
                target_start=start,
                target_end=end,
            )

            for text, candidate_confidence, candidate_start, candidate_end in aligned:
                key = normalize_token(text)
                if not key:
                    continue

                candidate = Candidate(
                    text=text,
                    confidence=round(candidate_confidence, 2),
                    source="faster-whisper-redecode",
                    pass_name=f"beam_{beam_size}",
                    start_time=candidate_start,
                    end_time=candidate_end,
                )

                previous = candidates.get(key)
                if previous is None or candidate.confidence > previous.confidence:
                    candidates[key] = candidate

        # Never remove the original. The correction engine must be able to
        # decide that no correction is justified.
        original_key = normalize_token(original)
        if original_key:
            # Always preserve the original ASR result as the authoritative
            # "no correction" option. Even if re-decoding produced the same
            # spelling, it must remain explicitly marked as original-asr.
            candidates[original_key] = Candidate(
                text=original,
                confidence=round(confidence, 2),
                source="original-asr",
                pass_name="original",
                start_time=start,
                end_time=end,
            )

        ranked = sorted(
            candidates.values(),
            key=lambda item: item.confidence,
            reverse=True,
        )[: self.max_candidates]

        return CandidateReport(
            word_index=word_index,
            original_text=original,
            original_confidence=round(confidence, 2),
            start_time=start,
            end_time=end,
            suspicious=True,
            candidates=ranked,
        )

    def generate_for_report(
        self,
        audio_path: str,
        report: Dict[str, Any],
        max_words: Optional[int] = None,
    ) -> Dict[str, Any]:
        words = self._words(report)

        suspicious = [
            (index, word)
            for index, word in enumerate(words, start=1)
            if str(word.get("text", "")).strip()
            and float(word.get("confidence", 0.0) or 0.0)
            < self.suspicious_confidence
        ]

        if max_words is not None:
            suspicious = suspicious[: int(max_words)]

        reports = [
            self.generate_for_word(audio_path, word, index)
            for index, word in suspicious
        ]

        return {
            "engine": "LyricCandidateGenerator",
            "version": "1.1.0",
            "model": Path(self.model_path).name,
            "language": self.language,
            "device": self.device,
            "compute_type": self.compute_type,
            "suspicious_confidence": self.suspicious_confidence,
            "context_padding": self.context_padding,
            "beam_sizes": list(self.beam_sizes),
            "source_audio": str(audio_path),
            "word_count": len(words),
            "suspicious_word_count": len(suspicious),
            "reports": [item.to_dict() for item in reports],
        }

    def generate_for_file(
        self,
        audio_path: str,
        input_json: str,
        output_json: str,
        max_words: Optional[int] = None,
    ) -> Dict[str, Any]:
        with open(input_json, "r", encoding="utf-8") as handle:
            report = json.load(handle)

        result = self.generate_for_report(
            audio_path=audio_path,
            report=report,
            max_words=max_words,
        )

        with open(output_json, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)

        return result