"""
PhoenixVoiceEngine
Tonic Cadential Context Analyzer V1.0

Evidence-only analysis of phrase-final contexts.

Purpose:
- inspect the final 2-4 pitch classes of each phrase
- identify recurring approach patterns into candidate tonics
- compare candidate tonic cadential behavior
- preserve source pitch/timing/performance
- make no tonic, jins, or maqam decision
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TonicCadentialContextAnalyzer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    NOTE_NAMES = (
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
    )

    # ------------------------------------------------------------------
    # FILE IO
    # ------------------------------------------------------------------

    def _load(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # NOTE HELPERS
    # ------------------------------------------------------------------

    @classmethod
    def _name(cls, pc: int) -> str:
        return cls.NOTE_NAMES[int(pc) % 12]

    # ------------------------------------------------------------------
    # EVENT PITCH EXTRACTION
    # ------------------------------------------------------------------

    @staticmethod
    def _event_pc(event: Dict[str, Any]) -> Optional[int]:
        """
        Extract pitch class from supported schemas.

        Supported:
        - event.pitch_class
        - event.midi_note
        - event.midi
        - event.melody.pitch_class
        - event.melody.midi_note
        - event.melody.midi
        - event.note.pitch_class
        - event.note.midi_note
        - event.note.midi

        No pitch correction is performed.
        """

        # --------------------------------------------------------------
        # Nested melody schema
        # --------------------------------------------------------------

        melody = event.get("melody")

        if isinstance(melody, dict):
            value = melody.get("pitch_class")

            if isinstance(value, (int, float)):
                return int(value) % 12

            value = melody.get("midi_note")

            if isinstance(value, (int, float)):
                return int(round(float(value))) % 12

            value = melody.get("midi")

            if isinstance(value, (int, float)):
                return int(round(float(value))) % 12

        # --------------------------------------------------------------
        # Direct event schema
        # --------------------------------------------------------------

        for key in ("pitch_class", "midi_note", "midi"):
            value = event.get(key)

            if isinstance(value, (int, float)):

                if key == "pitch_class":
                    return int(value) % 12

                return int(round(float(value))) % 12

        # --------------------------------------------------------------
        # Nested note schema
        # --------------------------------------------------------------

        note = event.get("note")

        if isinstance(note, dict):

            for key in ("pitch_class", "midi_note", "midi"):
                value = note.get(key)

                if isinstance(value, (int, float)):

                    if key == "pitch_class":
                        return int(value) % 12

                    return int(round(float(value))) % 12

        return None

    # ------------------------------------------------------------------
    # PHRASE EXTRACTION
    # ------------------------------------------------------------------

    def _extract_phrase(
        self,
        phrase: Dict[str, Any],
    ) -> Dict[str, Any]:

        events = phrase.get("events", [])

        pcs: List[int] = []

        for event in events:

            if not isinstance(event, dict):
                continue

            pc = self._event_pc(event)

            if pc is not None:
                pcs.append(pc)

        return {
            "phrase_index": phrase.get("phrase_index"),
            "pitch_classes": pcs,
            "pitch_class_names": [
                self._name(x)
                for x in pcs
            ],
        }

    # ------------------------------------------------------------------
    # CADENTIAL CONTEXT
    # ------------------------------------------------------------------

    @staticmethod
    def _context_from_pcs(
        pcs: List[int],
        tonic: int,
        width: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Return the final `width` notes when the phrase ends on tonic.

        Example:

            phrase = C A# G
            tonic  = G
            width  = 2

        returns:

            A# G
        """

        if not pcs:
            return None

        tonic = int(tonic) % 12

        # The phrase must actually end on the candidate tonic.
        if pcs[-1] != tonic:
            return None

        context = pcs[
            max(0, len(pcs) - width):
        ]

        return {
            "width": len(context),
            "pitch_classes": context,
            "pitch_class_names": [
                TonicCadentialContextAnalyzer._name(x)
                for x in context
            ],
        }

    # ------------------------------------------------------------------
    # CANDIDATE ANALYSIS
    # ------------------------------------------------------------------

    def _candidate_analysis(
        self,
        tonic: int,
        phrase_records: List[Dict[str, Any]],
        widths: Tuple[int, ...],
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:

        tonic = int(tonic) % 12

        # --------------------------------------------------------------
        # Phrases ending on this candidate tonic
        # --------------------------------------------------------------

        ending_phrases = [
            p
            for p in phrase_records
            if p["pitch_classes"]
            and p["pitch_classes"][-1] == tonic
        ]

        # --------------------------------------------------------------
        # IMPORTANT:
        #
        # Count every context width independently.
        #
        # This allows:
        #
        # A# -> G = 2
        #
        # to be discovered even if the complete 3-note contexts are:
        #
        # C -> A# -> G
        # D -> A# -> G
        #
        # which are different.
        # --------------------------------------------------------------

        pattern_counts_by_width = {
            int(width): Counter()
            for width in widths
        }

        context_records: List[Dict[str, Any]] = []

        for phrase in ending_phrases:

            windows: Dict[str, Dict[str, Any]] = {}

            for width in widths:

                ctx = self._context_from_pcs(
                    phrase["pitch_classes"],
                    tonic,
                    width,
                )

                if ctx is None:
                    continue

                windows[str(width)] = ctx

                pattern = tuple(
                    ctx["pitch_classes"]
                )

                pattern_counts_by_width[
                    int(width)
                ][pattern] += 1

            if windows:

                context_records.append(
                    {
                        "phrase_index": phrase["phrase_index"],
                        "windows": windows,
                    }
                )

        # --------------------------------------------------------------
        # BUILD RECURRING CONTEXTS
        # --------------------------------------------------------------

        recurring_patterns: List[Dict[str, Any]] = []

        for width in sorted(pattern_counts_by_width):

            counts = pattern_counts_by_width[width]

            for pattern, count in counts.most_common():

                # A one-off pattern is not considered recurring.
                if count < 2:
                    continue

                recurring_patterns.append(
                    {
                        "width": width,
                        "pitch_classes": list(pattern),
                        "pitch_class_names": [
                            self._name(x)
                            for x in pattern
                        ],
                        "count": count,
                        "phrase_ratio": round(
                            count / len(phrase_records),
                            6,
                        )
                        if phrase_records
                        else 0.0,
                        "ending_ratio": round(
                            count / len(ending_phrases),
                            6,
                        )
                        if ending_phrases
                        else 0.0,
                    }
                )

        # --------------------------------------------------------------
        # Sort strongest recurring contexts first.
        #
        # Count is primary.
        # Ending ratio is secondary.
        # Width is tertiary.
        # --------------------------------------------------------------

        recurring_patterns.sort(
            key=lambda x: (
                x["count"],
                x["ending_ratio"],
                x["width"],
            ),
            reverse=True,
        )

        # --------------------------------------------------------------
        # RECURRENCE EVIDENCE
        # --------------------------------------------------------------

        recurring_count = sum(
            x["count"]
            for x in recurring_patterns
        )

        strongest_recurrence = (
            recurring_patterns[0]["ending_ratio"]
            if recurring_patterns
            else 0.0
        )

        # --------------------------------------------------------------
        # ENDING RATIO
        # --------------------------------------------------------------

        total_phrases = len(phrase_records)

        ending_count = len(ending_phrases)

        ending_ratio = (
            ending_count / total_phrases
            if total_phrases
            else 0.0
        )

        # --------------------------------------------------------------
        # RECURRENCE SCORE
        # --------------------------------------------------------------

        recurrence_score = min(
            1.0,
            recurring_count / max(ending_count, 1),
        )

        # --------------------------------------------------------------
        # PENULTIMATE NOTE EVIDENCE
        # --------------------------------------------------------------

        penultimate = Counter()

        for record in context_records:

            # We specifically use the width-2 context.
            ctx = record["windows"].get("2")

            if not ctx:
                continue

            pcs = ctx["pitch_classes"]

            if len(pcs) >= 2:

                penultimate_note = pcs[-2]

                penultimate[
                    penultimate_note
                ] += 1

        # --------------------------------------------------------------
        # APPROACH DIVERSITY
        # --------------------------------------------------------------

        approach_diversity = min(
            1.0,
            len(penultimate) / 6.0,
        )

        # --------------------------------------------------------------
        # CADENTIAL CONTEXT SCORE
        #
        # Evidence-only score.
        #
        # No decision threshold here.
        # --------------------------------------------------------------

        cadential_context_score = round(
            0.35 * ending_ratio
            + 0.30 * recurrence_score
            + 0.20 * strongest_recurrence
            + 0.15 * approach_diversity,
            6,
        )

        candidate = {
            "tonic_pitch_class": tonic,
            "tonic_name": self._name(tonic),

            "phrase_count": total_phrases,

            "ending_phrase_count": ending_count,

            "ending_phrase_ratio": round(
                ending_ratio,
                6,
            ),

            "penultimate_pitch_class_counts": {
                str(k): v
                for k, v
                in penultimate.most_common()
            },

            "penultimate_pitch_class_names": {
                self._name(k): v
                for k, v
                in penultimate.most_common()
            },

            "recurring_contexts": recurring_patterns,

            "cadential_context_score": (
                cadential_context_score
            ),

            "evidence_only": True,
        }

        return candidate, context_records

    # ------------------------------------------------------------------
    # MAIN ANALYZER
    # ------------------------------------------------------------------

    def analyze(
        self,
        phrase_data: Dict[str, Any],
        candidates: Optional[List[int]] = None,
        context_widths: Tuple[int, ...] = (
            2,
            3,
            4,
        ),
    ) -> Dict[str, Any]:

        # --------------------------------------------------------------
        # Candidate pitch classes
        # --------------------------------------------------------------

        candidates = [
            int(x) % 12
            for x in (
                candidates
                or [7, 0]
            )
        ]

        # --------------------------------------------------------------
        # Extract phrases
        # --------------------------------------------------------------

        phrases = (
            phrase_data
            .get("phrases", {})
            .get("phrases", [])
        )

        phrase_records = [
            self._extract_phrase(p)
            for p in phrases
            if isinstance(p, dict)
        ]

        # --------------------------------------------------------------
        # Analyze candidates
        # --------------------------------------------------------------

        ranking: List[Dict[str, Any]] = []

        all_contexts: Dict[
            str,
            List[Dict[str, Any]]
        ] = {}

        for tonic in candidates:

            candidate, contexts = (
                self._candidate_analysis(
                    tonic,
                    phrase_records,
                    context_widths,
                )
            )

            ranking.append(candidate)

            all_contexts[str(tonic)] = contexts

        # --------------------------------------------------------------
        # Ranking
        # --------------------------------------------------------------

        ranking.sort(
            key=lambda x: x[
                "cadential_context_score"
            ],
            reverse=True,
        )

        top = (
            ranking[0]
            if ranking
            else None
        )

        second = (
            ranking[1]
            if len(ranking) > 1
            else None
        )

        margin = (
            round(
                top[
                    "cadential_context_score"
                ]
                - second[
                    "cadential_context_score"
                ],
                6,
            )
            if top and second
            else 0.0
        )

        # --------------------------------------------------------------
        # FINAL EVIDENCE OBJECT
        # --------------------------------------------------------------

        return {
            "version": self.VERSION,

            "feature_version": (
                self.FEATURE_VERSION
            ),

            "patch_version": (
                self.PATCH_VERSION
            ),

            "input": {
                "phrase_count": len(
                    phrases
                ),

                "candidate_pitch_classes": (
                    candidates
                ),

                "context_widths": list(
                    context_widths
                ),
            },

            "evidence": {
                "candidate_cadential_evidence": (
                    ranking
                ),

                "phrase_contexts_by_candidate": (
                    all_contexts
                ),
            },

            "ranking": {
                "candidates": ranking,

                "top": top,

                "second": second,

                "margin": margin,
            },

            # ----------------------------------------------------------
            # IMPORTANT:
            #
            # This analyzer is evidence-only.
            # ----------------------------------------------------------

            "decision": {
                "status": "EVIDENCE_ONLY",

                "tonic_pitch_class": None,

                "tonic_name": None,

                "maqam": None,

                "jins": None,

                "confidence": None,

                "reason": [
                    "TONIC_CADENTIAL_CONTEXT_EVIDENCE_ONLY"
                ],
            },

            # ----------------------------------------------------------
            # PROTECTION
            # ----------------------------------------------------------

            "protection": {
                "source_pitch_modified": False,

                "source_timing_modified": False,

                "source_performance_modified": False,

                "tonic_decision_made": False,

                "maqam_decision_made": False,

                "jins_decision_made": False,
            },
        }

    # ------------------------------------------------------------------
    # FILE ANALYSIS
    # ------------------------------------------------------------------

    def analyze_file(
        self,
        phrase_path: str,
        output_path: str,
        candidates: Optional[List[int]] = None,
        context_widths: Tuple[int, ...] = (
            2,
            3,
            4,
        ),
    ) -> Dict[str, Any]:

        phrase_data = self._load(
            phrase_path
        )

        result = self.analyze(
            phrase_data,
            candidates=candidates,
            context_widths=context_widths,
        )

        output = Path(
            output_path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            output,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                result,
                f,
                ensure_ascii=False,
                indent=2,
            )

        return result