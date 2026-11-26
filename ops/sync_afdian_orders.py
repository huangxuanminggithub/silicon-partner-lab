#!/usr/bin/env python3
"""
Official Afdian Open API Read-Only Order Reconciler for Silicon Partner Lab (EXP-001).

Uses Afdian's documented Open API (`https://afdian.com/dashboard/dev`):
  - POST https://afdian.com/api/open/ping
  - POST https://afdian.com/api/open/query-order

Security & Governance Properties:
  - Uses ONLY scoped read-only `AFDIAN_USER_ID` + `AFDIAN_API_TOKEN` (never session cookies).
  - Never logs or prints `AFDIAN_API_TOKEN`.
  - Deduplicates strictly by `proof_ref == "afdian:<out_trade_no>"` against `LEDGER.json`.
  - Records net payout after Afdian's 6% platform & payment channel fee (`* 0.94`), converted
    to USD at configurable `AFDIAN_CNY_PER_USD` (default `7.25`), preserving SHA-256 chain.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ledger  # noqa: E402

AFDIAN_API_BASE = os.environ.get("AFDIAN_API_BASE", "https://ifdian.net/api/open")
AFDIAN_API_FALLBACK = "https://afdian.com/api/open"
AFDIAN_NET_RATIO = Decimal("0.94")  # 100% - 6% Afdian platform + channel fee
DEFAULT_CNY_PER_USD = Decimal("7.25")


def compute_afdian_sign(token: str, params_json: str, ts: int, user_id: str) -> str:
    """Compute official Afdian MD5 request signature: md5('{token}params{params}ts{ts}user_id{user_id}')."""
    raw = f"{token}params{params_json}ts{ts}user_id{user_id}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def build_signed_payload(
    user_id: str, token: str, params: dict[str, Any], ts: int | None = None
) -> dict[str, Any]:
    timestamp = int(time.time()) if ts is None else int(ts)
    params_json = json.dumps(params, separators=(",", ":"), ensure_ascii=False)
    sign = compute_afdian_sign(token=token, params_json=params_json, ts=timestamp, user_id=user_id)
    return {
        "user_id": user_id,
        "params": params_json,
        "ts": timestamp,
        "sign": sign,
    }


def _post_once(url: str, body: bytes) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SiliconPartnerLab-LedgerReconciler/0.2",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def default_post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        return _post_once(url, body)
    except Exception:
        if AFDIAN_API_BASE in url and AFDIAN_API_BASE != AFDIAN_API_FALLBACK:
            fallback_url = url.replace(AFDIAN_API_BASE, AFDIAN_API_FALLBACK, 1)
            return _post_once(fallback_url, body)
        raise


def fetch_paid_orders(
    user_id: str,
    token: str,
    max_pages: int = 3,
    post_fn: Callable[[str, dict[str, Any]], dict[str, Any]] = default_post_json,
) -> list[dict[str, Any]]:
    """Fetch paid orders (`status == 2` and `total_amount > 0`) across recent pages."""
    paid: list[dict[str, Any]] = []
    page = 1
    while page <= max_pages:
        payload = build_signed_payload(user_id=user_id, token=token, params={"page": page})
        resp = post_fn(f"{AFDIAN_API_BASE}/query-order", payload)
        if resp.get("ec") != 200:
            raise RuntimeError(
                f"Afdian API error ec={resp.get('ec')}: {resp.get('em', 'unknown error')}"
            )
        data = resp.get("data") or {}
        orders = data.get("list") or []
        for order in orders:
            if order.get("status") != 2:
                continue
            gross = Decimal(str(order.get("total_amount", "0.00")))
            if gross <= Decimal("0.00"):
                continue
            paid.append(order)
        total_page = int(data.get("total_page") or 1)
        if page >= total_page or not orders:
            break
        page += 1
    # Process oldest-first so ledger sequence follows chronological order
    paid.reverse()
    return paid


def existing_proof_refs(chain: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for entry in chain:
        if entry.get("type") == "REVENUE_CONFIRMED":
            ref = str(entry.get("payload", {}).get("proof_ref", "")).strip()
            if ref:
                refs.add(ref)
    return refs


def summarize_order_item(order: dict[str, Any]) -> str:
    skus = order.get("sku_detail") or []
    if skus and isinstance(skus, list):
        names = [str(s.get("name", "")).strip() for s in skus if s.get("name")]
        if names:
            return " + ".join(names)
    title = str(order.get("title") or "").strip()
    return title or "Afdian Support / Digital Item"


def reconcile_orders_to_ledger(
    ledger_path: Path,
    orders: list[dict[str, Any]],
    cny_per_usd: Decimal = DEFAULT_CNY_PER_USD,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    chain = ledger.load_chain(ledger_path)
    _ = ledger.replay_state(chain)
    seen = existing_proof_refs(chain)

    recorded: list[dict[str, Any]] = []
    for order in orders:
        trade_no = str(order.get("out_trade_no", "")).strip()
        if not trade_no:
            continue
        proof_ref = f"afdian:{trade_no}"
        if proof_ref in seen:
            continue

        gross_cny = ledger.q2(Decimal(str(order["total_amount"])))
        net_cny = ledger.q2(gross_cny * AFDIAN_NET_RATIO)
        net_usd = ledger.q2(net_cny / cny_per_usd)
        if net_usd <= Decimal("0.00"):
            continue

        item_label = summarize_order_item(order)
        source = f"Afdian ({item_label}; gross CNY {gross_cny}, net CNY {net_cny} @ {cny_per_usd})"
        if dry_run:
            recorded.append(
                {
                    "proof_ref": proof_ref,
                    "gross_cny": str(gross_cny),
                    "net_usd": str(net_usd),
                    "source": source,
                }
            )
        else:
            entry = ledger.record_revenue(
                path=ledger_path,
                amount=net_usd,
                source=source,
                proof_ref=proof_ref,
            )
            recorded.append(entry)
        seen.add(proof_ref)

    return recorded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync paid Afdian orders into LEDGER.json")
    parser.add_argument("--ledger", type=Path, default=ledger.DEFAULT_LEDGER_PATH)
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument(
        "--cny-per-usd",
        default=os.environ.get("AFDIAN_CNY_PER_USD", str(DEFAULT_CNY_PER_USD)),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-if-unconfigured",
        action="store_true",
        help="Exit 0 cleanly when AFDIAN_USER_ID / AFDIAN_API_TOKEN are not set yet.",
    )
    args = parser.parse_args(argv)

    user_id = os.environ.get("AFDIAN_USER_ID", "").strip()
    token = os.environ.get("AFDIAN_API_TOKEN", "").strip()

    if not user_id or not token:
        if args.skip_if_unconfigured:
            print("SKIP: AFDIAN_USER_ID or AFDIAN_API_TOKEN not configured yet.")
            return 0
        print(
            "ERROR: Missing AFDIAN_USER_ID or AFDIAN_API_TOKEN environment variables.",
            file=sys.stderr,
        )
        return 2

    cny_per_usd = Decimal(str(args.cny_per_usd))
    orders = fetch_paid_orders(user_id=user_id, token=token, max_pages=args.max_pages)
    new_entries = reconcile_orders_to_ledger(
        ledger_path=args.ledger,
        orders=orders,
        cny_per_usd=cny_per_usd,
        dry_run=args.dry_run,
    )
    print(
        f"Fetched {len(orders)} paid order(s); recorded {len(new_entries)} new ledger entry(ies)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
