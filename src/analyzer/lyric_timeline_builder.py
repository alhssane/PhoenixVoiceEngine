"""
Phoenix Voice Studio
Lyric Timeline Builder

Builds a structured lyric timeline from vocal phrases.

This module does not perform lyric recognition.
Lyrics are supplied by the caller and mapped to
existing vocal phrase timing and musical information.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class LyricWord:
    """A single lyric word or lyric unit with timing."""

    index: int
    text: str
    start_time: float
    end_time: float
    duration: float
    note_names: List[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self):
        return {
            "index": self.index,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "note_names": list(self.note_names),
            "confidence": self.confidence,
        }


@dataclass
class LyricPhrase:
    """A lyric phrase mapped to a vocal phrase."""

    index: int
    start_time: float
    end_time: float
    duration: float
    lyric: str
    words: List[LyricWord] = field(default_factory=list)
    note_names: List[str] = field(default_factory=list)
    pitch_center_hz: float = 0.0
    pitch_center_midi: float = 0.0
    confidence: float = 0.0
    source_phrase: Any = None

    def to_dict(self):
        return {
            "index": self.index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "lyric": self.lyric,
            "words": [word.to_dict() for word in self.words],
            "note_names": list(self.note_names),
            "pitch_center_hz": self.pitch_center_hz,
            "pitch_center_midi": self.pitch_center_midi,
            "confidence": self.confidence,
        }


@dataclass
class LyricTimelineReport:
    """Complete lyric timeline."""

    file_name: str
    duration: float
    phrase_count: int
    total_lyric_duration: float
    lyric_coverage: float
    average_phrase_duration: float
    phrases: List[LyricPhrase] = field(default_factory=list)

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "duration": self.duration,
            "phrase_count": self.phrase_count,
            "total_lyric_duration": self.total_lyric_duration,
            "lyric_coverage": self.lyric_coverage,
            "average_phrase_duration": self.average_phrase_duration,
            "phrases": [phrase.to_dict() for phrase in self.phrases],
        }


class LyricTimelineBuilder:
    """
    Builds a lyric timeline from VocalPhrase objects.

    This stage does not perform Whisper/ASR.
    It receives lyric text and attaches it to the
    timing and musical information already detected.
    """

    def __init__(self, minimum_word_duration: float = 0.025):
        if minimum_word_duration <= 0:
            raise ValueError(
                "minimum_word_duration must be greater than zero."
            )

        self.minimum_word_duration = float(minimum_word_duration)

    def build(
        self,
        vocal_phrase_report,
        lyrics: Optional[List[str]] = None,
    ) -> LyricTimelineReport:
        duration = max(
            0.0,
            float(getattr(vocal_phrase_report, "duration", 0.0)),
        )

        file_name = str(
            getattr(vocal_phrase_report, "file_name", "unknown")
        )

        source_phrases = list(
            getattr(vocal_phrase_report, "phrases", []) or []
        )

        if lyrics is None:
            lyrics = []

        lyrics = [str(value).strip() for value in lyrics]

        phrases = []

        for index, source_phrase in enumerate(source_phrases, start=1):
            lyric = lyrics[index - 1] if index - 1 < len(lyrics) else ""

            phrase = self._build_phrase(
                index=index,
                source_phrase=source_phrase,
                lyric=lyric,
                timeline_duration=duration,
            )

            if phrase is not None:
                phrases.append(phrase)

        total_lyric_duration = sum(
            phrase.duration for phrase in phrases if phrase.lyric
        )

        total_lyric_duration = min(
            total_lyric_duration,
            duration,
        )

        lyric_coverage = (
            total_lyric_duration / duration * 100.0
            if duration > 0
            else 0.0
        )

        lyric_coverage = min(100.0, max(0.0, lyric_coverage))

        average_phrase_duration = (
            sum(phrase.duration for phrase in phrases) / len(phrases)
            if phrases
            else 0.0
        )

        return LyricTimelineReport(
            file_name=file_name,
            duration=round(duration, 6),
            phrase_count=len(phrases),
            total_lyric_duration=round(total_lyric_duration, 6),
            lyric_coverage=round(lyric_coverage, 2),
            average_phrase_duration=round(average_phrase_duration, 6),
            phrases=phrases,
        )

    def _build_phrase(
        self,
        index,
        source_phrase,
        lyric,
        timeline_duration,
    ):
        start_time = max(
            0.0,
            self._get_value(source_phrase, "start_time", 0.0),
        )

        end_time = max(
            start_time,
            self._get_value(source_phrase, "end_time", start_time),
        )

        # Never allow a lyric phrase to exceed the source timeline.
        end_time = min(end_time, timeline_duration)

        if end_time <= start_time:
            return None

        duration = end_time - start_time

        note_names = list(
            getattr(source_phrase, "note_names", []) or []
        )

        pitch_center_hz = self._get_value(
            source_phrase,
            "pitch_center_hz",
            0.0,
        )

        pitch_center_midi = self._get_value(
            source_phrase,
            "pitch_center_midi",
            0.0,
        )

        confidence = self._get_value(
            source_phrase,
            "average_confidence",
            0.0,
        )

        if confidence <= 1.0:
            confidence *= 100.0

        confidence = min(100.0, max(0.0, confidence))

        words = self._split_lyric(
            lyric=lyric,
            start_time=start_time,
            end_time=end_time,
            note_names=note_names,
            confidence=confidence,
        )

        return LyricPhrase(
            index=index,
            start_time=round(start_time, 6),
            end_time=round(end_time, 6),
            duration=round(duration, 6),
            lyric=lyric,
            words=words,
            note_names=note_names,
            pitch_center_hz=round(pitch_center_hz, 3),
            pitch_center_midi=round(pitch_center_midi, 3),
            confidence=round(confidence, 2),
            source_phrase=source_phrase,
        )

    def _split_lyric(
        self,
        lyric,
        start_time,
        end_time,
        note_names,
        confidence,
    ):
        if not lyric:
            return []

        tokens = [token for token in lyric.split() if token]

        if not tokens:
            return []

        duration = max(0.0, end_time - start_time)

        if duration <= 0:
            return []

        # Equal timing is intentional at this stage.
        # Real word/phoneme alignment will be added later.
        word_duration = duration / len(tokens)
        word_duration = max(
            self.minimum_word_duration,
            word_duration,
        )

        words = []

        for index, token in enumerate(tokens, start=1):
            word_start = start_time + (index - 1) * word_duration
            word_end = start_time + index * word_duration

            word_start = min(
                end_time,
                max(start_time, word_start),
            )

            word_end = min(
                end_time,
                max(word_start, word_end),
            )

            if index == len(tokens):
                word_end = end_time

            words.append(
                LyricWord(
                    index=index,
                    text=token,
                    start_time=round(word_start, 6),
                    end_time=round(word_end, 6),
                    duration=round(
                        max(0.0, word_end - word_start),
                        6,
                    ),
                    note_names=list(note_names),
                    confidence=round(confidence, 2),
                )
            )

        return words

    @staticmethod
    def _get_value(obj, name, default=0.0):
        value = getattr(obj, name, default)

        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)