"""Command-line entry point for VeriPR v0.2.0."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .config import load_policy
from .core import VERSION, generate_receipt
from .render import BrandOptions, render_html, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VeriPR — Deterministic Verification Receipt & AI Anti-Cheat Auditor"
    )
    parser.add_argument("--version", action="version", version=f"VeriPR {VERSION}")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Target git repository")
    parser.add_argument("--base", default=None, help="Base git ref for diff (default: HEAD~1)")
    parser.add_argument("--head", default="HEAD", help="Head git ref (default: HEAD)")
    parser.add_argument("--staged", action="store_true", help="Inspect staged diff instead of commit diff")
    parser.add_argument("--config", type=Path, default=None, help="Path to .veripr.toml policy file")
    parser.add_argument(
        "--cmd",
        action="append",
        default=[],
        help="Verification command to execute (can be specified multiple times)",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Glob pattern of file paths to exclude from line-level cheat scanning",
    )
    parser.add_argument("--md", type=Path, default=None, help="Write Markdown PR receipt to path")
    parser.add_argument("--html", type=Path, default=None, help="Write HTML certificate to path")
    parser.add_argument("--json", type=Path, default=None, help="Write JSON receipt to path")
    parser.add_argument(
        "--fail-on-cheat",
        action="store_true",
        help="Exit non-zero if HIGH severity cheat signals or command failures occur",
    )
    # Pro white-label client delivery options
    parser.add_argument("--vendor", default="", help="[Pro] Vendor / agency / engineer brand name")
    parser.add_argument("--client", default="", help="[Pro] Client name for delivery certificate")
    parser.add_argument("--project", default="", help="[Pro] Display project name on certificate")
    parser.add_argument("--milestone", default="", help="[Pro] Delivery milestone label")
    parser.add_argument("--lang", choices=["en", "zh"], default="en", help="[Pro] Certificate language")
    parser.add_argument(
        "--signoff",
        action="store_true",
        help="[Pro] Include formal Vendor & Client acceptance sign-off block in HTML certificate",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg_path = args.config or (args.repo / ".veripr.toml")
    policy = load_policy(cfg_path if cfg_path.exists() else None)

    receipt = generate_receipt(
        repo=args.repo,
        base_ref=args.base,
        head_ref=args.head,
        staged=args.staged,
        commands=args.cmd,
        ignore_patterns=args.ignore,
        policy=policy,
    )

    brand = BrandOptions(
        vendor_name=args.vendor,
        client_name=args.client,
        project_name=args.project,
        milestone=args.milestone,
        lang=args.lang,
        include_signoff=args.signoff,
    )

    md = render_markdown(receipt)
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(md, encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(receipt, brand=brand), encoding="utf-8")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(asdict(receipt), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(md)
    if args.fail_on_cheat and receipt.verdict in ("CHEAT_SIGNALS_DETECTED", "VERIFICATION_FAILED"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
