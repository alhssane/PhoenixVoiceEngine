from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend
from scripts.rewrite_arabic_lyrics_g2p_melody_map_v2 import (
    VOWELS,
    Syllable,
    choose_partition,
    load_dictionary,
    normalize_phone,
    parse_reference,
    render_group,
    syllabify_word,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phoenix V4 Arabic lyric rewrite: exact reference note/F0 timeline with explicit slur handling."
    )
    ap.add_argument("--text", required=True)
    ap.add_argument("--reference-ds", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument(
        "--dictionary",
        type=Path,
        default=Path(
            r"D:\PhoenixVoiceEngine\external\DiffSinger-openvpi\checkpoints\phoenix_freed_joud_clean_v1\dictionary-ar.txt"
        ),
    )
    args = ap.parse_args()

    reference_path = args.reference_ds.resolve()
    output_path = args.output.resolve()
    if not reference_path.is_file():
        raise FileNotFoundError(reference_path)

    reference, slots = parse_reference(reference_path)

    frontend = PhoenixArabicG2PFrontend()
    if not frontend.is_available():
        raise RuntimeError(f"Phoenix G2P module not found: {frontend.module_path}")

    converted = frontend.convert(args.text)
    syllables: list[Syllable] = []
    for word_index, item in enumerate(converted.words):
        syllables.extend(syllabify_word(list(item.phones), word_index))

    if not syllables:
        raise RuntimeError("G2P produced no usable syllables.")

    dictionary = load_dictionary(args.dictionary.resolve())
    if dictionary is not None:
        produced = {normalize_phone(p) for s in syllables for p in s.phones}
        missing = sorted(produced - dictionary)
        if missing:
            raise RuntimeError(
                "G2P produced phones outside checkpoint vocabulary: "
                f"{missing}"
            )

    groups = choose_partition(syllables, slots)
    voiced_count = sum(1 for slot in slots if slot.voiced)

    rendered_by_note: dict[int, tuple[list[str], list[float], int]] = {}
    slur_by_note: dict[int, int] = {}
    mapping_report: list[dict] = []

    for syllable_indices, note_indices in groups:
        syllable_items = [syllables[i] for i in syllable_indices]
        note_items = [slots[i] for i in note_indices]
        rendered = render_group(syllable_items, note_items)

        if len(rendered) != len(note_indices):
            raise RuntimeError("Rendered group count does not match mapped note count.")

        is_melisma = len(syllable_indices) == 1 and len(note_indices) > 1
        for local, (note_index, (phones, durations)) in enumerate(zip(note_indices, rendered)):
            rendered_by_note[note_index] = (phones, durations, len(phones))
            # DiffSinger slur semantics: first note carries the lyric onset;
            # continuation notes sustain the same lyric vowel.
            slur_by_note[note_index] = 1 if is_melisma and local > 0 else 0

        mapping_report.append({
            "syllable_indices": syllable_indices,
            "note_indices": note_indices,
            "melisma": is_melisma,
            "notes": [slots[i].note for i in note_indices],
            "note_durations": [slots[i].duration for i in note_indices],
            "syllables": [
                {
                    "word_index": syllables[i].word_index,
                    "index_in_word": syllables[i].index_in_word,
                    "phones": list(syllables[i].phones),
                }
                for i in syllable_indices
            ],
        })

    final_ph: list[str] = []
    final_dur: list[float] = []
    final_ph_num: list[int] = []
    final_notes = [slot.note for slot in slots]
    final_note_dur = [slot.duration for slot in slots]
    final_note_slur: list[int] = []

    for idx, slot in enumerate(slots):
        if not slot.voiced:
            final_ph.append("SP")
            final_dur.append(slot.duration)
            final_ph_num.append(1)
            final_note_slur.append(0)
            continue

        if idx not in rendered_by_note:
            raise RuntimeError(f"Voiced note {idx} was not mapped.")

        phones, durations, count = rendered_by_note[idx]
        if len(phones) != len(durations):
            raise RuntimeError(f"Phone/duration mismatch at note {idx}.")

        final_ph.extend(phones)
        final_dur.extend(durations)
        final_ph_num.append(count)
        final_note_slur.append(slur_by_note.get(idx, 0))

    if len(final_notes) != len(final_note_dur) or len(final_notes) != len(final_note_slur):
        raise RuntimeError("Note timeline invariant failed.")

    if sum(final_ph_num) != len(final_ph):
        raise RuntimeError("ph_num coverage invariant failed.")

    if abs(sum(final_dur) - sum(final_note_dur)) > 1e-5:
        raise RuntimeError(
            f"Duration invariant failed: phones={sum(final_dur):.6f}, "
            f"notes={sum(final_note_dur):.6f}"
        )

    # Hard melody lock: both note sequence/durations and F0 are copied from
    # the verified Stage10 reference. Only lyric phones, phone durations,
    # ph_num, and slur flags are rewritten.
    reference_f0 = str(reference["f0_seq"]).split()
    out = dict(reference)
    out.update({
        "text": args.text,
        "ph_seq": " ".join(final_ph),
        "ph_dur": " ".join(f"{x:.6f}" for x in final_dur),
        "ph_num": " ".join(str(x) for x in final_ph_num),
        "note_seq": " ".join(final_notes),
        "note_dur": " ".join(f"{x:.6f}" for x in final_note_dur),
        "note_slur": " ".join(str(x) for x in final_note_slur),
        "f0_seq": " ".join(reference_f0),
        "rewrite_engine": "phoenix_arabic_g2p_melody_map_v4",
        "rewrite_reference": "note_timeline_and_f0_verbatim",
        "reference_f0_preserved": True,
        "reference_note_timeline_preserved": True,
        "g2p_module_path": str(frontend.module_path),
        "syllable_count": len(syllables),
        "voiced_note_count": voiced_count,
        "slur_note_count": sum(final_note_slur),
        "mapping": mapping_report,
    })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([out], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "LYRICS_REWRITE_V4_DS_READY",
        "output": str(output_path),
        "g2p_words": len(converted.words),
        "syllables": len(syllables),
        "voiced_notes": voiced_count,
        "notes_total": len(slots),
        "phones": len(final_ph),
        "duration_sec": round(sum(final_note_dur), 6),
        "dictionary_checked": dictionary is not None,
        "reference_f0_preserved": True,
        "reference_note_timeline_preserved": True,
        "slur_note_count": sum(final_note_slur),
        "mapping_groups": len(groups),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
