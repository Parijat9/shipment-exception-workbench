# Shipment issue tracker

Turns short shipment updates into tasks that someone can review and follow up on.

A note such as “arrival delayed by 150 minutes” needs a clear next step. This project gives the task a reason, a priority, an owner role and a response deadline.

![Shipment tasks ready for review](docs/preview.png)

[Open the sample report](https://parijat9.github.io/reports/exceptions.html)

## What it does

- Reads a shipment note and looks for a known issue.
- Sets the priority and response time using fixed business rules.
- Leaves unclear notes for a person to review.
- Stops repeat updates from creating duplicate tasks.
- Tracks approvals, failed sends and tasks that need another check.

## Try it

Python 3.10 or newer is enough for the default example. It runs locally without accounts or extra packages.

```bash
python -m unittest discover -s tests -v
python run.py
python evaluate.py
```

Open `build/index.html` in your browser. The files in `build/` also contain the task list and test results.

## How it works

1. Receive a shipment update.
2. Check the note and suggest the issue type.
3. Assign the owner role and response deadline.
4. Ask a person to approve the task.
5. Record whether the task was sent successfully.

If a send times out, the task is set aside for checking. Sending it again without checking could create duplicate work.

## What the example shows

The demo sends the same 80 updates through the process twice. It keeps 80 tasks, completes 27 simulated sends and leaves 53 tasks awaiting review. These are practice records; the demo does not send tasks to a real team.

There is also a set of 19 sample notes. The simple keyword method answers 10 of them correctly. It leaves the rest for review, including four notes whose wording it misses. These cases are kept in the results so the limits are easy to see.

## Optional note-reading service

The project can also ask an OpenAI model to suggest an issue type and quote the words that support it. A person still reviews the result. This option is not required for the demo.

To try it, set `OPENAI_API_KEY` and `OPENAI_MODEL` in your shell and run `python evaluate.py --live`. This uses paid API calls. Live results have not been measured; the connection code has been tested with sample responses.

## Connecting other tools

[Power Automate and Zoho Projects notes](integrations/README.md) explain the fields and steps needed to connect the workflow. They are setup instructions, not a working connection to a company account.

[Task commands and troubleshooting](docs/operations.md) explain how to add, approve and check tasks.
