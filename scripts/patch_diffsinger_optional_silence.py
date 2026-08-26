from __future__ import annotations

import argparse
from pathlib import Path

OLD = "        ph_idx_required = set(range(1, len(self.phoneme_dictionary)))\n"
NEW = """        ph_idx_required = set(range(1, len(self.phoneme_dictionary)))
        # AP/SP are optional silence/breath tokens. They are part of the
        # DiffSinger vocabulary, but a tightly cropped singing-only dataset
        # may legitimately contain neither token. Keep every real phoneme
        # mandatory while excluding AP/SP from the coverage gate.
        optional_ids = {
            idx for idx in ph_idx_required
            if self.phoneme_dictionary.decode_one(idx, scalar=False) in {'AP', 'SP'}
        }
        ph_idx_required.difference_update(optional_ids)
"""
MARKER = "# PHOENIX_OPTIONAL_AP_SP_PATCH_V1"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=True)
    args = ap.parse_args()
    path = Path(args.file).resolve()
    text = path.read_text(encoding='utf-8')
    if MARKER in text:
        print(f'Patch already present: {path}')
        return
    if OLD not in text:
        raise RuntimeError(f'Expected coverage line not found in {path}')
    patched = text.replace(OLD, NEW + f'        {MARKER}\n', 1)
    backup = path.with_suffix(path.suffix + '.phoenix-backup')
    if not backup.exists():
        backup.write_text(text, encoding='utf-8')
    path.write_text(patched, encoding='utf-8')
    print(f'Patched optional AP/SP coverage: {path}')
    print(f'Backup: {backup}')


if __name__ == '__main__':
    main()
