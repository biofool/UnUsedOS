"""CloudManagement intent/actual reporting helper for UnusedOS VM tests (issue #73).

Wraps the cloud_management_client to declare intent before VM creation
and report actuals after teardown. All calls are best-effort: if the
CloudManagement hub is unreachable or the client is not configured
(missing env vars), the VM test proceeds normally — chaos/CI testing
should never block on the monitoring hub.

Environment variables (all optional — client is a no-op without them):
  CLOUDMANAGEMENT_URL          — hub URL (default http://127.0.0.1:8080)
  CLOUDMANAGEMENT_PROJECT_ID   — registered project ID (e.g. security-unusedos)
  CLOUDMANAGEMENT_REPORT_TOKEN — per-project auth token
  CLOUDMANAGEMENT_GATE_TOKEN   — Cloudflare Worker gate token (if applicable)

Usage from shell scripts:
  # Declare intent before VM creation
  python3 -m unusedos.cloudmgmt_report declare \\
    --job-id "unusedos-vm-$(date +%s)" \\
    --expected-hours 1 \\
    --expected-cost-usd 0.05

  # Report actuals after teardown
  python3 -m unusedos.cloudmgmt_report actual \\
    --intent-id "$INTENT_ID" \\
    --actual-hours 0.8 \\
    --actual-cost-usd 0.04 \\
    --status completed
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any

# Best-effort import — cloud_management_client may not be installed.
try:
    from cloud_management_client import CloudManagementClient
    _HAS_CLIENT = True
except ImportError:
    _HAS_CLIENT = False


def _get_client() -> Any | None:
    """Return a CloudManagementClient if configured, else None."""
    if not _HAS_CLIENT:
        print("SKIP: cloud_management_client not installed", file=sys.stderr)
        return None
    client = CloudManagementClient(
        project_id=os.environ.get("CLOUDMANAGEMENT_PROJECT_ID", ""),
        report_token=os.environ.get("CLOUDMANAGEMENT_REPORT_TOKEN", ""),
        base_url=os.environ.get("CLOUDMANAGEMENT_URL", "http://127.0.0.1:8080"),
        gate_token=os.environ.get("CLOUDMANAGEMENT_GATE_TOKEN", ""),
        source_repo="vigilent/Security",
        application="UnusedOS",
    )
    if not client.enabled:
        print("SKIP: CloudManagement client not configured (set CLOUDMANAGEMENT_PROJECT_ID and CLOUDMANAGEMENT_REPORT_TOKEN)", file=sys.stderr)
        return None
    return client


def cmd_declare(args: argparse.Namespace) -> int:
    """Declare intent before VM creation."""
    client = _get_client()
    if client is None:
        # Print a placeholder intent_id so the caller script can continue
        print("none")
        return 0

    job_id = args.job_id or f"unusedos-vm-{int(time.time())}"
    resp = client.declare_intent(
        job_id=job_id,
        provider="gcp_compute",
        api="compute.instance_hours",
        expected_calls=round(args.expected_hours * 60),  # minutes as "calls"
        expected_cost_usd=args.expected_cost_usd,
        job_name="UnusedOS VM build/deploy test",
        kill={
            "type": "http_callback",
            "url": os.environ.get("UNUSEDOS_KILL_URL", ""),
            "method": "POST",
        } if os.environ.get("UNUSEDOS_KILL_URL") else {},
    )
    if not resp.approved:
        print(f"WARN: intent not approved: {resp.reason}", file=sys.stderr)
        print("none")
        return 0
    print(resp.intent_id)
    return 0


def cmd_actual(args: argparse.Namespace) -> int:
    """Report actuals after VM teardown."""
    if args.intent_id == "none" or not args.intent_id:
        print("SKIP: no intent to report actuals for (intent was not declared)", file=sys.stderr)
        return 0

    client = _get_client()
    if client is None:
        return 0

    client.report_actual(
        intent_id=args.intent_id,
        provider="gcp_compute",
        api="compute.instance_hours",
        actual_calls=round(args.actual_hours * 60),  # minutes as "calls"
        actual_cost_usd=args.actual_cost_usd,
        status=args.status,
        sync=True,
    )
    client.flush(timeout=3.0)
    client.close()
    print(f"OK: reported actuals for {args.intent_id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CloudManagement intent/actual reporting for UnusedOS VM tests")
    sub = parser.add_subparsers(dest="command", required=True)

    p_declare = sub.add_parser("declare", help="Declare intent before VM creation")
    p_declare.add_argument("--job-id", default="", help="Job ID (default: auto-generated)")
    p_declare.add_argument("--expected-hours", type=float, default=1.0, help="Expected VM-hours")
    p_declare.add_argument("--expected-cost-usd", type=float, default=0.05, help="Expected cost in USD")

    p_actual = sub.add_parser("actual", help="Report actuals after VM teardown")
    p_actual.add_argument("--intent-id", required=True, help="Intent ID from declare")
    p_actual.add_argument("--actual-hours", type=float, required=True, help="Actual VM-hours run")
    p_actual.add_argument("--actual-cost-usd", type=float, required=True, help="Actual cost in USD")
    p_actual.add_argument("--status", default="completed", help="Status: completed|failed")

    args = parser.parse_args()
    if args.command == "declare":
        return cmd_declare(args)
    elif args.command == "actual":
        return cmd_actual(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
