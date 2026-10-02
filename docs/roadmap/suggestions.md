(sec-suggestions)=
# Open suggestions

Suggestions made by Claude during development that have not been decided yet. When Rahul accepts or declines one,
it moves to the [decision log](decisions.md) with the decider and the reason, and its row here is marked.

```{table} Open suggestions.
:name: tab-suggestions

| id | date | suggestion | why | status |
|---|---|---|---|---|
| S-001 | 2026-09-26 | Row-vectorise the ADM kernel along `k` | LLVM cannot keep per-point scratch arrays in registers; 3–5× expected | open (roadmap item 2) |
| S-002 | 2026-09-26 | BSSN/Z4c + moving punctures as the next physics milestone, with problems 4 and 6 as acceptance tests | every current physics limitation traces to ADM or the puncture | open (roadmap item 3) |
| S-003 | 2026-10-02 | Re-enable force-push protection for GitLab `main`; delete the local `backup/*` branches | they were only needed for the history rewrites | open |
| S-004 | 2026-10-02 | Connect Zenodo; put the concept DOI and an ORCID into `CITATION.cff`, `NOTICE`, README | citable releases | open (needs public repo) |
| S-005 | 2026-10-02 | Rehearse a TestPyPI release before `pynr 0.1.0` | catch packaging problems on a throw-away index | open |
| S-006 | 2026-10-02 | conda-forge recipe after the first PyPI release | conda users, clusters | open |
| S-007 | 2026-10-02 | pre-commit hook running `arch/check_drift.py` and `ruff` | catch drift before CI | open |
| S-008 | 2026-10-02 | Branch protection on GitHub `main` (only promotion commits) | enforce the promotion flow | open |
| S-009 | 2026-10-02 | TikZ export of the architecture graphs for LaTeX-only notes | only needed if notes leave Sphinx | open (deferred) |
```
