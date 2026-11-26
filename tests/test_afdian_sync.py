import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import ledger
from ops.sync_afdian_orders import (
    compute_afdian_sign,
    fetch_paid_orders,
    reconcile_orders_to_ledger,
)


class TestAfdianOrderSync(unittest.TestCase):
    def test_official_doc_md5_signature_vector(self) -> None:
        # Official example from https://guide.afdian.com/creator/developer
        sign = compute_afdian_sign(
            token="123",
            params_json='{"a":333}',
            ts=1624339905,
            user_id="abc",
        )
        self.assertEqual(sign, "a4acc28b81598b7e5d84ebdc3e91710c")

    def test_idempotent_order_reconciliation_and_profit_share(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "LEDGER.json"
            ledger.init_ledger(ledger_path, Decimal("100.00"))

            def fake_post(url: str, payload: dict) -> dict:
                self.assertTrue(url.endswith("/query-order"))
                return {
                    "ec": 200,
                    "em": "",
                    "data": {
                        "total_page": 1,
                        "list": [
                            {
                                "out_trade_no": "202611260002",
                                "status": 2,
                                "total_amount": "0.00",  # free redeem code -> ignored
                                "sku_detail": [{"name": "Redeem"}],
                            },
                            {
                                "out_trade_no": "202611260001",
                                "status": 2,
                                "total_amount": "49.00",
                                "sku_detail": [{"name": "VeriPR Pro v0.2.0"}],
                            },
                        ],
                    },
                }

            orders = fetch_paid_orders("uid_demo", "tok_demo", max_pages=1, post_fn=fake_post)
            self.assertEqual(len(orders), 1)

            # First sync records 49 * 0.94 = 46.06 CNY -> / 7.25 = $6.35 USD
            added_first = reconcile_orders_to_ledger(
                ledger_path, orders, cny_per_usd=Decimal("7.25")
            )
            self.assertEqual(len(added_first), 1)

            # Second sync with exact same order list must be 100% idempotent (0 duplicates)
            added_second = reconcile_orders_to_ledger(
                ledger_path, orders, cny_per_usd=Decimal("7.25")
            )
            self.assertEqual(len(added_second), 0)

            ok, _ = ledger.verify_chain(ledger.load_chain(ledger_path))
            self.assertTrue(ok)
            state = ledger.replay_state(ledger.load_chain(ledger_path))
            self.assertEqual(state.total_revenue, Decimal("6.35"))
            self.assertEqual(state.ai_fund_balance, Decimal("1.27"))
            self.assertEqual(state.human_profit_share, Decimal("5.08"))


if __name__ == "__main__":
    unittest.main()
