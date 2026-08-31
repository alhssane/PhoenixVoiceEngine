#!/usr/bin/env python3
"""Prepare a guarded DiffSinger acoustic generalization experiment.

The tool copies an existing YAML configuration and changes only explicitly
requested scalar keys. It refuses to overwrite the source, verifies that
position embeddings are disabled, and writes a machine-readable manifest.

DiffSinger configs commonly inherit settings through ``base_config``. Therefore
an override such as ``use_pos_embed: false`` is allowed to be absent from the
child config and is inserted at top level so it overrides the inherited value.

This is an ablation/generalization experiment, not a claim that a tiny dataset
is sufficient for production lyric replacement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCALAR_RE = re.compile(
    r"^(?P<indent>\s*)(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?P<sep>\s*:\s*)"
    r"(?P<value>.*?)(?P<comment>\s+#.*)?$"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if re.fullmatch(r"[A-Za-z0-9_./\\:-]+", text):
        return text
    return json.dumps(text, ensure_ascii=False)


def replace_top_level_scalar(
    text: str, key: str, value: Any, *, required: bool
) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    hits = 0
    replacement = yaml_scalar(value)
    output: list[str] = []

    for line in lines:
        raw = line.rstrip("\r\n")
        ending = line[len(raw):]
        match = SCALAR_RE.match(raw)
        if match and not match.group("indent") and match.group("key") == key:
            comment = match.group("comment") or ""
            output.append(f"{key}: {replacement}{comment}{ending}")
            hits += 1
        else:
            output.append(line)

    if hits == 0:
        if required:
            raise ValueError(f"Required top-level YAML key not found: {key}")
        if output and not output[-1].endswith(("\n", "\r")):
            output[-1] += "\n"
        output.append(f"{key}: {replacement}\n")
        hits = 1
    elif hits > 1:
        raise ValueError(f"Top-level YAML key appears more than once: {key}")

    return "".join(output), hits


def read_top_level_scalar(text: str, key: str) -> str | None:
    for line in text.splitlines():
        match = SCALAR_RE.match(line)
        if match and not match.group("indent") and match.group("key") == key:
            return match.group("value").strip()
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config", required=True, type=Path)
    parser.add_argument("--output-config", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument(
        "--experiment-name", default="phoenix_freed_joud_generalization_v1"
    )
    parser.add_argument("--binary-data-dir", default=None)
    parser.add_argument("--work-dir", default=None)
    args = parser.parse_args()

    source = args.base_config.resolve()
    output = args.output_config.resolve()
    manifest_path = args.manifest.resolve()

    if not source.is_file():
        raise FileNotFoundError(source)
    if source == output:
        raise ValueError("Refusing to overwrite the base configuration")

    source_bytes = source.read_bytes()
    text = source_bytes.decode("utf-8-sig")

    # Child configs inherit values from base_config. Explicitly writing this at
    # top level is the intended override when the base config owns the key.
    text, _ = replace_top_level_scalar(text, "use_pos_embed", False, required=False)

    # Experiment identity keys vary across DiffSinger configurations. If no
    # identity key exists in the child, add exp_name explicitly so the new run
    # cannot silently share the old experiment namespace.
    exp_key = None
    for candidate in ("exp_name", "experiment_name"):
        if read_top_level_scalar(text, candidate) is not None:
            text, _ = replace_top_level_scalar(
                text, candidate, args.experiment_name, required=True
            )
            exp_key = candidate
            break
    if exp_key is None:
        text, _ = replace_top_level_scalar(
            text, "exp_name", args.experiment_name, required=False
        )
        exp_key = "exp_name"

    if args.binary_data_dir is not None:
        text, _ = replace_top_level_scalar(
            text, "binary_data_dir", args.binary_data_dir, required=False
        )
    if args.work_dir is not None:
        text, _ = replace_top_level_scalar(
            text, "work_dir", args.work_dir, required=False
        )

    if read_top_level_scalar(text, "use_pos_embed") != "false":
        raise RuntimeError("Failed to disable use_pos_embed")

    if read_top_level_scalar(text, exp_key) != yaml_scalar(args.experiment_name):
        raise RuntimeError(f"Failed to set {exp_key}")

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")

    output_bytes = output.read_bytes()
    manifest = {
        "status": "GENERALIZATION_EXPERIMENT_CONFIG_READY",
        "base_config": str(source),
        "output_config": str(output),
        "base_sha256": sha256_bytes(source_bytes),
        "output_sha256": sha256_bytes(output_bytes),
        "experiment_name_requested": args.experiment_name,
        "experiment_name_key_updated": exp_key,
        "use_pos_embed": False,
        "binary_data_dir": args.binary_data_dir,
        "work_dir": args.work_dir,
        "guardrails": {
            "base_not_overwritten": True,
            "position_embedding_disabled": True,
            "checkpoint_reuse_not_configured_by_this_tool": True,
        },
        "warning": (
            "This configuration is for a controlled generalization ablation. "
            "Eleven training samples remain insufficient for production lyric replacement."
        ),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
