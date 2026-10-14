# Workflow operations

## Roles and SLA

Weather routes to dispatch, equipment to carrier management, facility delays to
customer operations, documentation to billing, and unknown reasons to operations review.
A predicted delay of at least 120 minutes has a 30-minute response SLA; other events
have a 120-minute SLA. Deadlines start at event receipt in UTC. These are illustrative
policy settings and are not a carrier contract or a promise to a customer.

Reviewers confirm the reason and evidence before approval. A model may not authorize
its own action, change an owner ID or invent a deadline.

## State transitions

`review -> approved -> sending -> sent`

A documented pre-send failure changes `sending` to `retry`, then to `failed` at the
attempt limit. An unknown response changes it to `reconcile`. A process crash can
leave `sending`. Both require inspection of the remote system by the external key.
Do not reset these states until you know whether a task exists remotely.

`Outbox(path)` persists the queue. `add(payload)` enforces idempotency,
`approve(key, reviewer)` records review and `dispatch(sender)` performs delivery.
The default demo uses an in-memory database to make repeated demonstrations identical.
The `workflow.py` CLI exposes a persistent offline queue for manual review exercises.

## Acceptance and rollout

1. Agree owner mappings and SLA thresholds with operations.
2. Evaluate reason classification on independently labeled, de-identified notes.
3. Shadow the workflow without creating external tasks. Measure review time and rejection reasons.
4. Test duplicate delivery, timeout ambiguity and provider outages in a sandbox.
5. Enable a limited pilot only after task ownership, reconciliation and rollback are assigned.

Track classification accuracy, abstention, review rejection rate, overdue review,
duplicate remote tasks and unresolved delivery outcomes. No time-saving percentage is
claimed because this repository has no observed manual-work baseline.
