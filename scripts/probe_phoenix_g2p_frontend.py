from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend


def main() -> int:
    words = [
        "عمر",
        "الكون",
        "الدنيا",
        "الحسن",
        "باني",
        "نور",
    ]

    frontend = PhoenixArabicG2PFrontend()
    print("MODULE_AVAILABLE:", frontend.is_available())
    print("MODULE_PATH:", frontend.module_path)

    if not frontend.is_available():
        print("STATUS: REAL_G2P_MODULE_NOT_FOUND")
        return 2

    failures = 0
    for word in words:
        try:
            result = frontend.convert(word)
        except Exception as exc:
            failures += 1
            print("\nWORD:", word)
            print("ERROR:", type(exc).__name__, str(exc))
            continue

        print("\nWORD:", word)
        print("NORMALIZED:", result.normalized_text)
        print("CANONICAL:", " ".join(result.canonical_phones))
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    status = "G2P_FRONTEND_PASS" if failures == 0 else "G2P_FRONTEND_FAIL"
    print("\nFAILURES:", failures)
    print("STATUS:", status)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
