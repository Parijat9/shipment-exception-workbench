# Power Automate and Zoho Projects

This directory contains a deployment contract, not an exported tenant solution.
The repository does not possess tenant connections, user IDs or project IDs.
`integrations.py` creates a portable task envelope and a candidate Zoho field mapping.
The latter is not a verified V3 HTTP request body. Confirm the target action schema
in your tenant before deployment; legacy Zoho REST examples are not a version guarantee.

## Flow design

1. Receive an approved task envelope through an authenticated HTTP request trigger.
2. Parse it using `task.schema.json`. Reject missing keys or unknown owner roles.
3. Use a Dataverse table with `idempotency_key` as an alternate key. Create a ledger
   row before creating the remote task. A duplicate key routes to reconciliation.
4. Resolve owner role to a configured Zoho user. Keep credentials in a managed connection.
5. Create a Zoho Projects task, retaining the external key in a custom field or description.
6. Record the remote task ID and return it to the caller.
7. On an ambiguous timeout, stop and look up the external key. Do not repeat Create Task.

A Dataverse key prevents duplicate ledger rows, not an atomic transaction across Zoho
and Dataverse. That gap is why reconciliation is required. Keep flow trigger concurrency
at one for the initial pilot. The external API action belongs in the flow; Office Scripts
run by Power Automate cannot make external API calls.

The task due time is ISO-8601 UTC. Configure the target timezone explicitly and preserve
the timestamp in the description if the chosen Zoho action accepts dates only.

## Validation before enabling

Use a sandbox project. Submit the same approved key twice, force a 429 before delivery,
force a timeout after remote creation, and confirm that each state has an operator path.
Check licensing for HTTP/Dataverse actions and organizational DLP rules.

## References

- [Power Automate request authentication](https://learn.microsoft.com/en-us/power-automate/oauth-authentication)
- [Office Scripts parameters](https://learn.microsoft.com/en-us/office/dev/scripts/develop/power-automate-parameters-returns)
- [External calls from Office Scripts](https://learn.microsoft.com/en-us/office/dev/scripts/develop/external-calls)
- [Zoho Projects tasks API](https://www.zoho.com/projects/help/rest-api/tasks-api.html)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
