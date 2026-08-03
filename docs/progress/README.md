# Progress files

One file per roadmap phase, created **when the phase starts** — not in advance.

These are the **volatile** half of the docs. Keep them separate from `decisions.md` so that reading current state doesn't drag stable content along, and so decisions stay stable while progress churns.

## Format

Each file has a fixed shape so an agent can read the top and stop:

```markdown
# Phase N — <name>

**Status:** not started | in progress | blocked | done
**Updated:** YYYY-MM-DD

## Current state
Two or three sentences. What works right now, what doesn't.

## Next action
The single next thing to do. Not a list.

## Done
- [x] ...

## Open questions
Things needing a decision. Promote to `decisions.md` once resolved.

## Notes
Gotchas, dead ends, things that cost time. Most valuable section
for a future session — write down what surprised you.
```

## Rules

- **Current state** and **Next action** stay at the top. A session should get oriented from the first 10 lines.
- Resolving an open question means adding a `D-##` to `decisions.md` and linking it here — never leaving the answer only in a progress file.
- Record dead ends. "Tried X, it failed because Y" saves a future session from repeating it and is the most common thing lost between sessions.
- Check `docs/verification.md` when starting a phase — it lists the expected values for bugs in that phase that produce plausible output without erroring. Add the relevant `V-##` cases to the phase's Done checklist.
- Finding a new silent-failure mode means adding a `V-##` case, not just fixing it. The next such bug is usually in the same family.
- Finishing a phase means setting status to `done` and updating the table in `roadmap.md` plus the **Status** line in `CLAUDE.md`.
