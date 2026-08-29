from scripts.rewrite_arabic_lyrics_g2p_melody_lock_v1 import (
    allocate_duration,
    syllabify_word,
)


def test_syllabify_arabic_phone_sequence():
    assert [s.phones for s in syllabify_word(["^", "u", "m", "r"], 0)] == [
        ("^", "u", "m", "r")
    ]
    assert [s.phones for s in syllabify_word(["<", "a", "l", "k", "a", "w", "n"], 0)] == [
        ("<", "a"),
        ("l", "k", "a", "w", "n"),
    ]
    assert [s.phones for s in syllabify_word(["<", "a", "d", "d", "u", "n", "y", "aa"], 0)] == [
        ("<", "a"),
        ("d", "d", "u"),
        ("n", "y", "a"),
    ]


def test_allocate_duration_preserves_total():
    values = allocate_duration(0.5, ("b", "a", "n"))
    assert len(values) == 3
    assert all(x > 0 for x in values)
    assert abs(sum(values) - 0.5) < 1e-6
    assert values[1] > values[0]
    assert values[1] > values[2]
