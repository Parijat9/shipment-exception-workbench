"""Persistent local review exercise. This command never writes to external systems."""

import argparse
import json
from pathlib import Path
from engine import Outbox, proposal, classify


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="build/review.db")
    sub = p.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("event_file")
    approve = sub.add_parser("approve")
    approve.add_argument("key")
    approve.add_argument("--reviewer", required=True)
    sub.add_parser("list")
    sub.add_parser("simulate-dispatch")
    args = p.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    box = Outbox(args.db)
    try:
        if args.command == "add":
            event = json.loads(Path(args.event_file).read_text())
            print(box.add(proposal(event, classify(event["note"]))))
        elif args.command == "approve":
            box.approve(args.key, args.reviewer)
        elif args.command == "simulate-dispatch":
            box.dispatch(lambda task: "SIM-" + task["idempotency_key"])
        print(json.dumps(box.rows(), indent=2))
    finally:
        box.close()


if __name__ == "__main__":
    main()
