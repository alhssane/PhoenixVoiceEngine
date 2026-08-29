from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend

MODEL_PHONE_NORMALIZATION = {"aa": "a", "ii": "i", "uu": "u"}
VOWELS = {"a", "i", "u"}
SPECIAL_PHONES = {"SP", "AP", "<PAD>"}
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass(frozen=True)
class Syllable:
    word_index: int
    index_in_word: int
    phones: tuple[str, ...]


@dataclass(frozen=True)
class TimelineRegion:
    start_frame: int
    end_frame: int
    voiced: bool

    @property
    def frames(self) -> int:
        return self.end_frame - self.start_frame


@dataclass(frozen=True)
class PhoneSpan:
    phone: str
    start_frame: int
    end_frame: int

    @property
    def frames(self) -> int:
        return self.end_frame - self.start_frame


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


def load_dictionary(path: Path) -> set[str] | None:
    if not path.is_file():
        return None
    parts = path.read_text(encoding="utf-8").split()
    if parts and parts[0].upper().startswith("PHOENIX_"):
        parts = parts[1:]
    return set(parts)


def parse_reference(path: Path) -> tuple[dict, list[float], float]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list) or len(payload) != 1:
        raise RuntimeError("V3 requires exactly one reference DS segment.")

    segment = payload[0]
    for key in ("f0_seq", "f0_timestep"):
        if key not in segment:
            raise RuntimeError(f"Reference DS is missing required field: {key}")

    f0 = [float(x) for x in str(segment["f0_seq"]).split()]
    timestep = float(segment["f0_timestep"])
    if not f0 or timestep <= 0:
        raise RuntimeError("Reference f0_seq/f0_timestep is invalid.")
    if any(not math.isfinite(x) or x < 0 for x in f0):
        raise RuntimeError("Reference f0_seq contains invalid values.")
    return segment, f0, timestep


def smooth_voicing(
    f0: list[float],
    timestep: float,
    bridge_gap_sec: float,
    remove_island_sec: float,
) -> list[bool]:
    voiced = [x > 0 for x in f0]
    bridge = max(0, int(round(bridge_gap_sec / timestep)))
    island = max(0, int(round(remove_island_sec / timestep)))

    # Bridge short unvoiced gaps between two voiced areas. These tiny gaps are
    # usually pitch-tracker dropouts, not linguistic silence.
    i = 0
    while i < len(voiced):
        if voiced[i]:
            i += 1
            continue
        start = i
        while i < len(voiced) and not voiced[i]:
            i += 1
        end = i
        if start > 0 and end < len(voiced) and end - start <= bridge:
            for j in range(start, end):
                voiced[j] = True

    # Remove tiny isolated voiced islands surrounded by real silence.
    i = 0
    while i < len(voiced):
        if not voiced[i]:
            i += 1
            continue
        start = i
        while i < len(voiced) and voiced[i]:
            i += 1
        end = i
        if start > 0 and end < len(voiced) and end - start <= island:
            for j in range(start, end):
                voiced[j] = False

    return voiced


def build_regions(mask: list[bool]) -> list[TimelineRegion]:
    if not mask:
        return []
    regions: list[TimelineRegion] = []
    start = 0
    current = mask[0]
    for i in range(1, len(mask)):
        if mask[i] != current:
            regions.append(TimelineRegion(start, i, current))
            start = i
            current = mask[i]
    regions.append(TimelineRegion(start, len(mask), current))
    return regions


def distribute_syllables(
    syllable_count: int,
    voiced_regions: list[TimelineRegion],
) -> list[int]:
    if syllable_count <= 0:
        raise RuntimeError("G2P produced no lyric syllables.")
    if not voiced_regions:
        raise RuntimeError("Reference F0 contains no voiced regions.")

    # Regions shorter than a syllable are still allowed, but each region must
    # receive at least one syllable only when enough syllables exist. Otherwise
    # the shortest regions become sustained-vowel continuations.
    total_frames = sum(r.frames for r in voiced_regions)
    raw = [syllable_count * r.frames / total_frames for r in voiced_regions]
    counts = [int(math.floor(x)) for x in raw]

    if syllable_count >= len(voiced_regions):
        counts = [max(1, x) for x in counts]
    else:
        # Assign one syllable to the longest regions. Other regions will be
        # handled as continuation regions with a sustained previous vowel.
        order = sorted(range(len(voiced_regions)), key=lambda i: voiced_regions[i].frames, reverse=True)
        counts = [0] * len(voiced_regions)
        for i in order[:syllable_count]:
            counts[i] = 1
        return counts

    delta = syllable_count - sum(counts)
    fractions = [raw[i] - math.floor(raw[i]) for i in range(len(raw))]
    if delta > 0:
        order = sorted(range(len(raw)), key=lambda i: (fractions[i], voiced_regions[i].frames), reverse=True)
        for i in range(delta):
            counts[order[i % len(order)]] += 1
    elif delta < 0:
        order = sorted(range(len(raw)), key=lambda i: (fractions[i], voiced_regions[i].frames))
        remaining = -delta
        for idx in order:
            removable = max(0, counts[idx] - 1)
            take = min(removable, remaining)
            counts[idx] -= take
            remaining -= take
            if remaining == 0:
                break
        if remaining:
            raise RuntimeError("Cannot distribute syllables across voiced regions safely.")

    if sum(counts) != syllable_count:
        raise RuntimeError("Syllable distribution coverage invariant failed.")
    return counts


def split_integer(total: int, weights: list[float], minimum: int = 1) -> list[int]:
    if total <= 0 or not weights or any(x <= 0 for x in weights):
        raise ValueError("Invalid integer duration allocation request.")
    if total < minimum * len(weights):
        minimum = 1

    remaining = total - minimum * len(weights)
    if remaining < 0:
        raise ValueError("Not enough frames for phone allocation.")

    scaled = [remaining * w / sum(weights) for w in weights]
    values = [minimum + int(math.floor(x)) for x in scaled]
    delta = total - sum(values)
    order = sorted(range(len(weights)), key=lambda i: scaled[i] - math.floor(scaled[i]), reverse=True)
    for i in range(delta):
        values[order[i % len(order)]] += 1
    if sum(values) != total or any(x <= 0 for x in values):
        raise RuntimeError("Integer duration allocation invariant failed.")
    return values


def allocate_syllables_to_region(
    region: TimelineRegion,
    syllables: list[Syllable],
    timestep: float,
    min_consonant_sec: float,
    min_vowel_sec: float,
) -> list[PhoneSpan]:
    if not syllables:
        return []

    # Allocate region time across syllables using their minimum pronounceable
    # phone budgets. This prevents a 20 ms pitch fragment from receiving an
    # entire word, which caused V2's unintelligible humming.
    syllable_weights: list[float] = []
    for syllable in syllables:
        budget = sum(min_vowel_sec if p in VOWELS else min_consonant_sec for p in syllable.phones)
        syllable_weights.append(max(budget, timestep))

    syllable_frames = split_integer(region.frames, syllable_weights, minimum=1)
    result: list[PhoneSpan] = []
    cursor = region.start_frame

    for syllable, frames in zip(syllables, syllable_frames):
        phone_weights = [
            max(min_vowel_sec if p in VOWELS else min_consonant_sec, timestep)
            for p in syllable.phones
        ]
        phone_frames = split_integer(frames, phone_weights, minimum=1)
        for phone, count in zip(syllable.phones, phone_frames):
            result.append(PhoneSpan(phone, cursor, cursor + count))
            cursor += count

    if cursor != region.end_frame:
        raise RuntimeError("Voiced-region phone coverage invariant failed.")
    return result


def midi_to_name(midi: float) -> str:
    value = max(24, min(96, int(round(midi))))
    return f"{NOTE_NAMES[value % 12]}{value // 12 - 1}"


def f0_to_note(values: list[float], fallback: float) -> tuple[str, float]:
    voiced = sorted(x for x in values if x > 0)
    if voiced:
        hz = voiced[len(voiced) // 2]
    elif fallback > 0:
        hz = fallback
    else:
        return "rest", fallback
    midi = 69.0 + 12.0 * math.log2(hz / 440.0)
    return midi_to_name(midi), hz


def nearest_voiced_f0(f0: list[float], index: int) -> float:
    for radius in range(1, len(f0)):
        left = index - radius
        right = index + radius
        if left >= 0 and f0[left] > 0:
            return f0[left]
        if right < len(f0) and f0[right] > 0:
            return f0[right]
    return 0.0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phoenix V3 Arabic lyric rewrite using a pronounceable phone timeline derived from reference F0."
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
    ap.add_argument("--bridge-gap-sec", type=float, default=0.090)
    ap.add_argument("--remove-island-sec", type=float, default=0.025)
    ap.add_argument("--min-consonant-sec", type=float, default=0.035)
    ap.add_argument("--min-vowel-sec", type=float, default=0.080)
    args = ap.parse_args()

    reference_path = args.reference_ds.resolve()
    output_path = args.output.resolve()
    if not reference_path.is_file():
        raise FileNotFoundError(reference_path)

    reference, f0, timestep = parse_reference(reference_path)
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
    produced = {p for syllable in syllables for p in syllable.phones}
    if dictionary is not None:
        missing = sorted(produced - dictionary - SPECIAL_PHONES)
        if missing:
            raise RuntimeError(
                "G2P produced phones outside checkpoint 1600 vocabulary: "
                f"{missing}. Do not edit the dictionary manually."
            )

    mask = smooth_voicing(
        f0,
        timestep,
        bridge_gap_sec=args.bridge_gap_sec,
        remove_island_sec=args.remove_island_sec,
    )
    regions = build_regions(mask)
    voiced_regions = [r for r in regions if r.voiced]
    counts = distribute_syllables(len(syllables), voiced_regions)

    phone_spans: list[PhoneSpan] = []
    syllable_cursor = 0
    last_vowel = "a"
    voiced_index = 0

    for region in regions:
        if not region.voiced:
            phone_spans.append(PhoneSpan("SP", region.start_frame, region.end_frame))
            continue

        count = counts[voiced_index]
        voiced_index += 1
        if count > 0:
            assigned = syllables[syllable_cursor:syllable_cursor + count]
            syllable_cursor += count
            for syllable in assigned:
                vowels = [p for p in syllable.phones if p in VOWELS]
                if vowels:
                    last_vowel = vowels[-1]
            phone_spans.extend(
                allocate_syllables_to_region(
                    region,
                    assigned,
                    timestep,
                    args.min_consonant_sec,
                    args.min_vowel_sec,
                )
            )
        else:
            # More voiced regions than lyric syllables: sustain the previous
            # vowel rather than inventing a new onset consonant.
            phone_spans.append(PhoneSpan(last_vowel, region.start_frame, region.end_frame))

    if syllable_cursor != len(syllables):
        raise RuntimeError("Final syllable coverage invariant failed.")
    if not phone_spans or phone_spans[0].start_frame != 0:
        raise RuntimeError("Phone timeline does not start at frame zero.")
    for left, right in zip(phone_spans, phone_spans[1:]):
        if left.end_frame != right.start_frame:
            raise RuntimeError("Phone timeline contains a gap or overlap.")
    if phone_spans[-1].end_frame != len(f0):
        raise RuntimeError("Phone timeline does not cover the complete F0 sequence.")

    ph_seq: list[str] = []
    ph_dur: list[float] = []
    note_seq: list[str] = []
    note_dur: list[float] = []
    ph_num: list[int] = []
    note_slur: list[int] = []
    fallback_hz = 0.0

    for span in phone_spans:
        duration = span.frames * timestep
        if duration <= 0:
            raise RuntimeError("Generated a non-positive phone duration.")
        ph_seq.append(span.phone)
        ph_dur.append(duration)
        ph_num.append(1)

        if span.phone == "SP":
            note_seq.append("rest")
            note_dur.append(duration)
            note_slur.append(0)
            continue

        fallback = fallback_hz or nearest_voiced_f0(f0, span.start_frame)
        note, fallback_hz = f0_to_note(f0[span.start_frame:span.end_frame], fallback)
        if note == "rest":
            raise RuntimeError(
                f"Unable to derive pitch for voiced phone {span.phone!r} at frames "
                f"{span.start_frame}:{span.end_frame}."
            )
        note_seq.append(note)
        note_dur.append(duration)
        note_slur.append(0)

    total_duration = len(f0) * timestep
    if abs(sum(ph_dur) - total_duration) > 1e-7:
        raise RuntimeError("Phone timeline duration does not match reference F0 duration.")
    if abs(sum(note_dur) - total_duration) > 1e-7:
        raise RuntimeError("Note timeline duration does not match reference F0 duration.")

    non_silence = [d for p, d in zip(ph_seq, ph_dur) if p != "SP"]
    consonants = [d for p, d in zip(ph_seq, ph_dur) if p not in VOWELS and p != "SP"]
    vowels = [d for p, d in zip(ph_seq, ph_dur) if p in VOWELS]

    out = dict(reference)
    out.update({
        "text": args.text,
        "ph_seq": " ".join(ph_seq),
        "ph_dur": " ".join(f"{x:.9f}" for x in ph_dur),
        "ph_num": " ".join(str(x) for x in ph_num),
        "note_seq": " ".join(note_seq),
        "note_dur": " ".join(f"{x:.9f}" for x in note_dur),
        "note_slur": " ".join(str(x) for x in note_slur),
        "rewrite_engine": "phoenix_arabic_g2p_phone_timeline_v3",
        "rewrite_reference": "f0_seq_verbatim_phone_timeline_rebuilt",
        "g2p_module_path": str(frontend.module_path),
        "syllable_count": len(syllables),
        "phone_count": len(ph_seq),
        "voiced_region_count": len(voiced_regions),
        "reference_f0_preserved": True,
        "timeline_duration_sec": total_duration,
        "timing_policy": {
            "bridge_gap_sec": args.bridge_gap_sec,
            "remove_island_sec": args.remove_island_sec,
            "min_consonant_sec": args.min_consonant_sec,
            "min_vowel_sec": args.min_vowel_sec,
        },
    })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([out], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = {
        "status": "LYRICS_REWRITE_V3_DS_READY",
        "output": str(output_path),
        "g2p_words": len(converted.words),
        "syllables": len(syllables),
        "phones": len(ph_seq),
        "voiced_regions": len(voiced_regions),
        "duration_sec": round(total_duration, 6),
        "dictionary_checked": dictionary is not None,
        "reference_f0_preserved": True,
        "min_non_silence_phone_sec": round(min(non_silence), 6) if non_silence else None,
        "min_consonant_sec_actual": round(min(consonants), 6) if consonants else None,
        "min_vowel_sec_actual": round(min(vowels), 6) if vowels else None,
        "max_phone_sec": round(max(ph_dur), 6),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
