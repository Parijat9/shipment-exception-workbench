# Working conventions

Run `python -m unittest discover -s tests -v` and `python run.py` after a change.
Use synthetic fixtures only. Never add client records, credentials or private URLs.
Keep business calculations in SQL or tested Python functions, not in prose.
A changed metric needs a definition, boundary tests and an explanation of who uses it.
Do not change golden results just to silence a failing test. Explain the difference.
External integrations default to local simulation. Never enable external writes in CI.
