# VeriPR — Deterministic Proof-of-Verification Receipt for AI-Assisted PRs

> Writing plausible code became nearly free. Verifying that an AI agent didn't skip tests, delete assertions, suppress linters, or silently break auth didn't.

**VeriPR** is a zero-dependency, 100% deterministic CLI (0 LLM calls, 0 API keys, 0 token cost) that audits a Git diff, runs your actual test/lint commands bound to `HEAD`, and emits a tamper-evident **SHA-256 Verification Receipt** in Markdown (ready for GitHub PRs), JSON (for CI gates), and self-contained HTML (ready for client handoff / compliance archive).

## What It Catches Deterministically
- **Test Tampering**: Newly added `.skip`, `@pytest.mark.skip`, `@unittest.skip`, `#[ignore]`, deleted test files, or a net drop in test assertions.
- **Linter & Type-Check Escape Hatches**: Newly added `@ts-ignore`, `@ts-expect-error`, `eslint-disable`, `# noqa`, `# type: ignore`, `# pragma: no cover`, `as any`.
- **Silent Error Swallowing**: Newly introduced bare `except: pass` or empty `catch () {}`.
- **Sensitive Surface Radar**: Touches to auth/login, billing/payment/ledger, DB migrations, CI workflows, `.env`, or lockfiles.
- **Commit-Bound Execution Proof**: Runs real verification commands and seals `HEAD` SHA, exit codes, durations, and stdout SHA-256 digests into one canonical receipt hash.

## Quick Start

```bash
python3 veripr.py \
  --repo . \
  --cmd "python3 -m unittest discover -s tests" \
  --md receipt.md \
  --html receipt.html \
  --fail-on-cheat
```

## Origin
Built as **Product #001** inside the **\$100 Silicon Partner Accountability Experiment (`EXP-001`)** — an experiment testing whether an AI operating under a hash-chained ledger, 25% spend cap, and 20% High-Water-Mark profit share can create genuine, verifiable value starting from \$0 spent.
