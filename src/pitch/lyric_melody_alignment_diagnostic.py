from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class LyricMelodyAlignmentDiagnostic:
    """
    PhoenixVoiceEngine
    Lyric–Melody Alignment Diagnostic V1.0

    Diagnostic-only component.

    It compares:
        1. Finalized lyric words
        2. Melody events
        3. Raw pitch frames

    It does NOT:
        - modify lyrics
        - modify lyric timing
        - modify melody events
        - modify pitch data
        - invent notes
        - perform automatic correction
        - change alignment results

    Its purpose is to explain why a lyric word may have
    NO_MELODY_OVERLAP.

    Diagnostic classifications:

        ALIGNED
        TRUE_NO_MELODY
        POSSIBLE_PITCH_GAP
        POSSIBLE_BOUNDARY_MISMATCH
        NO_NEARBY_MELODY
    """

    VERSION = "1.0.0"

    DEFAULT_NEARBY_THRESHOLD = 0.25
    DEFAULT_PITCH_COVERAGE_THRESHOLD = 0.10

    def __init__(
        self,
        nearby_threshold: float = DEFAULT_NEARBY_THRESHOLD,
        pitch_coverage_threshold: float = (
            DEFAULT_PITCH_COVERAGE_THRESHOLD
        ),
    ) -> None:

        if nearby_threshold < 0:
            raise ValueError(
                "nearby_threshold cannot be negative."
            )

        if not 0.0 <= pitch_coverage_threshold <= 1.0:
            raise ValueError(
                "pitch_coverage_threshold must be between 0 and 1."
            )

        self.nearby_threshold = float(
            nearby_threshold
        )

        self.pitch_coverage_threshold = float(
            pitch_coverage_threshold
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

    # ============================================================
    # Extraction
    # ============================================================

    def _extract_words(
        self,
        lyrics_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        words = lyrics_data.get(
            "words"
        )

        if isinstance(
            words,
            list,
        ):
            return words

        items = lyrics_data.get(
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

    def _extract_events(
        self,
        melody_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        melody = melody_data.get(
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
                "Melody data must contain melody.events."
            )

        return events

    def _extract_pitch_frames(
        self,
        pitch_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        pitch = pitch_data.get(
            "pitch"
        )

        if not isinstance(
            pitch,
            dict,
        ):
            raise ValueError(
                "Pitch data must contain a pitch object."
            )

        possible_keys = (
            "frames",
            "points",
            "contour",
            "data",
        )

        for key in possible_keys:

            frames = pitch.get(
                key
            )

            if isinstance(
                frames,
                list,
            ):
                return frames

        return []

    # ============================================================
    # Timing Helpers
    # ============================================================

    @staticmethod
    def _duration(
        start_time: float,
        end_time: float,
    ) -> float:

        return max(
            0.0,
            end_time - start_time,
        )

    @staticmethod
    def _overlap(
        start_a: float,
        end_a: float,
        start_b: float,
        end_b: float,
    ) -> float:

        start = max(
            start_a,
            start_b,
        )

        end = min(
            end_a,
            end_b,
        )

        return max(
            0.0,
            end - start,
        )

    @staticmethod
    def _distance_between_ranges(
        start_a: float,
        end_a: float,
        start_b: float,
        end_b: float,
    ) -> float:

        if end_a < start_b:
            return start_b - end_a

        if end_b < start_a:
            return start_a - end_b

        return 0.0

    # ============================================================
    # Nearest Melody
    # ============================================================

    def _nearest_previous_event(
        self,
        start_time: float,
        events: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:

        previous = None

        for event in events:

            try:
                end_time = float(
                    event["end_time"]
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            if end_time <= start_time:

                if (
                    previous is None
                    or end_time
                    > float(
                        previous["end_time"]
                    )
                ):
                    previous = event

        return previous

    def _nearest_next_event(
        self,
        end_time: float,
        events: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:

        following = None

        for event in events:

            try:
                start_time = float(
                    event["start_time"]
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            if start_time >= end_time:

                if (
                    following is None
                    or start_time
                    < float(
                        following["start_time"]
                    )
                ):
                    following = event

        return following

    # ============================================================
    # Pitch Frame Analysis
    # ============================================================

    def _frame_time(
        self,
        frame: Dict[str, Any],
    ) -> Optional[float]:

        possible_keys = (
            "time",
            "timestamp",
            "start_time",
        )

        for key in possible_keys:

            value = frame.get(
                key
            )

            if value is not None:

                try:
                    return float(
                        value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        return None

    def _frame_is_voiced(
        self,
        frame: Dict[str, Any],
    ) -> bool:

        for key in (
            "voiced",
            "is_voiced",
        ):

            if key in frame:
                return bool(
                    frame[key]
                )

        for key in (
            "f0_hz",
            "f0",
            "frequency",
            "frequency_hz",
        ):

            value = frame.get(
                key
            )

            if value is None:
                continue

            try:

                return float(
                    value
                ) > 0.0

            except (
                TypeError,
                ValueError,
            ):
                return False

        return False

    def _pitch_inside_word(
        self,
        start_time: float,
        end_time: float,
        pitch_frames: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        duration = self._duration(
            start_time,
            end_time,
        )

        if duration <= 0:
            return {
                "frame_count": 0,
                "voiced_frame_count": 0,
                "voiced_ratio": 0.0,
                "pitch_coverage": 0.0,
                "status": "INVALID_DURATION",
            }

        times = []

        for frame in pitch_frames:

            time = self._frame_time(
                frame
            )

            if time is None:
                continue

            if (
                start_time
                <= time
                <= end_time
            ):
                times.append(
                    (
                        time,
                        self._frame_is_voiced(
                            frame
                        ),
                    )
                )

        frame_count = len(
            times
        )

        voiced_frame_count = sum(
            1
            for _, voiced in times
            if voiced
        )

        if frame_count == 0:

            return {
                "frame_count": 0,
                "voiced_frame_count": 0,
                "voiced_ratio": 0.0,
                "pitch_coverage": 0.0,
                "status": "NO_PITCH_FRAMES",
            }

        voiced_ratio = (
            voiced_frame_count
            / frame_count
        )

        # The diagnostic deliberately does not invent a
        # continuous pitch region. It only reports observed
        # frame coverage.

        pitch_coverage = (
            voiced_ratio
        )

        if (
            pitch_coverage
            >= self.pitch_coverage_threshold
        ):

            status = "PITCH_PRESENT"

        else:

            status = "LOW_PITCH_COVERAGE"

        return {
            "frame_count": frame_count,
            "voiced_frame_count": (
                voiced_frame_count
            ),
            "voiced_ratio": round(
                voiced_ratio,
                6,
            ),
            "pitch_coverage": round(
                pitch_coverage,
                6,
            ),
            "status": status,
        }

    # ============================================================
    # Word Diagnostic
    # ============================================================

    def diagnose_word(
        self,
        word: Dict[str, Any],
        events: List[Dict[str, Any]],
        pitch_frames: List[Dict[str, Any]],
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

        # --------------------------------------------------------
        # Direct melody overlap
        # --------------------------------------------------------

        overlapping_events = []

        for event in events:

            try:

                event_start = float(
                    event["start_time"]
                )

                event_end = float(
                    event["end_time"]
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                continue

            overlap = self._overlap(
                start_time,
                end_time,
                event_start,
                event_end,
            )

            if overlap > 0:

                overlapping_events.append(
                    {
                        "event_index": event.get(
                            "event_index"
                        ),
                        "start_time": event_start,
                        "end_time": event_end,
                        "overlap": round(
                            overlap,
                            6,
                        ),
                        "note_name": event.get(
                            "note_name"
                        ),
                        "midi_note": event.get(
                            "midi_note"
                        ),
                        "f0_mean_hz": event.get(
                            "f0_mean_hz"
                        ),
                    }
                )

        # --------------------------------------------------------
        # Pitch analysis
        # --------------------------------------------------------

        pitch_result = (
            self._pitch_inside_word(
                start_time,
                end_time,
                pitch_frames,
            )
        )

        # --------------------------------------------------------
        # Nearest events
        # --------------------------------------------------------

        previous = (
            self._nearest_previous_event(
                start_time,
                events,
            )
        )

        following = (
            self._nearest_next_event(
                end_time,
                events,
            )
        )

        previous_info = None

        if previous is not None:

            previous_end = float(
                previous["end_time"]
            )

            previous_info = {
                "event_index": previous.get(
                    "event_index"
                ),
                "start_time": float(
                    previous["start_time"]
                ),
                "end_time": previous_end,
                "gap_before_word": round(
                    start_time
                    - previous_end,
                    6,
                ),
                "note_name": previous.get(
                    "note_name"
                ),
                "midi_note": previous.get(
                    "midi_note"
                ),
            }

        next_info = None

        if following is not None:

            next_start = float(
                following["start_time"]
            )

            next_info = {
                "event_index": following.get(
                    "event_index"
                ),
                "start_time": next_start,
                "end_time": float(
                    following["end_time"]
                ),
                "gap_after_word": round(
                    next_start
                    - end_time,
                    6,
                ),
                "note_name": following.get(
                    "note_name"
                ),
                "midi_note": following.get(
                    "midi_note"
                ),
            }

        # --------------------------------------------------------
        # Classification
        # --------------------------------------------------------

        if overlapping_events:

            classification = "ALIGNED"

            reason = (
                "Melody event overlaps the lyric word."
            )

        else:

            previous_gap = (
                previous_info[
                    "gap_before_word"
                ]
                if previous_info is not None
                else None
            )

            next_gap = (
                next_info[
                    "gap_after_word"
                ]
                if next_info is not None
                else None
            )

            nearby_previous = (
                previous_gap is not None
                and previous_gap
                <= self.nearby_threshold
            )

            nearby_next = (
                next_gap is not None
                and next_gap
                <= self.nearby_threshold
            )

            pitch_present = (
                pitch_result[
                    "status"
                ]
                == "PITCH_PRESENT"
            )

            if pitch_present:

                classification = (
                    "POSSIBLE_PITCH_GAP"
                )

                reason = (
                    "Voiced pitch frames exist inside "
                    "the lyric interval, but no melody "
                    "event overlaps it."
                )

            elif (
                nearby_previous
                or nearby_next
            ):

                classification = (
                    "POSSIBLE_BOUNDARY_MISMATCH"
                )

                reason = (
                    "A nearby melody event exists outside "
                    "the lyric boundaries."
                )

            elif (
                pitch_result["status"]
                in {
                    "NO_PITCH_FRAMES",
                    "LOW_PITCH_COVERAGE",
                }
            ):

                classification = (
                    "TRUE_NO_MELODY"
                )

                reason = (
                    "No overlapping melody event and no "
                    "significant voiced pitch evidence "
                    "inside the lyric interval."
                )

            else:

                classification = (
                    "NO_NEARBY_MELODY"
                )

                reason = (
                    "No overlapping or nearby melody event "
                    "was found."
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
                end_time - start_time,
                6,
            ),
            "classification": classification,
            "reason": reason,
            "overlapping_event_count": len(
                overlapping_events
            ),
            "overlapping_events": (
                overlapping_events
            ),
            "previous_event": previous_info,
            "next_event": next_info,
            "pitch": pitch_result,
        }

    # ============================================================
    # Full Diagnostic
    # ============================================================

    def diagnose(
        self,
        lyrics_data: Dict[str, Any],
        melody_data: Dict[str, Any],
        pitch_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        words = self._extract_words(
            lyrics_data
        )

        events = self._extract_events(
            melody_data
        )

        pitch_frames = (
            self._extract_pitch_frames(
                pitch_data
            )
        )

        results = []

        for word in words:

            result = self.diagnose_word(
                word,
                events,
                pitch_frames,
            )

            results.append(
                result
            )

        counts = {
            "ALIGNED": 0,
            "TRUE_NO_MELODY": 0,
            "POSSIBLE_PITCH_GAP": 0,
            "POSSIBLE_BOUNDARY_MISMATCH": 0,
            "NO_NEARBY_MELODY": 0,
        }

        for result in results:

            classification = result[
                "classification"
            ]

            if classification in counts:

                counts[
                    classification
                ] += 1

        return {
            "version": self.VERSION,
            "source": (
                "FinalLyrics + Melody + Pitch"
            ),
            "no_auto_correction": True,
            "lyric_word_count": len(
                words
            ),
            "melody_event_count": len(
                events
            ),
            "pitch_frame_count": len(
                pitch_frames
            ),
            "diagnostic_count": len(
                results
            ),
            "classification_counts": counts,
            "settings": {
                "nearby_threshold": (
                    self.nearby_threshold
                ),
                "pitch_coverage_threshold": (
                    self.pitch_coverage_threshold
                ),
            },
            "words": results,
        }

    # ============================================================
    # File Analysis
    # ============================================================

    def analyze_file(
        self,
        lyrics_path: str | Path,
        melody_path: str | Path,
        pitch_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:

        lyrics_data = self._load_json(
            lyrics_path
        )

        melody_data = self._load_json(
            melody_path
        )

        pitch_data = self._load_json(
            pitch_path
        )

        result = self.diagnose(
            lyrics_data,
            melody_data,
            pitch_data,
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