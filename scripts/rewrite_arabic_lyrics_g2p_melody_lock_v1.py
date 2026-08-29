from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend

# Stage4/Stage6 intentionally normalize long vowels for the trained DiffSinger
# vocabulary. The G2P frontend keeps the linguistically correct long-vowel form,
# while this inference adapter maps it to the phone representation the baseline
# acoustic checkpoint was actually trained on.
MODEL_PHONE_NORMALIZATION = {
    "aa": "a",
    "ii": "i",
    "uu": "u",
}

VOWELS = {"a", "i", "u", "aa", "ii", "uu"}
REST_PHONE = "SP"
SPECIAL_PHONES = {"SP", "AP", "<PAD>"}


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


def syllabify_word(phones: Iterable[str], word_index: int) -> list[Syllable]:
    seq = [normalize_model_phone(p) for p in phones if p not in {"|", "SP", "AP"}]
    if not seq:
        return []

    vowel_indices = [i for i, p in enumerate(seq) if p in {"a", "i", "u"}]
    if not vowel_indices:
        # Fail-safe: a word without a vowel is kept as one timing unit instead
        # of inventing a syllable boundary.
        return [Syllable(word_index, tuple(seq))]

    result: list[Syllable] = []
    for idx, vowel_pos in enumerate(vowel_indices):
        start = 0 if idx == 0 else vowel_indices[idx - 1] + 1
        end = vowel_pos + 1
        if idx == len(vowel_indices) - 1:
            end = len(seq)
        phones_for_syllable = tuple(seq[start:end])
        if phones_for_syllable:
            result.append(Syllable(word_index, phones_for_syllable))
    return result


def allocate_duration(total: float, phones: tuple[str, ...]) -> list[float]:
    if total <= 0:
        raise ValueError("Syllable duration must be positive.")
    if not phones:
        raise ValueError("Cannot allocate duration to an empty syllable.")

    # Keep consonants short and vowels dominant. This is only the timing
    # frontend; the reference F0 curve remains untouched.
    weights = []
    for phone in phones:
        if phone in {"a", "i", "u"}:
            weights.append(4.0)
        elif phone in {"w", "y"}:
            weights.append(0.75)
        else:
            weights.append(0.65)

    weight_sum = sum(weights)
    durations = [total * w / weight_sum for w in weights]

    # Keep tiny consonants audible while preserving the exact total duration.
    minimum = 0.001
    for i, value in enumerate(durations):
        if value < minimum:
            durations[i] = minimum

    scale = total / sum(durations)
    durations = [x * scale for x in durations]

    # Quantize to 6 decimals and repair the final value so duration coverage
    # remains exact at the serialized precision.
    rounded = [round(x, 6) for x in durations]
    rounded[-1] = round(total - sum(rounded[:-1]), 6)
    if rounded[-1] <= 0:
        raise ValueError(
            f"Unable to allocate {total:.6f}s across phones {phones!r}."
        )
    return rounded


def parse_reference(ds_path: Path) -> tuple[dict, list[NoteSlot]]:
    payload = json.loads(ds_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list) or not payload:
        raise RuntimeError("Reference DS must contain a non-empty JSON array.")
    if len(payload) != 1:
        raise RuntimeError(
            "V1 lyric rewrite requires exactly one reference segment. "
            "Use the segment-specific DS file for multi-segment songs."
        )

    seg = payload[0]
    for key in ("f0_seq", "f0_timestep", "note_seq", "note_dur"):
        if key not in seg:
            raise RuntimeError(f"Reference DS is missing required field: {key}")

    notes = split_tokens(seg["note_seq"])
    note_dur = [float(x) for x in split_tokens(seg["note_dur"])]
    if len(notes) != len(note_dur):
        raise RuntimeError("note_seq/note_dur length mismatch.")
    if any(x <= 0 for x in note_dur):
        raise RuntimeError("Reference note durations must all be > 0.")

    f0 = [float(x) for x in split_tokens(seg["f0_seq"])]
    if not f0:
        raise RuntimeError("Reference DS has an empty f0_seq.")
    f0_timestep = float(seg["f0_timestep"])
    if f0_timestep <= 0:
        raise RuntimeError("Reference f0_timestep must be > 0.")

    note_total = sum(note_dur)
    f0_total = len(f0) * f0_timestep
    if abs(note_total - f0_total) > 0.20:
        raise RuntimeError(
            "Reference melody/F0 duration mismatch is too large: "
            f"notes={note_total:.4f}s, f0={f0_total:.4f}s. "
            "Do not rewrite this DS until the reference timing is repaired."
        )

    return seg, [NoteSlot(n, d) for n, d in zip(notes, note_dur)]


def fit_syllables_to_voiced_slots(
    syllables: list[Syllable], voiced_slots: list[NoteSlot], allow_fit: bool
) -> list[list[NoteSlot]]:
    if not syllables:
        raise RuntimeError("G2P produced no syllables.")
    if not voiced_slots:
        raise RuntimeError("Reference melody contains no voiced notes.")

    n_syll = len(syllables)
    n_notes = len(voiced_slots)

    if not allow_fit and n_syll != n_notes:
        raise RuntimeError(
            f"Strict melody fit requires syllables == voiced notes, "
            f"but got {n_syll} syllables and {n_notes} voiced notes. "
            "Use a lyric with the same syllable count or pass --fit."
        )

    if n_syll > n_notes:
        raise RuntimeError(
            f"New lyric has {n_syll} syllables but the reference melody has "
            f"only {n_notes} voiced notes. --fit cannot safely invent extra "
            "melody events; use a melody with more notes."
        )

    # Every syllable gets at least one voiced note. Extra notes are assigned
    # deterministically to the syllables with the largest phone-count weight.
    groups = [[] for _ in syllables]
    base = n_notes // n_syll
    extra = n_notes % n_syll
    order = sorted(
        range(n_syll),
        key=lambda i: (len(syllables[i].phones), -i),
        reverse=True,
    )

    counts = [base] * n_syll
    for i in order[:extra]:
        counts[i] += 1

    cursor = 0
    for i, count in enumerate(counts):
        groups[i] = voiced_slots[cursor:cursor + count]
        cursor += count

    assert cursor == n_notes
    return groups


def build_output(
    reference: dict,
    slots: list[NoteSlot],
    syllables: list[Syllable],
    allow_fit: bool,
    text: str,
    dictionary: set[str] | None,
) -> dict:
    voiced = [slot for slot in slots if slot.note.lower() != "rest"]
    groups = fit_syllables_to_voiced_slots(syllables, voiced, allow_fit)

    ph_seq: list[str] = []
    ph_dur: list[float] = []
    ph_num: list[int] = []
    syllable_report = []

    syllable_index = 0
    voiced_cursor = 0
    syllable_by_index = {id(s): i for i, s in enumerate(syllables)}

    for slot in slots:
        if slot.note.lower() == "rest":
            ph_seq.append(REST_PHONE)
            ph_dur.append(round(slot.duration, 6))
            ph_num.append(1)
            continue

        # Consume the group belonging to the next syllable.
        group = groups[syllable_index]
        group_total = sum(x.duration for x in group)
        syllable = syllables[syllable_index]
        durations = allocate_duration(group_total, syllable.phones)

        ph_seq.extend(syllable.phones)
        ph_dur.extend(durations)
        ph_num.append(len(syllable.phones))

        syllable_report.append(
            {
                "syllable_index": syllable_index,
                "word_index": syllable.word_index,
                "phones": list(syllable.phones),
                "note_seq": [x.note for x in group],
                "duration": round(group_total, 6),
            }
        )
        syllable_index += 1
        voiced_cursor += len(group)

    if syllable_index != len(syllables):
        raise RuntimeError("Internal syllable allocation coverage failure.")

    if dictionary is not None:
        missing = sorted({p for p in ph_seq if p not in dictionary})
        if missing:
            raise RuntimeError(
                "The G2P result contains phones that the selected acoustic "
                f"checkpoint was not trained to encode: {missing}. "
                "Do NOT edit phonemes.txt manually. A model-vocabulary "
                "expansion requires a new compatible training run."
            )

    total_ph = sum(ph_dur)
    total_notes = sum(x.duration for x in slots)
    if abs(total_ph - total_notes) > 1e-5:
        raise RuntimeError(
            f"Duration invariant failed: phones={total_ph:.6f}, notes={total_notes:.6f}"
        )

    out = dict(reference)
    out["text"] = text
    out["ph_seq"] = " ".join(ph_seq)
    out["ph_dur"] = " ".join(f"{x:.6f}" for x in ph_dur)
    out["ph_num"] = " ".join(str(x) for x in ph_num)
    out["note_seq"] = " ".join(x.note for x in slots)
    out["note_dur"] = " ".join(f"{x.duration:.6f}" for x in slots)
    out["rewrite_engine"] = "phoenix_arabic_g2p_v02_melody_lock_v1"
    out["rewrite_reference"] = "f0_seq_and_note_timeline_preserved"
    out["syllable_count"] = len(syllables)
    out["voiced_note_count"] = len(voiced)
    out["fit_mode"] = "proportional_note_grouping" if allow_fit else "strict_one_syllable_per_note"
    out["syllable_alignment"] = syllable_report
    out["g2p"] = {
        "module_path": str(
            Path(
                os.environ.get(
                    "PHOENIX_ARABIC_G2P_MODULE_PATH",
                    r"D:\PhoenixVoiceEngine\external\YingMusic-Singer-Plus\phoenix_arabic_g2p_v02.py",
                )
            )
        ),
        "phones_normalized_for_baseline": True,
    }
    return out


def load_dictionary(path: Path) -> set[str]:
    parts = path.read_text(encoding="utf-8").split()
    if parts and parts[0].upper().startswith("PHOENIX_"):
        parts = parts[1:]
    return set(parts)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Phoenix V1: rewrite Arabic lyrics with the real G2P frontend "
            "while preserving the reference melody/F0 timeline."
        )
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
        help="Trained checkpoint phone dictionary. Missing phones are rejected.",
    )
    ap.add_argument(
        "--fit",
        action="store_true",
        help="Allow one syllable to span multiple melody notes when syllables < voiced notes.",
    )
    args = ap.parse_args()

    reference_path = args.reference_ds.resolve()
    output_path = args.output.resolve()
    if not reference_path.is_file():
        raise FileNotFoundError(reference_path)

    reference, slots = parse_reference(reference_path)

    frontend = PhoenixArabicG2PFrontend()
    if not frontend.is_available():
        raise RuntimeError(
            f"Phoenix Arabic G2P module not found: {frontend.module_path}"
        )

    g2p_result = frontend.convert(args.text)
    syllables: list[Syllable] = []
    for word_index, item in enumerate(g2p_result.words):
        syllables.extend(syllabify_word(item.phones, word_index))

    dictionary = None
    dictionary_path = args.dictionary.resolve()
    if dictionary_path.is_file():
        dictionary = load_dictionary(dictionary_path)
    else:
        print(f"WARNING: checkpoint dictionary not found; skipping vocabulary gate: {dictionary_path}")

    output = build_output(
        reference,
        slots,
        syllables,
        args.fit,
        args.text,
        dictionary,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([output], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "LYRICS_REWRITE_DS_READY",
                "output": str(output_path),
                "text": args.text,
                "g2p_words": len(g2p_result.words),
                "syllables": len(syllables),
                "voiced_notes": len([x for x in slots if x.note.lower() != "rest"]),
                "total_duration_sec": round(sum(x.duration for x in slots), 6),
                "phones": len(output["ph_seq"].split()),
                "fit_mode": output["fit_mode"],
                "dictionary_checked": dictionary is not None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
