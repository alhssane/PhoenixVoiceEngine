"""
PhoenixVoiceEngine - Lyric Human Review Session V1.0

Human-controlled review session for lyric candidates.

Responsibilities:
- Load a Lyric Review Queue.
- Track the current review item.
- Navigate next/previous.
- Record explicit human decisions.
- Preserve original lyrics.
- Allow candidate acceptance.
- Allow custom correction.
- Allow skipping.
- Save review session state.
- Build final lyrics without modifying source files.

IMPORTANT:
This module never performs automatic lyric correction.
Every modification requires an explicit human decision.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


class LyricReviewSession:
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

    def __init__(
        self,
        review_queue: Dict[str, Any],
    ) -> None:
        if not isinstance(review_queue, dict):
            raise TypeError(
                "review_queue must be a dictionary."
            )

        self.source_queue = deepcopy(
            review_queue
        )

        self.queue: List[Dict[str, Any]] = deepcopy(
            review_queue.get(
                "queue",
                [],
            )
        )

        self.queue_count = len(
            self.queue
        )

        self.current_index = 0

        self.decisions: Dict[
            int,
            Dict[str, Any],
        ] = {}

        self.session_version = self.VERSION

    # =========================================================
    # Session information
    # =========================================================

    @property
    def current_item(
        self,
    ) -> Optional[Dict[str, Any]]:
        if not self.queue:
            return None

        if (
            self.current_index < 0
            or self.current_index >= self.queue_count
        ):
            return None

        return self.queue[
            self.current_index
        ]

    @property
    def current_position(
        self,
    ) -> int:
        if not self.queue:
            return 0

        return self.current_index + 1

    @property
    def reviewed_count(
        self,
    ) -> int:
        return len(
            self.decisions
        )

    @property
    def pending_count(
        self,
    ) -> int:
        return max(
            0,
            self.queue_count
            - self.reviewed_count,
        )

    @property
    def completed(
        self,
    ) -> bool:
        return (
            self.queue_count > 0
            and self.pending_count == 0
        )

    # =========================================================
    # Validation
    # =========================================================

    def _require_current_item(
        self,
    ) -> Dict[str, Any]:
        item = self.current_item

        if item is None:
            raise RuntimeError(
                "There is no current review item."
            )

        return item

    def _validate_word_index(
        self,
        word_index: int,
    ) -> int:
        try:
            word_index = int(
                word_index
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "word_index must be an integer."
            ) from exc

        if word_index < 0:
            raise ValueError(
                "word_index must be >= 0."
            )

        return word_index

    # =========================================================
    # Navigation
    # =========================================================

    def next(
        self,
    ) -> Optional[Dict[str, Any]]:
        """
        Move to the next queue item.

        Does not create a decision.
        """

        if not self.queue:
            return None

        if (
            self.current_index
            < self.queue_count - 1
        ):
            self.current_index += 1

        return self.current_item

    def previous(
        self,
    ) -> Optional[Dict[str, Any]]:
        """
        Move to the previous queue item.

        Does not create a decision.
        """

        if not self.queue:
            return None

        if self.current_index > 0:
            self.current_index -= 1

        return self.current_item

    def goto(
        self,
        position: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Move to a 1-based queue position.
        """

        try:
            position = int(
                position
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "position must be an integer."
            ) from exc

        if not self.queue:
            return None

        if (
            position < 1
            or position > self.queue_count
        ):
            raise IndexError(
                "Queue position out of range."
            )

        self.current_index = (
            position - 1
        )

        return self.current_item

    # =========================================================
    # Decision helpers
    # =========================================================

    def _record_decision(
        self,
        decision: str,
        final_text: str,
        *,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:

        decision = str(
            decision
        ).strip().upper()

        if decision not in self.VALID_DECISIONS:
            raise ValueError(
                f"Invalid decision: {decision}"
            )

        item = self._require_current_item()

        original_text = str(
            item.get(
                "original_text",
                "",
            )
        ).strip()

        final_text = str(
            final_text
        ).strip()

        if not final_text:
            raise ValueError(
                "final_text cannot be empty."
            )

        # -----------------------------------------------------
        # Original protection
        # -----------------------------------------------------
        #
        # KEEP_ORIGINAL must preserve the exact
        # original text.
        #
        if decision == self.KEEP_ORIGINAL:
            final_text = original_text

        # -----------------------------------------------------
        # Candidate acceptance
        # -----------------------------------------------------
        #
        # The selected candidate must actually
        # exist in the queue item's candidates.
        #
        if decision == self.ACCEPT_CANDIDATE:

            candidates = item.get(
                "candidate_texts",
                [],
            )

            if not candidates:
                candidates = [
                    item.get(
                        "candidate_text",
                        "",
                    )
                ]

            normalized_candidates = {
                str(x).strip()
                for x in candidates
            }

            if final_text not in normalized_candidates:
                raise ValueError(
                    "Candidate text is not present "
                    "in the review item."
                )

        # -----------------------------------------------------
        # Custom correction
        # -----------------------------------------------------
        #
        # Human explicitly provides the final word.
        #
        if decision == self.CUSTOM_CORRECTION:
            if not final_text:
                raise ValueError(
                    "Custom correction cannot be empty."
                )

        word_index = self._validate_word_index(
            item.get(
                "word_index",
                0,
            )
        )

        record = {
            "word_index": word_index,
            "queue_position": item.get(
                "queue_position"
            ),
            "original_text": original_text,
            "candidate_text": item.get(
                "candidate_text"
            ),
            "final_text": final_text,
            "decision": decision,
            "note": note,
            "priority": item.get(
                "priority"
            ),
            "margin_vs_original": item.get(
                "margin_vs_original"
            ),
            "independent_support_count": item.get(
                "independent_support_count"
            ),
            "start_time": item.get(
                "start_time"
            ),
            "end_time": item.get(
                "end_time"
            ),
            "status": (
                "REVIEWED"
                if decision != self.SKIP
                else "SKIPPED"
            ),
        }

        self.decisions[
            word_index
        ] = record

        return deepcopy(
            record
        )

    # =========================================================
    # Public decisions
    # =========================================================

    def keep_original(
        self,
        *,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        item = self._require_current_item()

        return self._record_decision(
            self.KEEP_ORIGINAL,
            str(
                item.get(
                    "original_text",
                    "",
                )
            ).strip(),
            note=note,
        )

    def accept_candidate(
        self,
        candidate_text: Optional[str] = None,
        *,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:

        item = self._require_current_item()

        if candidate_text is None:
            candidate_text = str(
                item.get(
                    "candidate_text",
                    "",
                )
            ).strip()

        return self._record_decision(
            self.ACCEPT_CANDIDATE,
            candidate_text,
            note=note,
        )

    def custom_correction(
        self,
        text: str,
        *,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:

        return self._record_decision(
            self.CUSTOM_CORRECTION,
            text,
            note=note,
        )

    def skip(
        self,
        *,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:

        item = self._require_current_item()

        # SKIP never changes the lyric.
        original_text = str(
            item.get(
                "original_text",
                "",
            )
        ).strip()

        return self._record_decision(
            self.SKIP,
            original_text,
            note=note,
        )

    # =========================================================
    # Decision lookup
    # =========================================================

    def get_decision(
        self,
        word_index: int,
    ) -> Optional[Dict[str, Any]]:

        word_index = self._validate_word_index(
            word_index
        )

        decision = self.decisions.get(
            word_index
        )

        if decision is None:
            return None

        return deepcopy(
            decision
        )

    # =========================================================
    # Statistics
    # =========================================================

    def statistics(
        self,
    ) -> Dict[str, Any]:

        counts = {
            self.KEEP_ORIGINAL: 0,
            self.ACCEPT_CANDIDATE: 0,
            self.CUSTOM_CORRECTION: 0,
            self.SKIP: 0,
        }

        for decision in self.decisions.values():
            action = decision[
                "decision"
            ]

            if action in counts:
                counts[action] += 1

        return {
            "queue_count": self.queue_count,
            "reviewed_count": self.reviewed_count,
            "pending_count": self.pending_count,
            "completed": self.completed,
            "decision_counts": counts,
            "current_position": (
                self.current_position
            ),
        }

    # =========================================================
    # Session serialization
    # =========================================================

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "engine": (
                "LyricReviewSession"
            ),
            "version": self.VERSION,
            "mode": (
                "human_review_only"
            ),
            "no_auto_correction": True,
            "queue_count": self.queue_count,
            "current_position": (
                self.current_position
            ),
            "current_index": (
                self.current_index
            ),
            "reviewed_count": (
                self.reviewed_count
            ),
            "pending_count": (
                self.pending_count
            ),
            "completed": (
                self.completed
            ),
            "statistics": self.statistics(),
            "decisions": list(
                self.decisions.values()
            ),
        }

    # =========================================================
    # Save / Load Session
    # =========================================================

    def save(
        self,
        output_json: str,
    ) -> Dict[str, Any]:

        path = Path(
            output_json
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = self.to_dict()

        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return data

    # =========================================================
    # Final lyrics
    # =========================================================

    def build_final_lyrics(
        self,
    ) -> Dict[str, Any]:

        if not self.completed:
            raise RuntimeError(
                "Review session is not complete. "
                "All queue items must be reviewed "
                "before building final lyrics."
            )

        final_words: List[
            Dict[str, Any]
        ] = []

        # -----------------------------------------------------
        # Preserve original queue order.
        # -----------------------------------------------------

        for item in self.queue:

            word_index = self._validate_word_index(
                item.get(
                    "word_index",
                    0,
                )
            )

            original_text = str(
                item.get(
                    "original_text",
                    "",
                )
            ).strip()

            decision = self.decisions.get(
                word_index
            )

            if decision is None:
                raise RuntimeError(
                    f"Missing decision for "
                    f"word index {word_index}."
                )

            final_text = str(
                decision.get(
                    "final_text",
                    original_text,
                )
            ).strip()

            final_words.append(
                {
                    "word_index": word_index,
                    "original_text": original_text,
                    "final_text": final_text,
                    "decision": decision[
                        "decision"
                    ],
                    "start_time": item.get(
                        "start_time"
                    ),
                    "end_time": item.get(
                        "end_time"
                    ),
                }
            )

        # -----------------------------------------------------
        # Final output
        # -----------------------------------------------------

        return {
            "engine": (
                "LyricReviewSession"
            ),
            "version": self.VERSION,
            "mode": (
                "human_review_finalization"
            ),
            "no_auto_correction": True,
            "word_count": len(
                final_words
            ),
            "words": final_words,
        }

    def save_final_lyrics(
        self,
        output_json: str,
    ) -> Dict[str, Any]:

        result = self.build_final_lyrics()

        path = Path(
            output_json
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return result

    # =========================================================
    # Factory
    # =========================================================

    @classmethod
    def from_file(
        cls,
        queue_json: str,
    ) -> "LyricReviewSession":

        path = Path(
            queue_json
        )

        if not path.is_file():
            raise FileNotFoundError(
                f"Review queue not found: "
                f"{queue_json}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        return cls(data)