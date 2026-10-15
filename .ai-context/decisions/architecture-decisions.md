# Architecture Decisions

> No ADR directory exists. Decisions below are **DECLARED** in README/
> TechnicalMarketingReadMe or **INFERRED** from comments/scripts on
> `origin/Public`. None are **OBSERVED** as formal ADRs.

## DECLARED decisions

- **D-001 — Access-time-based detection.** Use filesystem `atime` to determine
  actual file usage rather than package metadata alone. (DECLARED,
  TechnicalMarketingReadMe "Technical Differentiators".)
- **D-002 — pandas for data processing.** Merge package↔file data on `path`,
  group by package, rank by oldest access time. (DECLARED, origin/Public README.)
- **D-003 — Mixed tooling.** Bash for collection, Python for analysis, Jupyter
  for exploration. (DECLARED, TechnicalMarketingReadMe.)
- **D-004 — Security patch pipeline.** Produce installable patches via
  `unattended-upgrades`, not just reports. (DECLARED.)
- **D-005 — Alternatives rejected.** SELinux, auditd, eBPF, AppArmor rejected
  for real-time performance impact and engineering cost. (DECLARED, origin/Public README.)

## INFERRED decisions

- **D-006 — No CI.** Analysis is manual/notebook-driven. (DECLARED limitation.)
- **D-007 — Patch scripts are Alpha / dev-only.** `CreateSecurityPatch/README.md`
  states "Version 0.5 Alpha" and "does not need to get deployed to production".
  (DECLARED on origin/Public.)

## UNKNOWN

- No formal ADR process exists. Whether the main-vs-Public split is intentional
  is UNKNOWN (see conflicts.yaml CONFLICT-001).
