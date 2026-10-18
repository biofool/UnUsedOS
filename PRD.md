# Sub-project branch policy — PRD

## Rule

**Every branch of `vigilent/Security` named after a sub-project folder**
tracks the canonical `VigilentSupport+SecurityAI` branch for **everything
outside that folder**. Branch-specific content lives only inside the
branch's own folder (`UnusedOS` → `UnusedOS/`, `InternalCA` → `InternalCA/`,
`SOAR` → `SOAR/`, `VigilentSupport+SecurityAI` → `VigilentSupport_Security_AI/`,
and any future `<Folder>` branch). This document uses `UnusedOS` as the
worked example; the same procedure applies to every sub-project branch.

Concretely, on this branch:

- Every path outside `UnusedOS/` is byte-identical to
  `origin/VigilentSupport+SecurityAI`.
- `UnusedOS/` contains this sub-project's own files and may diverge freely.
- Any commit that touches a path outside `UnusedOS/` is a policy violation —
  those changes belong on `VigilentSupport+SecurityAI` instead.

This document lives inside `UnusedOS/` so it complies with its own rule.

## Rationale

`vigilent/Security` is a monorepo of independent sub-projects. The
`VigilentSupport+SecurityAI` branch carries the canonical, maintained state
of the repo (including the live Support + Security Questionnaire app). The
`UnusedOS` branch exists only to develop the UnusedOS sub-project; letting
the rest of its tree drift leaves it carrying stale snapshots — e.g. it was
still running pre-#700 fail-open rate-limiter code while claiming the
fail-closed fix in docstrings.

## Sync procedure (overwrite, not merge)

Do not merge `VigilentSupport+SecurityAI` into `UnusedOS` — overwrite:

```bash
git fetch origin
git read-tree --reset -u origin/VigilentSupport+SecurityAI
git restore --source=HEAD --staged --worktree -- UnusedOS/
# stage any in-scope UnusedOS/ edits, then:
git commit -m "Sync monorepo to VigilentSupport+SecurityAI outside UnusedOS/"
git push origin UnusedOS
```

Verify afterwards that the residual diff vs canonical touches only
`UnusedOS/`:

```bash
git diff origin/VigilentSupport+SecurityAI HEAD --stat -- . ':(exclude)UnusedOS'
# expected: empty
```

## History

- 2026-10-06 — policy established for `UnusedOS`; branch synced to
  `origin/VigilentSupport+SecurityAI` outside `UnusedOS/` (177 files).
  Local-only ignores for `insights/` and `SecOnion/` added to
  `.git/info/exclude` (they were covered by the old branch `.gitignore`;
  they are not committed).
- 2026-10-06 — generalized repo-wide: the policy now applies to **every**
  sub-project branch, recorded in root `AGENTS.md` ("Sub-project branch
  policy") and in AI global memory
  (`~/.codeium/windsurf/memories/global_rules.md`).
