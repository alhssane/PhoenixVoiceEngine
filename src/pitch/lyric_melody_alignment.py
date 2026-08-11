from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class LyricMelodyAlignment:
    """
    PhoenixVoiceEngine
    Lyric–Melody Alignment V1.0

    Aligns finalized lyric words with existing melody events
    using temporal overlap only.

    This component does NOT:
    - modify lyrics
    - modify lyric timing
    - modify melody events
    - correct words
    - invent notes
    - invent timings
    - perform automatic lyric correction

    It only creates a temporal relationship between:

        lyric word -> melody events
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        minimum_overlap_ratio: float = 0.0,
    ) -> None:

        if not 0.0 <= minimum_overlap_ratio <= 1.0:
            raise ValueError(
                "minimum_overlap_ratio must be between 0 and 1."
            )

        self.minimum_overlap_ratio = float(
            minimum_overlap_ratio
        )

    # ============================================================
    # Loading
    # ============================================================

    def _load_json(
        self,
        path: str | Path,
    ) -> Dict[str, Any]:

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                f"JSON file must contain an object: {file_path}"
            )

        return data

    def load_lyrics(
        self,
        path: str | Path,
    ) -> Dict[str, Any]:

        return self._load_json(
            path
        )

    def load_melody(
        self,
        path: str | Path,
    ) -> Dict[str, Any]:

        return self._load_json(
            path
        )

    # ============================================================
    # Input Normalization
    # ============================================================

    def _extract_lyrics(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        words = data.get(
            "words"
        )

        if isinstance(
            words,
            list,
        ):
            return words

        items = data.get(
            "items"
        )

        if isinstance(
            items,
            list,
        ):
            return items

        raise ValueError(
            "Lyrics data must contain a words or items list."
        )

    def _extract_melody(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        melody = data.get(
            "melody"
        )

        if not isinstance(
            melody,
            dict,
        ):
            raise ValueError(
                "Melody data must contain a melody object."
            )

        events = melody.get(
            "events"
        )

        if not isinstance(
            events,
            list,
        ):
            raise ValueError(
                "Melody data must contain a melody.events list."
            )

        return events

    # ============================================================
    # Validation
    # ============================================================

    def _validate_time_range(
        self,
        start_time: Any,
        end_time: Any,
        label: str,
    ) -> tuple[float, float]:

        try:

            start = float(
                start_time
            )

            end = float(
                end_time
            )

        except (
            TypeError,
            ValueError,
        ):

            raise ValueError(
                f"{label} contains invalid timing."
            )

        if start < 0:

            raise ValueError(
                f"{label} start_time cannot be negative."
            )

        if end <= start:

            raise ValueError(
                f"{label} end_time must be greater than start_time."
            )

        return start, end

    def _validate_lyrics(
        self,
        words: List[Dict[str, Any]],
    ) -> None:

        previous_start = None

        for position, word in enumerate(
            words,
            start=1,
        ):

            if not isinstance(
                word,
                dict,
            ):

                raise ValueError(
                    f"Invalid lyric item at position {position}."
                )

            text = word.get(
                "final_text"
            )

            if text is None:

                text = word.get(
                    "text",
                    "",
                )

            if not isinstance(
                text,
                str,
            ):

                text = str(
                    text
                )

            self._validate_time_range(
                word.get(
                    "start_time"
                ),
                word.get(
                    "end_time"
                ),
                f"Lyric word {position}",
            )

            start = float(
                word["start_time"]
            )

            if (
                previous_start is not None
                and start < previous_start
            ):

                raise ValueError(
                    "Lyric words are not chronologically ordered."
                )

            previous_start = start

    def _validate_melody(
        self,
        events: List[Dict[str, Any]],
    ) -> None:

        """
        Validate melody event timing.

        IMPORTANT:
        Melody events are allowed to arrive in an arbitrary
        order. Alignment will create a sorted internal copy.

        The original melody data is never modified.
        """

        for position, event in enumerate(
            events,
            start=1,
        ):

            if not isinstance(
                event,
                dict,
            ):

                raise ValueError(
                    f"Invalid melody event at position {position}."
                )

            self._validate_time_range(
                event.get(
                    "start_time"
                ),
                event.get(
                    "end_time"
                ),
                f"Melody event {position}",
            )

    # ============================================================
    # Temporal Overlap
    # ============================================================

    @staticmethod
    def _overlap(
        lyric_start: float,
        lyric_end: float,
        melody_start: float,
        melody_end: float,
    ) -> float:

        start = max(
            lyric_start,
            melody_start,
        )

        end = min(
            lyric_end,
            melody_end,
        )

        return max(
            0.0,
            end - start,
        )

    @staticmethod
    def _overlap_ratio(
        overlap: float,
        duration: float,
    ) -> float:

        if duration <= 0:

            return 0.0

        return (
            overlap
            / duration
        )

    # ============================================================
    # Melody Event Match
    # ============================================================

    def _match_event(
        self,
        lyric_start: float,
        lyric_end: float,
        event: Dict[str, Any],
    ) -> Dict[str, Any] | None:

        melody_start = float(
            event["start_time"]
        )

        melody_end = float(
            event["end_time"]
        )

        overlap = self._overlap(
            lyric_start,
            lyric_end,
            melody_start,
            melody_end,
        )

        if overlap <= 0:

            return None

        lyric_duration = (
            lyric_end
            - lyric_start
        )

        event_duration = (
            melody_end
            - melody_start
        )

        lyric_overlap_ratio = (
            self._overlap_ratio(
                overlap,
                lyric_duration,
            )
        )

        event_overlap_ratio = (
            self._overlap_ratio(
                overlap,
                event_duration,
            )
        )

        if (
            lyric_overlap_ratio
            < self.minimum_overlap_ratio
        ):

            return None

        return {
            "event_index": event.get(
                "event_index"
            ),
            "start_time": melody_start,
            "end_time": melody_end,
            "duration": round(
                event_duration,
                6,
            ),
            "overlap": round(
                overlap,
                6,
            ),
            "lyric_overlap_ratio": round(
                lyric_overlap_ratio,
                6,
            ),
            "event_overlap_ratio": round(
                event_overlap_ratio,
                6,
            ),
            "note_name": event.get(
                "note_name"
            ),
            "midi_note": event.get(
                "midi_note"
            ),
            "midi_mean": event.get(
                "midi_mean"
            ),
            "f0_mean_hz": event.get(
                "f0_mean_hz"
            ),
            "confidence": event.get(
                "confidence"
            ),
        }

    # ============================================================
    # Single Word Alignment
    # ============================================================

    def align_word(
        self,
        word: Dict[str, Any],
        melody_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        start_time = float(
            word["start_time"]
        )

        end_time = float(
            word["end_time"]
        )

        text = word.get(
            "final_text"
        )

        if text is None:

            text = word.get(
                "text",
                "",
            )

        text = str(
            text
        )

        matched_events: List[
            Dict[str, Any]
        ] = []

        for event in melody_events:

            match = self._match_event(
                start_time,
                end_time,
                event,
            )

            if match is None:
                continue

            matched_events.append(
                match
            )

        matched_events.sort(
            key=lambda item: (
                item["start_time"],
                (
                    item["event_index"]
                    if item["event_index"]
                    is not None
                    else 0
                ),
            )
        )

        notes = [
            item["note_name"]
            for item in matched_events
            if item.get(
                "note_name"
            )
            is not None
        ]

        midi_notes = [
            item["midi_note"]
            for item in matched_events
            if item.get(
                "midi_note"
            )
            is not None
        ]

        if matched_events:

            alignment_status = (
                "ALIGNED"
            )

        else:

            alignment_status = (
                "NO_MELODY_OVERLAP"
            )

        return {
            "word_index": word.get(
                "index"
            ),
            "text": text,
            "original_text": word.get(
                "original_text",
                text,
            ),
            "final_text": text,
            "start_time": start_time,
            "end_time": end_time,
            "duration": round(
                end_time
                - start_time,
                6,
            ),
            "alignment_status": (
                alignment_status
            ),
            "melody_event_count": len(
                matched_events
            ),
            "notes": notes,
            "midi_notes": midi_notes,
            "melody_events": matched_events,
        }

    # ============================================================
    # Full Alignment
    # ============================================================

    def align(
        self,
        lyrics_data: Dict[str, Any],
        melody_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        words = self._extract_lyrics(
            lyrics_data
        )

        events = self._extract_melody(
            melody_data
        )

        # --------------------------------------------------------
        # Validate the source data first.
        # --------------------------------------------------------

        self._validate_lyrics(
            words
        )

        self._validate_melody(
            events
        )

        # --------------------------------------------------------
        # IMPORTANT:
        # Work on a sorted COPY.
        #
        # The original melody list is never modified.
        # This allows Alignment to handle source files whose
        # events are not already chronologically ordered.
        # --------------------------------------------------------

        events = sorted(
            events,
            key=lambda event: (
                float(
                    event["start_time"]
                ),
                float(
                    event["end_time"]
                ),
                (
                    event.get(
                        "event_index"
                    )
                    if event.get(
                        "event_index"
                    )
                    is not None
                    else 0
                ),
            ),
        )

        aligned_words: List[
            Dict[str, Any]
        ] = []

        for word in words:

            aligned = self.align_word(
                word,
                events,
            )

            aligned_words.append(
                aligned
            )

        aligned_count = sum(
            1
            for item in aligned_words
            if item["alignment_status"]
            == "ALIGNED"
        )

        unaligned_count = (
            len(aligned_words)
            - aligned_count
        )

        return {
            "version": self.VERSION,
            "source": (
                "LyricFinalization + MelodyAnalyzer"
            ),
            "no_auto_correction": True,
            "lyric_word_count": len(
                aligned_words
            ),
            "melody_event_count": len(
                events
            ),
            "aligned_word_count": (
                aligned_count
            ),
            "unaligned_word_count": (
                unaligned_count
            ),
            "alignment_coverage": round(
                (
                    aligned_count
                    / len(aligned_words)
                )
                if aligned_words
                else 0.0,
                6,
            ),
            "words": aligned_words,
        }

    # ============================================================
    # File Analysis
    # ============================================================

    def analyze_file(
        self,
        lyrics_path: str | Path,
        melody_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:

        lyrics_data = self.load_lyrics(
            lyrics_path
        )

        melody_data = self.load_melody(
            melody_path
        )

        result = self.align(
            lyrics_data,
            melody_data,
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