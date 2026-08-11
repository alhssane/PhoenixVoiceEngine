from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class LyricFinalizer:
    """
    PhoenixVoiceEngine
    Lyric Finalization & Export V1.0

    Converts human review decisions into final lyrics.

    Supports two modes:

    1. Legacy V1.0 queue mode
       - Used by the original unit tests.
       - Finalizes the reviewed queue items only.

    2. Full Lyrics mode
       - Uses the original complete lyrics document.
       - Applies human decisions by word_index.
       - Preserves all unreviewed words.
       - Preserves original timing and metadata.
       - Produces the complete final lyric document.

    IMPORTANT:
    This class never performs automatic lyric correction.
    Only explicit human review decisions are applied.
    """

    VERSION = "1.0.0"

    KEEP_ORIGINAL = "KEEP_ORIGINAL"
    ACCEPT_CANDIDATE = "ACCEPT_CANDIDATE"
    CUSTOM_CORRECTION = "CUSTOM_CORRECTION"
    SKIP = "SKIP"

    VALID_DECISIONS = {
        KEEP_ORIGINAL,
        ACCEPT_CANDIDATE,
        CUSTOM_CORRECTION,
        SKIP,
    }

    def __init__(self) -> None:
        pass

    # ================================================================
    # Loading
    # ================================================================

    def load_session(
        self,
        session_path: str | Path,
    ) -> Dict[str, Any]:
        path = Path(session_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Review session not found: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(
                "Review session must be a dictionary."
            )

        return data

    def load_lyrics(
        self,
        lyrics_path: str | Path,
    ) -> Dict[str, Any]:
        path = Path(lyrics_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Lyrics file not found: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(
                "Lyrics document must be a dictionary."
            )

        words = data.get("words")

        if not isinstance(words, list):
            raise ValueError(
                "Lyrics document must contain a words list."
            )

        if not words:
            raise ValueError(
                "Lyrics words list is empty."
            )

        return data

    # ================================================================
    # Session Validation
    # ================================================================

    def validate_session(
        self,
        session: Dict[str, Any],
    ) -> None:
        if not isinstance(session, dict):
            raise ValueError(
                "Session must be a dictionary."
            )

        decisions = session.get("decisions")
        queue = session.get("queue")

        # ============================================================
        # NEW HUMAN REVIEW SESSION FORMAT
        # ============================================================

        if decisions is not None:
            if not isinstance(decisions, list):
                raise ValueError(
                    "Session decisions must be a list."
                )

            for index, item in enumerate(decisions):
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Invalid decision at index {index}."
                    )

                decision = item.get("decision")

                if decision not in self.VALID_DECISIONS:
                    raise ValueError(
                        f"Invalid or missing review decision "
                        f"at index {index}: {decision!r}"
                    )

                word_index = item.get("word_index")

                if word_index is None:
                    raise ValueError(
                        f"Missing word_index at decision "
                        f"index {index}."
                    )

                try:
                    int(word_index)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"Invalid word_index at decision "
                        f"index {index}: {word_index!r}"
                    )

                if decision == self.ACCEPT_CANDIDATE:
                    candidate = item.get(
                        "candidate_text"
                    )

                    if candidate is None:
                        candidate = item.get(
                            "accepted_candidate"
                        )

                    if candidate is None:
                        raise ValueError(
                            "ACCEPT_CANDIDATE requires "
                            "candidate_text."
                        )

                    if not str(candidate).strip():
                        raise ValueError(
                            "ACCEPT_CANDIDATE requires "
                            "a non-empty candidate."
                        )

                if decision == self.CUSTOM_CORRECTION:
                    correction = item.get(
                        "final_text"
                    )

                    if correction is None:
                        correction = item.get(
                            "custom_correction"
                        )

                    if correction is None:
                        correction = item.get(
                            "correction"
                        )

                    if correction is None:
                        raise ValueError(
                            "CUSTOM_CORRECTION requires "
                            "a correction value."
                        )

                    if not str(correction).strip():
                        raise ValueError(
                            "CUSTOM_CORRECTION requires "
                            "a non-empty correction."
                        )

            return

        # ============================================================
        # LEGACY V1.0 QUEUE FORMAT
        # ============================================================

        if queue is not None:
            if not isinstance(queue, list):
                raise ValueError(
                    "Session queue must be a list."
                )

            if not queue:
                raise ValueError(
                    "Review session queue is empty."
                )

            for index, item in enumerate(queue):
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Invalid review item at index {index}."
                    )

                decision = item.get(
                    "review_decision"
                )

                if decision is None:
                    decision = item.get(
                        "decision"
                    )

                if decision not in self.VALID_DECISIONS:
                    raise ValueError(
                        f"Invalid or missing review decision "
                        f"at index {index}: {decision!r}"
                    )

            return

        raise ValueError(
            "Session must contain either "
            "decisions or queue."
        )

    # ================================================================
    # Lyrics Validation
    # ================================================================

    def validate_lyrics(
        self,
        lyrics: Dict[str, Any],
    ) -> None:
        if not isinstance(lyrics, dict):
            raise ValueError(
                "Lyrics must be a dictionary."
            )

        words = lyrics.get("words")

        if not isinstance(words, list):
            raise ValueError(
                "Lyrics must contain a words list."
            )

        if not words:
            raise ValueError(
                "Lyrics words list cannot be empty."
            )

        expected_index = 1

        for position, word in enumerate(words):
            if not isinstance(word, dict):
                raise ValueError(
                    f"Invalid lyric word at position "
                    f"{position}."
                )

            if "text" not in word:
                raise ValueError(
                    f"Missing text at lyric position "
                    f"{position}."
                )

            index = word.get("index")

            if index is None:
                raise ValueError(
                    f"Missing index at lyric position "
                    f"{position}."
                )

            try:
                index = int(index)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Invalid lyric index at position "
                    f"{position}: {index!r}"
                )

            if index != expected_index:
                raise ValueError(
                    "Lyric word indices must be sequential. "
                    f"Expected {expected_index}, got {index}."
                )

            expected_index += 1

    # ================================================================
    # Decision Map
    # ================================================================

    def _build_decision_map(
        self,
        session: Dict[str, Any],
    ) -> Dict[int, Dict[str, Any]]:
        decisions = session.get(
            "decisions",
            [],
        )

        if not isinstance(decisions, list):
            raise ValueError(
                "Session decisions must be a list."
            )

        result: Dict[int, Dict[str, Any]] = {}

        for item in decisions:
            word_index = int(
                item["word_index"]
            )

            if word_index in result:
                raise ValueError(
                    f"Duplicate human decision "
                    f"for word_index {word_index}."
                )

            result[word_index] = item

        return result

    # ================================================================
    # Resolve Final Text
    # ================================================================

    def _resolve_text(
        self,
        original: str,
        item: Dict[str, Any],
    ) -> Tuple[str, str]:
        decision = item.get(
            "review_decision"
        )

        if decision is None:
            decision = item.get(
                "decision"
            )

        if decision == self.KEEP_ORIGINAL:
            return original, decision

        if decision == self.SKIP:
            return original, decision

        if decision == self.ACCEPT_CANDIDATE:
            candidate = item.get(
                "accepted_candidate"
            )

            if candidate is None:
                candidate = item.get(
                    "candidate_text"
                )

            if candidate is None:
                raise ValueError(
                    "ACCEPT_CANDIDATE requires "
                    "an accepted candidate."
                )

            candidate = str(
                candidate
            ).strip()

            if not candidate:
                raise ValueError(
                    "ACCEPT_CANDIDATE candidate "
                    "cannot be empty."
                )

            return candidate, decision

        if decision == self.CUSTOM_CORRECTION:
            correction = item.get(
                "custom_correction"
            )

            if correction is None:
                correction = item.get(
                    "correction"
                )

            if correction is None:
                correction = item.get(
                    "final_text"
                )

            if correction is None:
                raise ValueError(
                    "CUSTOM_CORRECTION requires "
                    "a correction value."
                )

            correction = str(
                correction
            ).strip()

            if not correction:
                raise ValueError(
                    "CUSTOM_CORRECTION correction "
                    "cannot be empty."
                )

            return correction, decision

        raise ValueError(
            f"Unsupported review decision: {decision}"
        )

    # ================================================================
    # Build Final Word
    # ================================================================

    def _build_final_word(
        self,
        original_word: Dict[str, Any],
        decision_item: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        original_text = str(
            original_word.get(
                "text",
                "",
            )
        )

        if decision_item is None:
            final_text = original_text
            decision = self.KEEP_ORIGINAL
            reviewed = False

        else:
            final_text, decision = self._resolve_text(
                original_text,
                decision_item,
            )
            reviewed = True

        # Start with the original word so ALL original
        # metadata and timing remain untouched.
        result = dict(
            original_word
        )

        result["original_text"] = original_text
        result["final_text"] = final_text
        result["decision"] = decision
        result["reviewed"] = reviewed

        if decision_item is not None:
            result["review_queue_position"] = (
                decision_item.get(
                    "queue_position"
                )
            )

            result["review_priority"] = (
                decision_item.get(
                    "priority"
                )
            )

            result["review_status"] = (
                decision_item.get(
                    "status",
                    "REVIEWED",
                )
            )

        return result

    # ================================================================
    # Legacy Queue Finalization
    # ================================================================

    def _finalize_queue(
        self,
        session: Dict[str, Any],
    ) -> Dict[str, Any]:
        queue = session.get("queue")

        if not isinstance(queue, list):
            raise ValueError(
                "Session must contain a queue list."
            )

        if not queue:
            raise ValueError(
                "Review session queue is empty."
            )

        items: List[Dict[str, Any]] = []

        for index, item in enumerate(queue):
            decision = item.get(
                "review_decision"
            )

            if decision is None:
                decision = item.get(
                    "decision"
                )

            if decision not in self.VALID_DECISIONS:
                raise ValueError(
                    f"Invalid or missing review "
                    f"decision at index {index}: "
                    f"{decision!r}"
                )

            original = str(
                item.get(
                    "original_text",
                    "",
                )
            )

            final_text, resolved_decision = (
                self._resolve_text(
                    original,
                    item,
                )
            )

            items.append(
                {
                    "position": index + 1,
                    "original_text": original,
                    "final_text": final_text,
                    "decision": resolved_decision,
                    "start_time": float(
                        item.get(
                            "start_time",
                            0.0,
                        )
                    ),
                    "end_time": float(
                        item.get(
                            "end_time",
                            0.0,
                        )
                    ),
                    "queue_position": item.get(
                        "queue_position",
                        index + 1,
                    ),
                }
            )

        return {
            "version": self.VERSION,
            "source": "LyricReviewSession",
            "review_session_version": session.get(
                "version"
            ),
            "item_count": len(items),
            "items": items,
            "no_auto_correction": True,
        }

    # ================================================================
    # Full Lyrics Finalization
    # ================================================================

    def _finalize_full_lyrics(
        self,
        session: Dict[str, Any],
        lyrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.validate_lyrics(
            lyrics
        )

        decision_map = self._build_decision_map(
            session
        )

        original_words = lyrics["words"]

        final_words: List[Dict[str, Any]] = []

        for original_word in original_words:
            word_index = int(
                original_word["index"]
            )

            decision_item = decision_map.get(
                word_index
            )

            final_word = self._build_final_word(
                original_word,
                decision_item,
            )

            final_words.append(
                final_word
            )

        reviewed_count = sum(
            1
            for item in final_words
            if item.get("reviewed") is True
        )

        unreviewed_count = (
            len(final_words)
            - reviewed_count
        )

        return {
            "version": self.VERSION,
            "source": "LyricReviewSession",
            "review_session_version": session.get(
                "version"
            ),
            "lyrics_source": lyrics.get(
                "file_name"
            ),
            "file_name": lyrics.get(
                "file_name"
            ),
            "duration": lyrics.get(
                "duration"
            ),
            "language": lyrics.get(
                "language"
            ),
            "language_probability": lyrics.get(
                "language_probability"
            ),
            "segment_count": lyrics.get(
                "segment_count"
            ),
            "word_count": len(
                final_words
            ),
            "reviewed_count": reviewed_count,
            "unreviewed_count": unreviewed_count,
            "no_auto_correction": True,
            "segments": lyrics.get(
                "segments",
                [],
            ),
            "words": final_words,
        }

    # ================================================================
    # Public Finalize
    # ================================================================

    def finalize(
        self,
        session: Dict[str, Any],
        lyrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Finalize reviewed lyrics.

        If lyrics is None:
            Legacy V1.0 queue behavior.

        If lyrics is supplied:
            Complete lyrics behavior.
        """

        self.validate_session(
            session
        )

        if lyrics is not None:
            return self._finalize_full_lyrics(
                session,
                lyrics,
            )

        return self._finalize_queue(
            session
        )

    # ================================================================
    # TXT Export
    # ================================================================

    def to_text(
        self,
        final_data: Dict[str, Any],
    ) -> str:
        words = final_data.get(
            "words"
        )

        if isinstance(words, list):
            parts: List[str] = []

            for item in words:
                text = str(
                    item.get(
                        "final_text",
                        item.get(
                            "text",
                            "",
                        ),
                    )
                ).strip()

                if text:
                    parts.append(
                        text
                    )

            return " ".join(
                parts
            )

        items = final_data.get(
            "items",
            [],
        )

        lines: List[str] = []

        for item in items:
            text = str(
                item.get(
                    "final_text",
                    "",
                )
            ).strip()

            if text:
                lines.append(
                    text
                )

        return "\n".join(
            lines
        )

    # ================================================================
    # SRT Time
    # ================================================================

    def _srt_time(
        self,
        seconds: float,
    ) -> str:
        milliseconds = int(
            round(seconds * 1000)
        )

        hours = (
            milliseconds
            // 3_600_000
        )

        milliseconds %= 3_600_000

        minutes = (
            milliseconds
            // 60_000
        )

        milliseconds %= 60_000

        secs = (
            milliseconds
            // 1_000
        )

        milliseconds %= 1_000

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d},"
            f"{milliseconds:03d}"
        )

    # ================================================================
    # VTT Time
    # ================================================================

    def _vtt_time(
        self,
        seconds: float,
    ) -> str:
        milliseconds = int(
            round(seconds * 1000)
        )

        hours = (
            milliseconds
            // 3_600_000
        )

        milliseconds %= 3_600_000

        minutes = (
            milliseconds
            // 60_000
        )

        milliseconds %= 60_000

        secs = (
            milliseconds
            // 1_000
        )

        milliseconds %= 1_000

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d}."
            f"{milliseconds:03d}"
        )

    # ================================================================
    # SRT Export
    # ================================================================

    def to_srt(
        self,
        final_data: Dict[str, Any],
    ) -> str:
        words = final_data.get(
            "words"
        )

        if isinstance(words, list):
            blocks: List[str] = []

            counter = 1

            for item in words:
                text = str(
                    item.get(
                        "final_text",
                        item.get(
                            "text",
                            "",
                        ),
                    )
                ).strip()

                if not text:
                    continue

                start = float(
                    item.get(
                        "start_time",
                        0.0,
                    )
                )

                end = float(
                    item.get(
                        "end_time",
                        0.0,
                    )
                )

                blocks.append(
                    f"{counter}\n"
                    f"{self._srt_time(start)} --> "
                    f"{self._srt_time(end)}\n"
                    f"{text}\n"
                )

                counter += 1

            return "\n".join(
                blocks
            )

        items = final_data.get(
            "items",
            [],
        )

        blocks = []

        for index, item in enumerate(
            items,
            start=1,
        ):
            text = str(
                item.get(
                    "final_text",
                    "",
                )
            ).strip()

            if not text:
                continue

            start = float(
                item.get(
                    "start_time",
                    0.0,
                )
            )

            end = float(
                item.get(
                    "end_time",
                    0.0,
                )
            )

            blocks.append(
                f"{index}\n"
                f"{self._srt_time(start)} --> "
                f"{self._srt_time(end)}\n"
                f"{text}\n"
            )

        return "\n".join(
            blocks
        )

    # ================================================================
    # VTT Export
    # ================================================================

    def to_vtt(
        self,
        final_data: Dict[str, Any],
    ) -> str:
        words = final_data.get(
            "words"
        )

        lines = [
            "WEBVTT",
            "",
        ]

        if isinstance(words, list):
            for item in words:
                text = str(
                    item.get(
                        "final_text",
                        item.get(
                            "text",
                            "",
                        ),
                    )
                ).strip()

                if not text:
                    continue

                start = float(
                    item.get(
                        "start_time",
                        0.0,
                    )
                )

                end = float(
                    item.get(
                        "end_time",
                        0.0,
                    )
                )

                lines.extend(
                    [
                        (
                            f"{self._vtt_time(start)} --> "
                            f"{self._vtt_time(end)}"
                        ),
                        text,
                        "",
                    ]
                )

            return "\n".join(
                lines
            )

        items = final_data.get(
            "items",
            [],
        )

        for item in items:
            text = str(
                item.get(
                    "final_text",
                    "",
                )
            ).strip()

            if not text:
                continue

            start = float(
                item.get(
                    "start_time",
                    0.0,
                )
            )

            end = float(
                item.get(
                    "end_time",
                    0.0,
                )
            )

            lines.extend(
                [
                    (
                        f"{self._vtt_time(start)} --> "
                        f"{self._vtt_time(end)}"
                    ),
                    text,
                    "",
                ]
            )

        return "\n".join(
            lines
        )

    # ================================================================
    # Export
    # ================================================================

    def export(
        self,
        session_path: str | Path,
        output_directory: str | Path,
        basename: str = "final_lyrics",
        lyrics_path: Optional[str | Path] = None,
    ) -> Dict[str, Any]:
        session = self.load_session(
            session_path
        )

        lyrics = None

        if lyrics_path is not None:
            lyrics = self.load_lyrics(
                lyrics_path
            )

        final_data = self.finalize(
            session,
            lyrics=lyrics,
        )

        output_dir = Path(
            output_directory
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_path = (
            output_dir
            / f"{basename}.json"
        )

        txt_path = (
            output_dir
            / f"{basename}.txt"
        )

        srt_path = (
            output_dir
            / f"{basename}.srt"
        )

        vtt_path = (
            output_dir
            / f"{basename}.vtt"
        )

        with json_path.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                final_data,
                f,
                ensure_ascii=False,
                indent=2,
            )

        txt_path.write_text(
            self.to_text(
                final_data
            ),
            encoding="utf-8",
        )

        srt_path.write_text(
            self.to_srt(
                final_data
            ),
            encoding="utf-8",
        )

        vtt_path.write_text(
            self.to_vtt(
                final_data
            ),
            encoding="utf-8",
        )

        return {
            "version": self.VERSION,
            "json": str(
                json_path
            ),
            "txt": str(
                txt_path
            ),
            "srt": str(
                srt_path
            ),
            "vtt": str(
                vtt_path
            ),
            "item_count": final_data.get(
                "word_count",
                final_data.get(
                    "item_count",
                    0,
                ),
            ),
        }