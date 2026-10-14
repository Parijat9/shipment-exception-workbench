"""Deterministic SLAs, constrained note classification and an approval outbox."""

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone

CATEGORIES = ("weather", "equipment", "facility", "documentation", "unknown")
OWNERS = {
    "weather": "dispatch",
    "equipment": "carrier_management",
    "facility": "customer_operations",
    "documentation": "billing",
    "unknown": "operations_review",
}
TERMS = {
    "weather": ("snow", "storm", "flood", "ice"),
    "equipment": ("breakdown", "flat tire", "engine", "mechanical"),
    "facility": ("dock", "queue", "warehouse", "appointment"),
    "documentation": ("pod", "paperwork", "bill of lading", "document"),
}


def timestamp(value):
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("Timezone required")
    return d.astimezone(timezone.utc)


def classify(note):
    hits = []
    for category, terms in TERMS.items():
        for term in terms:
            match = re.search(r"\b" + re.escape(term) + r"\b", note, re.I)
            if match:
                hits.append((category, match.group(0)))
                break
    # Ambiguous messages go to review; negation is deliberately not guessed.
    if len(hits) != 1 or re.search(
        r"\b(no|not|never|ignore|instruction|system)\b", note, re.I
    ):
        return {"category": "unknown", "evidence": ""}
    category, evidence = hits[0]
    return {"category": category, "evidence": evidence}


def validate_prediction(prediction, note):
    if set(prediction) != {"category", "evidence"}:
        raise ValueError("Unexpected fields")
    category = prediction["category"]
    evidence = prediction["evidence"]
    if category not in CATEGORIES or not isinstance(evidence, str):
        raise ValueError("Invalid classification")
    if category == "unknown":
        if evidence != "":
            raise ValueError("Unknown classification must abstain")
    elif not evidence or evidence not in note or len(evidence) > 240:
        raise ValueError("Evidence must be an exact short source excerpt")
    # Evidence membership is a structural check, not proof of semantic accuracy.
    return prediction


def proposal(event, prediction):
    required = {
        "event_id",
        "shipment_id",
        "promised_at",
        "eta_at",
        "note",
        "received_at",
    }
    if set(event) != required:
        raise ValueError("Event contract mismatch")
    if not re.fullmatch(r"EV[0-9]{5}", event["event_id"]) or not re.fullmatch(
        r"S[0-9]{6}", event["shipment_id"]
    ):
        raise ValueError("Invalid event or shipment identifier")
    if not isinstance(event["note"], str) or len(event["note"]) > 4000:
        raise ValueError("Invalid note")
    received = timestamp(event["received_at"])
    late = max(
        0,
        int(
            (
                timestamp(event["eta_at"]) - timestamp(event["promised_at"])
            ).total_seconds()
            / 60
        ),
    )
    prediction = validate_prediction(prediction, event["note"])
    category = prediction["category"]
    priority = "high" if late >= 120 else "normal"
    # SLA and ownership remain code-owned. The model cannot choose a recipient or deadline.
    due = received + timedelta(minutes=30 if priority == "high" else 120)
    key = hashlib.sha256(event["event_id"].encode()).hexdigest()[:24]
    return {
        "idempotency_key": key,
        "event_id": event["event_id"],
        "shipment_id": event["shipment_id"],
        "category": category,
        "evidence": prediction["evidence"],
        "late_minutes": late,
        "priority": priority,
        "owner_role": OWNERS[category],
        "due_at": due.isoformat(),
        "title": f"Review {event['shipment_id']}: {category}",
        "requires_review": True,
    }


class RetryableError(Exception):
    pass


class AmbiguousDelivery(Exception):
    pass


class Outbox:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS task(id TEXT PRIMARY KEY, payload TEXT NOT NULL,
          state TEXT NOT NULL, reviewer TEXT, attempts INTEGER NOT NULL DEFAULT 0, remote_id TEXT);
        CREATE TABLE IF NOT EXISTS audit(sequence INTEGER PRIMARY KEY,task_id TEXT,state TEXT,actor TEXT);
        """)

    def add(self, payload):
        key = payload["idempotency_key"]
        raw = json.dumps(payload, sort_keys=True)
        old = self.db.execute("SELECT payload FROM task WHERE id=?", (key,)).fetchone()
        if old and old["payload"] != raw:
            raise ValueError("Conflicting event replay")
        with self.db:
            cur = self.db.execute(
                "INSERT OR IGNORE INTO task(id,payload,state) VALUES(?,?,'review')",
                (key, raw),
            )
            if cur.rowcount:
                self.db.execute(
                    "INSERT INTO audit(task_id,state,actor) VALUES(?,'review','pipeline')",
                    (key,),
                )
        return key

    def approve(self, key, reviewer):
        if not reviewer.strip():
            raise ValueError("Reviewer required")
        with self.db:
            changed = self.db.execute(
                "UPDATE task SET state='approved',reviewer=? WHERE id=? AND state='review'",
                (reviewer, key),
            ).rowcount
            if not changed:
                raise ValueError("Only review tasks can be approved")
            self.db.execute(
                "INSERT INTO audit(task_id,state,actor) VALUES(?,'approved',?)",
                (key, reviewer),
            )

    def dispatch(self, sender, max_attempts=3):
        # Single-worker SQLite design. Claim transaction commits before network I/O.
        # A crash after claiming leaves 'sending' for reconciliation, never blind replay.
        rows = self.db.execute(
            "SELECT * FROM task WHERE state IN ('approved','retry') AND attempts<? ORDER BY id",
            (max_attempts,),
        ).fetchall()
        for row in rows:
            with self.db:
                changed = self.db.execute(
                    "UPDATE task SET state='sending',attempts=attempts+1 WHERE id=? AND state IN ('approved','retry')",
                    (row["id"],),
                ).rowcount
            if not changed:
                continue
            remote = None
            try:
                remote = sender(json.loads(row["payload"]))
                if not isinstance(remote, str) or not remote:
                    raise AmbiguousDelivery()
                state = "sent"
            except RetryableError:
                state = "retry" if row["attempts"] + 1 < max_attempts else "failed"
            except Exception:
                state = "reconcile"
            with self.db:
                self.db.execute(
                    "UPDATE task SET state=?,remote_id=? WHERE id=?",
                    (state, remote, row["id"]),
                )
                self.db.execute(
                    "INSERT INTO audit(task_id,state,actor) VALUES(?,?,'dispatcher')",
                    (row["id"], state),
                )

    def rows(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM task ORDER BY id")]

    def close(self):
        self.db.close()
