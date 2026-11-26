"""VeriPR Pro — Multi-Commit / Sprint Engineering Accountability Scorecard Rollup."""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import PolicyConfig, load_policy
from .core import analyze_diff, determine_verdict, resolve_diff_text, run_git


@dataclass
class CommitAuditSummary:
    sha: str
    short_sha: str
    date: str
    author: str
    subject: str
    files_changed: int
    insertions: int
    deletions: int
    assertions_added: int
    assertions_removed: int
    high_findings: int
    medium_findings: int
    info_findings: int
    verdict: str


def audit_commit_range(
    repo: Path,
    limit: int = 10,
    rev_range: str | None = None,
    policy: PolicyConfig | None = None,
    ignore_patterns: list[str] | None = None,
) -> list[CommitAuditSummary]:
    repo = repo.resolve()
    log_args = ["log", "--format=%H|%cs|%an|%s", f"-n{limit}"]
    if rev_range:
        log_args.append(rev_range)
    raw = run_git(repo, log_args)
    rows: list[CommitAuditSummary] = []

    for line in raw.splitlines():
        if not line.strip():
            continue
        sha, date_str, author, subject = line.split("|", 3)
        _, diff_text = resolve_diff_text(repo, base_ref=None, head_ref=sha, staged=False)
        stats = analyze_diff(diff_text, ignore_patterns=ignore_patterns, policy=policy)
        findings = stats["findings"]
        high = sum(1 for f in findings if f.severity == "HIGH")
        med = sum(1 for f in findings if f.severity == "MEDIUM")
        info = sum(1 for f in findings if f.severity == "INFO")
        verdict = determine_verdict(findings, commands=[])
        rows.append(
            CommitAuditSummary(
                sha=sha,
                short_sha=sha[:8],
                date=date_str,
                author=author,
                subject=subject,
                files_changed=stats["files_changed"],
                insertions=stats["insertions"],
                deletions=stats["deletions"],
                assertions_added=stats["assertions_added"],
                assertions_removed=stats["assertions_removed"],
                high_findings=high,
                medium_findings=med,
                info_findings=info,
                verdict=verdict,
            )
        )
    return rows


def render_rollup_csv(rows: list[CommitAuditSummary]) -> str:
    buf = io.StringIO()
    fields = list(CommitAuditSummary.__dataclass_fields__.keys())
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow(asdict(row))
    return buf.getvalue()


def render_rollup_html(repo_name: str, rows: list[CommitAuditSummary]) -> str:
    total_commits = len(rows)
    cheat_commits = sum(1 for r in rows if r.verdict == "CHEAT_SIGNALS_DETECTED")
    net_assertions = sum(r.assertions_added - r.assertions_removed for r in rows)
    clean_rate = round(
        100.0 * sum(1 for r in rows if r.verdict == "VERIFIED_CLEAN") / max(total_commits, 1), 1
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    tr_html = "".join(
        f"<tr>"
        f"<td><code>{html.escape(r.short_sha)}</code></td>"
        f"<td>{html.escape(r.date)}</td>"
        f"<td>{html.escape(r.author)}</td>"
        f"<td>{html.escape(r.subject[:70])}</td>"
        f"<td>+{r.assertions_added}/-{r.assertions_removed}</td>"
        f"<td>{r.high_findings}H / {r.medium_findings}M / {r.info_findings}I</td>"
        f"<td><span class='pill {r.verdict.lower()}'>{html.escape(r.verdict)}</span></td>"
        f"</tr>"
        for r in rows
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>VeriPR Pro Sprint Scorecard — {html.escape(repo_name)}</title>
<style>
  body {{ margin:0; padding:32px 16px; background:#faf9f6; color:#121417;
         font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
  .wrap {{ max-width:1040px; margin:0 auto; background:#fff; border:1px solid #e2e0d8;
           border-radius:12px; overflow:hidden; }}
  header {{ padding:24px 28px; border-bottom:1px solid #e2e0d8; }}
  .kicker {{ font-size:11px; letter-spacing:.1em; text-transform:uppercase; color:#525866; font-weight:700; }}
  h1 {{ margin:6px 0 0; font-size:22px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; padding:18px 28px;
           background:#fcfbf8; border-bottom:1px solid #e2e0d8; }}
  .kpi {{ padding:12px; border:1px solid #e2e0d8; border-radius:8px; background:#fff; }}
  .kpi .k {{ font-size:11px; text-transform:uppercase; color:#525866; }}
  .kpi .v {{ font-size:20px; font-weight:700; margin-top:4px; font-family:ui-monospace,monospace; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th, td {{ padding:10px 12px; border-bottom:1px solid #e2e0d8; text-align:left; }}
  th {{ font-size:11px; text-transform:uppercase; color:#525866; background:#faf9f6; }}
  code {{ font-family:ui-monospace,monospace; background:#f2f0e8; padding:2px 6px; border-radius:4px; }}
  .pill {{ padding:2px 8px; border-radius:999px; font-size:11px; font-weight:700; }}
  .pill.verified_clean {{ background:#d1fae5; color:#065f46; }}
  .pill.verified_with_warnings {{ background:#fef3c7; color:#92400e; }}
  .pill.cheat_signals_detected {{ background:#fee2e2; color:#991b1b; }}
  footer {{ padding:14px 28px; background:#121417; color:#d4d4d8; font-size:12px; }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="kicker">VeriPR Pro · Sprint Engineering Accountability Scorecard</div>
      <h1>{html.escape(repo_name)}</h1>
    </header>
    <div class="kpis">
      <div class="kpi"><div class="k">Commits Audited</div><div class="v">{total_commits}</div></div>
      <div class="kpi"><div class="k">Clean Rate</div><div class="v">{clean_rate}%</div></div>
      <div class="kpi"><div class="k">Cheat Signal Commits</div><div class="v">{cheat_commits}</div></div>
      <div class="kpi"><div class="k">Net Assertion Delta</div><div class="v">{net_assertions:+d}</div></div>
    </div>
    <table>
      <thead><tr><th>Commit</th><th>Date</th><th>Author</th><th>Subject</th><th>Assertions</th><th>Signals</th><th>Verdict</th></tr></thead>
      <tbody>{tr_html}</tbody>
    </table>
    <footer>Generated deterministically by VeriPR Pro Rollup · {now} · 0 LLM calls</footer>
  </div>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="VeriPR Pro — Multi-Commit Sprint Scorecard Rollup")
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--range", dest="rev_range", default=None, help="Git revision range, e.g. v0.1..HEAD")
    p.add_argument("--config", type=Path, default=None, help="Path to .veripr.toml policy file")
    p.add_argument("--ignore", action="append", default=[])
    p.add_argument("--html", type=Path, default=None)
    p.add_argument("--csv", type=Path, default=None)
    p.add_argument("--json", type=Path, default=None)
    args = p.parse_args(argv)

    cfg_path = args.config or (args.repo / ".veripr.toml")
    policy = load_policy(cfg_path if cfg_path.exists() else None)
    rows = audit_commit_range(
        args.repo, limit=args.limit, rev_range=args.rev_range, policy=policy, ignore_patterns=args.ignore
    )

    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        args.html.write_text(render_rollup_html(args.repo.resolve().name, rows), encoding="utf-8")
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        args.csv.write_text(render_rollup_csv(rows), encoding="utf-8")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps([asdict(r) for r in rows], indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"Audited {len(rows)} commit(s) in {args.repo.resolve().name}:")
    for r in rows:
        print(f"  {r.short_sha} [{r.verdict}] +{r.assertions_added}/-{r.assertions_removed} | {r.subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
