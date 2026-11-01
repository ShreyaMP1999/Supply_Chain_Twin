"""Dependency-free shipment reconstruction and disruption intelligence."""
from datetime import datetime, timezone
import json

STATES = {"ordered", "departed", "port_arrival", "delivered"}

def timestamp(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timezone required")
    return dt.astimezone(timezone.utc)

def reconstruct(events):
    unique = {}
    for event in events:
        if event["state"] not in STATES:
            raise ValueError("Unknown state")
        timestamp(event["event_time"])
        key = event["event_id"]
        if key in unique and unique[key] != event:
            raise ValueError("Conflicting event ID")
        unique[key] = event
    shipments = {}
    for event in sorted(unique.values(), key=lambda e: (timestamp(e["event_time"]), e["event_id"])):
        shipments.setdefault(event["shipment_id"], []).append(event)
    return shipments

def assess(order, timeline, weather, port, now):
    due = timestamp(order["due_at"])
    delivered = [e for e in timeline if e["state"] == "delivered"]
    completed = min((timestamp(e["event_time"]) for e in delivered), default=None)
    overdue = max(0, ((completed or timestamp(now)) - due).total_seconds() / 3600)
    reasons = []
    score = 0
    if overdue:
        score += min(60, overdue * 3)
        reasons.append("delivery overdue")
    if not completed:
        if weather["severity"] >= 0.7:
            score += 25
            reasons.append("severe weather")
        if port["queue_hours"] >= 24:
            score += 25
            reasons.append("port congestion")
    return {"shipment_id": order["shipment_id"], "status": "delivered" if completed else (timeline[-1]["state"] if timeline else "awaiting_events"),
            "risk_score": round(min(100, score), 1), "delay_hours": round(overdue, 1),
            "reasons": reasons, "timeline": [e["state"] for e in timeline]}

def demo():
    events = [
        {"event_id": "e2", "shipment_id": "S1", "state": "port_arrival", "event_time": "2026-01-02T00:00:00Z"},
        {"event_id": "e1", "shipment_id": "S1", "state": "departed", "event_time": "2026-01-01T00:00:00Z"},
        {"event_id": "e4", "shipment_id": "S2", "state": "delivered", "event_time": "2026-01-03T00:00:00Z"},
        {"event_id": "e3", "shipment_id": "S2", "state": "departed", "event_time": "2026-01-01T00:00:00Z"}]
    timelines = reconstruct(events + [events[0]])
    return [assess({"shipment_id": sid, "due_at": "2026-01-02T00:00:00Z"},
                   timeline, {"severity": 0.9}, {"queue_hours": 36}, "2026-01-04T00:00:00Z")
            for sid, timeline in timelines.items()]

if __name__ == "__main__":
    print(json.dumps(demo(), indent=2))
