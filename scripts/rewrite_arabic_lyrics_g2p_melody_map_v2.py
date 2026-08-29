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

MODEL_PHONE_NORMALIZATION = {"aa": "a", "ii": "i", "uu": "u"}
VOWELS = {"a", "i", "u"}
REST_PHONES = {"SP", "AP"}


@dataclass(frozen=True)
class Syllable:
    word_index: int
    index_in_word: int
    phones: tuple[str, ...]


@dataclass(frozen=True)
class NoteSlot:
    note: str
    duration: float

    @property
    def voiced(self) -> bool:
        return self.note.lower() != "rest"


def normalize_phone(phone: str) -> str:
    return MODEL_PHONE_NORMALIZATION.get(phone, phone)


def syllabify_word(phones: list[str], word_index: int) -> list[Syllable]:
    seq = [normalize_phone(p) for p in phones if p not in {"|", "SP", "AP"}]
    if not seq:
        return []

    vowel_indices = [i for i, p in enumerate(seq) if p in VOWELS]
    if not vowel_indices:
        return [Syllable(word_index, 0, tuple(seq))]

    result: list[Syllable] = []
    for i, vowel_pos in enumerate(vowel_indices):
        start = 0 if i == 0 else vowel_indices[i - 1] + 1
        end = len(seq) if i == len(vowel_indices) - 1 else vowel_pos + 1
        part = tuple(seq[start:end])
        if part:
            result.append(Syllable(word_index, i, part))
    return result


def parse_reference(path: Path) -> tuple[dict, list[NoteSlot]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list) or len(payload) != 1:
        raise RuntimeError("V2 requires exactly one reference segment.")

    seg = payload[0]
    for key in ("f0_seq", "f0_timestep", "note_seq", "note_dur"):
        if key not in seg:
            raise RuntimeError(f"Reference DS is missing: {key}")

    notes = seg["note_seq"].split()
    durations = [float(x) for x in seg["note_dur"].split()]
    if len(notes) != len(durations):
        raise RuntimeError("Reference note_seq/note_dur mismatch.")
    if any(x <= 0 for x in durations):
        raise RuntimeError("Reference note durations must be > 0.")

    f0 = seg["f0_seq"].split()
    timestep = float(seg["f0_timestep"])
    if not f0 or timestep <= 0:
        raise RuntimeError("Reference f0_seq/f0_timestep is invalid.")

    return seg, [NoteSlot(n, d) for n, d in zip(notes, durations)]


def allocate(total: float, phones: tuple[str, ...]) -> list[float]:
    if total <= 0 or not phones:
        raise ValueError("Invalid duration or empty phone sequence.")

    weights = [4.0 if p in VOWELS else 0.65 for p in phones]
    raw = [total * w / sum(weights) for w in weights]
    raw = [max(0.001, x) for x in raw]
    scale = total / sum(raw)
    values = [x * scale for x in raw]
    rounded = [round(x, 6) for x in values]
    rounded[-1] = round(total - sum(rounded[:-1]), 6)
    if rounded[-1] <= 0:
        raise ValueError("Phone duration allocation produced a non-positive final span.")
    return rounded


def choose_partition(
    syllables: list[Syllable],
    slots: list[NoteSlot],
) -> list[tuple[list[int], list[int]]]:
    """
    Dynamically map consecutive lyric syllables to consecutive voiced notes.

    Normal case:
      1 syllable -> 1 note

    If the counts differ slightly:
      1 syllable -> 2..4 notes  : melisma; later notes sustain the final vowel
      2..4 syllables -> 1 note  : compressed lyric inside the note

    The original note timeline is never changed. This is deliberately a
    conservative V2 mapper; large mismatches are rejected rather than
    producing an uncontrolled lyric/melody alignment.
    """
    voiced = [i for i, slot in enumerate(slots) if slot.voiced]
    n, m = len(syllables), len(voiced)
    if n == 0 or m == 0:
        raise RuntimeError("Cannot map empty lyrics or melody.")

    inf = float("inf")
    dp = [[inf] * (m + 1) for _ in range(n + 1)]
    prev: list[list[tuple[int, int] | None]] = [
        [None] * (m + 1) for _ in range(n + 1)
    ]
    dp[0][0] = 0.0
    max_group = 4

    for i in range(n + 1):
        for j in range(m + 1):
            base = dp[i][j]
            if base == inf:
                continue

            # One syllable assigned to 1..4 notes.
            if i < n and j < m:
                for b in range(1, min(max_group, m - j) + 1):
                    duration = sum(
                        slots[voiced[k]].duration for k in range(j, j + b)
                    )
                    # Strongly prefer the ordinary 1:1 mapping.
                    cost = 0.0 if b == 1 else 1.5 * (b - 1) + abs(duration - 0.55)
                    ni, nj = i + 1, j + b
                    value = base + cost
                    if value < dp[ni][nj]:
                        dp[ni][nj] = value
                        prev[ni][nj] = (1, b)

            # 2..4 syllables compressed into one note.
            if i < n and j < m:
                for a in range(2, min(max_group, n - i) + 1):
                    duration = slots[voiced[j]].duration
                    avg = duration / a
                    cost = 10.0 * (a - 1) + abs(avg - 0.18)
                    ni, nj = i + a, j + 1
                    value = base + cost
                    if value < dp[ni][nj]:
                        dp[ni][nj] = value
                        prev[ni][nj] = (a, 1)

    if dp[n][m] == inf:
        raise RuntimeError(
            f"V2 cannot safely map {n} lyric syllables onto {m} voiced notes. "
            "The difference is too large for conservative melody locking."
        )

    groups: list[tuple[list[int], list[int]]] = []
    i, j = n, m
    while i or j:
        transition = prev[i][j]
        if transition is None:
            raise RuntimeError("Melody mapping backtrace failed.")
        a, b = transition
        syllable_indices = list(range(i - a, i))
        note_indices = voiced[j - b:j]
        groups.append((syllable_indices, note_indices))
        i -= a
        j -= b

    groups.reverse()
    if sum(len(x[0]) for x in groups) != n:
        raise RuntimeError("Syllable coverage invariant failed.")
    if sum(len(x[1]) for x in groups) != m:
        raise RuntimeError("Voiced-note coverage invariant failed.")
    return groups


def render_group(
    syllables: list[Syllable],
    note_slots: list[NoteSlot],
) -> list[tuple[list[str], list[float]]]:
    if not syllables or not note_slots:
        raise RuntimeError("Cannot render an empty mapping group.")

    if len(syllables) == 1 and len(note_slots) > 1:
        # Melisma: onset/consonants happen once; the final vowel is sustained
        # across subsequent pitch changes.
        first = syllables[0].phones
        vowel_positions = [i for i, p in enumerate(first) if p in VOWELS]
        if not vowel_positions:
            raise RuntimeError(
                "Cannot create melisma for a syllable without a vowel."
            )
        vowel = first[vowel_positions[-1]]
        parts = [first] + [(vowel,) for _ in note_slots[1:]]
        return [
            (list(part), allocate(slot.duration, part))
            for slot, part in zip(note_slots, parts)
        ]

    # One note carrying several syllables: all phones share that note's
    # duration, preserving the exact note boundary and total timing.
    phones = tuple(p for s in syllables for p in s.phones)
    return [(list(phones), allocate(note_slots[0].duration, phones))]


def load_dictionary(path: Path) -> set[str] | None:
    if not path.is_file():
        return None
    parts = path.read_text(encoding="utf-8").split()
    if parts and parts[0].upper().startswith("PHOENIX_"):
        parts = parts[1:]
    return set(parts)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phoenix V2 Arabic lyric rewrite with conservative dynamic melody mapping."
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

    result = frontend.convert(args.text)
    syllables: list[Syllable] = []
    for word_index, item in enumerate(result.words):
        # PhoneConversion exposes .phones. The old V1 bug used a non-existent
        # .canonical_phones attribute.
        syllables.extend(syllabify_word(list(item.phones), word_index))

    dictionary = load_dictionary(args.dictionary.resolve())
    if dictionary is not None:
        produced = {normalize_phone(p) for s in syllables for p in s.phones}
        missing = sorted(produced - dictionary)
        if missing:
            raise RuntimeError(
                "G2P produced phones outside the checkpoint vocabulary: "
                f"{missing}"
            )

    voiced_count = sum(1 for slot in slots if slot.voiced)
    groups = choose_partition(syllables, slots)

    rendered_by_note: dict[int, tuple[list[str], list[float], int]] = {}
    mapping_report: list[dict] = []

    for syllable_indices, note_indices in groups:
        syllable_items = [syllables[i] for i in syllable_indices]
        note_items = [slots[i] for i in note_indices]
        rendered = render_group(syllable_items, note_items)

        if len(rendered) != len(note_indices):
            raise RuntimeError(
                "Rendered group count does not match mapped note count."
            )

        for note_index, (phones, durations) in zip(note_indices, rendered):
            rendered_by_note[note_index] = (
                phones,
                durations,
                len(phones),
            )

        mapping_report.append({
            "syllable_indices": syllable_indices,
            "note_indices": note_indices,
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

    for idx, slot in enumerate(slots):
        if not slot.voiced:
            final_ph.append("SP")
            final_dur.append(slot.duration)
            final_ph_num.append(1)
            continue

        if idx not in rendered_by_note:
            raise RuntimeError(f"Voiced note {idx} was not mapped.")

        phones, durations, count = rendered_by_note[idx]
        if len(phones) != len(durations):
            raise RuntimeError(f"Phone/duration mismatch at note {idx}.")
        final_ph.extend(phones)
        final_dur.extend(durations)
        final_ph_num.append(count)

    if len(final_notes) != len(final_note_dur):
        raise RuntimeError("Note timeline invariant failed.")
    if sum(final_ph_num) != len(final_ph):
        raise RuntimeError("ph_num coverage invariant failed.")

    total_ph = sum(final_dur)
    total_notes = sum(final_note_dur)
    if abs(total_ph - total_notes) > 1e-5:
        raise RuntimeError(
            f"Duration invariant failed: phones={total_ph:.6f}, "
            f"notes={total_notes:.6f}"
        )

    # Critical melody lock: copy the reference F0 sequence verbatim. The
    # rewrite changes only lyric phones and their allocation to the existing
    # note timeline.
    out = dict(reference)
    out.update({
        "text": args.text,
        "ph_seq": " ".join(final_ph),
        "ph_dur": " ".join(f"{x:.6f}" for x in final_dur),
        "ph_num": " ".join(str(x) for x in final_ph_num),
        "note_seq": " ".join(final_notes),
        "note_dur": " ".join(f"{x:.6f}" for x in final_note_dur),
        "note_slur": " ".join("0" for _ in final_notes),
        "rewrite_engine": "phoenix_arabic_g2p_melody_map_v2",
        "rewrite_reference": "note_timeline_and_f0_seq_verbatim",
        "syllable_count": len(syllables),
        "voiced_note_count": voiced_count,
        "mapping": mapping_report,
        "g2p_module_path": str(frontend.module_path),
    })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([out], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "LYRICS_REWRITE_V2_DS_READY",
        "output": str(output_path),
        "g2p_words": len(result.words),
        "syllables": len(syllables),
        "voiced_notes": voiced_count,
        "notes_total": len(slots),
        "phones": len(final_ph),
        "duration_sec": round(total_notes, 6),
        "dictionary_checked": dictionary is not None,
        "reference_f0_preserved": True,
        "reference_note_timeline_preserved": True,
        "mapping_groups": len(groups),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
