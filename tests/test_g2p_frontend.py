from __future__ import annotations

import os
from pathlib import Path

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend
from src.arabic.model_phone_contract import normalize_model_sequence


def test_phoenix_g2p_frontend_real_module() -> None:
    module_path = Path(
        os.environ.get(
            "PHOENIX_ARABIC_G2P_MODULE_PATH",
            r"D:\PhoenixVoiceEngine\external\YingMusic-Singer-Plus\phoenix_arabic_g2p_v03.py",
        )
    )

    frontend = PhoenixArabicG2PFrontend(module_path)
    if not module_path.is_file():
        import pytest

        pytest.skip(f"Real Phoenix G2P module not available: {module_path}")

    expected = {
        "نار": ("n", "aa", "r"),
        "باب": ("b", "aa", "b"),
        "مال": ("m", "aa", "l"),
        "دار": ("d", "aa", "r"),
        "سار": ("s", "aa", "r"),
        "فار": ("f", "aa", "r"),
    }

    for word, phones in expected.items():
        result = frontend.convert_word(word)
        assert result.canonical_phones == phones
        assert normalize_model_sequence(result.canonical_phones) == tuple(
            "a" if p == "aa" else p for p in phones
        )

    result = frontend.convert("عمر")
    assert result.canonical_phones == ("^", "u", "m", "r")

    result = frontend.convert("الحسن")
    assert result.canonical_phones == ("<", "a", "l", "H", "a", "s", "a", "n")
