#!/usr/bin/env python3
"""Builds the distributable VeriPR Pro Kit ZIP archive and SHA-256 checksums."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERIPR_DIR = ROOT / "products" / "veripr"
DIST_DIR = ROOT / "dist"
VERSION = "0.2.0"
ZIP_NAME = f"veripr-pro-kit-v{VERSION}.zip"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_samples(samples_dir: Path) -> None:
    samples_dir.mkdir(parents=True, exist_ok=True)
    env = dict(**__import__("os").environ, PYTHONPATH=str(VERIPR_DIR))
    # Generate sample white-label bilingual Chinese client certificate
    subprocess.run(
        [
            sys.executable,
            "-m",
            "veripr",
            "--repo",
            str(ROOT),
            "--ignore",
            "products/veripr/veripr/*",
            "--ignore",
            "products/veripr/tests/*",
            "--ignore",
            "site/*",
            "--ignore",
            "*.md",
            "--cmd",
            "python3 -m unittest discover -s tests -v",
            "--cmd",
            "python3 ledger.py verify",
            "--vendor",
            "Silicon Partner Lab (示例交付方)",
            "--client",
            "示例验收甲方科技公司",
            "--project",
            "VeriPR v0.2.0 交付演示",
            "--milestone",
            "Milestone 1 · 确定性验收闭环",
            "--lang",
            "zh",
            "--signoff",
            "--html",
            str(samples_dir / "sample-client-certificate-zh.html"),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    # Generate sample Sprint Rollup Scorecard
    subprocess.run(
        [
            sys.executable,
            "-m",
            "veripr.rollup",
            "--repo",
            str(ROOT),
            "--limit",
            "10",
            "--ignore",
            "products/veripr/veripr/*",
            "--ignore",
            "products/veripr/tests/*",
            "--ignore",
            "site/*",
            "--ignore",
            "*.md",
            "--html",
            str(samples_dir / "sample-sprint-scorecard.html"),
            "--csv",
            str(samples_dir / "sample-sprint-scorecard.csv"),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def build_zip() -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    samples_dir = DIST_DIR / "_samples"
    build_samples(samples_dir)

    zip_path = DIST_DIR / ZIP_NAME
    prefix = f"veripr-pro-kit-v{VERSION}"

    include_files: list[tuple[Path, str]] = [
        (VERIPR_DIR / "pyproject.toml", f"{prefix}/pyproject.toml"),
        (VERIPR_DIR / "README.md", f"{prefix}/README.md"),
        (VERIPR_DIR / "action.yml", f"{prefix}/action.yml"),
        (VERIPR_DIR / "veripr.py", f"{prefix}/veripr.py"),
        (ROOT / "CHARTER.md", f"{prefix}/bonus_silicon_partner/CHARTER.md"),
        (ROOT / "ledger.py", f"{prefix}/bonus_silicon_partner/ledger.py"),
    ]

    for py_file in sorted((VERIPR_DIR / "veripr").glob("*.py")):
        include_files.append((py_file, f"{prefix}/veripr/{py_file.name}"))

    for test_file in sorted((VERIPR_DIR / "tests").glob("*.py")):
        include_files.append((test_file, f"{prefix}/tests/{test_file.name}"))

    for pro_file in sorted((VERIPR_DIR / "pro_kit").rglob("*")):
        if pro_file.is_file():
            rel = pro_file.relative_to(VERIPR_DIR / "pro_kit")
            include_files.append((pro_file, f"{prefix}/pro_kit/{rel.as_posix()}"))

    for sample_file in sorted(samples_dir.glob("*")):
        if sample_file.is_file():
            include_files.append((sample_file, f"{prefix}/samples/{sample_file.name}"))

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src, arcname in include_files:
            zf.write(src, arcname=arcname)

    digest = sha256_file(zip_path)
    (DIST_DIR / "SHA256SUMS.txt").write_text(f"{digest}  {ZIP_NAME}\n", encoding="utf-8")
    print(f"Built {zip_path} ({zip_path.stat().st_size} bytes)")
    print(f"SHA-256: {digest}")
    return zip_path


if __name__ == "__main__":
    build_zip()
