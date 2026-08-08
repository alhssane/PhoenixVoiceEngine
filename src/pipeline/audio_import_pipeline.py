"""
Phoenix Voice Studio
Audio Import Pipeline
"""

from pathlib import Path

from src.analyzer.audio_inspector import AudioInspector
from src.audio.auto_fix_engine import AutoFixEngine


class AudioImportPipeline:
    """
    Main pipeline for importing and preparing audio.

    The original audio file is never modified.
    """

    def __init__(self):

        self.inspector = AudioInspector()
        self.auto_fix = AutoFixEngine()

    def run(self, audio_path: str):

        path = Path(audio_path)

        if not path.exists():

            raise FileNotFoundError(
                f"File not found:\n{audio_path}"
            )

        print()
        print("=" * 60)
        print("Phoenix Audio Import Pipeline")
        print("=" * 60)

        # --------------------------------------------------
        # STEP 1: Inspect original audio
        # --------------------------------------------------

        original_report = self.inspector.inspect(
            str(path)
        )

        print()
        print("Original Audio")
        print("-" * 60)

        self._print_report(original_report)

        # --------------------------------------------------
        # STEP 2: Determine whether automatic preparation
        # is required.
        # --------------------------------------------------

        needs_mono = original_report["channels"] != 1

        processed_path = None
        final_report = original_report
        auto_fixed = False

        # --------------------------------------------------
        # STEP 3: Automatic preparation
        # --------------------------------------------------

        if needs_mono:

            print()
            print("Automatic Preparation")
            print("-" * 60)

            output_directory = (
                Path("workspace")
                / "processed_audio"
            )

            output_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            output_path = (
                output_directory
                / f"{path.stem}_processed.wav"
            )

            print(
                "Detected multi-channel audio."
            )

            print(
                "Action: Convert to Mono"
            )

            print(
                f"Output: {output_path}"
            )

            fix_report = self.auto_fix.process(
                input_path=str(path),
                output_path=str(output_path),
                convert_stereo=True,
                normalize=False,
            )

            processed_path = fix_report.output_path
            auto_fixed = True

            print()
            print("Automatic Fix Completed")
            print(
                f"Channels: "
                f"{fix_report.original_channels} "
                f"-> "
                f"{fix_report.final_channels}"
            )

            # --------------------------------------------------
            # STEP 4: Inspect processed audio again
            # --------------------------------------------------

            final_report = self.inspector.inspect(
                processed_path
            )

        # --------------------------------------------------
        # STEP 5: Final report
        # --------------------------------------------------

        print()
        print("=" * 60)
        print("Final Audio Report")
        print("=" * 60)

        self._print_report(final_report)

        print()

        if auto_fixed:

            print(
                "Auto Fix       : APPLIED"
            )

            print(
                f"Processed File : {processed_path}"
            )

        else:

            print(
                "Auto Fix       : NOT REQUIRED"
            )

        print()

        if final_report["ready_for_training"]:

            print(
                "Training Ready : YES"
            )

        else:

            print(
                "Training Ready : NO"
            )

        print("=" * 60)

        return {
            "original": original_report,
            "final": final_report,
            "auto_fixed": auto_fixed,
            "processed_path": processed_path,
        }

    @staticmethod
    def _print_report(report: dict):

        print(
            f"File Name     : "
            f"{report['file_name']}"
        )

        print(
            f"Format        : "
            f"{report['format']}"
        )

        print(
            f"Duration      : "
            f"{report['duration']} sec"
        )

        print(
            f"Sample Rate   : "
            f"{report['sample_rate']}"
        )

        print(
            f"Channels      : "
            f"{report['channels']}"
        )

        print(
            f"Subtype       : "
            f"{report['subtype']}"
        )

        print(
            f"Training Ready: "
            f"{'YES' if report['ready_for_training'] else 'NO'}"
        )