from pathlib import Path

from src.transcription.real_lyrics_extractor import (
    RealLyricsExtractor
)


def run():

    print()

    print("PhoenixVoiceEngine")
    print("Real Lyrics Extractor V1.0")

    print("=" * 60)

    extractor = (
        RealLyricsExtractor()
    )

    audio_path = Path(
        r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
    )

    result = extractor.extract(
        audio_path
    )

    output_path = Path(
        r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_aljood_lyrics.json"
    )

    extractor.save(
        result,
        output_path
    )

    print()

    print(
        "Language:",
        result["language"]
    )

    print(
        "Segments:",
        len(
            result["segments"]
        )
    )

    print()

    print(
        "File saved:"
    )

    print(
        output_path
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()