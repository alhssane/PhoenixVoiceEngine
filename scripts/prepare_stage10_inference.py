import csv, json, math
from pathlib import Path

import click
import librosa
import numpy as np

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
F0_MIN = 65.0
F0_MAX = 1100.0
HOP_LENGTH = 512


def midi_to_name(midi: float) -> str:
    n = int(round(float(midi)))
    n = max(24, min(96, n))
    return f"{NOTE_NAMES[n % 12]}{n // 12 - 1}"


def f0_to_midi(f0):
    return 69.0 + 12.0 * np.log2(np.maximum(f0, 1e-6) / 440.0)


def extract_f0(y, sr):
    f0, _, _ = librosa.pyin(
        y,
        fmin=F0_MIN,
        fmax=F0_MAX,
        sr=sr,
        frame_length=2048,
        hop_length=HOP_LENGTH,
    )
    f0 = np.asarray(f0, dtype=np.float32)
    f0 = np.nan_to_num(f0, nan=0.0, posinf=0.0, neginf=0.0)
    f0 = np.clip(f0, 0.0, F0_MAX)
    return f0


def median_voiced_note_from_f0(f0, sr, start, dur):
    start_idx = max(0, int(round(start * sr / HOP_LENGTH)))
    end_idx = min(len(f0), int(round((start + dur) * sr / HOP_LENGTH)) + 1)
    vals = f0[start_idx:end_idx]
    vals = vals[vals > 0]
    if vals.size < 2:
        return 'rest'
    midi = float(np.median(f0_to_midi(vals)))
    return midi_to_name(midi)


@click.command()
@click.option('--raw', type=click.Path(exists=True, file_okay=False, path_type=Path), default=Path(r'D:/PhoenixVoiceEngine/datasets/freed_joud_diffsinger_raw/raw'))
@click.option('--out', type=click.Path(file_okay=True, dir_okay=False, path_type=Path), default=Path(r'D:/PhoenixVoiceEngine/samples/phoenix_freed_joud_stage10.ds'))
def main(raw: Path, out: Path):
    csv_path = raw / 'transcriptions.csv'
    wav_dir = raw / 'wavs'
    if not csv_path.exists():
        raise click.ClickException(f'Missing {csv_path}')

    rows = list(csv.DictReader(csv_path.open('r', encoding='utf-8')))
    if not rows:
        raise click.ClickException('transcriptions.csv is empty')

    row = next((r for r in rows if '<' not in r.get('ph_seq', '').split()), rows[0])
    name = row['name']
    ph_seq = row['ph_seq'].split()
    ph_dur = [float(x) for x in row['ph_dur'].split()]

    if len(ph_seq) != len(ph_dur):
        raise click.ClickException(f'{name}: ph_seq/ph_dur mismatch')

    wav = wav_dir / f'{name}.wav'
    if not wav.exists():
        raise click.ClickException(f'Missing WAV: {wav}')

    y, sr = librosa.load(wav, sr=None, mono=True)
    f0 = extract_f0(y, sr)
    f0_timestep = HOP_LENGTH / float(sr)

    notes = []
    note_durs = []
    ph_num = []
    t = 0.0

    for p, d in zip(ph_seq, ph_dur):
        note = 'rest' if p in {'SP', 'AP'} else median_voiced_note_from_f0(f0, sr, t, d)
        notes.append(note)
        note_durs.append(round(d, 6))
        ph_num.append(1)
        t += d

    # Keep one note per phoneme for a deterministic acoustic smoke test.
    payload = [{
        'offset': 0.0,
        'text': row.get('name', name),
        'ph_seq': ' '.join(ph_seq),
        'ph_dur': ' '.join(f'{x:.6f}' for x in ph_dur),
        'ph_num': ' '.join(str(x) for x in ph_num),
        'note_seq': ' '.join(notes),
        'note_dur': ' '.join(f'{x:.6f}' for x in note_durs),
        'note_slur': ' '.join('0' for _ in notes),
        'f0_seq': ' '.join(f'{float(x):.6f}' for x in f0),
        'f0_timestep': f0_timestep,
    }]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    print(json.dumps({
        'status': 'STAGE10_DS_READY',
        'source': name,
        'phones': len(ph_seq),
        'notes': len(notes),
        'f0_values': len(f0),
        'f0_timestep': f0_timestep,
        'voiced_frames': int(np.count_nonzero(f0 > 0)),
        'ds_file': str(out),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
