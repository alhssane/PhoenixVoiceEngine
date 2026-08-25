from src.analysis.arabic_phoneme_engine import ArabicPhonemeEngine


def test_arabic_normalization_removes_diacritics_and_tatweel():
    assert ArabicPhonemeEngine.normalize("مَرْحَبًا ــ يا") == "مرحبا يا"


def test_arabic_phonemizer_produces_nonempty_phonemes():
    result = ArabicPhonemeEngine().phonemize("يا غالية")
    assert result.text == "يا غالية"
    assert result.phonemes
