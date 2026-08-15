from src.synthesis.neural_singing_synthesis_engine import (
    NeuralSingingSynthesisEngine,
)


def run():

    lyrics = """

بان نور الحسن في طلتك وحل الجبال وغنة الدنيا سعادة

"""

    result = (
        NeuralSingingSynthesisEngine()
        .generate(
            lyrics,
            "fareed",
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Neural Singing Synthesis Engine V1.0"
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