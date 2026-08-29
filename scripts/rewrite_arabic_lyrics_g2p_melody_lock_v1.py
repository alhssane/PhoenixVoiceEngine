from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend

# Stage4/Stage6 normalize long vowels for the trained DiffSinger vocabulary.
MODEL_PHONE_NORMALIZATION = {"aa": "a", "ii": "i", "uu": "u"}
VOWELS = {"a", "i", "u"}
REST_PHONE = "SP"


@dataclass(frozen=True)
class Syllable:
    word_index: int
    phones: tuple[str, ...]


@dataclass(frozen=True)
class NoteSlot:
    note: str
    duration: float


def split_tokens(value: str) -> list[str]:
    return [x for x in str(value or "").split() if x]


def normalize_model_phone(phone: str) -> str:
    return MODEL_PHONE_NORMALIZATION.get(phone, phone)


def syllabify_word(phones: list[str], word_index: int) -> list[Syllable]:
    seq = [normalize_model_phone(p) for p in phones if p not in {"|", "SP", "AP"}]
    if not seq:
        return []

    vowel_indices = [i for i, p in enumerate(seq) if p in VOWELS]
    if not vowel_indices:
        return [Syllable(word_index, tuple(seq))]

    result: list[Syllable] = []
    for i, vowel_pos in enumerate(vowel_indices):
        start = 0 if i == 0 else vowel_indices[i - 1] + 1
        end = len(seq) if i == len(vowel_indices) - 1 else vowel_pos + 1
        part = tuple(seq[start:end])
        if part:
            result.append(Syllable(word_index, part))
    return result


def allocate_duration(total: float, phones: tuple[str, ...]) -> list[float]:
    if total <= 0 or not phones:
        raise ValueError("Invalid syllable duration or empty phone sequence.")

    # Consonants stay short; the vowel carries most of the note.
    weights = [4.0 if p in VOWELS else 0.65 for p in phones]
    scale = total / sum(weights)
    values = [x * scale for x in weights]

    # Avoid zero-length tokens, then repair the last value at 1e-6 precision.
    values = [max(0.001, x) for x in values]
    scale = total / sum(values)
    values = [x * scale for x in values]
    rounded = [round(x, 6) for x in values]
    rounded[-1] = round(total - sum(rounded[:-1]), 6)
    if rounded[-1] <= 0:
        raise ValueError(f"Cannot fit phones {phones!r} into {total:.6f}s.")
    return rounded


def parse_reference(ds_path: Path) -> tuple[dict, list[NoteSlot]]:
    payload = json.loads(ds_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list) or len(payload) != 1:
        raise RuntimeError("V1 requires a DS file containing exactly one segment.")

    seg = payload[0]
    for key in ("f0_seq", "f0_timestep", "note_seq", "note_dur"):
        if key not in seg:
            raise RuntimeError(f"Reference DS is missing: {key}")

    notes = split_tokens(seg["note_seq"])
    durations = [float(x) for x in split_tokens(seg["note_dur"])]
    if len(notes) != len(durations):
        raise RuntimeError("note_seq/note_dur length mismatch.")
    if any(x <= 0 for x in durations):
        raise RuntimeError("Reference note durations must be > 0.")

    f0 = split_tokens(seg["f0_seq"])
    timestep = float(seg["f0_timestep"])
    if not f0 or timestep <= 0:
        raise RuntimeError("Reference f0_seq/f0_timestep is invalid.")

    note_total = sum(durations)
    f0_total = len(f0) * timestep
    if abs(note_total - f0_total) > 0.20:
        raise RuntimeError(
            f"Reference timing is inconsistent: notes={note_total:.4f}s, "
            f"f0={f0_total:.4f}s. Repair the reference DS first."
        )

    return seg, [NoteSlot(n, d) for n, d in zip(notes, durations)]


def build_output(
    reference: dict,
    slots: list[NoteSlot],
    syllables: list[Syllable],
    text: str,
    dictionary: set[str] | None,
) -> dict:
    voiced_slots = [x for x in slots if x.note.lower() != "rest"]
    if len(syllables) != len(voiced_slots):
        raise RuntimeError(
            f"Safe V1 melody lock requires one lyric syllable per voiced note: "
            f"{len(syllables)} syllables vs {len(voiced_slots)} voiced notes. "
            "Do not force a mismatch. Use lyrics with the same syllable count "
            "or create a melody-mapping stage in V2."
        )

    ph_seq: list[str] = []
    ph_dur: list[float] = []
    ph_num: list[int] = []
    alignment: list[dict] = []

    syllable_index = 0
    for slot in slots:
        if slot.note.lower() == "rest":
            ph_seq.append(REST_PHONE)
            ph_dur.append(round(slot.duration, 6))
            ph_num.append(1)
            continue

        syllable = syllables[syllable_index]
        durations = allocate_duration(slot.duration, syllable.phones)
        ph_seq.extend(syllable.phones)
        ph_dur.extend(durations)

        # ph_num is intentionally one token per item in this direct-acoustic
        # adapter. Acoustic inference consumes ph_seq/ph_dur/f0 directly;
        # variance-duration prediction is not part of this V1 path.
        ph_num.extend([1] * len(syllable.phones))
        alignment.append({
            "syllable_index": syllable_index,
            "word_index": syllable.word_index,
            "phones": list(syllable.phones),
            "note": slot.note,
            "note_duration": round(slot.duration, 6),
        })
        syllable_index += 1

    if syllable_index != len(syllables):
        raise RuntimeError("Syllable coverage invariant failed.")

    if dictionary is not None:
        missing = sorted(set(ph_seq) - dictionary)
        if missing:
            raise RuntimeError(
                "G2P produced phones outside the selected checkpoint vocabulary: "
                f"{missing}. Do not edit phonemes.txt manually. "
                "Those phones require a compatible new training run."
            )

    total_ph = round(sum(ph_dur), 6)
    total_notes = round(sum(x.duration for x in slots), 6)
    if abs(total_ph - total_notes) > 1e-5:
        raise RuntimeError(
            f"Duration invariant failed: phones={total_ph}, notes={total_notes}"
        )

    out = dict(reference)
    out.update({
        "text": text,
        "ph_seq": " ".join(ph_seq),
        "ph_dur": " ".join(f"{x:.6f}" for x in ph_dur),
        "ph_num": " ".join(str(x) for x in ph_num),
        "note_seq": " ".join(x.note for x in slots),
        "note_dur": " ".join(f"{x.duration:.6f}" for x in slots),
        "rewrite_engine": "phoenix_arabic_g2p_v02_melody_lock_v1",
        "rewrite_reference": "f0_seq_and_note_timeline_preserved",
        "syllable_count": len(syllables),
        "voiced_note_count": len(voiced_slots),
        "syllable_alignment": alignment,
        "g2p_module_path": str(
            Path(os.environ.get(
                "PHOENIX_ARABIC_G2P_MODULE_PATH",
                r"D:\PhoenixVoiceEngine\external\YingMusic-Singer-Plus\phoenix_arabic_g2p_v02.py",
            ))
        ),
    })
    return out


def load_dictionary(path: Path) -> set[str]:
    parts = path.read_text(encoding="utf-8").split()
    if parts and parts[0].upper().startswith("PHOENIX_"):
        parts = parts[1:]
    return set(parts)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Rewrite Arabic lyrics through Phoenix G2P while locking reference melody/F0."
    )
    ap.add_argument("--text", required=True, help="New Arabic lyrics.")
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

    result = frontend.convert(args.text)
    syllables: list[Syllable] = []
    for word_index, item in enumerate(result.words):
        syllables.extend(syllabify_word(list(item.phones), word_index))

    dictionary = None
    dictionary_path = args.dictionary.resolve()
    if dictionary_path.is_file():
        dictionary = load_dictionary(dictionary_path)
    else:
        print(f"WARNING: checkpoint dictionary not found; vocabulary gate skipped: {dictionary_path}")

    out = build_output(reference, slots, syllables, args.text, dictionary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([out], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "LYRICS_REWRITE_DS_READY",
        "output": str(output_path),
        "g2p_words": len(result.words),
        "syllables": len(syllables),
        "voiced_notes": len([x for x in slots if x.note.lower() != "rest"]),
        "total_duration_sec": round(sum(x.duration for x in slots), 6),
        "phones": len(out["ph_seq"].split()),
        "dictionary_checked": dictionary is not None,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
