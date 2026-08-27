from src.arabic.transcript_contract import normalize_arabic, repair_mojibake


def test_repairs_legacy_arabic_mojibake():
    assert repair_mojibake("ط¨ط§ظ†") == "بان"
    assert normalize_arabic("ط¨ط§ظ†") == "بان"


def test_preserves_normal_arabic():
    assert normalize_arabic("باني") == "باني"
    assert normalize_arabic("نور") == "نور"
