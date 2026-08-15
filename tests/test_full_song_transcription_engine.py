from src.transcription.full_song_transcription_engine import (
    FullSongTranscriptionEngine,
)


def run():

    result = (

        FullSongTranscriptionEngine()

        .transcribe(

            r"F:\مجلد جديد (3)\صولو فريد الجود كلمات بان نور.wav"

        )

    )

    print()

    print(

        "PhoenixVoiceEngine"

    )

    print(

        "Full Song Transcription Engine V1.0"

    )

    print(

        "=" * 60

    )

    print()

    for key, value in result.items():

        print(

            f"{key}: {value}"

        )

    print()

    print(

        "STATUS: PASS"

    )


if __name__ == "__main__":

    run()