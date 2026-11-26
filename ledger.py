#!/usr/bin/env python3
"""
Silicon Partner Hash-Chained Accountability Ledger (v1.0)

Implements silicon-native financial governance in code:
- Append-only SHA-256 hash-chained entries (tamper-evident audit trail)
- Hard 25% single-spend cap against current cash balance
- Automatic 50% drawdown Yellow Card circuit breaker
- Strict High-Water Mark (HWM) 80/20 net profit allocation
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

DEFAULT_LEDGER_PATH = Path(__file__).resolve().parent / "LEDGER.json"
CENT = Decimal("0.01")
SINGLE_SPEND_CAP_RATIO = Decimal("0.25")
YELLOW_CARD_THRESHOLD_RATIO = Decimal("0.50")
AI_PROFIT_SHARE_RATIO = Decimal("0.20")


def q2(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def to_dec(value: str | int | float | Decimal) -> Decimal:
    return q2(Decimal(str(value)))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_entry_hash(entry_without_hash: dict[str, Any]) -> str:
    canonical = json.dumps(
        entry_without_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class LedgerState:
    initial_capital: Decimal
    cash_balance: Decimal
    total_spent: Decimal
    total_revenue: Decimal
    high_water_mark: Decimal
    ai_fund_balance: Decimal
    human_profit_share: Decimal
    status: str  # ACTIVE | YELLOW_CARD_FROZEN | BANKRUPT
    pending_proposals: dict[str, dict[str, Any]]

    @property
    def net_pnl(self) -> Decimal:
        return q2(self.total_revenue - self.total_spent)

    @property
    def deficit_to_hwm(self) -> Decimal:
        equity = q2(self.initial_capital + self.net_pnl)
        gap = q2(self.high_water_mark - equity)
        return gap if gap > Decimal("0.00") else Decimal("0.00")

    @property
    def max_single_spend(self) -> Decimal:
        if self.status != "ACTIVE":
            return Decimal("0.00")
        return q2(self.cash_balance * SINGLE_SPEND_CAP_RATIO)


class GovernanceError(Exception):
    """Raised when an action violates the Silicon Partner Charter."""


def load_chain(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise GovernanceError(f"Ledger not found at {path}. Run `init` first.")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise GovernanceError("Ledger file is empty or malformed.")
    return data


def save_chain(path: Path, chain: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(chain, f, indent=2, ensure_ascii=False)
        f.write("\n")


def verify_chain(chain: list[dict[str, Any]]) -> tuple[bool, str]:
    expected_prev = "0" * 64
    for idx, entry in enumerate(chain):
        if entry.get("seq") != idx:
            return False, f"Sequence mismatch at index {idx}: got {entry.get('seq')}"
        if entry.get("prev_hash") != expected_prev:
            return False, f"Broken prev_hash link at seq {idx}"
        recorded_hash = entry.get("hash")
        body = {k: v for k, v in entry.items() if k != "hash"}
        actual_hash = compute_entry_hash(body)
        if recorded_hash != actual_hash:
            return False, f"Hash tampering detected at seq {idx}"
        expected_prev = actual_hash
    return True, f"Verified {len(chain)} block(s). Tip hash: {expected_prev[:16]}..."


def replay_state(chain: list[dict[str, Any]]) -> LedgerState:
    ok, msg = verify_chain(chain)
    if not ok:
        raise GovernanceError(f"Cannot replay corrupted ledger: {msg}")

    genesis = chain[0]
    if genesis.get("type") != "GENESIS":
        raise GovernanceError("First ledger entry must be GENESIS.")

    initial_capital = to_dec(genesis["payload"]["initial_capital"])
    state = LedgerState(
        initial_capital=initial_capital,
        cash_balance=initial_capital,
        total_spent=Decimal("0.00"),
        total_revenue=Decimal("0.00"),
        high_water_mark=initial_capital,
        ai_fund_balance=Decimal("0.00"),
        human_profit_share=Decimal("0.00"),
        status="ACTIVE",
        pending_proposals={},
    )

    for entry in chain[1:]:
        etype = entry["type"]
        payload = entry["payload"]

        if etype == "SPEND_PROPOSAL":
            pid = payload["proposal_id"]
            state.pending_proposals[pid] = payload

        elif etype == "SPEND_REJECTED":
            pid = payload["proposal_id"]
            state.pending_proposals.pop(pid, None)

        elif etype == "SPEND_APPROVED":
            pid = payload["proposal_id"]
            amount = to_dec(payload["amount"])
            state.pending_proposals.pop(pid, None)
            state.cash_balance = q2(state.cash_balance - amount)
            state.total_spent = q2(state.total_spent + amount)
            _update_health_status(state)

        elif etype == "REVENUE_CONFIRMED":
            amount = to_dec(payload["amount"])
            state.cash_balance = q2(state.cash_balance + amount)
            state.total_revenue = q2(state.total_revenue + amount)
            equity = q2(state.initial_capital + state.net_pnl)
            if equity > state.high_water_mark:
                incremental_profit = q2(equity - state.high_water_mark)
                ai_cut = q2(incremental_profit * AI_PROFIT_SHARE_RATIO)
                human_cut = q2(incremental_profit - ai_cut)
                state.ai_fund_balance = q2(state.ai_fund_balance + ai_cut)
                state.human_profit_share = q2(state.human_profit_share + human_cut)
                state.high_water_mark = equity
            _update_health_status(state)

        elif etype == "UNFREEZE_APPROVED":
            if state.cash_balance > Decimal("0.00"):
                state.status = "ACTIVE"

    return state


def _update_health_status(state: LedgerState) -> None:
    if state.cash_balance <= Decimal("0.00"):
        state.status = "BANKRUPT"
    elif state.cash_balance < q2(state.initial_capital * YELLOW_CARD_THRESHOLD_RATIO):
        state.status = "YELLOW_CARD_FROZEN"


def append_entry(
    path: Path, entry_type: str, actor: str, payload: dict[str, Any]
) -> dict[str, Any]:
    chain = load_chain(path)
    prev = chain[-1]
    body = {
        "seq": len(chain),
        "timestamp": now_iso(),
        "type": entry_type,
        "actor": actor,
        "payload": payload,
        "prev_hash": prev["hash"],
    }
    body["hash"] = compute_entry_hash(body)
    chain.append(body)
    save_chain(path, chain)
    return body


def init_ledger(path: Path, initial_capital: Decimal = Decimal("100.00")) -> dict[str, Any]:
    if path.exists():
        raise GovernanceError(f"Ledger already exists at {path}")
    body = {
        "seq": 0,
        "timestamp": now_iso(),
        "type": "GENESIS",
        "actor": "HUMAN_AND_AI",
        "payload": {
            "experiment_id": "EXP-001",
            "currency": "USD",
            "initial_capital": str(q2(initial_capital)),
            "single_spend_cap_ratio": str(SINGLE_SPEND_CAP_RATIO),
            "yellow_card_threshold_ratio": str(YELLOW_CARD_THRESHOLD_RATIO),
            "ai_profit_share_ratio": str(AI_PROFIT_SHARE_RATIO),
            "note": "Silicon Partner Experiment Genesis Block",
        },
        "prev_hash": "0" * 64,
    }
    body["hash"] = compute_entry_hash(body)
    save_chain(path, [body])
    return body


def propose_spend(
    path: Path,
    proposal_id: str,
    amount: Decimal,
    category: str,
    reason: str,
    kill_criteria: str,
) -> dict[str, Any]:
    chain = load_chain(path)
    state = replay_state(chain)
    amount = q2(amount)

    if state.status != "ACTIVE":
        raise GovernanceError(
            f"Spend proposal blocked: governance status is {state.status}."
        )
    if amount <= Decimal("0.00"):
        raise GovernanceError("Spend amount must be positive.")
    if proposal_id in state.pending_proposals:
        raise GovernanceError(f"Proposal ID {proposal_id} is already pending.")
    if amount > state.max_single_spend:
        raise GovernanceError(
            f"Spend ${amount} exceeds 25% single-spend cap (${state.max_single_spend} "
            f"of current balance ${state.cash_balance})."
        )

    return append_entry(
        path,
        entry_type="SPEND_PROPOSAL",
        actor="SILICON_PARTNER",
        payload={
            "proposal_id": proposal_id,
            "amount": str(amount),
            "category": category,
            "reason": reason,
            "kill_criteria": kill_criteria,
        },
    )


def approve_spend(
    path: Path, proposal_id: str, approver_note: str, receipt_ref: str = ""
) -> dict[str, Any]:
    chain = load_chain(path)
    state = replay_state(chain)

    if state.status != "ACTIVE":
        raise GovernanceError(f"Cannot execute spend while status is {state.status}.")
    if proposal_id not in state.pending_proposals:
        raise GovernanceError(f"No pending proposal with ID {proposal_id}.")

    proposal = state.pending_proposals[proposal_id]
    amount = to_dec(proposal["amount"])
    if amount > state.max_single_spend:
        raise GovernanceError(
            f"Proposal {proposal_id} (${amount}) now exceeds current 25% cap (${state.max_single_spend})."
        )

    return append_entry(
        path,
        entry_type="SPEND_APPROVED",
        actor="HUMAN_PARTNER",
        payload={
            "proposal_id": proposal_id,
            "amount": str(amount),
            "category": proposal["category"],
            "approver_note": approver_note,
            "receipt_ref": receipt_ref,
        },
    )


def record_revenue(
    path: Path, amount: Decimal, source: str, proof_ref: str
) -> dict[str, Any]:
    chain = load_chain(path)
    _ = replay_state(chain)
    amount = q2(amount)
    if amount <= Decimal("0.00"):
        raise GovernanceError("Confirmed revenue must be positive.")

    return append_entry(
        path,
        entry_type="REVENUE_CONFIRMED",
        actor="HUMAN_PARTNER",
        payload={
            "amount": str(amount),
            "source": source,
            "proof_ref": proof_ref,
        },
    )


def unfreeze(path: Path, postmortem_ref: str, approver_note: str) -> dict[str, Any]:
    chain = load_chain(path)
    state = replay_state(chain)
    if state.status == "BANKRUPT":
        raise GovernanceError("Cannot unfreeze a BANKRUPT ledger.")
    return append_entry(
        path,
        entry_type="UNFREEZE_APPROVED",
        actor="HUMAN_PARTNER",
        payload={
            "postmortem_ref": postmortem_ref,
            "approver_note": approver_note,
        },
    )


def print_status(path: Path) -> None:
    chain = load_chain(path)
    ok, verify_msg = verify_chain(chain)
    state = replay_state(chain)

    print("=== Silicon Partner Ledger Status (EXP-001) ===")
    print(f"Integrity          : {'PASS' if ok else 'FAIL'} ({verify_msg})")
    print(f"Governance Status  : {state.status}")
    print(f"Initial Capital    : ${state.initial_capital}")
    print(f"Cash Balance       : ${state.cash_balance}")
    print(f"Total Spent        : ${state.total_spent}")
    print(f"Confirmed Revenue  : ${state.total_revenue}")
    print(f"Net P&L            : ${state.net_pnl}")
    print(f"High-Water Mark    : ${state.high_water_mark}")
    print(f"Deficit to HWM     : ${state.deficit_to_hwm}")
    print(f"Human Profit (80%) : ${state.human_profit_share}")
    print(f"AI Auto Fund (20%) : ${state.ai_fund_balance}")
    print(f"Max Single Spend   : ${state.max_single_spend}")
    print(f"Pending Proposals  : {len(state.pending_proposals)}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Silicon Partner Accountability Ledger CLI")
    p.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER_PATH)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize Genesis block")
    p_init.add_argument("--capital", default="100.00")

    sub.add_parser("status", help="Show current balances and governance status")
    sub.add_parser("verify", help="Verify cryptographic hash chain integrity")

    p_prop = sub.add_parser("propose-spend", help="Submit a spend proposal (AI)")
    p_prop.add_argument("--id", required=True)
    p_prop.add_argument("--amount", required=True)
    p_prop.add_argument("--category", required=True)
    p_prop.add_argument("--reason", required=True)
    p_prop.add_argument("--kill-criteria", required=True)

    p_app = sub.add_parser("approve-spend", help="Approve pending spend (Human)")
    p_app.add_argument("--id", required=True)
    p_app.add_argument("--note", required=True)
    p_app.add_argument("--receipt", default="")

    p_rev = sub.add_parser("record-revenue", help="Record confirmed net revenue (Human)")
    p_rev.add_argument("--amount", required=True)
    p_rev.add_argument("--source", required=True)
    p_rev.add_argument("--proof", required=True)

    p_un = sub.add_parser("unfreeze", help="Unfreeze after Yellow Card postmortem (Human)")
    p_un.add_argument("--postmortem", required=True)
    p_un.add_argument("--note", required=True)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "init":
            entry = init_ledger(args.ledger, to_dec(args.capital))
            print(f"Initialized Genesis block at {args.ledger} (hash={entry['hash'][:16]}...)")
        elif args.cmd == "status":
            print_status(args.ledger)
        elif args.cmd == "verify":
            ok, msg = verify_chain(load_chain(args.ledger))
            print(f"{'PASS' if ok else 'FAIL'}: {msg}")
            return 0 if ok else 1
        elif args.cmd == "propose-spend":
            entry = propose_spend(
                args.ledger,
                args.id,
                to_dec(args.amount),
                args.category,
                args.reason,
                args.kill_criteria,
            )
            print(f"Recorded proposal {args.id} (seq={entry['seq']}, hash={entry['hash'][:16]}...)")
        elif args.cmd == "approve-spend":
            entry = approve_spend(args.ledger, args.id, args.note, args.receipt)
            print(f"Approved spend {args.id} (seq={entry['seq']}, hash={entry['hash'][:16]}...)")
        elif args.cmd == "record-revenue":
            entry = record_revenue(args.ledger, to_dec(args.amount), args.source, args.proof)
            print(f"Recorded revenue ${to_dec(args.amount)} (seq={entry['seq']}, hash={entry['hash'][:16]}...)")
        elif args.cmd == "unfreeze":
            entry = unfreeze(args.ledger, args.postmortem, args.note)
            print(f"Unfrozen ledger (seq={entry['seq']}, hash={entry['hash'][:16]}...)")
        return 0
    except GovernanceError as exc:
        print(f"GOVERNANCE ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
