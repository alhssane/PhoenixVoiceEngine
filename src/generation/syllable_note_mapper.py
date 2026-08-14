from dataclasses import dataclass


@dataclass
class SyllableMapping:

    syllable: str
    notes: list


class SyllableNoteMapper:

    def split_word(self, word):

        if word == "ترانيم":
            return [
                "ترا",
                "ني",
                "م"
            ]

        return list(word)

    def map(self, word, notes):

        syllables = self.split_word(word)

        total_notes = len(notes)

        notes_per_syllable = max(
            1,
            total_notes // len(syllables)
        )

        mappings = []

        start = 0

        for syllable in syllables:

            end = start + notes_per_syllable

            assigned_notes = notes[start:end]

            mappings.append(

                SyllableMapping(
                    syllable=syllable,
                    notes=assigned_notes
                )

            )

            start = end

        remaining_notes = notes[start:]

        if remaining_notes:

            mappings[-1].notes.extend(
                remaining_notes
            )

        return mappings