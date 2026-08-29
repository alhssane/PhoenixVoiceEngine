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
        # A simple Arabic singing syllable contract:
        # consonants before a vowel belong to that syllable; trailing
        # consonants belong to the final syllable.
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


def choose_partition(syllables: list[Syllable], slots: list[NoteSlot]) -> list[list[int]]:
    """
    Map consecutive syllables to consecutive voiced-note slots.

    A group with:
      - one syllable / many slots = melisma (repeat its vowel on later slots)
      - many syllables / one slot = compressed lyric (all phones share the note)

    Dynamic programming minimizes duration imbalance and strongly prefers
    one-syllable/one-note mappings. It never changes the melody note timeline.
    """
    voiced = [i for i, s in enumerate(slots) if s.voiced]
    n, m = len(syllables), len(voiced)
    if n == 0 or m == 0:
        raise RuntimeError("Cannot map empty lyrics or melody.")

    # dp[i][j] maps first i syllables to first j voiced notes.
    inf = float("inf")
    dp = [[inf] * (m + 1) for _ in range(n + 1)]
    prev: list[list[tuple[int, int] | None]] = [
        [None] * (m + 1) for _ in range(n + 1)
    ]
    dp[0][0] = 0.0

    # Keep group sizes small. Large compression/melisma is musically risky.
    max_group = 4

    for i in range(n + 1):
        for j in range(m + 1):
            base = dp[i][j]
            if base == inf:
                continue
            if i == n and j == m:
                continue

            # One or more syllables in one note.
            if i < n and j < m:
                for a in range(1, min(max_group, n - i) + 1):
                    b = 1
                    if j + b > m:
                        continue
                    dur = sum(slots[voiced[k]].duration for k in range(j, j + b))
                    target = max(0.05, dur / a)
                    cost = 8.0 * (a - 1) + abs(target - 0.35)
                    ni, nj = i + a, j + b
                    val = base + cost
                    if val < dp[ni][nj]:
                        dp[ni][nj] = val
                        prev[ni][nj] = (a, b)

            # One syllable across multiple adjacent notes (melisma).
            if i < n and j < m:
                for b in range(2, min(max_group, m - j) + 1):
                    a = 1
                    dur = sum(slots[voiced[k]].duration for k in range(j, j + b))
                    cost = 1.5 * (b - 1) + abs(dur - 0.55)
                    ni, nj = i + a, j + b
                    val = base + cost
                    if val < dp[ni][nj]:
                        dp[ni][nj] = val
                        prev[ni][nj] = (a, b)

    if dp[n][m] == inf:
        raise RuntimeError(
            f"Cannot safely map {n} syllables onto {m} voiced notes. "
            "Use V3 with wider musical remapping rather than forcing it."
        )

    groups: list[list[int]] = []
    i, j = n, m
    while i or j:
        item = prev[i][j]
        if item is None:
            raise RuntimeError("Melody mapping backtrace failed.")
        a, b = item
        groups.append(list(range(i - a, i)))
        i -= a
        j -= b
    groups.reverse()

    # The current V2 contract expects one syllable group per note group.
    # For a compressed group, its syllables share one note.
    if sum(len(g) for g in groups) != n:
        raise RuntimeError("Syllable coverage invariant failed.")
    return groups


def render_group(syllables: list[Syllable], note_slots: list[NoteSlot]) -> tuple[list[str], list[float], int]:
    total = sum(x.duration for x in note_slots)
    if len(syllables) == 1 and len(note_slots) > 1:
        # Melisma: put the consonants on the first note, then sustain the
        # final vowel on subsequent notes. This preserves changing pitch
        # without repeating onset consonants.
        first = syllables[0].phones
        vowel_positions = [i for i, p in enumerate(first) if p in VOWELS]
        if not vowel_positions:
            phones = first
            durs = allocate(total, phones)
            return phones, durs, len(phones)

        v = first[vowel_positions[-1]]
        phone_parts: list[tuple[str, ...]] = [first] + [(v,) for _ in note_slots[1:]]
        out_p: list[str] = []
        out_d: list[float] = []
        for slot, part in zip(note_slots, phone_parts):
            ds = allocate(slot.duration, part)
            out_p.extend(part)
            out_d.extend(ds)
        return out_p, out_d, len(out_p)

    # Multiple syllables in one note: concatenate their phones. The note's
    # ph_num is therefore the total phone count in that note.
    phones = tuple(p for s in syllables for p in s.phones)
    return list(phones), allocate(total, phones), len(phones)


def load_dictionary(path: Path) -> set[str] | None:
    if not path.is_file():
        return None
    parts = path.read_text(encoding="utf-8").split()
    if parts and parts[0].upper().startswith("PHOENIX_"):
        parts = parts[1:]
    return set(parts)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phoenix V2 Arabic lyric rewrite with dynamic melody mapping."
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
    reference, slots = parse_reference(reference_path)

    frontend = PhoenixArabicG2PFrontend()
    if not frontend.is_available():
        raise RuntimeError(f"Phoenix G2P module not found: {frontend.module_path}")

    result = frontend.convert(args.text)
    syllables: list[Syllable] = []
    for word_index, item in enumerate(result.words):
        # IMPORTANT: PhoneConversion exposes .phones; V1 incorrectly used
        # .canonical_phones here. Keep the frontend contract unchanged.
        syllables.extend(
            syllabify_word(list(item.phones), word_index)
        )

    dictionary = load_dictionary(args.dictionary.resolve())
    if dictionary is not None:
        produced = {normalize_phone(p) for s in syllables for p in s.phones}
        missing = sorted(produced - dictionary)
        if missing:
            raise RuntimeError(
                "G2P produced phones outside the checkpoint vocabulary: "
                f"{missing}"
            )

    voiced_indices = [i for i, s in enumerate(slots) if s.voiced]
    groups = choose_partition(syllables, slots)

    ph_seq: list[str] = []
    ph_dur: list[float] = []
    ph_num: list[int] = []
    alignment: list[dict] = []
    cursor = 0

    for group in groups:
        syllable_items = [syllables[i] for i in group]
        # Determine how many voiced slots this group consumes from the
        # partition by reading its duration budget from the next slots.
        used = 1
        if len(syllable_items) == 1:
            # The partition's note span is inferred from total coverage below.
            # Find the smallest prefix whose count keeps remaining groups
            # feasible; DP backtrace itself is not exposed, so reconstruct
            # greedily from the expected ratio.
            remaining_syllables = sum(len(g) for g in groups[groups.index(group)+1:])
            remaining_notes = len(voiced_indices) - (cursor + 1)
            if remaining_syllables < remaining_notes:
                used = min(4, remaining_notes - remaining_syllables + 1)
        note_indices = voiced_indices[cursor:cursor + used]
        cursor += used
        if not note_indices:
            raise RuntimeError("V2 note coverage failed.")

        note_items = [slots[i] for i in note_indices]
        phones, durations, count = render_group(syllable_items, note_items)
        ph_seq.extend(phones)
        ph_dur.extend(durations)

        # Each rendered note receives its own ph_num count. For compressed
        # syllables this is all phones on the single note; for melisma the
        # first note gets the onset phones and later notes get the sustained
        # vowel.
        if len(syllable_items) == 1 and len(note_items) > 1:
            parts = [len(syllable_items[0].phones)] + [1] * (len(note_items) - 1)
            ph_num.extend(parts)
        else:
            ph_num.append(count)

        alignment.append({
            "syllable_indices": group,
            "note_indices": note_indices,
            "notes": [slots[i].note for i in note_indices],
            "durations": [slots[i].duration for i in note_indices],
        })

    # Insert original rests at their original positions. We render voiced
    # phones separately and then rebuild the full note timeline.
    rendered_by_note: dict[int, tuple[list[str], list[float], int]] = {}
    # Re-run groups deterministically using the recorded alignment.
    syll_cursor = 0
    for item in alignment:
        note_indices = item["note_indices"]
        syll_items = [syllables[i] for i in item["syllable_indices"]]
        note_items = [slots[i] for i in note_indices]
        p, d, _ = render_group(syll_items, note_items)
        if len(syll_items) == 1 and len(note_items) > 1:
            counts = [len(syll_items[0].phones)] + [1] * (len(note_items) - 1)
        else:
            counts = [len(p)]
        if len(counts) != len(note_indices):
            raise RuntimeError("Rendered note/phone count mismatch.")
        pos = 0
        for ni, c, slot in zip(note_indices, counts, note_items):
            rendered_by_note[ni] = (p[pos:pos+c], d[pos:pos+c], c)
            pos += c

    final_ph: list[str] = []
    final_dur: list[float] = []
    final_ph_num: list[int] = []
    final_notes: list[str] = []
    final_note_dur: list[float] = []
    for idx, slot in enumerate(slots):
        final_notes.append(slot.note)
        final_note_dur.append(slot.duration)
        if not slot.voiced:
            final_ph.append("SP")
            final_dur.append(slot.duration)
            final_ph_num.append(1)
            continue
        if idx not in rendered_by_note:
            raise RuntimeError(f"Voiced note {idx} was not mapped.")
        p, d, c = rendered_by_note[idx]
        final_ph.extend(p)
        final_dur.extend(d)
        final_ph_num.append(c)

    if len(final_notes) != len(final_note_dur):
        raise RuntimeError("Note coverage invariant failed.")
    if sum(final_ph_num) != len(final_ph):
        raise RuntimeError("ph_num coverage invariant failed.")
    if abs(sum(final_dur) - sum(final_note_dur)) > 1e-5:
        raise RuntimeError(
            f"Duration invariant failed: phones={sum(final_dur):.6f}, "
            f"notes={sum(final_note_dur):.6f}"
        )

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
        "rewrite_reference": "melody_note_timeline_and_f0_seq_preserved",
        "syllable_count": len(syllables),
        "voiced_note_count": len(voiced_indices),
        "mapping": alignment,
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
        "voiced_notes": len(voiced_indices),
        "notes_total": len(slots),
        "phones": len(final_ph),
        "duration_sec": round(sum(final_dur), 6),
        "dictionary_checked": dictionary is not None,
        "reference_f0_preserved": True,
        "reference_note_timeline_preserved": True,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
