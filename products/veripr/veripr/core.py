"""Core deterministic diff auditing, command execution, and SHA-256 sealing."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PolicyConfig

VERSION = "0.2.0"


@dataclass
class Finding:
    severity: str  # HIGH | MEDIUM | INFO
    category: str
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
    (
        "Dependency Lockfile",
        re.compile(
            r"(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock|poetry\.lock|uv\.lock)$"
        ),
    ),
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


def resolve_diff_text(
    repo: Path, base_ref: str | None, head_ref: str = "HEAD", staged: bool = False
) -> tuple[str, str]:
    if staged:
        return "STAGED", run_git(repo, ["diff", "--cached", "--unified=0", "--no-color"])

    if base_ref:
        return base_ref, run_git(
            repo, ["diff", f"{base_ref}...{head_ref}", "--unified=0", "--no-color"]
        )

    parent_ref = f"{head_ref}~1"
    has_parent = (
        subprocess.run(
            ["git", "rev-parse", "--verify", parent_ref],
            cwd=repo,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )
    if has_parent:
        return parent_ref, run_git(
            repo, ["diff", f"{parent_ref}..{head_ref}", "--unified=0", "--no-color"]
        )
    empty_tree = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
    return "EMPTY_TREE", run_git(repo, ["diff", empty_tree, head_ref, "--unified=0", "--no-color"])


def analyze_diff(
    diff_text: str,
    ignore_patterns: list[str] | None = None,
    policy: PolicyConfig | None = None,
) -> dict[str, Any]:
    policy = policy or PolicyConfig()
    merged_ignores = list(policy.ignore_patterns) + list(ignore_patterns or [])
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
        return any(fnmatch.fnmatch(path, pat) for pat in merged_ignores)

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            parts = raw_line.split(" ")
            if len(parts) >= 4:
                current_file = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                touched_files.add(current_file)
            prev_added_line = ""
            continue

        if raw_line.startswith("deleted file mode "):
            if (
                current_file
                and not is_ignored(current_file)
                and is_test_source_file(current_file)
                and "test-file-deleted" not in policy.disabled_rules
            ):
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

            if is_ignored(current_file) or NON_SOURCE_ARTIFACT_PATTERN.search(current_file):
                prev_added_line = content
                continue

            if (
                "silent-except-pass" not in policy.disabled_rules
                and re.match(r"^\s*pass\s*$", content)
                and re.match(r"^\s*except(\s+Exception(\s+as\s+\w+)?)?\s*:\s*$", prev_added_line)
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
                if rule_name in policy.disabled_rules:
                    continue
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

            for crule in policy.custom_rules:
                if crule.rule in policy.disabled_rules:
                    continue
                if crule.pattern.search(content):
                    findings.append(
                        Finding(
                            severity=crule.severity,
                            category=crule.category,
                            file=current_file,
                            line_preview=content.strip()[:120],
                            rule=crule.rule,
                            detail=crule.detail,
                        )
                    )

            prev_added_line = content

        elif raw_line.startswith("-"):
            deletions += 1
            content = raw_line[1:]
            if is_test_source_file(current_file) and ASSERTION_PATTERN.search(content):
                assertions_removed += 1
            prev_added_line = ""

    if (
        "net-assertion-drop" not in policy.disabled_rules
        and assertions_removed > assertions_added
        and (assertions_removed - assertions_added) >= policy.max_assertion_drop
    ):
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

    all_sensitive = list(SENSITIVE_PATH_PATTERNS) + [
        (sp.label, sp.pattern) for sp in policy.extra_sensitive_paths
    ]
    if "sensitive-path-touched" not in policy.disabled_rules:
        for fpath in sorted(touched_files):
            if NON_SOURCE_ARTIFACT_PATTERN.search(fpath) or is_ignored(fpath):
                continue
            for label, pat in all_sensitive:
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


def determine_verdict(
    findings: list[Finding],
    commands: list[CommandRun],
    dirty: bool = False,
    require_clean_tree: bool = False,
) -> str:
    if any(c.exit_code != 0 for c in commands):
        return "VERIFICATION_FAILED"
    if require_clean_tree and dirty:
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
    head_ref: str = "HEAD",
    staged: bool = False,
    commands: list[str] | None = None,
    ignore_patterns: list[str] | None = None,
    policy: PolicyConfig | None = None,
) -> Receipt:
    repo = repo.resolve()
    policy = policy or PolicyConfig()
    head_sha = run_git(repo, ["rev-parse", head_ref]).strip()
    branch = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    dirty = bool(run_git(repo, ["status", "--porcelain"]).strip())
    resolved_base, diff_text = resolve_diff_text(repo, base_ref, head_ref=head_ref, staged=staged)

    diff_stats = analyze_diff(diff_text, ignore_patterns=ignore_patterns, policy=policy)
    merged_cmds = list(commands) if commands else list(policy.default_commands)
    cmd_runs = execute_verification_commands(repo, merged_cmds)
    verdict = determine_verdict(
        diff_stats["findings"],
        cmd_runs,
        dirty=dirty,
        require_clean_tree=policy.require_clean_tree,
    )

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
