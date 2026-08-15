class LyricToPhonemeEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        word,
    ):

        phonemes = []

        for letter in word:

            if letter.strip():

                phonemes.append(
                    letter
                )

        return phonemes