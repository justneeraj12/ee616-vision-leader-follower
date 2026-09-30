#!/usr/bin/env python3
"""Build a review ZIP containing exactly the Gate 7 frozen-file set."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]
CHECKSUM_PATH = PACKAGE_DIR / "FROZEN_SHA256SUMS"
OUTPUT_PATH = PROJECT_ROOT / "deliverables" / "Neeraj_Kanchani_EE616_Gate7_Frozen_Project_Package.zip"
SUMMARY_PATH = PACKAGE_DIR / "package_summary.json"
ARCHIVE_ROOT = "ee616-vision-leader-follower-gate7"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    if not CHECKSUM_PATH.is_file():
        raise FileNotFoundError("run verify_frozen_evidence.py --write first")
    relative_paths = []
    for line in CHECKSUM_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            _, relative = line.split("  ", 1)
            relative_paths.append(Path(relative))
    relative_paths.append(CHECKSUM_PATH.relative_to(PROJECT_ROOT))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(set(relative_paths), key=lambda path: path.as_posix()):
            source = PROJECT_ROOT / relative
            archive.write(source, f"{ARCHIVE_ROOT}/{relative.as_posix()}")
    summary = {
        "archive": OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "archive_sha256": _sha256(OUTPUT_PATH),
        "archive_size_bytes": OUTPUT_PATH.stat().st_size,
        "frozen_file_count": len(set(relative_paths)) - 1,
        "scope": "Frozen simulation project review package; not physical-robot or safety evidence.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

