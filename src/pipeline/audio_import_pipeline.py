"""
Phoenix Voice Studio
Audio Import Pipeline
"""

from pathlib import Path

from src.analyzer.audio_inspector import AudioInspector
from src.analyzer.audio_quality_engine import AudioQualityEngine
from src.audio.auto_fix_engine import AutoFixEngine


class AudioImportPipeline:
    """
    Main pipeline for importing, preparing, and evaluating audio.

    The original audio file is never modified.
    """

    def __init__(self):

        self.inspector = AudioInspector()
        self.auto_fix = AutoFixEngine()
        self.quality_engine = AudioQualityEngine()

    def run(self, audio_path: str):

        path = Path(audio_path)

        if not path.exists():

            raise FileNotFoundError(
                f"File not found:\n{audio_path}"
            )

        if not path.is_file():

            raise ValueError(
                f"Audio path is not a file:\n{audio_path}"
            )

        print()
        print("=" * 60)
        print("Phoenix Audio Import Pipeline")
        print("=" * 60)

        # ==================================================
        # STEP 1
        # Inspect original audio
        # ==================================================

        original_report = self.inspector.inspect(
            str(path)
        )

        print()
        print("Original Audio")
        print("-" * 60)

        self._print_inspector_report(
            original_report
        )

        # ==================================================
        # STEP 2
        # Determine automatic preparation
        # ==================================================

        needs_mono = (
            original_report["channels"] != 1
        )

        processed_path = None
        final_report = original_report
        auto_fixed = False

        # ==================================================
        # STEP 3
        # Automatic preparation
        # ==================================================

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

            # ==============================================
            # STEP 4
            # Inspect processed audio again
            # ==============================================

            final_report = self.inspector.inspect(
                processed_path
            )

        # ==================================================
        # STEP 5
        # Quality analysis
        # ==================================================

        quality_path = (
            processed_path
            if processed_path
            else str(path)
        )

        print()
        print("Audio Quality Analysis")
        print("-" * 60)

        quality_report = self.quality_engine.analyze(
            quality_path
        )

        self._print_quality_report(
            quality_report
        )

        # ==================================================
        # STEP 6
        # Final report
        # ==================================================

        print()
        print("=" * 60)
        print("Final Audio Report")
        print("=" * 60)

        self._print_inspector_report(
            final_report
        )

        print()

        if auto_fixed:

            print(
                "Auto Fix          : APPLIED"
            )

            print(
                f"Processed File    : "
                f"{processed_path}"
            )

        else:

            print(
                "Auto Fix          : NOT REQUIRED"
            )

        print()

        print(
            f"Technical Score   : "
            f"{quality_report.technical_score}/100"
        )

        print(
            f"Signal Score      : "
            f"{quality_report.signal_score}/100"
        )

        print(
            f"Training Suitability: "
            f"{quality_report.training_suitability}/100"
        )

        print(
            f"Training Status   : "
            f"{quality_report.status}"
        )

        print()

        if quality_report.recommendations:

            print("Recommendations")
            print("-" * 60)

            for recommendation in (
                quality_report.recommendations
            ):

                print(
                    f"- {recommendation}"
                )

        print()

        if quality_report.status in {
            "READY",
            "READY_WITH_PROCESSING",
        }:

            print(
                "Training Ready    : YES"
            )

        else:

            print(
                "Training Ready    : NO"
            )

        print("=" * 60)

        return {
            "original": original_report,
            "final": final_report,
            "quality": quality_report.to_dict(),
            "auto_fixed": auto_fixed,
            "processed_path": processed_path,
        }

    @staticmethod
    def _print_inspector_report(
        report: dict,
    ):

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

    @staticmethod
    def _print_quality_report(
        report,
    ):

        print(
            f"Peak              : "
            f"{report.peak_dbfs} dBFS"
        )

        print(
            f"RMS               : "
            f"{report.rms_dbfs} dBFS"
        )

        print(
            f"Clipping Ratio    : "
            f"{report.clipping_ratio}"
        )

        print(
            f"Silence Ratio     : "
            f"{report.silence_ratio}"
        )

        print(
            f"Dynamic Range     : "
            f"{report.dynamic_range_db} dB"
        )

        print(
            f"Technical Score   : "
            f"{report.technical_score}/100"
        )

        print(
            f"Signal Score      : "
            f"{report.signal_score}/100"
        )

        print(
            f"Training Suitability: "
            f"{report.training_suitability}/100"
        )

        print(
            f"Status            : "
            f"{report.status}"
        )