from src.arabic.model_phone_contract import (
    normalize_model_sequence,
    normalize_model_phone,
    validate_model_sequence,
)


def test_long_vowels_normalize_without_reordering() -> None:
    assert normalize_model_sequence(["d", "aa", "r"]) == ("d", "a", "r")
    assert normalize_model_sequence(["s", "ii", "r"]) == ("s", "i", "r")
    assert normalize_model_sequence(["f", "uu", "l"]) == ("f", "u", "l")


def test_existing_phone_is_unchanged() -> None:
    assert normalize_model_phone("sh") == "sh"
    assert normalize_model_phone("r") == "r"


def test_active_vocabulary_gate_fails_closed() -> None:
    validate_model_sequence(["d", "a", "r"], {"d", "a", "r"})

    try:
        validate_model_sequence(["d", "w", "r"], {"d", "a", "r"})
    except ValueError as exc:
        assert "w" in str(exc)
    else:
        raise AssertionError("Unsupported phone was accepted")
