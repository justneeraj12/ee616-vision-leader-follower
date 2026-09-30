#!/usr/bin/env python3
"""Create or verify the Gate 7 frozen-evidence checksum manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import yaml


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]
MANIFEST_PATH = PACKAGE_DIR / "gate7_manifest.yaml"
CHECKSUM_PATH = PACKAGE_DIR / "FROZEN_SHA256SUMS"


def _load_manifest() -> dict:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Gate 7 manifest must contain a mapping")
    return data


def _is_excluded(path: Path, manifest: dict) -> bool:
    relative = path.relative_to(PROJECT_ROOT)
    excluded_names = set(manifest.get("excluded_generated_names", []))
    if any(part in excluded_names for part in relative.parts):
        return True
    return any(path.name.endswith(suffix) for suffix in manifest.get("excluded_suffixes", []))


def _frozen_files(manifest: dict) -> list[Path]:
    collected: set[Path] = set()
    for raw in manifest["frozen_sources"]:
        source = PROJECT_ROOT / raw
        if not source.exists():
            raise FileNotFoundError(f"required frozen source does not exist: {raw}")
        candidates = source.rglob("*") if source.is_dir() else [source]
        for candidate in candidates:
            if candidate.is_file() and not candidate.is_symlink() and not _is_excluded(candidate, manifest):
                collected.add(candidate.resolve())
    collected.add(MANIFEST_PATH.resolve())
    collected.add((PACKAGE_DIR / "verify_frozen_evidence.py").resolve())
    collected.add((PACKAGE_DIR / "build_review_package.py").resolve())
    return sorted(collected, key=lambda path: path.relative_to(PROJECT_ROOT).as_posix())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _status_errors(manifest: dict) -> list[str]:
    errors = []
    for item in manifest["evidence_status_expectations"]:
        path = PROJECT_ROOT / item["path"]
        if not path.is_file():
            errors.append(f"missing evidence summary: {item['path']}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        actual = data.get("status")
        if actual != item["expected"]:
            errors.append(
                f"status mismatch for {item['path']}: expected {item['expected']}, got {actual}"
            )
    return errors


def write_checksums(manifest: dict) -> int:
    errors = _status_errors(manifest)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    lines = [
        f"{_sha256(path)}  {path.relative_to(PROJECT_ROOT).as_posix()}"
        for path in _frozen_files(manifest)
        if path != CHECKSUM_PATH.resolve()
    ]
    CHECKSUM_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} frozen-file checksums to {CHECKSUM_PATH}")
    return 0


def verify_checksums(manifest: dict) -> int:
    errors = _status_errors(manifest)
    if not CHECKSUM_PATH.is_file():
        errors.append("missing FROZEN_SHA256SUMS; run with --write first")
    else:
        for line_number, line in enumerate(CHECKSUM_PATH.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                expected, relative = line.split("  ", 1)
            except ValueError:
                errors.append(f"invalid checksum line {line_number}")
                continue
            path = PROJECT_ROOT / relative
            if not path.is_file():
                errors.append(f"missing frozen file: {relative}")
            elif _sha256(path) != expected:
                errors.append(f"checksum mismatch: {relative}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    count = sum(1 for line in CHECKSUM_PATH.read_text(encoding="utf-8").splitlines() if line.strip())
    print(f"Gate 7 verification passed: {count} files and all evidence statuses match.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="replace the checksum manifest")
    args = parser.parse_args()
    manifest = _load_manifest()
    return write_checksums(manifest) if args.write else verify_checksums(manifest)


if __name__ == "__main__":
    raise SystemExit(main())
