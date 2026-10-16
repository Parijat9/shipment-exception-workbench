import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from engine import Outbox, classify, proposal, RetryableError
from evaluate import evaluate
from integrations import power_automate_payload
from report import render, comparison_chart


def run(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fixtures = json.loads(
        (Path(__file__).parent / "fixtures/evaluation.json").read_text()
    )
    box = (
        Outbox()
    )  # Deterministic demo reset; production callers pass a persistent path.
    tasks = []
    base = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
    for i in range(80):
        event = {
            "event_id": f"EV{i:05}",
            "shipment_id": f"S{i+1:06}",
            "promised_at": base.isoformat(),
            "eta_at": (base + timedelta(minutes=(i % 6) * 45)).isoformat(),
            "received_at": (base - timedelta(hours=1)).isoformat(),
            "note": fixtures[i % len(fixtures)]["note"],
        }
        task = proposal(event, classify(event["note"]))
        tasks.append(task)
        key = box.add(task)
        box.add(task)
        # Explicitly simulated review, never approval by the model.
        if i % 3 == 0:
            box.approve(key, "demo_reviewer")
    calls = {}

    def sender(task):
        key = task["idempotency_key"]
        calls[key] = calls.get(key, 0) + 1
        if calls[key] == 1:
            raise RetryableError("Simulated pre-send failure")
        return "SIM-" + key

    box.dispatch(sender)
    box.dispatch(sender)
    box.dispatch(sender)
    rows = box.rows()
    evaluation = evaluate(classify)
    metrics = {
        "events": 80,
        "unique_tasks": len(rows),
        "sent_simulated": sum(r["state"] == "sent" for r in rows),
        "awaiting_review": sum(r["state"] == "review" for r in rows),
        "holdout_accuracy": evaluation["accuracy"],
        "holdout_coverage": evaluation["coverage"],
        "live_ai_tested": False,
        "live_integrations_tested": False,
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (out / "evaluation-baseline.json").write_text(
        json.dumps(evaluation, indent=2) + "\n"
    )
    (out / "tasks.json").write_text(json.dumps(tasks, indent=2) + "\n")
    (out / "power-automate-payload.json").write_text(
        json.dumps(power_automate_payload(tasks[0]), indent=2) + "\n"
    )
    views = [
        {
            **{
                k: t[k]
                for k in (
                    "shipment_id",
                    "category",
                    "late_minutes",
                    "priority",
                    "owner_role",
                    "due_at",
                )
            },
            "state": next(r["state"] for r in rows if r["id"] == t["idempotency_key"]),
        }
        for t in tasks
    ]
    categories = sorted({t["category"] for t in tasks})
    chart = comparison_chart(
        "Issues by type",
        categories,
        [("Tasks", [sum(t["category"] == c for t in tasks) for c in categories])],
    )
    render(
        out / "index.html",
        "Shipment issue tracker",
        "Turn shipment updates into tasks with an owner and a deadline, without creating duplicates.",
        {
            "Shipment updates": 80,
            "Unique tasks": len(rows),
            "Simulated sends": metrics["sent_simulated"],
            "Awaiting review": metrics["awaiting_review"],
        },
        views,
        f"Keyword matching made the right decision for {evaluation['accuracy']:.1%} of {evaluation['cases']} sample notes. It missed some notes that used different words for the same issue. The optional language-model service has not been tested live. Rules set each task's owner and deadline. A person reviews every task before it is sent.",
        chart=chart,
    )
    box.close()
    return metrics


if __name__ == "__main__":
    print(json.dumps(run("build"), indent=2))
