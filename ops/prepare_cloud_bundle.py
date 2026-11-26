#!/usr/bin/env python3
"""Packages all persistent EXP-001 files into cloud_sync_bundle/ with SHA-256 manifest for Google Drive sync."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE_DIR = ROOT / "cloud_sync_bundle"

PERSISTENT_FILES = [
    "README.md",
    "CHARTER.md",
    "LEDGER.json",
    "JOURNAL.md",
    "ops/HUMAN_ACTION_ITEMS.md",
    "ops/HUMAN_ACTION_ITEMS.json",
    "ops/CLOUD_DRIVE_SYNC_PLAN.md",
    "research/001-market-scan.md",
    "research/002-monetization-and-distribution.md",
    "launch/LAUNCH_KIT_CN.md",
    "launch/LAUNCH_KIT_EN.md",
    "dist/veripr-pro-kit-v0.2.0.zip",
    "dist/SHA256SUMS.txt",
    "site/index.html",
    "site/styles.css",
    "site/app.js",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    manifest_entries = []
    for rel in PERSISTENT_FILES:
        src = ROOT / rel
        if not src.exists():
            raise FileNotFoundError(f"Missing persistent file for cloud sync: {rel}")
        dst = BUNDLE_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        manifest_entries.append(
            {
                "path": rel,
                "size_bytes": src.stat().st_size,
                "sha256": sha256_file(src),
            }
        )

    manifest = {
        "experiment_id": "EXP-001",
        "target_gdrive_folder": "Silicon-Partner-EXP-001",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_count": len(manifest_entries),
        "files": manifest_entries,
    }
    manifest_path = BUNDLE_DIR / "SYNC_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Prepared cloud_sync_bundle with {len(manifest_entries)} files + SYNC_MANIFEST.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
