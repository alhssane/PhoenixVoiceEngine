class MicrotonalNoteEngine:

    VERSION = "1.0.0"

    NOTES_24 = [
        "C",
        "C_half_sharp",
        "C#",
        "D_half_flat",
        "D",
        "D_half_sharp",
        "D#",
        "E_half_flat",
        "E",
        "F",
        "F_half_sharp",
        "F#",
        "G_half_flat",
        "G",
        "G_half_sharp",
        "G#",
        "A_half_flat",
        "A",
        "A_half_sharp",
        "A#",
        "B_half_flat",
        "B",
        "B_half_sharp",
        "C_octave",
    ]

    def get_scale(self):

        return list(
            self.NOTES_24
        )

    def note_count(self):

        return len(
            self.NOTES_24
        )

    def has_microtones(self):

        return any(
            "half"
            in note
            for note in self.NOTES_24
        )