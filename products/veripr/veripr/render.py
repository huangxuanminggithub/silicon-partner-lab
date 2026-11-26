"""Markdown & HTML renderers (including Pro white-label bilingual client certificates)."""

from __future__ import annotations

import html
from dataclasses import dataclass

from .core import Receipt


@dataclass
class BrandOptions:
    vendor_name: str = ""
    client_name: str = ""
    project_name: str = ""
    milestone: str = ""
    lang: str = "en"  # en | zh
    include_signoff: bool = False


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
        "### 1. Deterministic Verification Runs",
    ]

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

    lines.extend(["", "### 2. Anti-Cheat & Risk Surface Audit"])
    if not r.findings:
        lines.append(
            "✅ No test-tampering, lint-suppression, error-swallowing, or sensitive-path signals detected."
        )
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


def render_html(r: Receipt, brand: BrandOptions | None = None) -> str:
    brand = brand or BrandOptions()
    zh = brand.lang.lower().startswith("zh")

    colors = {
        "VERIFIED_CLEAN": ("#065f46", "#d1fae5", "#10b981"),
        "VERIFIED_WITH_WARNINGS": ("#92400e", "#fef3c7", "#f59e0b"),
        "CHEAT_SIGNALS_DETECTED": ("#991b1b", "#fee2e2", "#ef4444"),
        "VERIFICATION_FAILED": ("#991b1b", "#fee2e2", "#ef4444"),
    }
    fg, bg, border = colors.get(r.verdict, ("#1f2937", "#f3f4f6", "#9ca3af"))

    t = {
        "brand_kicker": (
            f"{brand.vendor_name} · 代码交付确定性验收证书"
            if (zh and brand.vendor_name)
            else (
                "VeriPR · 代码交付确定性验证证书"
                if zh
                else (
                    f"{brand.vendor_name} · Deterministic Delivery Verification Certificate"
                    if brand.vendor_name
                    else "VeriPR · Deterministic Proof-of-Verification Certificate"
                )
            )
        ),
        "scope": "变更范围" if zh else "Scope",
        "tree": "工作区状态" if zh else "Working Tree",
        "clean": "干净（无未提交改动）" if zh else "Clean",
        "dirty": "存在未提交改动" if zh else "Dirty (uncommitted edits)",
        "files": "变更文件" if zh else "Files Changed",
        "lines": "增删行数" if zh else "Diff Lines",
        "assertions": "测试断言净变" if zh else "Assertion Delta",
        "findings": "审计信号" if zh else "Audit Findings",
        "sec1": "1. Commit 绑定的确定性测试执行记录" if zh else "1. Commit-Bound Verification Runs",
        "sec2": "2. 防作弊与高危变更面确定性审计" if zh else "2. Deterministic Anti-Cheat & Risk Surface Audit",
        "no_cmd": "未执行验证命令。" if zh else "No verification commands executed.",
        "no_find": (
            "未检测到删测跳过、静态检查屏蔽、异常吞没或高危路径触碰信号。"
            if zh
            else "No test-tampering, linter-suppression, or sensitive-path alerts detected."
        ),
        "cmd_col": "执行命令" if zh else "Command",
        "status_col": "结果" if zh else "Status",
        "dur_col": "耗时" if zh else "Duration",
        "digest_col": "输出 SHA-256" if zh else "Output SHA-256",
        "sev_col": "级别" if zh else "Severity",
        "rule_col": "规则" if zh else "Rule",
        "file_col": "文件" if zh else "File",
        "detail_col": "说明" if zh else "Detail",
        "seal_label": "SHA-256 不可篡改封签" if zh else "SHA-256 Receipt Seal",
    }

    title_main = brand.project_name or r.repo_name
    client_meta_html = ""
    if brand.client_name or brand.milestone or brand.vendor_name:
        bits = []
        if brand.vendor_name:
            bits.append(
                f"<span><strong>{'交付方' if zh else 'Vendor'}:</strong> {html.escape(brand.vendor_name)}</span>"
            )
        if brand.client_name:
            bits.append(
                f"<span><strong>{'验收甲方' if zh else 'Client'}:</strong> {html.escape(brand.client_name)}</span>"
            )
        if brand.milestone:
            bits.append(
                f"<span><strong>{'里程碑' if zh else 'Milestone'}:</strong> {html.escape(brand.milestone)}</span>"
            )
        client_meta_html = f"<div class='meta-bar'>{''.join(bits)}</div>"

    cmd_rows = ""
    if not r.commands:
        cmd_rows = f"<tr><td colspan='4' class='muted'>{t['no_cmd']}</td></tr>"
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
        finding_rows = f"<tr><td colspan='4' class='clean'>{t['no_find']}</td></tr>"
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

    signoff_html = ""
    if brand.include_signoff:
        signoff_html = f"""
    <section class="signoff">
      <h2>{'3. 交付验收签字栏（Client Acceptance Sign-Off）' if zh else '3. Client Delivery Acceptance Sign-Off'}</h2>
      <div class="sig-grid">
        <div class="sig-box">
          <div class="sig-label">{'交付工程师 / 负责人签名' if zh else 'Delivering Engineer / Vendor'}</div>
          <div class="sig-line"></div>
          <div class="sig-sub">{html.escape(brand.vendor_name or 'Name & Date')}</div>
        </div>
        <div class="sig-box">
          <div class="sig-label">{'甲方验收确认签名' if zh else 'Client Acceptance Representative'}</div>
          <div class="sig-line"></div>
          <div class="sig-sub">{html.escape(brand.client_name or 'Name & Date')}</div>
        </div>
      </div>
    </section>"""

    dirty_text = t["dirty"] if r.working_tree_dirty else t["clean"]
    return f"""<!DOCTYPE html>
<html lang="{'zh-CN' if zh else 'en'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VeriPR Certificate — {html.escape(title_main)} ({r.head_sha[:8]})</title>
<style>
  :root {{ --ink:#121417; --muted:#525866; --line:#e2e0d8; --panel:#ffffff; --bg:#faf9f6; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:32px 16px; background:var(--bg); color:var(--ink);
         font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Noto Sans SC",sans-serif; }}
  .cert {{ max-width:920px; margin:0 auto; background:var(--panel); border:1px solid var(--line);
           border-radius:12px; box-shadow:0 8px 28px rgba(18,20,23,.05); overflow:hidden; }}
  .header {{ padding:28px 32px; border-bottom:1px solid var(--line); display:flex;
             justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; }}
  .brand {{ font-size:11px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); font-weight:700; }}
  h1 {{ margin:6px 0 4px; font-size:24px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); font-size:13px; }}
  .meta-bar {{ display:flex; flex-wrap:wrap; gap:18px; padding:12px 32px; background:#f5f3ec;
               border-bottom:1px solid var(--line); font-size:13px; color:var(--ink); }}
  .verdict {{ padding:8px 14px; border-radius:999px; font-weight:700; font-size:12px;
              letter-spacing:.04em; color:{fg}; background:{bg}; border:1px solid {border}; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px;
           padding:20px 32px; background:#fcfbf8; border-bottom:1px solid var(--line); }}
  .kpi {{ padding:12px 14px; border:1px solid var(--line); border-radius:8px; background:#fff; }}
  .kpi .k {{ font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
  .kpi .v {{ margin-top:4px; font-size:16px; font-weight:700; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
  section {{ padding:22px 32px; border-bottom:1px solid var(--line); }}
  h2 {{ margin:0 0 12px; font-size:15px; letter-spacing:-.01em; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th, td {{ text-align:left; padding:10px 10px; border-bottom:1px solid var(--line); vertical-align:top; }}
  th {{ font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); background:#faf9f6; }}
  code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; background:#f2f0e8;
          padding:2px 6px; border-radius:4px; }}
  .preview {{ margin-top:4px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11px; color:var(--muted); }}
  .pill {{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:700; }}
  .pill.pass {{ background:#d1fae5; color:#065f46; }}
  .pill.fail, .pill.high {{ background:#fee2e2; color:#991b1b; }}
  .pill.medium {{ background:#fef3c7; color:#92400e; }}
  .pill.info {{ background:#e0f2fe; color:#075985; }}
  .clean {{ color:#065f46; font-weight:600; }}
  .muted {{ color:var(--muted); }}
  .sig-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; margin-top:14px; }}
  .sig-box {{ border:1px dashed var(--line); border-radius:8px; padding:16px; background:#fcfbf8; }}
  .sig-label {{ font-size:12px; color:var(--muted); font-weight:600; }}
  .sig-line {{ height:38px; border-bottom:1px solid #94a3b8; margin:8px 0; }}
  .sig-sub {{ font-size:12px; color:var(--muted); }}
  .seal {{ padding:18px 32px; background:#121417; color:#d4d4d8; font-size:12px;
           display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }}
  .seal code {{ background:#23262d; color:#6ee7b7; }}
  @media print {{ body {{ background:#fff; padding:0; }} .cert {{ box-shadow:none; border:none; }} }}
</style>
</head>
<body>
  <div class="cert">
    <div class="header">
      <div>
        <div class="brand">{html.escape(t['brand_kicker'])}</div>
        <h1>{html.escape(title_main)} <span class="sub">({html.escape(r.branch)})</span></h1>
        <div class="sub">{t['scope']}: <code>{html.escape(r.base_ref)}</code> → <code>{html.escape(r.head_sha[:12])}</code> · {t['tree']}: {dirty_text}</div>
      </div>
      <div class="verdict">{html.escape(r.verdict)}</div>
    </div>{client_meta_html}
    <div class="grid">
      <div class="kpi"><div class="k">{t['files']}</div><div class="v">{r.files_changed}</div></div>
      <div class="kpi"><div class="k">{t['lines']}</div><div class="v">+{r.insertions} / -{r.deletions}</div></div>
      <div class="kpi"><div class="k">{t['assertions']}</div><div class="v">+{r.assertions_added} / -{r.assertions_removed}</div></div>
      <div class="kpi"><div class="k">{t['findings']}</div><div class="v">{len(r.findings)}</div></div>
    </div>
    <section>
      <h2>{t['sec1']}</h2>
      <table>
        <thead><tr><th>{t['cmd_col']}</th><th>{t['status_col']}</th><th>{t['dur_col']}</th><th>{t['digest_col']}</th></tr></thead>
        <tbody>{cmd_rows}</tbody>
      </table>
    </section>
    <section>
      <h2>{t['sec2']}</h2>
      <table>
        <thead><tr><th>{t['sev_col']}</th><th>{t['rule_col']}</th><th>{t['file_col']}</th><th>{t['detail_col']}</th></tr></thead>
        <tbody>{finding_rows}</tbody>
      </table>
    </section>{signoff_html}
    <div class="seal">
      <div>{t['seal_label']}: <code>{r.receipt_sha256}</code></div>
      <div>VeriPR v{r.version} · {r.generated_at} · 0 LLM Calls</div>
    </div>
  </div>
</body>
</html>
"""
