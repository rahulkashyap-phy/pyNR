# Templates and maintenance rules

## Adding a plan (rkdev only)

1. When a plan is approved, copy it **unchanged** to `docs/roadmap/plans/<name>.md` in the same commit as its first
   code. `docs/roadmap/plans/` is listed in `.rkdev-only`, so plans never reach `main`.
2. Add a row to the plans table in [Roadmap](index.md) (name, date, owner, status, roadmap item). Track the status
   there, not in the plan file: proposed → approved → in progress → done.
3. Plans marked *in progress* for more than 60 days without a related commit make `arch/check_drift.py` warn.

## Adding a decision

Append a row to the [decision log](decisions.md):

```text
| D-0NN | YYYY-MM-DD | <the decision, one sentence> | Rahul / Claude → Rahul / Claude (impl.) | <why; alternatives considered> | <files, pages, tests affected> |
```

Never delete a row. If a decision is reversed, add a new one and write "superseded by D-0MM" into the old row.

## Adding or closing a suggestion

Append to [open suggestions](suggestions.md):

```text
| S-0NN | YYYY-MM-DD | <suggestion> | <why> | open |
```

When it is decided, change the status to `accepted → D-0NN` or `declined (<reason>)`, and add the decision row.

## Branches

Development happens on `rkdev`. `main` is updated only by promotion from `rkdev`. On the `rkdev` branch, the details
are in the "rkdev: personal workflow" section of these docs.
