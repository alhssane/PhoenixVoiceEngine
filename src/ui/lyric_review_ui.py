from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from src.analyzer.lyric_review_session import LyricReviewSession


class LyricReviewUI:
    """
    PhoenixVoiceEngine
    Lyric Human Review Interface V1.0

    Interactive human review interface.

    Principles:
    - Original lyric is always protected.
    - No automatic correction.
    - Human decision is required.
    - After a review action, the UI automatically moves
      to the next review item.
    - Manual Previous / Next navigation remains available.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        queue_path: str | Path,
        audio_path: str | Path,
        output_session_path: str | Path,
        output_final_path: str | Path,
        context_padding: float = 1.5,
    ) -> None:

        self.queue_path = Path(queue_path)
        self.audio_path = Path(audio_path)

        self.output_session_path = Path(
            output_session_path
        )

        self.output_final_path = Path(
            output_final_path
        )

        self.context_padding = float(
            context_padding
        )

        self.queue_data: Dict[str, Any] = {}
        self.queue: List[Dict[str, Any]] = []

        self.session: Optional[
            LyricReviewSession
        ] = None

        self._load_queue()

    # ================================================================
    # Queue Loading
    # ================================================================

    def _load_queue(self) -> None:
        """
        Load the complete review queue document.

        LyricReviewSession requires the complete dictionary,
        not only the inner queue list.
        """

        if not self.queue_path.exists():
            raise FileNotFoundError(
                "Review queue not found:\n"
                f"{self.queue_path}"
            )

        with self.queue_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "Review queue root must be a dictionary."
            )

        queue = data.get("queue")

        if not isinstance(queue, list):
            raise ValueError(
                "Review queue must contain a 'queue' list."
            )

        if not queue:
            raise ValueError(
                "Review queue is empty."
            )

        self.queue_data = data
        self.queue = queue

        # IMPORTANT:
        # Pass the complete dictionary.
        self.session = LyricReviewSession(
            self.queue_data
        )

    # ================================================================
    # Session
    # ================================================================

    def _require_session(
        self,
    ) -> LyricReviewSession:

        if self.session is None:
            raise RuntimeError(
                "Review session has not been initialized."
            )

        return self.session

    def _current_index(self) -> int:

        session = self._require_session()

        return session.current_index

    def _current_item(
        self,
    ) -> Optional[Dict[str, Any]]:

        session = self._require_session()

        index = session.current_index

        if index < 0:
            return None

        if index >= len(session.queue):
            return None

        return session.queue[index]

    # ================================================================
    # Utility
    # ================================================================

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    # ================================================================
    # Candidate Display
    # ================================================================

    def _candidate_lines(
        self,
        item: Optional[Dict[str, Any]],
    ) -> str:

        if not item:
            return (
                "لا توجد حالة مراجعة حالية."
            )

        candidates = item.get(
            "candidates",
            [],
        )

        if not isinstance(
            candidates,
            list,
        ):

            return (
                "لا توجد مرشحات إضافية."
            )

        if not candidates:
            return (
                "لا توجد مرشحات إضافية."
            )

        lines: List[str] = []

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):

            if not isinstance(
                candidate,
                dict,
            ):
                continue

            text = str(
                candidate.get(
                    "text",
                    "",
                )
            )

            confidence = self._safe_float(
                candidate.get(
                    "confidence"
                )
            )

            fusion = candidate.get(
                "fusion",
                {},
            )

            if not isinstance(
                fusion,
                dict,
            ):

                fusion = {}

            score = self._safe_float(
                fusion.get(
                    "candidate_total_score"
                )
            )

            margin = self._safe_float(
                fusion.get(
                    "margin_vs_original"
                )
            )

            supports = fusion.get(
                "independent_support_count",
                0,
            )

            decision = str(
                fusion.get(
                    "decision",
                    "UNKNOWN",
                )
            )

            lines.append(
                f"{index}. {text} | "
                f"confidence={confidence:.2f}% | "
                f"score={score:.2f} | "
                f"margin={margin:.2f} | "
                f"supports={supports} | "
                f"{decision}"
            )

        if not lines:
            return (
                "لا توجد مرشحات قابلة للعرض."
            )

        return "\n".join(lines)

    # ================================================================
    # Current Item Information
    # ================================================================

    def _item_info(self) -> str:

        item = self._current_item()

        if item is None:
            return (
                "## لا توجد حالة مراجعة حالية"
            )

        original = str(
            item.get(
                "original_text",
                "",
            )
        )

        candidate = str(
            item.get(
                "candidate_text",
                "",
            )
        )

        priority = str(
            item.get(
                "priority",
                "UNKNOWN",
            )
        )

        decision = str(
            item.get(
                "decision",
                "UNKNOWN",
            )
        )

        confidence = self._safe_float(
            item.get(
                "original_confidence"
            )
        )

        margin = self._safe_float(
            item.get(
                "margin_vs_original"
            )
        )

        supports = item.get(
            "independent_support_count",
            0,
        )

        start_time = self._safe_float(
            item.get(
                "start_time"
            )
        )

        end_time = self._safe_float(
            item.get(
                "end_time"
            )
        )

        queue_position = item.get(
            "queue_position",
            self._current_index() + 1,
        )

        return f"""
## الحالة {queue_position}

### الكلمة الأصلية

# `{original}`

### المرشح المقترح

# `{candidate}`

---

**Priority:** `{priority}`

**System Decision:** `{decision}`

**Original Confidence:** `{confidence:.2f}%`

**Margin vs Original:** `{margin:.2f}`

**Independent Evidence:** `{supports}`

**Time:** `{start_time:.2f}s → {end_time:.2f}s`
"""

    # ================================================================
    # Status
    # ================================================================

    def _status_text(self) -> str:

        session = self._require_session()

        total = len(
            session.queue
        )

        current = (
            session.current_index + 1
        )

        try:
            statistics = session.statistics()

        except Exception:
            statistics = {}

        keep_original = statistics.get(
            "keep_original",
            0,
        )

        accept_candidate = statistics.get(
            "accept_candidate",
            0,
        )

        custom_correction = statistics.get(
            "custom_correction",
            0,
        )

        skip = statistics.get(
            "skip",
            0,
        )

        return f"""
### 📋 Review Progress

**الحالة:** `{current} / {total}`

- ✅ إبقاء الأصل: `{keep_original}`
- ✔️ قبول المرشح: `{accept_candidate}`
- ✏️ تصحيح يدوي: `{custom_correction}`
- ⏭️ تخطي: `{skip}`
"""

    # ================================================================
    # Audio
    # ================================================================

    def _audio_path(self) -> Optional[str]:

        if not self.audio_path.exists():
            return None

        return str(
            self.audio_path
        )

    # ================================================================
    # Refresh
    # ================================================================

    def _refresh(
        self,
    ) -> Tuple[
        str,
        str,
        str,
        str,
    ]:

        item = self._current_item()

        return (
            self._status_text(),
            self._item_info(),
            self._candidate_lines(item),
            "",
        )

    # ================================================================
    # Automatic Advance
    # ================================================================

    def _advance_after_action(self) -> None:
        """
        Move to the next review item after a human decision.

        This is intentionally kept in the UI layer.
        LyricReviewSession remains responsible only for
        recording the decision.
        """

        session = self._require_session()

        current = session.current_index
        total = len(session.queue)

        # If there is another item, move forward.
        if current < total - 1:
            session.next()

    # ================================================================
    # Human Review Actions
    # ================================================================

    def keep_original(
        self,
    ) -> Tuple[str, str, str, str]:

        session = self._require_session()

        # Record human decision.
        session.keep_original()

        # Automatically move to next item.
        self._advance_after_action()

        return self._refresh()

    def accept_candidate(
        self,
    ) -> Tuple[str, str, str, str]:

        session = self._require_session()

        # Record human decision.
        session.accept_candidate()

        # Automatically move to next item.
        self._advance_after_action()

        return self._refresh()

    def custom_correction(
        self,
        correction: str,
    ) -> Tuple[str, str, str, str]:

        correction = (
            correction or ""
        ).strip()

        if not correction:
            raise gr.Error(
                "اكتب التصحيح اليدوي أولًا."
            )

        session = self._require_session()

        # Record human correction.
        session.custom_correction(
            correction
        )

        # Automatically move to next item.
        self._advance_after_action()

        return self._refresh()

    def skip(
        self,
    ) -> Tuple[str, str, str, str]:

        session = self._require_session()

        # Record skip.
        session.skip()

        # Automatically move to next item.
        self._advance_after_action()

        return self._refresh()

    # ================================================================
    # Manual Navigation
    # ================================================================

    def previous(
        self,
    ) -> Tuple[str, str, str, str]:

        session = self._require_session()

        session.previous()

        return self._refresh()

    def next(
        self,
    ) -> Tuple[str, str, str, str]:

        session = self._require_session()

        session.next()

        return self._refresh()

    # ================================================================
    # Save Session
    # ================================================================

    def save_session(self) -> str:

        session = self._require_session()

        self.output_session_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = session.to_dict()

        with self.output_session_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return f"""
### 💾 تم حفظ جلسة المراجعة

`{self.output_session_path}`
"""

    # ================================================================
    # Finalize
    # ================================================================

    def finalize(self) -> str:

        session = self._require_session()

        if not session.is_complete():
            raise gr.Error(
                "لا يمكن إنهاء المراجعة قبل "
                "معالجة جميع الحالات."
            )

        final_lyrics = session.finalize()

        self.output_final_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.output_final_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                final_lyrics,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return f"""
## 🏁 اكتملت المراجعة

تم إنشاء الكلمات النهائية:

`{self.output_final_path}`
"""

    # ================================================================
    # Gradio UI
    # ================================================================

    def build(self) -> gr.Blocks:

        with gr.Blocks(
            title=(
                "PhoenixVoiceEngine "
                "— Lyric Human Review"
            )
        ) as app:

            gr.Markdown(
                f"""
# 🎵 PhoenixVoiceEngine

## Lyric Human Review Interface V{self.VERSION}

واجهة المراجعة البشرية للكلمات المستخرجة.

> 🔒 **Original Protection**
>
> لا يتم تعديل النص الأصلي تلقائيًا.
> القرار النهائي دائمًا للمراجع البشري.
"""
            )

            # --------------------------------------------------------
            # Progress / Item
            # --------------------------------------------------------

            with gr.Row():

                with gr.Column(
                    scale=2
                ):

                    status = gr.Markdown(
                        self._status_text()
                    )

                    item_info = gr.Markdown(
                        self._item_info()
                    )

                with gr.Column(
                    scale=3
                ):

                    audio = gr.Audio(
                        value=self._audio_path(),
                        type="filepath",
                        label="🎧 الصوت الأصلي",
                    )

            # --------------------------------------------------------
            # Candidates
            # --------------------------------------------------------

            gr.Markdown(
                "## 🔎 Candidate Evidence"
            )

            candidates = gr.Textbox(
                value=self._candidate_lines(
                    self._current_item()
                ),
                label="المرشحون والأدلة",
                lines=8,
                interactive=False,
            )

            # --------------------------------------------------------
            # Human Decision
            # --------------------------------------------------------

            gr.Markdown(
                "## 🧠 قرار المراجع"
            )

            with gr.Row():

                keep_button = gr.Button(
                    "✅ إبقاء الأصل",
                    variant="secondary",
                )

                accept_button = gr.Button(
                    "✔️ قبول المرشح",
                    variant="primary",
                )

                skip_button = gr.Button(
                    "⏭️ تخطي",
                )

            # --------------------------------------------------------
            # Custom Correction
            # --------------------------------------------------------

            with gr.Row():

                correction = gr.Textbox(
                    label="✏️ التصحيح اليدوي",
                    placeholder=(
                        "اكتب الكلمة الصحيحة..."
                    ),
                    scale=4,
                )

                correction_button = gr.Button(
                    "اعتماد التصحيح",
                    scale=1,
                )

            # --------------------------------------------------------
            # Manual Navigation
            # --------------------------------------------------------

            gr.Markdown(
                "## 🧭 التنقل اليدوي"
            )

            with gr.Row():

                previous_button = gr.Button(
                    "⬅️ السابق"
                )

                next_button = gr.Button(
                    "التالي ➡️",
                    variant="primary",
                )

            # --------------------------------------------------------
            # Save / Finalize
            # --------------------------------------------------------

            gr.Markdown(
                "## 💾 الحفظ والإنهاء"
            )

            with gr.Row():

                save_button = gr.Button(
                    "💾 حفظ جلسة المراجعة"
                )

                finalize_button = gr.Button(
                    "🏁 إنهاء وإنشاء الكلمات النهائية",
                    variant="primary",
                )

            message = gr.Markdown()

            # --------------------------------------------------------
            # Common Review Outputs
            # --------------------------------------------------------

            review_outputs = [
                status,
                item_info,
                candidates,
                correction,
            ]

            # --------------------------------------------------------
            # Events
            # --------------------------------------------------------

            keep_button.click(
                fn=self.keep_original,
                outputs=review_outputs,
            )

            accept_button.click(
                fn=self.accept_candidate,
                outputs=review_outputs,
            )

            correction_button.click(
                fn=self.custom_correction,
                inputs=correction,
                outputs=review_outputs,
            )

            skip_button.click(
                fn=self.skip,
                outputs=review_outputs,
            )

            previous_button.click(
                fn=self.previous,
                outputs=review_outputs,
            )

            next_button.click(
                fn=self.next,
                outputs=review_outputs,
            )

            save_button.click(
                fn=self.save_session,
                outputs=message,
            )

            finalize_button.click(
                fn=self.finalize,
                outputs=message,
            )

        return app


# ====================================================================
# Factory
# ====================================================================

def create_app(
    queue_path: str,
    audio_path: str,
    output_session_path: str,
    output_final_path: str,
) -> gr.Blocks:

    ui = LyricReviewUI(
        queue_path=queue_path,
        audio_path=audio_path,
        output_session_path=output_session_path,
        output_final_path=output_final_path,
    )

    return ui.build()


# ====================================================================
# Main
# ====================================================================

if __name__ == "__main__":

    app = create_app(
        queue_path=(
            r"outputs\lyrics"
            r"\bender_review_queue_v101.json"
        ),
        audio_path=(
            r"F:\مجلد جديد"
            r"\كلمات جديده بصوت بندر.wav"
        ),
        output_session_path=(
            r"outputs\lyrics"
            r"\bender_review_session.json"
        ),
        output_final_path=(
            r"outputs\lyrics"
            r"\bender_final_lyrics.json"
        ),
    )

    app.launch(
        server_name="127.0.0.1",
        server_port=7861,
        inbrowser=True,
    )