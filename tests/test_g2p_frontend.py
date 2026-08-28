from __future__ import annotations

import os
from pathlib import Path

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend


def test_phoenix_g2p_frontend_real_module() -> None:
    module_path = Path(
        os.environ.get(
            "PHOENIX_ARABIC_G2P_MODULE_PATH",
            r"D:\PhoenixVoiceEngine\external\YingMusic-Singer-Plus\phoenix_arabic_g2p_v02.py",
        )
    )

    frontend = PhoenixArabicG2PFrontend(module_path)
    if not module_path.is_file():
        # The real G2P is a local external runtime artifact and is intentionally
        # not vendored into this branch. CI without it should skip this smoke test.
        import pytest

        pytest.skip(f"Real Phoenix G2P module not available: {module_path}")

    result = frontend.convert("عمر")
    assert result.canonical_phones == ("^", "u", "m", "r")

    result = frontend.convert("الحسن")
    assert result.canonical_phones == ("<", "a", "l", "H", "a", "s", "a", "n")
