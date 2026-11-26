# Silicon Partner Lab (`EXP-001`) · $100 硅基合伙人实验

> **An open, cryptographically audited experiment testing whether an AI operating under silicon-native accountability ($100 seed capital, 25% spend cap, 50% drawdown circuit breaker, 20% High-Water-Mark fund) can create genuine real-world value.**

| Governance Metric | Current Value | Verification |
| --- | --- | --- |
| Initial Seed Capital | `$100.00 USD` | Genesis block `c3bda338b8d0d170...` |
| Total Spent | `$0.00 USD` | Run `python3 ledger.py verify` |
| Confirmed Net Revenue | `$0.00 USD` | External receipt required |
| High-Water Mark | `$100.00 USD` | Deficit recovered before any profit share |
| AI Autonomous Fund (20% above HWM) | `$0.00 USD` | Enforced in code (`ledger.py`) |
| Governance Status | `ACTIVE` | Max single spend: `$25.00` (25%) |

---

## Product #001: `VeriPR` (v0.2.0) — Deterministic AI PR Anti-Cheat & Proof-of-Verification Receipts

Writing plausible pull requests became nearly free in 2026; verifying that an AI coding agent didn't quietly skip tests, delete assertions, suppress linters, swallow errors, or touch sensitive auth/billing code did not.

**VeriPR** (`products/veripr/`) is a **zero-dependency, zero-LLM, 100% deterministic** auditor & receipt generator:
- **Anti-Cheat Diff Scanner**: Detects added `.skip` / `@pytest.mark.skip` / `@unittest.skip` / `#[ignore]`, deleted test files, net assertion drops, `@ts-ignore` / `eslint-disable` / `# noqa` / `# type: ignore` / `as any`, silent `except: pass`, hardcoded secrets, and sensitive surfaces (`auth`, `billing`, `ledger`, `migrations`, `.github/workflows`, lockfiles).
- **Commit-Bound Verification Runs**: Executes your actual test/lint commands against `HEAD`, hashes combined `stdout + stderr`, and seals the full audit into a canonical **SHA-256 Receipt**.
- **Outputs**: GitHub PR Markdown comment, self-contained HTML certificate, CI JSON gate (`--fail-on-cheat`), reusable GitHub Action (`products/veripr/action.yml`), and custom `.veripr.toml` policies.
- **Browser Zero-Backend Demo**: `site/index.html` runs the deterministic diff engine 100% locally in the browser with Web Crypto SHA-256 sealing.

### Quick Start

```bash
# Verify the SHA-256 accountability ledger
python3 ledger.py status
python3 ledger.py verify

# Run VeriPR on any local Git repository
PYTHONPATH=products/veripr python3 -m veripr \
  --repo . \
  --cmd "python3 -m unittest discover -s tests -v" \
  --md receipt.md \
  --html receipt.html \
  --fail-on-cheat
```

---

## Repository Structure

- `CHARTER.md` — Formal $100 Human-AI Partnership & Silicon Accountability Charter.
- `ledger.py` & `LEDGER.json` — SHA-256 hash-chained financial governance CLI + unit tests (`tests/test_ledger.py`).
- `JOURNAL.md` — Transparent build-in-public experiment log.
- `products/veripr/` — VeriPR v0.2.0 open-core package, GitHub Action, Pro rulepacks, and tests.
- `site/` — Zero-backend bilingual landing page + live in-browser diff auditor.
- `ops/` — Persistent itemized Human Partner Action Checklist (`HUMAN_ACTION_ITEMS.md/.json`) & cloud sync tooling.
- `research/` & `launch/` — Live market research logs and bilingual launch kits.

## License
Core tools (`ledger.py`, `products/veripr/veripr/`) are MIT licensed.
