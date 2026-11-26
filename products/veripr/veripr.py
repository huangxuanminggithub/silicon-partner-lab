#!/usr/bin/env python3
"""
VeriPR v0.1 — Deterministic Proof-of-Verification & Anti-Cheat Receipt for AI-Assisted PRs.

Zero dependencies. Zero LLM calls. 100% deterministic.
Scans git diffs for common AI coding shortcuts/cheating patterns (skipped tests,
deleted assertions, suppressed linters/typechecks, silent exception swallowing,
sensitive path touches), runs real verification commands bound to HEAD SHA, and
emits tamper-evident SHA-256 receipts in Markdown, JSON, and self-contained HTML.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "0.1.0"


@dataclass
class Finding:
    severity: str  # HIGH | MEDIUM | INFO
    category: str  # TEST_TAMPERING | LINT_SUPPRESSION | ERROR_SWALLOWING | SECRET_OR_DEBUG | SENSITIVE_PATH
    file: str
    line_preview: str
    rule: str
    detail: str


@dataclass
class CommandRun:
    command: str
    exit_code: int
    duration_sec: float
    stdout_sha256: str
    stderr_sha256: str
    output_sha256: str
    output_tail: str


@dataclass
class Receipt:
    tool: str
    version: str
    generated_at: str
    repo_name: str
    branch: str
    base_ref: str
    head_sha: str
    working_tree_dirty: bool
    files_changed: int
    insertions: int
    deletions: int
    assertions_added: int
    assertions_removed: int
    test_files_deleted: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    commands: list[CommandRun] = field(default_factory=list)
    verdict: str = "VERIFIED_CLEAN"
    receipt_sha256: str = ""


# Deterministic pattern rules applied ONLY to newly added lines in git diff.
ADDED_LINE_RULES: list[tuple[str, str, str, re.Pattern[str], str]] = [
    (
        "HIGH",
        "TEST_TAMPERING",
        "test-skip-added",
        re.compile(
            r"\b(it|test|describe|context)\.skip\s*\(|\bx(it|test|describe)\s*\(|"
            r"@pytest\.mark\.skip\b|@unittest\.skip\b|\bt\.Skip\s*\(|#\[ignore\]",
            re.IGNORECASE,
        ),
        "Newly added test skip directive detected in diff",
    ),
    (
        "HIGH",
        "LINT_SUPPRESSION",
        "typecheck-suppression",
        re.compile(r"@ts-ignore\b|@ts-expect-error\b|@ts-nocheck\b|#\s*type:\s*ignore\b"),
        "Newly added static type-check suppression directive",
    ),
    (
        "MEDIUM",
        "LINT_SUPPRESSION",
        "linter-or-coverage-suppression",
        re.compile(
            r"eslint-disable\b|#\s*noqa\b|#\s*pragma:\s*no\s*cover\b|//\s*nolint\b|#\[allow\("
        ),
        "Newly added linter or test-coverage suppression directive",
    ),
    (
        "MEDIUM",
        "LINT_SUPPRESSION",
        "ts-any-escape-hatch",
        re.compile(r"\bas\s+any\b|:\s*any\b"),
        "TypeScript `any` escape hatch introduced",
    ),
    (
        "MEDIUM",
        "ERROR_SWALLOWING",
        "empty-catch-or-bare-except",
        re.compile(
            r"^\s*except\s*:\s*$|^\s*except\s+Exception(\s+as\s+\w+)?\s*:\s*pass\s*$|"
            r"catch\s*\([^)]*\)\s*\{\s*\}"
        ),
        "Potential silent error swallowing introduced",
    ),
    (
        "HIGH",
        "SECRET_OR_DEBUG",
        "potential-hardcoded-secret",
        re.compile(
            r"\bsk-[A-Za-z0-9]{20,}\b|\bghp_[A-Za-z0-9]{20,}\b|\bAKIA[0-9A-Z]{16}\b|"
            r"BEGIN\s+(RSA|EC|OPENSSH|PRIVATE)\s+KEY"
        ),
        "Potential hardcoded credential or private key detected",
    ),
    (
        "INFO",
        "SECRET_OR_DEBUG",
        "debug-breakpoint-leftover",
        re.compile(r"\b(pdb\.set_trace|breakpoint)\s*\(|\bdebugger\s*;"),
        "Interactive debugger breakpoint left in code",
    ),
]

SENSITIVE_PATH_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("CI/CD workflow", re.compile(r"(^|/)\.github/workflows/")),
    ("Authentication / Authorization", re.compile(r"(^|/)(auth|oauth|login|rbac|acl|permission)", re.I)),
    ("Payments / Billing / Ledger", re.compile(r"(^|/)(billing|payment|stripe|checkout|ledger|wallet)", re.I)),
    ("Database Migration / Schema", re.compile(r"(^|/)(migrations?|schema\.sql|alembic)", re.I)),
    ("Environment / Secrets Config", re.compile(r"(^|/)\.env(\.|$)|secrets?\.(ya?ml|json)", re.I)),
    ("Dependency Lockfile", re.compile(r"(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock|poetry\.lock|uv\.lock)$")),
]

NON_SOURCE_ARTIFACT_PATTERN = re.compile(
    r"(^|/)__pycache__/|\.(pyc|pyo|pyd|class|o|so|dylib|dll)$", re.I
)
TEST_FILE_PATTERN = re.compile(
    r"(^|/)(tests?|__tests__|spec)/|(\.|_)(test|spec)\.[A-Za-z0-9]+$|^test_.*\.py$", re.I
)
ASSERTION_PATTERN = re.compile(
    r"\b(assert\w*|expect|should|assertEqual|assertTrue|assertFalse|assertRaises|require\.\w+)\b"
)


def is_test_source_file(path: str) -> bool:
    if not path or NON_SOURCE_ARTIFACT_PATTERN.search(path):
        return False
    return bool(TEST_FILE_PATTERN.search(path))


def run_git(repo: Path, args: list[str], check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def resolve_diff_text(repo: Path, base_ref: str | None, staged: bool) -> tuple[str, str]:
    if staged:
        return "STAGED", run_git(repo, ["diff", "--cached", "--unified=0", "--no-color"])

    if base_ref:
        return base_ref, run_git(repo, ["diff", f"{base_ref}...HEAD", "--unified=0", "--no-color"])

    # Default: diff against HEAD~1 if available, else empty tree for initial commit
    has_parent = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD~1"],
        cwd=repo,
        capture_output=True,
        text=True,
    ).returncode == 0
    if has_parent:
        return "HEAD~1", run_git(repo, ["diff", "HEAD~1..HEAD", "--unified=0", "--no-color"])
    empty_tree = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    return "EMPTY_TREE", run_git(repo, ["diff", empty_tree, "HEAD", "--unified=0", "--no-color"])


def analyze_diff(diff_text: str, ignore_patterns: list[str] | None = None) -> dict[str, Any]:
    import fnmatch

    ignore_patterns = ignore_patterns or []
    current_file = ""
    touched_files: set[str] = set()
    test_files_deleted: list[str] = []
    insertions = 0
    deletions = 0
    assertions_added = 0
    assertions_removed = 0
    findings: list[Finding] = []
    flagged_sensitive: set[tuple[str, str]] = set()
    prev_added_line = ""

    def is_ignored(path: str) -> bool:
        return any(fnmatch.fnmatch(path, pat) for pat in ignore_patterns)

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            parts = raw_line.split(" ")
            if len(parts) >= 4:
                current_file = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                touched_files.add(current_file)
            prev_added_line = ""
            continue

        if raw_line.startswith("deleted file mode "):
            if current_file and not is_ignored(current_file) and is_test_source_file(current_file):
                test_files_deleted.append(current_file)
                findings.append(
                    Finding(
                        severity="HIGH",
                        category="TEST_TAMPERING",
                        file=current_file,
                        line_preview="(entire test file deleted)",
                        rule="test-file-deleted",
                        detail="A test file was deleted in this diff",
                    )
                )
            continue

        if raw_line.startswith("+++ ") or raw_line.startswith("--- ") or raw_line.startswith("@@ "):
            prev_added_line = ""
            continue

        if raw_line.startswith("+"):
            insertions += 1
            content = raw_line[1:]
            is_test = is_test_source_file(current_file)
            if is_test and ASSERTION_PATTERN.search(content):
                assertions_added += 1

            if is_ignored(current_file):
                prev_added_line = content
                continue

            # Check two-line Python silent except/pass pattern
            if re.match(r"^\s*pass\s*$", content) and re.match(
                r"^\s*except(\s+Exception(\s+as\s+\w+)?)?\s*:\s*$", prev_added_line
            ):
                findings.append(
                    Finding(
                        severity="MEDIUM",
                        category="ERROR_SWALLOWING",
                        file=current_file,
                        line_preview=f"{prev_added_line.strip()} pass",
                        rule="silent-except-pass",
                        detail="Silent `except: pass` error swallowing block introduced",
                    )
                )

            for sev, cat, rule_name, pattern, detail in ADDED_LINE_RULES:
                if pattern.search(content):
                    findings.append(
                        Finding(
                            severity=sev,
                            category=cat,
                            file=current_file,
                            line_preview=content.strip()[:120],
                            rule=rule_name,
                            detail=detail,
                        )
                    )
            prev_added_line = content

        elif raw_line.startswith("-"):
            deletions += 1
            content = raw_line[1:]
            if is_test_source_file(current_file) and ASSERTION_PATTERN.search(content):
                assertions_removed += 1
            prev_added_line = ""

    # Flag net assertion drop across test files
    if assertions_removed > assertions_added and (assertions_removed - assertions_added) >= 2:
        findings.append(
            Finding(
                severity="HIGH",
                category="TEST_TAMPERING",
                file="(test suite)",
                line_preview=f"-{assertions_removed} removed / +{assertions_added} added assertions",
                rule="net-assertion-drop",
                detail=(
                    f"Net drop of {assertions_removed - assertions_added} test assertions "
                    "across modified test files — verify tests were not weakened"
                ),
            )
        )

    # Sensitive path radar
    for fpath in sorted(touched_files):
        if NON_SOURCE_ARTIFACT_PATTERN.search(fpath):
            continue
        for label, pat in SENSITIVE_PATH_PATTERNS:
            if pat.search(fpath) and (fpath, label) not in flagged_sensitive:
                flagged_sensitive.add((fpath, label))
                findings.append(
                    Finding(
                        severity="INFO",
                        category="SENSITIVE_PATH",
                        file=fpath,
                        line_preview=fpath,
                        rule="sensitive-path-touched",
                        detail=f"Touches sensitive surface: {label}",
                    )
                )

    return {
        "files_changed": len(touched_files),
        "insertions": insertions,
        "deletions": deletions,
        "assertions_added": assertions_added,
        "assertions_removed": assertions_removed,
        "test_files_deleted": test_files_deleted,
        "findings": findings,
    }


def execute_verification_commands(repo: Path, commands: list[str]) -> list[CommandRun]:
    results: list[CommandRun] = []
    for cmd in commands:
        start = time.monotonic()
        proc = subprocess.run(
            cmd,
            cwd=repo,
            shell=True,
            capture_output=True,
            text=True,
        )
        duration = round(time.monotonic() - start, 3)
        stdout_hash = hashlib.sha256(proc.stdout.encode("utf-8", errors="replace")).hexdigest()
        stderr_hash = hashlib.sha256(proc.stderr.encode("utf-8", errors="replace")).hexdigest()
        combined = (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()
        output_hash = hashlib.sha256(combined.encode("utf-8", errors="replace")).hexdigest()
        tail_lines = combined.splitlines()[-12:] if combined else ["(no output)"]
        results.append(
            CommandRun(
                command=cmd,
                exit_code=proc.returncode,
                duration_sec=duration,
                stdout_sha256=stdout_hash,
                stderr_sha256=stderr_hash,
                output_sha256=output_hash,
                output_tail="\n".join(tail_lines),
            )
        )
    return results


def determine_verdict(findings: list[Finding], commands: list[CommandRun]) -> str:
    if any(c.exit_code != 0 for c in commands):
        return "VERIFICATION_FAILED"
    if any(f.severity == "HIGH" for f in findings):
        return "CHEAT_SIGNALS_DETECTED"
    if any(f.severity == "MEDIUM" for f in findings):
        return "VERIFIED_WITH_WARNINGS"
    return "VERIFIED_CLEAN"


def seal_receipt(receipt: Receipt) -> str:
    payload = asdict(receipt)
    payload.pop("receipt_sha256", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_receipt(
    repo: Path,
    base_ref: str | None = None,
    staged: bool = False,
    commands: list[str] | None = None,
    ignore_patterns: list[str] | None = None,
) -> Receipt:
    repo = repo.resolve()
    head_sha = run_git(repo, ["rev-parse", "HEAD"]).strip()
    branch = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    dirty = bool(run_git(repo, ["status", "--porcelain"]).strip())
    resolved_base, diff_text = resolve_diff_text(repo, base_ref, staged)

    diff_stats = analyze_diff(diff_text, ignore_patterns=ignore_patterns)
    cmd_runs = execute_verification_commands(repo, commands or [])
    verdict = determine_verdict(diff_stats["findings"], cmd_runs)

    receipt = Receipt(
        tool="VeriPR",
        version=VERSION,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        repo_name=repo.name,
        branch=branch,
        base_ref=resolved_base,
        head_sha=head_sha,
        working_tree_dirty=dirty,
        files_changed=diff_stats["files_changed"],
        insertions=diff_stats["insertions"],
        deletions=diff_stats["deletions"],
        assertions_added=diff_stats["assertions_added"],
        assertions_removed=diff_stats["assertions_removed"],
        test_files_deleted=diff_stats["test_files_deleted"],
        findings=diff_stats["findings"],
        commands=cmd_runs,
        verdict=verdict,
    )
    receipt.receipt_sha256 = seal_receipt(receipt)
    return receipt


def render_markdown(r: Receipt) -> str:
    badge = {
        "VERIFIED_CLEAN": "✅ VERIFIED CLEAN",
        "VERIFIED_WITH_WARNINGS": "⚠️ VERIFIED WITH WARNINGS",
        "CHEAT_SIGNALS_DETECTED": "🚨 CHEAT / RISK SIGNALS DETECTED",
        "VERIFICATION_FAILED": "❌ VERIFICATION FAILED",
    }.get(r.verdict, r.verdict)

    lines = [
        f"## VeriPR Proof-of-Verification Receipt — {badge}",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Repository / Branch | `{r.repo_name}` (`{r.branch}`) |",
        f"| Commit Scope | `{r.base_ref}` → `{r.head_sha[:12]}` |",
        f"| Working Tree | {'⚠️ Dirty (uncommitted changes present)' if r.working_tree_dirty else '✅ Clean'} |",
        f"| Diff Footprint | `{r.files_changed}` files (`+{r.insertions}` / `-{r.deletions}`) |",
        f"| Test Assertion Delta | `+{r.assertions_added}` added / `-{r.assertions_removed}` removed |",
        f"| Receipt Seal (SHA-256) | `{r.receipt_sha256[:24]}...` |",
        f"| Generated (UTC) | `{r.generated_at}` |",
        "",
    ]

    lines.append("### 1. Deterministic Verification Runs")
    if not r.commands:
        lines.append("_No verification commands were executed._")
    else:
        lines.append("| Command | Status | Duration | Output Digest (SHA-256) |")
        lines.append("| --- | --- | --- | --- |")
        for c in r.commands:
            st = "✅ PASS (0)" if c.exit_code == 0 else f"❌ FAIL ({c.exit_code})"
            lines.append(f"| `{c.command}` | {st} | {c.duration_sec}s | `{c.output_sha256[:16]}` |")
        for idx, c in enumerate(r.commands, 1):
            lines.extend(
                [
                    "",
                    f"<details><summary>Command #{idx} output tail (`{c.command}`)</summary>",
                    "",
                    "```text",
                    c.output_tail,
                    "```",
                    "</details>",
                ]
            )

    lines.append("")
    lines.append("### 2. Anti-Cheat & Risk Surface Audit")
    if not r.findings:
        lines.append("✅ No test-tampering, lint-suppression, error-swallowing, or sensitive-path signals detected.")
    else:
        lines.append("| Severity | Rule | File | Detail |")
        lines.append("| --- | --- | --- | --- |")
        for f in r.findings:
            lines.append(
                f"| `{f.severity}` | `{f.rule}` | `{f.file}` | {f.detail} (`{f.line_preview}`) |"
            )

    lines.extend(
        [
            "",
            f"> Sealed deterministically by **VeriPR v{r.version}** (0 LLM calls, 0 tokens burned).",
            "",
        ]
    )
    return "\n".join(lines)


def render_html(r: Receipt) -> str:
    colors = {
        "VERIFIED_CLEAN": ("#065f46", "#d1fae5", "#10b981"),
        "VERIFIED_WITH_WARNINGS": ("#92400e", "#fef3c7", "#f59e0b"),
        "CHEAT_SIGNALS_DETECTED": ("#991b1b", "#fee2e2", "#ef4444"),
        "VERIFICATION_FAILED": ("#991b1b", "#fee2e2", "#ef4444"),
    }
    fg, bg, border = colors.get(r.verdict, ("#1f2937", "#f3f4f6", "#9ca3af"))

    cmd_rows = ""
    if not r.commands:
        cmd_rows = "<tr><td colspan='4' class='muted'>No verification commands executed.</td></tr>"
    else:
        for c in r.commands:
            pill_cls = "pass" if c.exit_code == 0 else "fail"
            pill_txt = "PASS (0)" if c.exit_code == 0 else f"FAIL ({c.exit_code})"
            cmd_rows += (
                f"<tr>"
                f"<td><code>{html.escape(c.command)}</code></td>"
                f"<td><span class='pill {pill_cls}'>{pill_txt}</span></td>"
                f"<td>{c.duration_sec}s</td>"
                f"<td><code>{c.output_sha256[:16]}</code></td>"
                f"</tr>"
            )

    finding_rows = ""
    if not r.findings:
        finding_rows = (
            "<tr><td colspan='4' class='clean'>No test-tampering, linter-suppression, "
            "or sensitive-path alerts detected.</td></tr>"
        )
    else:
        for f in r.findings:
            sev_cls = f.severity.lower()
            finding_rows += (
                f"<tr>"
                f"<td><span class='pill {sev_cls}'>{html.escape(f.severity)}</span></td>"
                f"<td><code>{html.escape(f.rule)}</code></td>"
                f"<td><code>{html.escape(f.file)}</code></td>"
                f"<td>{html.escape(f.detail)}<div class='preview'>{html.escape(f.line_preview)}</div></td>"
                f"</tr>"
            )

    dirty_text = "Dirty (uncommitted edits)" if r.working_tree_dirty else "Clean"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VeriPR Certificate — {html.escape(r.repo_name)} ({r.head_sha[:8]})</title>
<style>
  :root {{ --ink:#0f172a; --muted:#475569; --line:#e2e8f0; --panel:#ffffff; --bg:#f8fafc; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:32px 16px; background:var(--bg); color:var(--ink);
         font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  .cert {{ max-width:920px; margin:0 auto; background:var(--panel); border:1px solid var(--line);
           border-radius:14px; box-shadow:0 8px 30px rgba(15,23,42,.06); overflow:hidden; }}
  .header {{ padding:28px 32px; border-bottom:1px solid var(--line); display:flex;
             justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; }}
  .brand {{ font-size:12px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); font-weight:700; }}
  h1 {{ margin:6px 0 4px; font-size:24px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); font-size:13px; }}
  .verdict {{ padding:8px 14px; border-radius:999px; font-weight:700; font-size:12px;
              letter-spacing:.04em; color:{fg}; background:{bg}; border:1px solid {border}; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px;
           padding:20px 32px; background:#fbfdff; border-bottom:1px solid var(--line); }}
  .kpi {{ padding:12px 14px; border:1px solid var(--line); border-radius:10px; background:#fff; }}
  .kpi .k {{ font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
  .kpi .v {{ margin-top:4px; font-size:16px; font-weight:700; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
  section {{ padding:22px 32px; border-bottom:1px solid var(--line); }}
  h2 {{ margin:0 0 12px; font-size:15px; letter-spacing:-.01em; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th, td {{ text-align:left; padding:10px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
  th {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); background:#f8fafc; }}
  code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; background:#f1f5f9;
          padding:2px 6px; border-radius:5px; }}
  .preview {{ margin-top:4px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11px; color:var(--muted); }}
  .pill {{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:700; }}
  .pill.pass {{ background:#d1fae5; color:#065f46; }}
  .pill.fail, .pill.high {{ background:#fee2e2; color:#991b1b; }}
  .pill.medium {{ background:#fef3c7; color:#92400e; }}
  .pill.info {{ background:#e0f2fe; color:#075985; }}
  .clean {{ color:#065f46; font-weight:600; }}
  .muted {{ color:var(--muted); }}
  .seal {{ padding:18px 32px; background:#0f172a; color:#cbd5e1; font-size:12px;
           display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }}
  .seal code {{ background:#1e293b; color:#38bdf8; }}
</style>
</head>
<body>
  <div class="cert">
    <div class="header">
      <div>
        <div class="brand">VeriPR · Deterministic Proof-of-Verification Certificate</div>
        <h1>{html.escape(r.repo_name)} <span class="sub">({html.escape(r.branch)})</span></h1>
        <div class="sub">Scope: <code>{html.escape(r.base_ref)}</code> → <code>{html.escape(r.head_sha[:12])}</code> · Working Tree: {dirty_text}</div>
      </div>
      <div class="verdict">{html.escape(r.verdict)}</div>
    </div>
    <div class="grid">
      <div class="kpi"><div class="k">Files Changed</div><div class="v">{r.files_changed}</div></div>
      <div class="kpi"><div class="k">Diff Lines</div><div class="v">+{r.insertions} / -{r.deletions}</div></div>
      <div class="kpi"><div class="k">Assertion Delta</div><div class="v">+{r.assertions_added} / -{r.assertions_removed}</div></div>
      <div class="kpi"><div class="k">Audit Findings</div><div class="v">{len(r.findings)}</div></div>
    </div>
    <section>
      <h2>1. Commit-Bound Verification Runs</h2>
      <table>
        <thead><tr><th>Command</th><th>Status</th><th>Duration</th><th>Output SHA-256</th></tr></thead>
        <tbody>{cmd_rows}</tbody>
      </table>
    </section>
    <section>
      <h2>2. Deterministic Anti-Cheat &amp; Risk Surface Audit</h2>
      <table>
        <thead><tr><th>Severity</th><th>Rule</th><th>File</th><th>Detail</th></tr></thead>
        <tbody>{finding_rows}</tbody>
      </table>
    </section>
    <div class="seal">
      <div>SHA-256 Receipt Seal: <code>{r.receipt_sha256}</code></div>
      <div>VeriPR v{r.version} · {r.generated_at} · 0 LLM Calls</div>
    </div>
  </div>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="VeriPR — Deterministic Verification Receipt & AI Anti-Cheat Auditor"
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Target git repository")
    parser.add_argument("--base", default=None, help="Base git ref for diff (default: HEAD~1)")
    parser.add_argument("--staged", action="store_true", help="Inspect staged diff instead of commit diff")
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
    args = parser.parse_args(argv)

    receipt = generate_receipt(
        repo=args.repo,
        base_ref=args.base,
        staged=args.staged,
        commands=args.cmd,
        ignore_patterns=args.ignore,
    )

    md = render_markdown(receipt)
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(md, encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_html(receipt), encoding="utf-8")
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
