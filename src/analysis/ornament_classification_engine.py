class OrnamentClassificationEngine:

    VERSION = "1.0.0"

    def classify(self, notes):

        if len(notes) < 3:

            return "UNKNOWN"

        unique_notes = []

        for note in notes:

            if note not in unique_notes:

                unique_notes.append(note)

        if len(unique_notes) < 2:

            return "STATIC"

        indexes = {}

        scale = [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B",
        ]

        for index, note in enumerate(scale):

            indexes[note] = index

        values = []

        for note in notes:

            values.append(indexes[note])

        differences = []

        for i in range(1, len(values)):

            differences.append(
                values[i] - values[i - 1]
            )

        if all(x > 0 for x in differences):

            return "ASCENDING"

        if all(x < 0 for x in differences):

            return "DESCENDING"

        if len(set(notes)) == 2:

            return "VIBRATO"

        highest = max(values)

        highest_index = values.index(highest)

        if (
            highest_index != 0
            and highest_index != len(values) - 1
        ):

            left = values[:highest_index]

            right = values[highest_index:]

            if (
                all(
                    left[i] <= left[i + 1]
                    for i in range(
                        len(left) - 1
                    )
                )
                and all(
                    right[i] >= right[i + 1]
                    for i in range(
                        len(right) - 1
                    )
                )
            ):

                return "ARCH"

        return "COMPLEX"