# Conventions — Observability

> **Evidence:** INFERRED from `origin/Public`. No observability code on `main`.

## Logging (INFERRED, weak)
- Python scripts: `print()` only. No `logging` module, no structured fields, no levels.
- Bash scripts: `echo` to stdout/stderr.
- StatsCollector: `vmstat 10 | logger -t VEMS` — routes to syslog with tag `VEMS`.

## Metrics (UNKNOWN)
- No metrics framework (no Prometheus, statsd, etc.). The `VEMS` syslog stream
  and `VMStatsDisplay/` dashboards are the closest analog. **unknown**.

## Tracing (UNKNOWN)
- No tracing. **unknown**.

## Health checks (UNKNOWN)
- No health-check endpoints or scripts. The systemd service uses
  `Restart=always`/`RestartSec=10` as a liveness substitute. **unknown**.

## Prohibited logging patterns
None documented. **unknown**.
