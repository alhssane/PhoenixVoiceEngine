from src.arabic.phoneme_contract import ipa_to_canonical, phonemize_arabic_word


def test_literal_arabic_hamza_maps_to_glottal_phone():
    assert ipa_to_canonical("abtdaːء", word="ابتداء") == ["a", "b", "t", "d", "aa", "<"]


def test_epritan_word_final_hamza_is_supported():
    class Epi:
        def transliterate(self, word, normpunc=True):
            assert word == "ابتداء"
            return "abtdaːء"

    conversion = phonemize_arabic_word(Epi(), "ابتداء")
    assert conversion.phones == ("a", "b", "t", "d", "aa", "<")
