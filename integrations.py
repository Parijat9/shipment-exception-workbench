"""Payload construction for controlled downstream integrations; no network writes."""


def power_automate_payload(task):
    return {
        k: task[k]
        for k in (
            "idempotency_key",
            "shipment_id",
            "title",
            "priority",
            "owner_role",
            "due_at",
            "category",
            "late_minutes",
        )
    }


def zoho_task_fields(task, owner_id):
    if not str(owner_id).isdigit():
        raise ValueError("Map an approved role to a Zoho user ID")
    return {
        "name": task["title"],
        "description": f"Shipment: {task['shipment_id']}\nReason: {task['category']}\nDelay: {task['late_minutes']} minutes\nExternal key: {task['idempotency_key']}",
        "person_responsible": str(owner_id),
        "priority": "High" if task["priority"] == "high" else "Medium",
    }
