from __future__ import annotations

import json
from pathlib import Path

import gradio as gr

from src.pipeline.song_project_engine import SongProjectEngine


engine = SongProjectEngine()


def prepare_song(audio, project_name: str, artist_name: str):
    if not audio:
        raise gr.Error("أضف ملف الصوت الصافي أولًا.")
    if not project_name.strip() or not artist_name.strip():
        raise gr.Error("أدخل اسم المشروع واسم الفنان/صاحب الصوت.")

    try:
        manifest = engine.prepare(audio, project_name.strip(), artist_name.strip())
        lyrics_path = Path(manifest["lyrics"])
        words = json.loads(lyrics_path.read_text(encoding="utf-8"))
        lyrics = " ".join(item["word"] for item in words)
        return (
            json.dumps(manifest, ensure_ascii=False, indent=2),
            lyrics,
            manifest["project"],
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


def generate_song(project_path: str, target_lyrics: str):
    if not project_path.strip():
        raise gr.Error("حلّل الأغنية أولًا لإنشاء المشروع.")
    try:
        result = engine.synthesize_edit(project_path.strip(), target_lyrics)
        return str(result.output_audio)
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


with gr.Blocks(title="Phoenix Voice Studio") as demo:
    gr.Markdown(
        "# 🎙️ Phoenix Voice Studio\n"
        "## تحليل أغنية عربية صافية → استخراج الكلمات → إعداد مشروع الأداء → تعديل الكلمات"
    )
    gr.Markdown(
        "**مهم:** استخدم صوتًا تملك حق استخدامه. لا يتم الادعاء بأن التحليل وحده هو تدريب نموذج صوتي؛ "
        "مرحلة التوليد تعتمد على backend غناء حقيقي ومصرّح به."
    )

    with gr.Tab("1 — إعداد الأغنية"):
        audio = gr.Audio(type="filepath", label="الصوت الصافي (Acapella / Dry Vocal)")
        with gr.Row():
            project_name = gr.Textbox(label="اسم المشروع", placeholder="زفة_محمد_وسارة")
            artist_name = gr.Textbox(label="اسم صاحب الصوت", placeholder="اسم الفنان")
        prepare_btn = gr.Button("🔬 تحليل واستخراج الكلمات", variant="primary")
        manifest = gr.Code(label="Project Manifest", language="json")
        original_lyrics = gr.Textbox(label="الكلمات المستخرجة — راجعها قبل التوليد", lines=8, rtl=True)
        project_path = gr.Textbox(label="مسار المشروع")
        prepare_btn.click(
            prepare_song,
            inputs=[audio, project_name, artist_name],
            outputs=[manifest, original_lyrics, project_path],
        )

    with gr.Tab("2 — تعديل الكلمات"):
        target_lyrics = gr.Textbox(
            label="الكلمات الجديدة",
            lines=12,
            rtl=True,
            placeholder="اكتب الكوبليه أو الكلمات الجديدة هنا...",
        )
        generate_btn = gr.Button("🎤 توليد الغناء", variant="primary")
        output = gr.Audio(label="النتيجة")
        generate_btn.click(
            generate_song,
            inputs=[project_path, target_lyrics],
            outputs=output,
        )

    gr.Markdown(
        "### مراحل الجودة\n"
        "1. فحص الصوت الصافي  •  2. استخراج كلمات عربية بتوقيت  •  "
        "3. تحليل النغم والأداء  •  4. مراجعة الكلمات  •  "
        "5. توليد بالـ backend  •  6. فحص النتيجة قبل اعتمادها"
    )


if __name__ == "__main__":
    demo.queue().launch(server_name="127.0.0.1", server_port=7860, share=False)
