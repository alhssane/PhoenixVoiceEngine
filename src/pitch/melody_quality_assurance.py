from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class MelodyQualityAssurance:
    """
    PhoenixVoiceEngine
    Melody Quality Assurance V1.0

    Validates melody events without modifying them.

    Checks:
    - Structure
    - Empty melody
    - Invalid duration
    - Timing order
    - Timing overlap
    - Duplicate event index
    - Invalid MIDI
    - Invalid F0
    - Invalid note names
    - Confidence range
    - Very short events
    - Large timing gaps
    - Melody coverage
    - No automatic correction
    """

    VERSION = "1.0.0"

    DEFAULT_MIN_DURATION = 0.08
    DEFAULT_MAX_GAP = 2.0
    DEFAULT_MIN_COVERAGE = 0.10

    VALID_NOTE_NAMES = {
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    }

    def __init__(
        self,
        min_duration: float = DEFAULT_MIN_DURATION,
        max_gap: float = DEFAULT_MAX_GAP,
        min_coverage: float = DEFAULT_MIN_COVERAGE,
    ) -> None:

        if min_duration <= 0:
            raise ValueError(
                "min_duration must be positive."
            )

        if max_gap < 0:
            raise ValueError(
                "max_gap cannot be negative."
            )

        if not 0.0 <= min_coverage <= 1.0:
            raise ValueError(
                "min_coverage must be between 0 and 1."
            )

        self.min_duration = float(
            min_duration
        )

        self.max_gap = float(
            max_gap
        )

        self.min_coverage = float(
            min_coverage
        )

    # ============================================================
    # Loading
    # ============================================================

    def load_file(
        self,
        path: str | Path,
    ) -> Dict[str, Any]:

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Melody file not found: {file_path}"
            )

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "Melody data must be a dictionary."
            )

        return data

    # ============================================================
    # Issue Helper
    # ============================================================

    @staticmethod
    def _issue(
        severity: str,
        issue_type: str,
        message: str,
        **extra: Any,
    ) -> Dict[str, Any]:

        result = {
            "severity": severity,
            "type": issue_type,
            "message": message,
        }

        result.update(extra)

        return result

    # ============================================================
    # Structure
    # ============================================================

    def _validate_structure(
        self,
        data: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> bool:

        valid = True

        melody = data.get(
            "melody"
        )

        if not isinstance(
            melody,
            dict,
        ):

            issues.append(
                self._issue(
                    "FAIL",
                    "INVALID_STRUCTURE",
                    "Melody file must contain a melody object.",
                )
            )

            return False

        events = melody.get(
            "events"
        )

        if not isinstance(
            events,
            list,
        ):

            issues.append(
                self._issue(
                    "FAIL",
                    "INVALID_STRUCTURE",
                    "Melody must contain an events list.",
                )
            )

            return False

        return valid

    # ============================================================
    # Event Validation
    # ============================================================

    def _validate_events(
        self,
        events: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
    ) -> None:

        previous_event = None
        seen_indices = set()

        for position, event in enumerate(
            events,
            start=1,
        ):

            if not isinstance(
                event,
                dict,
            ):

                issues.append(
                    self._issue(
                        "FAIL",
                        "INVALID_EVENT",
                        "Melody event must be a dictionary.",
                        position=position,
                    )
                )

                continue

            # ----------------------------------------------------
            # Event Index
            # ----------------------------------------------------

            event_index = event.get(
                "event_index"
            )

            if event_index in seen_indices:

                issues.append(
                    self._issue(
                        "FAIL",
                        "DUPLICATE_EVENT_INDEX",
                        "Duplicate melody event index detected.",
                        position=position,
                        event_index=event_index,
                    )
                )

            else:

                seen_indices.add(
                    event_index
                )

            # ----------------------------------------------------
            # Timing
            # ----------------------------------------------------

            try:

                start_time = float(
                    event.get(
                        "start_time"
                    )
                )

                end_time = float(
                    event.get(
                        "end_time"
                    )
                )

                duration = float(
                    event.get(
                        "duration"
                    )
                )

            except (
                TypeError,
                ValueError,
            ):

                issues.append(
                    self._issue(
                        "FAIL",
                        "INVALID_TIMING",
                        "Melody event contains invalid timing.",
                        position=position,
                    )
                )

                previous_event = event
                continue

            if start_time < 0:

                issues.append(
                    self._issue(
                        "FAIL",
                        "NEGATIVE_TIMING",
                        "Melody event has negative start time.",
                        position=position,
                        start_time=start_time,
                    )
                )

            if end_time < 0:

                issues.append(
                    self._issue(
                        "FAIL",
                        "NEGATIVE_TIMING",
                        "Melody event has negative end time.",
                        position=position,
                        end_time=end_time,
                    )
                )

            if end_time <= start_time:

                issues.append(
                    self._issue(
                        "FAIL",
                        "INVALID_DURATION",
                        "Melody event end time must be greater than start time.",
                        position=position,
                    )
                )

            if duration <= 0:

                issues.append(
                    self._issue(
                        "FAIL",
                        "INVALID_DURATION",
                        "Melody event duration must be positive.",
                        position=position,
                    )
                )

            expected_duration = (
                end_time
                - start_time
            )

            if abs(
                expected_duration
                - duration
            ) > 0.01:

                issues.append(
                    self._issue(
                        "WARNING",
                        "DURATION_MISMATCH",
                        "Stored duration differs from timing range.",
                        position=position,
                        expected_duration=round(
                            expected_duration,
                            6,
                        ),
                        duration=duration,
                    )
                )

            if (
                duration
                < self.min_duration
            ):

                issues.append(
                    self._issue(
                        "WARNING",
                        "VERY_SHORT_EVENT",
                        "Melody event is shorter than the recommended minimum duration.",
                        position=position,
                        duration=duration,
                    )
                )

            # ----------------------------------------------------
            # Order / Overlap
            # ----------------------------------------------------

            if previous_event is not None:

                try:

                    previous_end = float(
                        previous_event.get(
                            "end_time"
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    previous_end = None

                if previous_end is not None:

                    if (
                        start_time
                        < previous_end
                    ):

                        overlap = (
                            previous_end
                            - start_time
                        )

                        issues.append(
                            self._issue(
                                "WARNING",
                                "TIMING_OVERLAP",
                                "Melody event overlaps the previous event.",
                                position=position,
                                overlap=round(
                                    overlap,
                                    6,
                                ),
                            )
                        )

                    gap = (
                        start_time
                        - previous_end
                    )

                    if (
                        gap
                        > self.max_gap
                    ):

                        issues.append(
                            self._issue(
                                "WARNING",
                                "LARGE_TIMING_GAP",
                                "Large gap detected between melody events.",
                                position=position,
                                gap=round(
                                    gap,
                                    6,
                                ),
                            )
                        )

            # ----------------------------------------------------
            # F0
            # ----------------------------------------------------

            f0 = event.get(
                "f0_mean_hz"
            )

            try:

                f0 = float(f0)

                if f0 <= 0:

                    raise ValueError

            except (
                TypeError,
                ValueError,
            ):

                issues.append(
                    self._issue(
                        "FAIL",
                        "INVALID_F0",
                        "Melody event contains invalid F0.",
                        position=position,
                        f0=f0,
                    )
                )

            # ----------------------------------------------------
            # MIDI
            # ----------------------------------------------------

            midi = event.get(
                "midi_note"
            )

            try:

                midi = int(midi)

            except (
                TypeError,
                ValueError,
            ):

                issues.append(
                    self._issue(
                        "FAIL",
                        "INVALID_MIDI",
                        "Melody event contains invalid MIDI note.",
                        position=position,
                        midi=midi,
                    )
                )

            else:

                if midi < 0 or midi > 127:

                    issues.append(
                        self._issue(
                            "FAIL",
                            "INVALID_MIDI",
                            "MIDI note must be between 0 and 127.",
                            position=position,
                            midi=midi,
                        )
                    )

            # ----------------------------------------------------
            # Note Name
            # ----------------------------------------------------

            note_name = event.get(
                "note_name"
            )

            if not isinstance(
                note_name,
                str,
            ):

                issues.append(
                    self._issue(
                        "FAIL",
                        "INVALID_NOTE_NAME",
                        "Melody event contains invalid note name.",
                        position=position,
                    )
                )

            else:

                note_base = note_name[:-1]

                if (
                    len(note_name) >= 3
                    and note_name[-2].isdigit()
                ):

                    note_base = note_name[:-1]

                elif (
                    len(note_name) >= 2
                    and note_name[-1].isdigit()
                ):

                    note_base = note_name[:-1]

                if note_base not in self.VALID_NOTE_NAMES:

                    issues.append(
                        self._issue(
                            "FAIL",
                            "INVALID_NOTE_NAME",
                            "Melody event contains an invalid note name.",
                            position=position,
                            note_name=note_name,
                        )
                    )

            # ----------------------------------------------------
            # Confidence
            # ----------------------------------------------------

            confidence = event.get(
                "confidence"
            )

            try:

                confidence = float(
                    confidence
                )

            except (
                TypeError,
                ValueError,
            ):

                issues.append(
                    self._issue(
                        "FAIL",
                        "INVALID_CONFIDENCE",
                        "Melody confidence must be numeric.",
                        position=position,
                    )
                )

            else:

                if (
                    confidence < 0.0
                    or confidence > 1.0
                ):

                    issues.append(
                        self._issue(
                            "FAIL",
                            "INVALID_CONFIDENCE",
                            "Melody confidence must be between 0 and 1.",
                            position=position,
                            confidence=confidence,
                        )
                    )

            previous_event = event

    # ============================================================
    # Coverage
    # ============================================================

    def _validate_coverage(
        self,
        data: Dict[str, Any],
        events: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
    ) -> None:

        if not events:
            issues.append(
                self._issue(
                    "FAIL",
                    "EMPTY_MELODY",
                    "Melody contains no events.",
                )
            )

            return

        duration = None

        audio = data.get(
            "audio"
        )

        if isinstance(
            audio,
            dict,
        ):

            duration = audio.get(
                "duration"
            )

        if duration is None:

            duration = data.get(
                "duration"
            )

        if duration is None:

            return

        try:

            duration = float(
                duration
            )

        except (
            TypeError,
            ValueError,
        ):

            return

        if duration <= 0:
            return

        first_start = float(
            events[0].get(
                "start_time",
                0.0,
            )
        )

        last_end = float(
            events[-1].get(
                "end_time",
                0.0,
            )
        )

        covered_duration = max(
            0.0,
            last_end
            - first_start,
        )

        coverage = (
            covered_duration
            / duration
        )

        if (
            coverage
            < self.min_coverage
        ):

            issues.append(
                self._issue(
                    "WARNING",
                    "LOW_MELODY_COVERAGE",
                    "Melody events cover a small portion of the source duration.",
                    coverage=round(
                        coverage,
                        6,
                    ),
                )
            )

    # ============================================================
    # Analysis
    # ============================================================

    def analyze(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        issues: List[
            Dict[str, Any]
        ] = []

        structure_ok = (
            self._validate_structure(
                data,
                issues,
            )
        )

        events: List[
            Dict[str, Any]
        ] = []

        if structure_ok:

            events = data[
                "melody"
            ][
                "events"
            ]

            self._validate_events(
                events,
                issues,
            )

            self._validate_coverage(
                data,
                events,
                issues,
            )

        fail_count = sum(
            1
            for issue in issues
            if issue.get(
                "severity"
            )
            == "FAIL"
        )

        warning_count = sum(
            1
            for issue in issues
            if issue.get(
                "severity"
            )
            == "WARNING"
        )

        if fail_count > 0:
            status = "FAIL"
        elif warning_count > 0:
            status = "WARNING"
        else:
            status = "PASS"

        return {
            "version": self.VERSION,
            "status": status,
            "event_count": len(
                events
            ),
            "issue_count": len(
                issues
            ),
            "fail_count": fail_count,
            "warning_count": warning_count,
            "checks": {
                "structure": structure_ok,
                "timing": not any(
                    issue["type"]
                    in {
                        "INVALID_TIMING",
                        "INVALID_DURATION",
                        "NEGATIVE_TIMING",
                    }
                    for issue in issues
                    if issue.get(
                        "severity"
                    )
                    == "FAIL"
                ),
                "order": not any(
                    issue["type"]
                    == "TIMING_OVERLAP"
                    for issue in issues
                    if issue.get(
                        "severity"
                    )
                    == "FAIL"
                ),
                "duplicates": not any(
                    issue["type"]
                    == "DUPLICATE_EVENT_INDEX"
                    for issue in issues
                ),
                "pitch": not any(
                    issue["type"]
                    in {
                        "INVALID_F0",
                        "INVALID_MIDI",
                        "INVALID_NOTE_NAME",
                    }
                    for issue in issues
                    if issue.get(
                        "severity"
                    )
                    == "FAIL"
                ),
                "confidence": not any(
                    issue["type"]
                    == "INVALID_CONFIDENCE"
                    for issue in issues
                    if issue.get(
                        "severity"
                    )
                    == "FAIL"
                ),
            },
            "no_auto_correction": True,
            "issues": issues,
        }

    # ============================================================
    # File Analysis
    # ============================================================

    def analyze_file(
        self,
        melody_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:

        data = self.load_file(
            melody_path
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