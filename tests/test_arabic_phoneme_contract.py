from __future__ import annotations

import epitran

from src.arabic.phoneme_contract import (
    CANONICAL_PHONES,
    phonemize_arabic_word,
    phonemize_arabic_text,
)


def test_representative_arabic_words_have_no_silent_loss() -> None:
    epi = epitran.Epitran("ara-Arab")
    expected = {
        "بان": ["b", "aa", "n"],
        "نور": ["n", "uu", "r"],
        "الحسن": ["a", "l", "H", "s", "n"],
        "طلتك": ["T", "l", "t", "k"],
        "بالجزال": ["b", "aa", "l", "j", "z", "aa", "l"],
        "عبدالله": ["^", "b", "d", "aa", "l", "l", "h"],
        "الغزال": ["a", "l", "g", "z", "aa", "l"],
    }
    for word, phones in expected.items():
        result = phonemize_arabic_word(epi, word)
        assert list(result.phones) == phones
        assert all(phone in CANONICAL_PHONES for phone in result.phones)


def test_ta_marbuta_and_alif_maqsura_are_preserved() -> None:
    epi = epitran.Epitran("ara-Arab")
    assert phonemize_arabic_word(epi, "سعادة").phones[-1] == "a"
    assert phonemize_arabic_word(epi, "أحلى").phones[-1] == "a"


def test_words_are_separated_once() -> None:
    epi = epitran.Epitran("ara-Arab")
    phones = phonemize_arabic_text(epi, "بان نور")
    assert phones == ["b", "aa", "n", "|", "n", "uu", "r"]
