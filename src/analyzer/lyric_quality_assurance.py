from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class LyricQualityAssurance:
    """
    PhoenixVoiceEngine
    Lyric Quality Assurance V1.0

    Validates finalized lyrics without modifying them.

    Supports:

    1. Legacy V1.0 format:
       {
           "items": [...]
       }

    2. Full Final Lyrics format:
       {
           "words": [...]
       }

    IMPORTANT:
    This component NEVER performs automatic correction.
    It only detects and reports quality issues.
    """

    VERSION = "1.0.0"

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"

    def __init__(
        self,
        overlap_tolerance: float = 0.001,
        duplicate_threshold: int = 2,
    ) -> None:

        self.overlap_tolerance = float(
            overlap_tolerance
        )

        self.duplicate_threshold = int(
            duplicate_threshold
        )

    # ============================================================
    # Loading
    # ============================================================

    def load_final_lyrics(
        self,
        path: str | Path,
    ) -> Dict[str, Any]:

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Final lyrics not found:\n{path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "Final lyrics must be a dictionary."
            )

        return data

    # ============================================================
    # Helpers
    # ============================================================

    @staticmethod
    def _issue(
        severity: str,
        issue_type: str,
        message: str,
        position: int | None = None,
        **extra: Any,
    ) -> Dict[str, Any]:

        result = {
            "severity": severity,
            "type": issue_type,
            "message": message,
        }

        if position is not None:
            result["position"] = position

        result.update(extra)

        return result

    # ============================================================
    # Normalize Final Lyrics
    # ============================================================

    def _get_items(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        # --------------------------------------------------------
        # Legacy V1.0
        # --------------------------------------------------------

        items = data.get("items")

        if isinstance(items, list):
            return items

        # --------------------------------------------------------
        # Full Lyrics format
        # --------------------------------------------------------

        words = data.get("words")

        if isinstance(words, list):

            normalized: List[
                Dict[str, Any]
            ] = []

            for index, word in enumerate(
                words,
                start=1,
            ):

                if not isinstance(
                    word,
                    dict,
                ):
                    normalized.append(
                        {
                            "position": index,
                            "final_text": None,
                            "original_text": None,
                            "decision": None,
                        }
                    )

                    continue

                item = dict(word)

                # Full Finalizer format:
                #
                # text         = original/base text
                # final_text   = final reviewed text
                #
                # For older files that may only have "text",
                # use it as the final text.

                if "final_text" not in item:

                    item["final_text"] = item.get(
                        "text"
                    )

                if "original_text" not in item:

                    item["original_text"] = item.get(
                        "text"
                    )

                if "decision" not in item:

                    # Unreviewed words are intentionally
                    # preserved by the Finalizer.
                    #
                    # The Finalizer marks them as
                    # KEEP_ORIGINAL.

                    item["decision"] = (
                        "KEEP_ORIGINAL"
                    )

                # QA uses position for order checking.
                #
                # Do not modify the original JSON.
                item["position"] = index

                normalized.append(
                    item
                )

            return normalized

        return []

    # ============================================================
    # Structure
    # ============================================================

    def check_structure(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        issues: List[
            Dict[str, Any]
        ] = []

        items = data.get("items")
        words = data.get("words")

        # --------------------------------------------------------
        # Legacy V1.0 structure
        # --------------------------------------------------------

        if isinstance(items, list):

            if not items:

                issues.append(
                    self._issue(
                        self.FAIL,
                        "EMPTY_LYRICS",
                        "Final lyrics contain no items.",
                    )
                )

            return issues

        # --------------------------------------------------------
        # Full Lyrics structure
        # --------------------------------------------------------

        if isinstance(words, list):

            if not words:

                issues.append(
                    self._issue(
                        self.FAIL,
                        "EMPTY_LYRICS",
                        "Final lyrics contain no words.",
                    )
                )

            return issues

        # --------------------------------------------------------
        # Invalid structure
        # --------------------------------------------------------

        issues.append(
            self._issue(
                self.FAIL,
                "INVALID_STRUCTURE",
                "Final lyrics must contain an items list or words list.",
            )
        )

        return issues

    # ============================================================
    # Text Validation
    # ============================================================

    def check_text(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        issues: List[
            Dict[str, Any]
        ] = []

        for index, item in enumerate(
            items,
            start=1,
        ):

            text = item.get(
                "final_text"
            )

            if text is None:

                issues.append(
                    self._issue(
                        self.FAIL,
                        "MISSING_FINAL_TEXT",
                        "Final text is missing.",
                        index,
                    )
                )

                continue

            if not isinstance(
                text,
                str,
            ):

                issues.append(
                    self._issue(
                        self.FAIL,
                        "INVALID_FINAL_TEXT",
                        "Final text must be a string.",
                        index,
                    )
                )

                continue

            if not text.strip():

                issues.append(
                    self._issue(
                        self.WARNING,
                        "EMPTY_FINAL_TEXT",
                        "Final text is empty.",
                        index,
                    )
                )

        return issues

    # ============================================================
    # Timing Validation
    # ============================================================

    def check_timing(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        issues: List[
            Dict[str, Any]
        ] = []

        previous_end: float | None = None

        for index, item in enumerate(
            items,
            start=1,
        ):

            try:

                start = float(
                    item.get(
                        "start_time"
                    )
                )

                end = float(
                    item.get(
                        "end_time"
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                issues.append(
                    self._issue(
                        self.FAIL,
                        "INVALID_TIMING",
                        "Start/end time must be numeric.",
                        index,
                    )
                )

                continue

            if start < 0:

                issues.append(
                    self._issue(
                        self.FAIL,
                        "NEGATIVE_START_TIME",
                        "Start time cannot be negative.",
                        index,
                        start_time=start,
                    )
                )

            if end < 0:

                issues.append(
                    self._issue(
                        self.FAIL,
                        "NEGATIVE_END_TIME",
                        "End time cannot be negative.",
                        index,
                        end_time=end,
                    )
                )

            if end <= start:

                issues.append(
                    self._issue(
                        self.FAIL,
                        "INVALID_DURATION",
                        "End time must be greater than start time.",
                        index,
                        start_time=start,
                        end_time=end,
                    )
                )

            if previous_end is not None:

                overlap = (
                    previous_end - start
                )

                if (
                    overlap
                    > self.overlap_tolerance
                ):

                    issues.append(
                        self._issue(
                            self.WARNING,
                            "TIMING_OVERLAP",
                            "Lyric timing overlaps the previous item.",
                            index,
                            overlap=round(
                                overlap,
                                6,
                            ),
                        )
                    )

            previous_end = end

        return issues

    # ============================================================
    # Order Validation
    # ============================================================

    def check_order(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        issues: List[
            Dict[str, Any]
        ] = []

        positions = []

        for index, item in enumerate(
            items,
            start=1,
        ):

            position = item.get(
                "position"
            )

            if position is None:

                position = index

            try:

                position = int(
                    position
                )

            except (
                TypeError,
                ValueError,
            ):

                issues.append(
                    self._issue(
                        self.FAIL,
                        "INVALID_POSITION",
                        "Final lyric position must be numeric.",
                        index,
                        position=position,
                    )
                )

                continue

            positions.append(
                position
            )

        expected = list(
            range(
                1,
                len(items) + 1,
            )
        )

        if positions != expected:

            issues.append(
                self._issue(
                    self.FAIL,
                    "ORDER_MISMATCH",
                    "Final lyric positions are not sequential.",
                    actual_positions=positions,
                    expected_positions=expected,
                )
            )

        return issues

    # ============================================================
    # Duplicate Sequence Detection
    # ============================================================

    def check_duplicates(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        issues: List[
            Dict[str, Any]
        ] = []

        if (
            self.duplicate_threshold
            <= 0
        ):
            return issues

        previous_text: str | None = None
        repeat_count = 0

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

            if (
                text
                and text == previous_text
            ):

                repeat_count += 1

            else:

                repeat_count = 1
                previous_text = text

            if (
                text
                and repeat_count
                >= self.duplicate_threshold
            ):

                issues.append(
                    self._issue(
                        self.WARNING,
                        "REPEATED_LYRIC_SEQUENCE",
                        "The same lyric appears repeatedly in sequence.",
                        index,
                        text=text,
                        repeat_count=repeat_count,
                    )
                )

        return issues

    # ============================================================
    # Original / Final Consistency
    # ============================================================

    def check_consistency(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        issues: List[
            Dict[str, Any]
        ] = []

        valid_decisions = {
            "KEEP_ORIGINAL",
            "ACCEPT_CANDIDATE",
            "CUSTOM_CORRECTION",
            "SKIP",
        }

        for index, item in enumerate(
            items,
            start=1,
        ):

            original = item.get(
                "original_text"
            )

            final = item.get(
                "final_text"
            )

            decision = item.get(
                "decision"
            )

            if decision not in valid_decisions:

                issues.append(
                    self._issue(
                        self.FAIL,
                        "INVALID_DECISION",
                        "Final item contains an unsupported decision.",
                        index,
                        decision=decision,
                    )
                )

                continue

            if (
                decision
                in {
                    "KEEP_ORIGINAL",
                    "SKIP",
                }
                and original != final
            ):

                issues.append(
                    self._issue(
                        self.FAIL,
                        "ORIGINAL_MISMATCH",
                        "Original-preserving decision does not preserve the original text.",
                        index,
                    )
                )

            if (
                decision
                in {
                    "ACCEPT_CANDIDATE",
                    "CUSTOM_CORRECTION",
                }
                and (
                    final is None
                    or not str(final).strip()
                )
            ):

                issues.append(
                    self._issue(
                        self.FAIL,
                        "EMPTY_CORRECTION",
                        "Correction decision contains empty final text.",
                        index,
                    )
                )

        return issues

    # ============================================================
    # Full Word Integrity
    # ============================================================

    def check_word_integrity(
        self,
        data: Dict[str, Any],
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        issues: List[
            Dict[str, Any]
        ] = []

        words = data.get(
            "words"
        )

        if not isinstance(
            words,
            list,
        ):
            return issues

        expected_index = 1

        for position, word in enumerate(
            words,
            start=1,
        ):

            if not isinstance(
                word,
                dict,
            ):

                issues.append(
                    self._issue(
                        self.FAIL,
                        "INVALID_WORD",
                        "Lyrics word must be an object.",
                        position,
                    )
                )

                continue

            word_index = word.get(
                "index"
            )

            if word_index is None:

                issues.append(
                    self._issue(
                        self.FAIL,
                        "MISSING_WORD_INDEX",
                        "Lyrics word is missing its index.",
                        position,
                    )
                )

                continue

            try:

                word_index = int(
                    word_index
                )

            except (
                TypeError,
                ValueError,
            ):

                issues.append(
                    self._issue(
                        self.FAIL,
                        "INVALID_WORD_INDEX",
                        "Lyrics word index must be numeric.",
                        position,
                        index=word_index,
                    )
                )

                continue

            if word_index != expected_index:

                issues.append(
                    self._issue(
                        self.FAIL,
                        "WORD_INDEX_MISMATCH",
                        "Lyrics word indices are not sequential.",
                        position,
                        actual_index=word_index,
                        expected_index=expected_index,
                    )
                )

            expected_index += 1

        # --------------------------------------------------------
        # word_count metadata
        # --------------------------------------------------------

        declared_count = data.get(
            "word_count"
        )

        if declared_count is not None:

            try:

                declared_count = int(
                    declared_count
                )

                if declared_count != len(
                    words
                ):

                    issues.append(
                        self._issue(
                            self.FAIL,
                            "WORD_COUNT_MISMATCH",
                            "Declared word_count does not match the words list.",
                            word_count=declared_count,
                            actual_count=len(words),
                        )
                    )

            except (
                TypeError,
                ValueError,
            ):

                issues.append(
                    self._issue(
                        self.FAIL,
                        "INVALID_WORD_COUNT",
                        "word_count must be numeric.",
                    )
                )

        return issues

    # ============================================================
    # Main Analysis
    # ============================================================

    def analyze(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        issues: List[
            Dict[str, Any]
        ] = []

        # --------------------------------------------------------
        # Structure
        # --------------------------------------------------------

        structure_issues = (
            self.check_structure(
                data
            )
        )

        issues.extend(
            structure_issues
        )

        # --------------------------------------------------------
        # Normalize items / words
        # --------------------------------------------------------

        items = self._get_items(
            data
        )

        # --------------------------------------------------------
        # Full word integrity
        # --------------------------------------------------------

        if isinstance(
            data.get("words"),
            list,
        ):

            issues.extend(
                self.check_word_integrity(
                    data,
                    items,
                )
            )

        # --------------------------------------------------------
        # Do not perform detailed checks if structure is invalid
        # --------------------------------------------------------

        structure_failed = any(
            issue["severity"]
            == self.FAIL
            and issue["type"]
            in {
                "INVALID_STRUCTURE",
                "EMPTY_LYRICS",
            }
            for issue in structure_issues
        )

        if not structure_failed:

            issues.extend(
                self.check_text(
                    items
                )
            )

            issues.extend(
                self.check_timing(
                    items
                )
            )

            issues.extend(
                self.check_order(
                    items
                )
            )

            issues.extend(
                self.check_duplicates(
                    items
                )
            )

            issues.extend(
                self.check_consistency(
                    items
                )
            )

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------

        fail_count = sum(
            1
            for issue in issues
            if issue["severity"]
            == self.FAIL
        )

        warning_count = sum(
            1
            for issue in issues
            if issue["severity"]
            == self.WARNING
        )

        if fail_count > 0:

            status = self.FAIL

        elif warning_count > 0:

            status = self.WARNING

        else:

            status = self.PASS

        return {
            "version": self.VERSION,
            "status": status,
            "item_count": len(items),
            "issue_count": len(issues),
            "fail_count": fail_count,
            "warning_count": warning_count,
            "checks": {
                "structure": True,
                "text": True,
                "timing": True,
                "order": True,
                "duplicates": True,
                "consistency": True,
            },
            "issues": issues,
        }

    # ============================================================
    # File Analysis
    # ============================================================

    def analyze_file(
        self,
        input_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:

        data = self.load_final_lyrics(
            input_path
        )

        result = self.analyze(
            data
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