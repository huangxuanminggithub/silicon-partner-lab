#!/usr/bin/env python3
"""
Syncs EXP-001 persistent diary, handover manual, governance ledger, research,
launch kits, Pro Kit ZIP, and full Git repo disaster-recovery snapshot to Google Drive.

Requires the official `gdrive` plugin CLI to be authenticated.
"""

from __future__ import annotations

import json
import re
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "ops" / "GDRIVE_SYNC_STATE.json"
DIST_DIR = ROOT / "dist"

FOLDERS = {
    "root": "1lnGdO__apbU48WpKarwJSE9PcYY2FkDu",
    "00_Diary_and_Handover": "14gQFG05ccuFIXVRoUDXVwPkdKMoeOsAq",
    "01_Governance_and_Ledger": "1vwm4CnqVuK8-TW7GiamqxFyTTNHqbxQ7",
    "02_Research_and_Strategy": "1sX3gf8_q8fc5ztyb7w_pBH3yJ7dFZ_pj",
    "03_Launch_and_Distribution": "1kzsF95euKxd5qTsjyBJnS7XOAkerH1MD",
    "04_Product_Releases": "1bz-Fl9Y8xJijd-cldbi2ARDAkQy31CZa",
}

UPLOAD_PLAN: list[tuple[str, str]] = [
    ("diary/00_HANDOVER_AND_CONTINUITY.md", "00_Diary_and_Handover"),
    ("diary/01_SILICON_DIARY_AND_DECISIONS.md", "00_Diary_and_Handover"),
    ("JOURNAL.md", "00_Diary_and_Handover"),
    ("CHARTER.md", "01_Governance_and_Ledger"),
    ("LEDGER.json", "01_Governance_and_Ledger"),
    ("ops/HUMAN_ACTION_ITEMS.md", "01_Governance_and_Ledger"),
    ("ops/HUMAN_ACTION_ITEMS.json", "01_Governance_and_Ledger"),
    ("ops/CLOUD_DRIVE_SYNC_PLAN.md", "01_Governance_and_Ledger"),
    ("research/001-market-scan.md", "02_Research_and_Strategy"),
    ("research/002-monetization-and-distribution.md", "02_Research_and_Strategy"),
    ("launch/LAUNCH_KIT_CN.md", "03_Launch_and_Distribution"),
    ("launch/LAUNCH_KIT_EN.md", "03_Launch_and_Distribution"),
    ("README.md", "03_Launch_and_Distribution"),
    ("dist/veripr-pro-kit-v0.2.0.zip", "04_Product_Releases"),
    ("dist/SHA256SUMS.txt", "04_Product_Releases"),
    ("dist/veripr-site-standalone.html", "04_Product_Releases"),
    ("dist/_samples/sample-client-certificate-zh.html", "04_Product_Releases"),
    ("dist/silicon-partner-lab-repo-snapshot.tar.gz", "04_Product_Releases"),
]

ID_RE = re.compile(r"ID:\s*([A-Za-z0-9_-]+)")


def build_repo_snapshot() -> Path:
    """Create a complete portable tar.gz snapshot (including .git history) for cross-server migration."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    snap_path = DIST_DIR / "silicon-partner-lab-repo-snapshot.tar.gz"
    exclude_dirs = {"__pycache__", "dist", "cloud_sync_bundle", "receipts"}

    def _filter(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
        parts = Path(info.name).parts
        if any(p in exclude_dirs for p in parts) or info.name.endswith(".pyc"):
            return None
        return info

    with tarfile.open(snap_path, "w:gz") as tf:
        for item in sorted(ROOT.iterdir()):
            if item.name in exclude_dirs:
                continue
            tf.add(item, arcname=item.name, filter=_filter)
    print(f"Built portable repo snapshot: {snap_path} ({snap_path.stat().st_size} bytes)")
    return snap_path


def upload_file(local_path: Path, parent_id: str) -> str:
    proc = subprocess.run(
        ["gdrive", "mutate", "upload", str(local_path), "--parent", parent_id],
        capture_output=True,
        text=True,
        check=True,
    )
    out = (proc.stdout + "\n" + proc.stderr).strip()
    m = ID_RE.search(out)
    file_id = m.group(1) if m else out
    print(f"Uploaded {local_path.name} -> {parent_id} (ID: {file_id})")
    return file_id


def main() -> int:
    build_repo_snapshot()
    synced = []
    for rel_path, folder_key in UPLOAD_PLAN:
        local = ROOT / rel_path
        if not local.exists():
            raise FileNotFoundError(f"Missing file to upload: {local}")
        fid = upload_file(local, FOLDERS[folder_key])
        synced.append(
            {
                "local_path": rel_path,
                "folder": folder_key,
                "parent_id": FOLDERS[folder_key],
                "drive_file_id": fid,
                "size_bytes": local.stat().st_size,
            }
        )

    state = {
        "experiment_id": "EXP-001",
        "root_folder_name": "Silicon-Partner-EXP-001",
        "root_folder_id": FOLDERS["root"],
        "root_folder_url": f"https://drive.google.com/drive/folders/{FOLDERS['root']}",
        "folders": FOLDERS,
        "last_synced_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "uploaded_files": synced,
    }
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Also upload the sync state manifest itself into 01_Governance_and_Ledger
    state_fid = upload_file(STATE_PATH, FOLDERS["01_Governance_and_Ledger"])
    print(f"Sync complete! {len(synced) + 1} files persisted to Google Drive (state ID: {state_fid}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
