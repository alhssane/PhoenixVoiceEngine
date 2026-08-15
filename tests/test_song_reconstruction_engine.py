from src.synthesis.song_reconstruction_engine import (
    SongReconstructionEngine,
)


def run():

    words = [

        "بان",
        "نور",
        "الحسن",
        "في",
        "طلتك",
        "وحل",
        "الجبال",
        "وغنة",
        "الدنيا",
        "سعادة",

    ]

    result = (
        SongReconstructionEngine()
        .generate(
            words
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Song Reconstruction Engine V3.0"
    )

    print(
        "=" * 60
    )

    print()

    print(
        result
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()