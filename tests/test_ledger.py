import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import ledger


class TestSiliconPartnerLedger(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "LEDGER.json"
        ledger.init_ledger(self.path, Decimal("100.00"))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_genesis_and_verify(self) -> None:
        chain = ledger.load_chain(self.path)
        ok, _ = ledger.verify_chain(chain)
        self.assertTrue(ok)
        state = ledger.replay_state(chain)
        self.assertEqual(state.cash_balance, Decimal("100.00"))
        self.assertEqual(state.high_water_mark, Decimal("100.00"))
        self.assertEqual(state.max_single_spend, Decimal("25.00"))
        self.assertEqual(state.status, "ACTIVE")

    def test_single_spend_cap_enforced(self) -> None:
        with self.assertRaises(ledger.GovernanceError):
            ledger.propose_spend(
                self.path, "P-001", Decimal("25.01"), "domain", "too expensive", "cancel"
            )

    def test_high_water_mark_deficit_recovery(self) -> None:
        # Spend $20 -> balance $80, deficit $20
        ledger.propose_spend(self.path, "P-001", Decimal("20.00"), "infra", "test", "kill")
        ledger.approve_spend(self.path, "P-001", "approved")

        # Earn $15 -> still $5 below HWM ($100), so AI fund MUST remain $0.00
        ledger.record_revenue(self.path, Decimal("15.00"), "sale-1", "tx-1")
        state = ledger.replay_state(ledger.load_chain(self.path))
        self.assertEqual(state.cash_balance, Decimal("95.00"))
        self.assertEqual(state.deficit_to_hwm, Decimal("5.00"))
        self.assertEqual(state.ai_fund_balance, Decimal("0.00"))
        self.assertEqual(state.high_water_mark, Decimal("100.00"))

        # Earn $25 -> equity reaches $120 ($20 net profit above HWM)
        # AI gets 20% of $20 = $4.00; Human gets 80% = $16.00; new HWM = $120.00
        ledger.record_revenue(self.path, Decimal("25.00"), "sale-2", "tx-2")
        state = ledger.replay_state(ledger.load_chain(self.path))
        self.assertEqual(state.cash_balance, Decimal("120.00"))
        self.assertEqual(state.net_pnl, Decimal("20.00"))
        self.assertEqual(state.ai_fund_balance, Decimal("4.00"))
        self.assertEqual(state.human_profit_share, Decimal("16.00"))
        self.assertEqual(state.high_water_mark, Decimal("120.00"))

    def test_yellow_card_circuit_breaker_at_50_percent_drawdown(self) -> None:
        # Three valid spends reducing cash below $50: 100 -> 75 -> 57 -> 44
        ledger.propose_spend(self.path, "P-1", Decimal("25.00"), "test", "1", "k")
        ledger.approve_spend(self.path, "P-1", "ok")
        ledger.propose_spend(self.path, "P-2", Decimal("18.00"), "test", "2", "k")
        ledger.approve_spend(self.path, "P-2", "ok")
        ledger.propose_spend(self.path, "P-3", Decimal("13.00"), "test", "3", "k")
        ledger.approve_spend(self.path, "P-3", "ok")

        state = ledger.replay_state(ledger.load_chain(self.path))
        self.assertEqual(state.cash_balance, Decimal("44.00"))
        self.assertEqual(state.status, "YELLOW_CARD_FROZEN")

        # Next spend proposal must be blocked automatically
        with self.assertRaises(ledger.GovernanceError):
            ledger.propose_spend(self.path, "P-4", Decimal("5.00"), "test", "4", "k")

        # Unfreeze after postmortem restores ACTIVE status
        ledger.unfreeze(self.path, "postmortems/001.md", "reviewed")
        state = ledger.replay_state(ledger.load_chain(self.path))
        self.assertEqual(state.status, "ACTIVE")
        self.assertEqual(state.max_single_spend, Decimal("11.00"))

    def test_tamper_detection(self) -> None:
        ledger.propose_spend(self.path, "P-1", Decimal("10.00"), "test", "r", "k")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        # Maliciously mutate amount in history without recomputing chain
        data[1]["payload"]["amount"] = "1.00"
        self.path.write_text(json.dumps(data), encoding="utf-8")

        ok, msg = ledger.verify_chain(ledger.load_chain(self.path))
        self.assertFalse(ok)
        self.assertIn("tampering", msg.lower())


if __name__ == "__main__":
    unittest.main()
