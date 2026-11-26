/* VeriPR Browser Deterministic Diff Auditor & Bilingual Controller */

const CONFIG = {
  // Live open-source repository URL; add buyUrlCn / buyUrlGlobal once H-004 payment links are created
  repoUrl: "https://github.com/huangxuanminggithub/silicon-partner-lab",
  buyUrlCn: "",
  buyUrlGlobal: "",
  backerUrlCn: "",
};

const PRESETS = {
  cheating_ai: `diff --git a/tests/test_billing.py b/tests/test_billing.py
index 82a10f1..14b9c20 100644
--- a/tests/test_billing.py
+++ b/tests/test_billing.py
@@ -12,9 +12,5 @@ class TestBilling(unittest.TestCase):
-    def test_refund_cannot_exceed_charge(self):
-        self.assertRaises(ValueError, refund, 100, 150)
-        self.assertEqual(refund(100, 40), 60)
-        self.assertEqual(refund(100, 100), 0)
+    @unittest.skip("temporarily flaky after refactor")
+    def test_refund_cannot_exceed_charge(self):
+        assert True
diff --git a/src/auth/token_verify.ts b/src/auth/token_verify.ts
index 3a4b120..9d0e112 100644
--- a/src/auth/token_verify.ts
+++ b/src/auth/token_verify.ts
@@ -4,4 +4,7 @@ export function verifySession(raw: unknown) {
+  // @ts-ignore quick fix to pass tsc
+  const payload = raw as any;
+  try {
+    return payload.userId;
+  } catch (err) {}
 }`,

  fintech_risk: `diff --git a/payments/settlement.py b/payments/settlement.py
index 11c230a..7a8e411 100644
--- a/payments/settlement.py
+++ b/payments/settlement.py
@@ -18,3 +18,9 @@ def settle_payout(amount_usd):
+    # TODO: implement currency rounding later
+    fee = float(amount_usd) * 0.029
+    try:
+        return submit_bank(amount_usd - fee, verify=False)
+    except Exception:
+        pass`,

  clean_refactor: `diff --git a/src/ledger.py b/src/ledger.py
index 4421a90..8c9012f 100644
--- a/src/ledger.py
+++ b/src/ledger.py
@@ -10,2 +10,5 @@ def apply_fee(amount: Decimal, rate: Decimal) -> Decimal:
+    if amount < Decimal("0.00"):
+        raise ValueError("amount must be non-negative")
+    return (amount * rate).quantize(Decimal("0.01"))
diff --git a/tests/test_ledger.py b/tests/test_ledger.py
index 91c112a..3d0f221 100644
--- a/tests/test_ledger.py
+++ b/tests/test_ledger.py
@@ -20,0 +21,4 @@ class TestLedger(unittest.TestCase):
+    def test_negative_amount_rejected(self):
+        self.assertRaises(ValueError, apply_fee, Decimal("-1.00"), Decimal("0.05"))
+        self.assertEqual(apply_fee(Decimal("100.00"), Decimal("0.20")), Decimal("20.00"))`,
};

const ADDED_LINE_RULES = [
  {
    severity: "HIGH",
    rule: "test-skip-added",
    regex: /\b(it|test|describe|context)\.skip\s*\(|\bx(it|test|describe)\s*\(|@pytest\.mark\.skip\b|@unittest\.skip\b|\bt\.Skip\s*\(|#\[ignore\]/i,
    detailEn: "Newly added test skip directive detected in diff",
    detailZh: "检测到新增测试跳过指令（skip / ignore）",
  },
  {
    severity: "HIGH",
    rule: "fake-always-pass-test",
    regex: /assert\s+True\s*$|expect\s*\(\s*true\s*\)\.toBe\s*\(\s*true\s*\)/,
    detailEn: "Tautological always-true assertion detected",
    detailZh: "检测到恒真假测试断言（assert True）",
  },
  {
    severity: "HIGH",
    rule: "typecheck-suppression",
    regex: /@ts-ignore\b|@ts-expect-error\b|@ts-nocheck\b|#\s*type:\s*ignore\b/,
    detailEn: "Newly added static type-check suppression directive",
    detailZh: "检测到新增静态类型检查屏蔽指令",
  },
  {
    severity: "HIGH",
    rule: "no-float-money-math",
    regex: /\bfloat\s*\(.*(amount|price|balance|fee|total|usd|cny)/i,
    detailEn: "Floating-point conversion on monetary amount (Pro Fintech Rule)",
    detailZh: "金额字段使用浮点数运算（Pro 金融规则拦截）",
  },
  {
    severity: "HIGH",
    rule: "no-ssl-verify-false",
    regex: /verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['"]?0/,
    detailEn: "TLS certificate verification disabled (Pro Fintech Rule)",
    detailZh: "关闭 TLS 证书校验（Pro 安全规则拦截）",
  },
  {
    severity: "MEDIUM",
    rule: "linter-or-coverage-suppression",
    regex: /eslint-disable\b|#\s*noqa\b|#\s*pragma:\s*no\s*cover\b|\/\/\s*nolint\b/,
    detailEn: "Newly added linter or coverage suppression directive",
    detailZh: "检测到新增 Lint 或覆盖率屏蔽注释",
  },
  {
    severity: "MEDIUM",
    rule: "ts-any-escape-hatch",
    regex: /\bas\s+any\b|:\s*any\b/,
    detailEn: "TypeScript `any` escape hatch introduced",
    detailZh: "引入了 TypeScript `any` 类型逃生舱",
  },
  {
    severity: "MEDIUM",
    rule: "empty-catch-or-bare-except",
    regex: /^\s*except\s*:\s*$|^\s*except\s+Exception(\s+as\s+\w+)?\s*:\s*pass\s*$|catch\s*\([^)]*\)\s*\{\s*\}/,
    detailEn: "Potential silent error swallowing introduced",
    detailZh: "引入了静默吞没异常代码块",
  },
  {
    severity: "MEDIUM",
    rule: "placeholder-todo-ship",
    regex: /(TODO|FIXME|HACK)\s*:?\s*(implement|fix|later|placeholder|mock|stub)/i,
    detailEn: "Unfinished AI placeholder/stub comment left in diff",
    detailZh: "Diff 中残留未实现的占位符注释（TODO/stub）",
  },
  {
    severity: "HIGH",
    rule: "potential-hardcoded-secret",
    regex: /\bsk-[A-Za-z0-9]{20,}\b|\bghp_[A-Za-z0-9]{20,}\b|\bAKIA[0-9A-Z]{16}\b|BEGIN\s+(RSA|EC|OPENSSH|PRIVATE)\s+KEY/,
    detailEn: "Potential hardcoded credential or private key detected",
    detailZh: "检测到疑似硬编码密钥或私钥",
  },
];

const SENSITIVE_PATH_PATTERNS = [
  { labelEn: "CI/CD workflow", labelZh: "CI/CD 工作流", regex: /(^|\/)\.github\/workflows\// },
  { labelEn: "Authentication / Authorization", labelZh: "鉴权 / 登录模块", regex: /(^|\/)(auth|oauth|login|rbac|acl|permission)/i },
  { labelEn: "Payments / Billing / Ledger", labelZh: "支付 / 账单 / 账本模块", regex: /(^|\/)(billing|payment|stripe|checkout|ledger|wallet)/i },
  { labelEn: "Database Migration / Schema", labelZh: "数据库迁移 / Schema", regex: /(^|\/)(migrations?|schema\.sql|alembic)/i },
];

const TEST_FILE_RE = /(^|\/)(tests?|__tests__|spec)\/|(\.|_)(test|spec)\.[A-Za-z0-9]+$|^test_.*\.py$/i;
const ASSERTION_RE = /\b(assert\w*|expect|should|assertEqual|assertTrue|assertFalse|assertRaises|require\.\w+)\b/;

let currentLang = "zh";
let lastResult = null;

function analyzeDiffText(diffText) {
  let currentFile = "";
  const touchedFiles = new Set();
  let insertions = 0;
  let deletions = 0;
  let assertionsAdded = 0;
  let assertionsRemoved = 0;
  const findings = [];
  const flaggedSensitive = new Set();
  let prevAddedLine = "";

  for (const rawLine of diffText.split(/\r?\n/)) {
    if (rawLine.startsWith("diff --git ")) {
      const parts = rawLine.split(" ");
      if (parts.length >= 4) {
        currentFile = parts[3].startsWith("b/") ? parts[3].slice(2) : parts[3];
        touchedFiles.add(currentFile);
      }
      prevAddedLine = "";
      continue;
    }
    if (rawLine.startsWith("deleted file mode ")) {
      if (currentFile && TEST_FILE_RE.test(currentFile)) {
        findings.push({
          severity: "HIGH",
          rule: "test-file-deleted",
          file: currentFile,
          preview: "(entire test file deleted)",
          detailEn: "A test file was deleted in this diff",
          detailZh: "本次变更直接删除了测试文件",
        });
      }
      continue;
    }
    if (rawLine.startsWith("+++ ") || rawLine.startsWith("--- ") || rawLine.startsWith("@@ ")) {
      prevAddedLine = "";
      continue;
    }

    if (rawLine.startsWith("+")) {
      insertions += 1;
      const content = rawLine.slice(1);
      if (TEST_FILE_RE.test(currentFile) && ASSERTION_RE.test(content)) {
        assertionsAdded += 1;
      }
      if (
        /^\s*pass\s*$/.test(content) &&
        /^\s*except(\s+Exception(\s+as\s+\w+)?)?\s*:\s*$/.test(prevAddedLine)
      ) {
        findings.push({
          severity: "MEDIUM",
          rule: "silent-except-pass",
          file: currentFile || "(inline diff)",
          preview: `${prevAddedLine.trim()} pass`,
          detailEn: "Silent `except: pass` error swallowing block introduced",
          detailZh: "引入了静默吞异常的 `except: pass`",
        });
      }
      for (const r of ADDED_LINE_RULES) {
        if (r.regex.test(content)) {
          findings.push({
            severity: r.severity,
            rule: r.rule,
            file: currentFile || "(inline diff)",
            preview: content.trim().slice(0, 120),
            detailEn: r.detailEn,
            detailZh: r.detailZh,
          });
        }
      }
      prevAddedLine = content;
    } else if (rawLine.startsWith("-")) {
      deletions += 1;
      const content = rawLine.slice(1);
      if (TEST_FILE_RE.test(currentFile) && ASSERTION_RE.test(content)) {
        assertionsRemoved += 1;
      }
      prevAddedLine = "";
    }
  }

  if (assertionsRemoved > assertionsAdded && assertionsRemoved - assertionsAdded >= 2) {
    const netDrop = assertionsRemoved - assertionsAdded;
    findings.push({
      severity: "HIGH",
      rule: "net-assertion-drop",
      file: "(test suite)",
      preview: `-${assertionsRemoved} removed / +${assertionsAdded} added assertions`,
      detailEn: `Net drop of ${netDrop} test assertions — verify tests were not weakened`,
      detailZh: `测试断言净减少 ${netDrop} 条，请核查是否偷偷削弱了测试覆盖`,
    });
  }

  for (const fpath of Array.from(touchedFiles).sort()) {
    for (const sp of SENSITIVE_PATH_PATTERNS) {
      const key = `${fpath}::${sp.labelEn}`;
      if (sp.regex.test(fpath) && !flaggedSensitive.has(key)) {
        flaggedSensitive.add(key);
        findings.push({
          severity: "INFO",
          rule: "sensitive-path-touched",
          file: fpath,
          preview: fpath,
          detailEn: `Touches sensitive surface: ${sp.labelEn}`,
          detailZh: `触及高危变更面：${sp.labelZh}`,
        });
      }
    }
  }

  let verdict = "VERIFIED_CLEAN";
  if (findings.some((f) => f.severity === "HIGH")) {
    verdict = "CHEAT_SIGNALS_DETECTED";
  } else if (findings.some((f) => f.severity === "MEDIUM")) {
    verdict = "VERIFIED_WITH_WARNINGS";
  }

  return {
    filesChanged: touchedFiles.size,
    insertions,
    deletions,
    assertionsAdded,
    assertionsRemoved,
    findings,
    verdict,
    generatedAt: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
  };
}

async function sha256Hex(text) {
  if (window.crypto && window.crypto.subtle) {
    const enc = new TextEncoder().encode(text);
    const buf = await window.crypto.subtle.digest("SHA-256", enc);
    return Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }
  // Deterministic fallback when opened over non-secure file:// context without SubtleCrypto
  let h1 = 0xdeadbeef ^ text.length;
  let h2 = 0x41c6ce57 ^ text.length;
  for (let i = 0; i < text.length; i++) {
    const ch = text.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  const part = ((h1 >>> 0).toString(16).padStart(8, "0") + (h2 >>> 0).toString(16).padStart(8, "0"));
  return (part + part + part + part).slice(0, 64);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildMarkdownReceipt(res) {
  const badge =
    res.verdict === "VERIFIED_CLEAN"
      ? "✅ VERIFIED CLEAN"
      : res.verdict === "VERIFIED_WITH_WARNINGS"
      ? "⚠️ VERIFIED WITH WARNINGS"
      : "🚨 CHEAT / RISK SIGNALS DETECTED";
  const rows = res.findings.length
    ? [
        "| Severity | Rule | File | Detail |",
        "| --- | --- | --- | --- |",
        ...res.findings.map(
          (f) =>
            `| \`${f.severity}\` | \`${f.rule}\` | \`${f.file}\` | ${
              currentLang === "zh" ? f.detailZh : f.detailEn
            } (\`${f.preview}\`) |`
        ),
      ].join("\n")
    : "✅ No test-tampering, lint-suppression, or sensitive-path signals detected.";

  return [
    `## VeriPR Proof-of-Verification Receipt — ${badge}`,
    "",
    "| Field | Value |",
    "| --- | --- |",
    `| Diff Footprint | \`${res.filesChanged}\` files (\`+${res.insertions}\` / \`-${res.deletions}\`) |`,
    `| Test Assertion Delta | \`+${res.assertionsAdded}\` added / \`-${res.assertionsRemoved}\` removed |`,
    `| Receipt Seal (SHA-256) | \`${res.seal.slice(0, 24)}...\` |`,
    `| Generated (UTC) | \`${res.generatedAt}\` |`,
    "",
    "### Anti-Cheat & Risk Surface Audit",
    rows,
    "",
    "> Sealed deterministically by **VeriPR v0.2.0** (0 LLM calls, 0 tokens burned).",
  ].join("\n");
}

function renderAuditOutput(res) {
  const verdictRow = document.getElementById("verdictRow");
  const verdictTitle = document.getElementById("verdictTitle");
  const verdictSeal = document.getElementById("verdictSeal");
  const mFiles = document.getElementById("mFiles");
  const mLines = document.getElementById("mLines");
  const mAssertions = document.getElementById("mAssertions");
  const mSignals = document.getElementById("mSignals");
  const tbody = document.getElementById("findingsBody");

  verdictRow.classList.remove("clean", "warn", "cheat");
  if (res.verdict === "VERIFIED_CLEAN") {
    verdictRow.classList.add("clean");
    verdictTitle.textContent = currentLang === "zh" ? "VERIFIED_CLEAN · 未检出作弊信号" : "VERIFIED_CLEAN · No cheat signals";
  } else if (res.verdict === "VERIFIED_WITH_WARNINGS") {
    verdictRow.classList.add("warn");
    verdictTitle.textContent = currentLang === "zh" ? "VERIFIED_WITH_WARNINGS · 发现风险提示" : "VERIFIED_WITH_WARNINGS · Review warnings";
  } else {
    verdictRow.classList.add("cheat");
    verdictTitle.textContent = currentLang === "zh" ? "CHEAT_SIGNALS_DETECTED · 拦截到高危作弊信号" : "CHEAT_SIGNALS_DETECTED · High-risk signals caught";
  }

  verdictSeal.textContent = `SHA-256: ${res.seal.slice(0, 20)}...`;
  mFiles.textContent = String(res.filesChanged);
  mLines.textContent = `+${res.insertions} / -${res.deletions}`;
  mAssertions.textContent = `+${res.assertionsAdded} / -${res.assertionsRemoved}`;
  mSignals.textContent = String(res.findings.length);

  if (!res.findings.length) {
    tbody.innerHTML = `<tr><td colspan="4" style="color:var(--accent);font-weight:600;">${
      currentLang === "zh"
        ? "未检测到删测跳过、静态检查屏蔽、异常吞没或高危路径触碰信号。"
        : "No test-tampering, linter-suppression, error-swallowing, or sensitive-path alerts detected."
    }</td></tr>`;
    return;
  }

  tbody.innerHTML = res.findings
    .map((f) => {
      const detail = currentLang === "zh" ? f.detailZh : f.detailEn;
      return `<tr>
        <td><span class="sev-tag ${f.severity.toLowerCase()}">${escapeHtml(f.severity)}</span></td>
        <td><code>${escapeHtml(f.rule)}</code></td>
        <td><code>${escapeHtml(f.file)}</code></td>
        <td>${escapeHtml(detail)}<span class="finding-code">${escapeHtml(f.preview)}</span></td>
      </tr>`;
    })
    .join("");
}

async function runBrowserAudit() {
  const input = document.getElementById("diffInput").value;
  const res = analyzeDiffText(input);
  res.seal = await sha256Hex(JSON.stringify(res));
  lastResult = res;
  renderAuditOutput(res);
}

function applyLanguage(lang) {
  currentLang = lang;
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-zh][data-en]").forEach((el) => {
    el.textContent = el.getAttribute(lang === "zh" ? "data-zh" : "data-en");
  });
  document.getElementById("langToggle").textContent = lang === "zh" ? "EN" : "中文";
  if (lastResult) {
    renderAuditOutput(lastResult);
  }
}

function openInfoModal(title, body) {
  document.getElementById("modalTitle").textContent = title;
  document.getElementById("modalBody").textContent = body;
  document.getElementById("infoModal").classList.add("open");
}

function setupEvents() {
  document.getElementById("langToggle").addEventListener("click", () => {
    applyLanguage(currentLang === "zh" ? "en" : "zh");
  });

  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".preset-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const key = btn.getAttribute("data-preset");
      document.getElementById("diffInput").value = PRESETS[key] || "";
      runBrowserAudit();
    });
  });

  document.getElementById("runAuditBtn").addEventListener("click", runBrowserAudit);

  document.getElementById("copyMdBtn").addEventListener("click", async () => {
    if (!lastResult) await runBrowserAudit();
    const md = buildMarkdownReceipt(lastResult);
    try {
      await navigator.clipboard.writeText(md);
      const btn = document.getElementById("copyMdBtn");
      const orig = btn.textContent;
      btn.textContent = currentLang === "zh" ? "已复制 Markdown ✓" : "Copied Markdown ✓";
      setTimeout(() => (btn.textContent = orig), 1800);
    } catch {
      openInfoModal(
        currentLang === "zh" ? "Markdown 回执预览" : "Markdown Receipt",
        md
      );
    }
  });

  document.getElementById("exportCertBtn").addEventListener("click", async () => {
    if (!lastResult) await runBrowserAudit();
    const htmlDoc = `<!DOCTYPE html><html lang="${currentLang === "zh" ? "zh-CN" : "en"}"><head><meta charset="utf-8"><title>VeriPR Certificate</title><style>body{font:14px/1.6 -apple-system,sans-serif;padding:32px;background:#faf9f6;color:#13161b}.box{max-width:820px;margin:0 auto;background:#fff;border:1px solid #dddad0;border-radius:10px;padding:28px}pre{background:#14171c;color:#e6e8ec;padding:14px;border-radius:6px;white-space:pre-wrap;font-size:12px}</style></head><body><div class="box"><h1>VeriPR Proof-of-Verification Certificate</h1><p><strong>Verdict:</strong> ${escapeHtml(lastResult.verdict)} · <strong>SHA-256:</strong> <code>${escapeHtml(lastResult.seal)}</code></p><pre>${escapeHtml(buildMarkdownReceipt(lastResult))}</pre></div></body></html>`;
    const blob = new Blob([htmlDoc], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `veripr-certificate-${lastResult.seal.slice(0, 8)}.html`;
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById("buyProCnBtn").addEventListener("click", () => {
    if (CONFIG.buyUrlCn) {
      window.open(CONFIG.buyUrlCn, "_blank", "noopener");
    } else {
      openInfoModal(
        currentLang === "zh" ? "VeriPR Pro 早鸟通道即将开放" : "VeriPR Pro Early Bird Checkout",
        currentLang === "zh"
          ? "Pro 交付工具包（dist/veripr-pro-kit-v0.2.0.zip）已打包完毕，包含白标双语甲方验收证书、Sprint 审计总账与 3 套生产级规则包。请在 site/app.js 的 CONFIG.buyUrlCn 填入您的爱发电 / 面包多商品链接即可正式收款。"
          : "VeriPR Pro Kit (dist/veripr-pro-kit-v0.2.0.zip) is packaged and ready. Add your checkout URL to CONFIG.buyUrlCn / CONFIG.buyUrlGlobal in site/app.js to activate live payments."
      );
    }
  });

  document.getElementById("buyProGlobalBtn").addEventListener("click", () => {
    if (CONFIG.buyUrlGlobal) {
      window.open(CONFIG.buyUrlGlobal, "_blank", "noopener");
    } else {
      openInfoModal(
        currentLang === "zh" ? "海外收款链接待绑定" : "Global Checkout Pending Setup",
        currentLang === "zh"
          ? "海外收款（Creem / Polar.sh / Lemon Squeezy）开通后，将链接填入 site/app.js 的 CONFIG.buyUrlGlobal 即可自动生效。"
          : "Once your global Merchant of Record checkout link (Polar.sh / Creem / Lemon Squeezy) is active, set CONFIG.buyUrlGlobal in site/app.js."
      );
    }
  });

  document.getElementById("closeModalBtn").addEventListener("click", () => {
    document.getElementById("infoModal").classList.remove("open");
  });
  document.getElementById("infoModal").addEventListener("click", (e) => {
    if (e.target.id === "infoModal") e.target.classList.remove("open");
  });
}

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("diffInput").value = PRESETS.cheating_ai;
  setupEvents();
  applyLanguage("zh");
  runBrowserAudit();
});
