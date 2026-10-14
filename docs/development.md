# Development workflow

Start with the business question and a small failing example. Use Codex to propose
a query, migration or test, then inspect its grain, joins, boundary conditions and
side effects. Run the full suite and compare the generated metrics before accepting it.

Useful bounded tasks:

- Add a regression test for a duplicate source record without changing the expected total.
- Explain the join cardinality of the reporting SQL and identify any possible fan-out.
- Add a new exception type with an explicit owner, acceptance criteria and replay test.
- Review a proposed integration for timeout ambiguity, retries and duplicate side effects.

Keep prompts limited to synthetic examples and the repository. Record substantive
design decisions in docs rather than committing assistant transcripts. Code review,
tests and business reconciliation remain the acceptance criteria.
