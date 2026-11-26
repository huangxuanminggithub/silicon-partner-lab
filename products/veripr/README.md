# VeriPR v0.2.0 — Deterministic Proof-of-Verification & AI Anti-Cheat Auditor

> Writing plausible code became nearly free. Verifying that an AI coding agent didn't skip tests, delete assertions, suppress linters, swallow errors, or silently touch auth/billing didn't.

**VeriPR** is a zero-dependency, 100% deterministic Python 3.11+ CLI & GitHub Action (**0 LLM calls, 0 API keys, 0 token cost**) that scans Git diffs, executes real verification commands bound to `HEAD`, and emits tamper-evident **SHA-256 Verification Receipts** in Markdown, JSON, and self-contained HTML.

## What It Catches Deterministically
- **Test Tampering**: Added `.skip` / `@pytest.mark.skip` / `@unittest.skip` / `#[ignore]`, deleted test source files, tautological `assert True`, and net drops in test assertions.
- **Linter & Type-Check Suppression**: Added `@ts-ignore`, `@ts-expect-error`, `@ts-nocheck`, `eslint-disable`, `# noqa`, `# type: ignore`, `# pragma: no cover`, `as any`.
- **Silent Error Swallowing**: Bare `except: pass` and empty `catch (...) {}`.
- **Hardcoded Secrets & Debug Leftovers**: Suspicious API keys/private keys and `pdb`/`debugger` breakpoints.
- **Sensitive Surface Radar**: Touches to `auth`, `billing`/`payment`/`ledger`, DB migrations, `.github/workflows`, `.env`, and dependency lockfiles.
- **Custom Team Rules (`.veripr.toml`)**: Define unlimited custom regex policies, assertion-drop thresholds, and clean-tree requirements via stdlib `tomllib`.

## Quick Start

```bash
# Run directly with zero installation
PYTHONPATH=products/veripr python3 -m veripr \
  --repo . \
  --cmd "python3 -m unittest discover -s tests -v" \
  --md receipt.md \
  --html receipt.html \
  --fail-on-cheat
```

### Pro Client Delivery & Sprint Scorecard Mode
```bash
# White-label bilingual CN/EN printable client delivery certificate
PYTHONPATH=products/veripr python3 -m veripr \
  --config products/veripr/pro_kit/rulepacks/agency-client-delivery.toml \
  --cmd "pytest -q" \
  --vendor "Aurora Dev Studio" \
  --client "Acme Corp" \
  --project "Checkout API v2" \
  --milestone "M2 · Payment Webhook" \
  --lang zh --signoff \
  --html delivery-certificate.html

# Multi-commit Sprint Accountability Scorecard (HTML + CSV)
PYTHONPATH=products/veripr python3 -m veripr.rollup \
  --repo . --limit 20 \
  --html sprint-scorecard.html --csv sprint-scorecard.csv
```

## Origin
Built as **Product #001** inside the **$100 Silicon Partner Accountability Experiment (`EXP-001`)**.
