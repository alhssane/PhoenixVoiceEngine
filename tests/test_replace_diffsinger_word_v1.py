from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "replace_diffsinger_word_v1.py"
SPEC = importlib.util.spec_from_file_location("replace_diffsinger_word_v1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_payload() -> dict:
    return {
        "text": "وحلا القبال وغنت",
        "ph_seq": "u H l a l q b a l u g n t",
        "ph_dur": "0.10 0.10 0.10 0.1567 0.2313 0.0895 0.1417 0.2238 0.0970 0.10 0.10 0.10 0.10",
        "f0_seq": "100 101 102 103",
        "note_seq": "C4 D4",
        "note_dur": "0.5 0.5",
        "note_slur": "0 1",
    }


def test_full_word_replacement_preserves_duration_and_conditioning() -> None:
    payload = make_payload()
    result, report = MODULE.replace_word(
        payload=payload,
        start=3,
        expected=["a", "l", "q", "b", "a", "l"],
        replacement=["a", "l", "n", "u", "r"],
        replacement_durations=[0.1567, 0.2313, 0.1458, 0.25, 0.1562],
        replacement_text="وحلا النور وغنت",
    )

    assert result["ph_seq"].split()[3:8] == ["a", "l", "n", "u", "r"]
    assert abs(report["original_word_total_sec"] - 0.94) < 1e-9
    assert abs(report["replacement_word_total_sec"] - 0.94) < 1e-9
    assert abs(report["full_duration_before_sec"] - report["full_duration_after_sec"]) < 1e-9
    assert report["conditioning_unchanged"] is True
    assert result["f0_seq"] == payload["f0_seq"]
    assert result["note_seq"] == payload["note_seq"]
    assert result["text"] == "وحلا النور وغنت"


def test_full_word_guard_rejects_partial_or_wrong_span() -> None:
    with pytest.raises(ValueError, match="Full-word guard failed"):
        MODULE.replace_word(
            payload=make_payload(),
            start=6,
            expected=["b", "a", "r"],
            replacement=["n", "u", "r"],
        )


def test_automatic_distribution_preserves_word_total() -> None:
    _, report = MODULE.replace_word(
        payload=make_payload(),
        start=3,
        expected=["a", "l", "q", "b", "a", "l"],
        replacement=["a", "l", "n", "u", "r"],
    )

    assert len(report["replacement_durations"]) == 5
    assert all(value > 0 for value in report["replacement_durations"])
    assert abs(
        report["replacement_word_total_sec"] - report["original_word_total_sec"]
    ) < 1e-9


def test_rejects_explicit_durations_that_change_total() -> None:
    with pytest.raises(ValueError, match="must preserve the complete word span"):
        MODULE.replace_word(
            payload=make_payload(),
            start=3,
            expected=["a", "l", "q", "b", "a", "l"],
            replacement=["a", "l", "n", "u", "r"],
            replacement_durations=[0.1, 0.1, 0.1, 0.1, 0.1],
        )
