import unittest
from twin import reconstruct, assess, demo

class TwinTests(unittest.TestCase):
    def event(self, key, time, state="departed"):
        return dict(event_id=key, shipment_id="S", event_time=time, state=state)

    def test_late_departure_does_not_regress_delivery(self):
        a = self.event("a", "2026-01-02T00:00:00Z", "delivered")
        b = self.event("b", "2026-01-01T00:00:00Z")
        self.assertEqual([e["state"] for e in reconstruct([a,b,a])["S"]], ["departed","delivered"])

    def test_conflict_rejected(self):
        with self.assertRaises(ValueError):
            reconstruct([self.event("a","2026-01-01T00:00:00Z"), self.event("a","2026-01-02T00:00:00Z")])

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            reconstruct([self.event("a","2026-01-01T00:00:00")])

    def test_equivalent_offsets_order_correctly(self):
        a = self.event("a","2026-01-01T03:00:00+03:00")
        b = self.event("b","2026-01-01T01:00:00Z")
        self.assertEqual(reconstruct([b,a])["S"], [a,b])

    def test_demo_explains_risk(self):
        first, second = demo()
        self.assertEqual(first["risk_score"], 100)
        self.assertEqual(second["status"], "delivered")
        self.assertEqual(second["delay_hours"], 24)
        self.assertNotIn("severe weather", second["reasons"])

    def test_missing_events(self):
        r = assess({"shipment_id":"S","due_at":"2026-01-02T00:00:00Z"}, [], {"severity":0}, {"queue_hours":0}, "2026-01-01T00:00:00Z")
        self.assertEqual(r["status"], "awaiting_events")
        self.assertEqual(r["risk_score"], 0)
