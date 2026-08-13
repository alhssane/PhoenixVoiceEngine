from typing import Any, Dict, List


class ExpressionTransferEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    SUPPORTED_EXPRESSIONS = (
        "soft",
        "neutral",
        "emotional",
        "powerful",
        "whisper",
    )

    def build_expression(
        self,
        expression_type: str,
        start_time: float,
        end_time: float,
        intensity: float,
    ) -> Dict[str, Any]:

        expression_type = str(
            expression_type
        ).lower()

        if (
            expression_type
            not in self.SUPPORTED_EXPRESSIONS
        ):

            raise ValueError(
                "Unsupported expression."
            )

        intensity = max(
            0.0,
            min(
                1.0,
                float(intensity),
            ),
        )

        return {
            "type": expression_type,
            "start_time": float(start_time),
            "end_time": float(end_time),
            "duration": (
                float(end_time)
                - float(start_time)
            ),
            "intensity": intensity,
        }

    def transfer(
        self,
        expressions: List[Dict[str, Any]],
        words: List[str],
    ) -> List[Dict[str, Any]]:

        transferred = []

        for index, expression in enumerate(
            expressions
        ):

            word = (
                words[index]
                if index < len(words)
                else ""
            )

            transferred.append(
                {
                    "word": word,
                    "expression": expression[
                        "type"
                    ],
                    "intensity": expression[
                        "intensity"
                    ],
                    "start_time": expression[
                        "start_time"
                    ],
                    "end_time": expression[
                        "end_time"
                    ],
                }
            )

        return transferred

    def analyze(
        self,
        expressions: List[Dict[str, Any]],
        words: List[str],
    ) -> Dict[str, Any]:

        result = self.transfer(
            expressions,
            words,
        )

        return {
            "status": "READY",
            "count": len(result),
            "expressions": result,
        }