#!/usr/bin/env python3
"""
trigger_composer_dag.py

Triggers a Cloud Composer 3 DAG via the Airflow REST API,
polls for completion, and prints a full status summary.

Auth: CLOUD_SDK_TOKEN environment variable (Bearer token)
"""

import os
import time
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

import requests

# ---------------------------------------------------------------------------
# Load config from .env
# ---------------------------------------------------------------------------
load_dotenv()

def get_env_value(key: str, default: str = None, required: bool = False) -> str:
    val = os.environ.get(key, default)
    if required and not val:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return val

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
COMPOSER_WEB_SERVER_URL = get_env_value("COMPOSER_WEB_SERVER_URL", required=True)
COMPOSER_REGION         = get_env_value("COMPOSER_REGION", required=True)
DAG_ID                  = get_env_value("DAG_ID", required=True)
CLOUD_SDK_TOKEN         = get_env_value("CLOUD_SDK_TOKEN", required=True)
DAG_RUN_ID              = get_env_value("DAG_RUN_ID", f"triggered__{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}")
CONF_JSON               = get_env_value("DAG_CONF", "{}")
POLL_INTERVAL_SEC       = int(get_env_value("POLL_INTERVAL_SEC", "15"))
TIMEOUT_SEC             = int(get_env_value("TIMEOUT_SEC", "3600"))

TERMINAL_STATES = {"success", "failed", "upstream_failed", "skipped"}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------
def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Authorization":   f"Bearer {CLOUD_SDK_TOKEN}",
        "Content-Type":    "application/json",
        "X-Composer-Region": COMPOSER_REGION,        # passed on every request
    })
    return session


# ---------------------------------------------------------------------------
# Airflow REST API helpers
# ---------------------------------------------------------------------------
def api_url(path: str) -> str:
    base = COMPOSER_WEB_SERVER_URL.rstrip("/")
    return f"{base}/api/v1/{path.lstrip('/')}"


def trigger_dag(session: requests.Session, dag_id: str, run_id: str, conf: dict) -> dict:
    url = api_url(f"dags/{dag_id}/dagRuns")
    payload = {
        "dag_run_id": run_id,
        "conf": conf,
    }
    log.info("Triggering DAG '%s' | run_id='%s' | region='%s'", dag_id, run_id, COMPOSER_REGION)

    resp = session.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    log.info("DAG run created. State: %s", data.get("state"))
    return data


def get_dag_run(session: requests.Session, dag_id: str, run_id: str) -> dict:
    url = api_url(f"dags/{dag_id}/dagRuns/{run_id}")
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_task_instances(session: requests.Session, dag_id: str, run_id: str) -> list:
    url = api_url(f"dags/{dag_id}/dagRuns/{run_id}/taskInstances")
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json().get("task_instances", [])


# ---------------------------------------------------------------------------
# Polling loop
# ---------------------------------------------------------------------------
def wait_for_dag_completion(
    session: requests.Session,
    dag_id: str,
    run_id: str,
    poll_interval: int,
    timeout: int,
) -> dict:
    start = time.monotonic()
    attempt = 0

    while True:
        elapsed = time.monotonic() - start
        if elapsed > timeout:
            raise TimeoutError(
                f"DAG run '{run_id}' did not complete within {timeout}s."
            )

        attempt += 1
        dag_run = get_dag_run(session, dag_id, run_id)
        state = dag_run.get("state", "unknown").lower()

        log.info(
            "[Poll #%d | %.0fs elapsed] DAG run state: %s",
            attempt, elapsed, state.upper()
        )

        if state in TERMINAL_STATES:
            return dag_run

        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------
def print_summary(dag_run: dict, task_instances: list) -> None:
    sep = "=" * 70
    print(f"\n{sep}")
    print("  DAG RUN SUMMARY")
    print(sep)
    print(f"  DAG ID          : {dag_run.get('dag_id')}")
    print(f"  Run ID          : {dag_run.get('dag_run_id')}")
    print(f"  Region          : {COMPOSER_REGION}")
    print(f"  Final State     : {dag_run.get('state', '').upper()}")
    print(f"  Logical Date    : {dag_run.get('logical_date') or dag_run.get('execution_date')}")
    print(f"  Start Time      : {dag_run.get('start_date')}")
    print(f"  End Time        : {dag_run.get('end_date')}")
    print(f"  External Trigger: {dag_run.get('external_trigger')}")

    if dag_run.get("conf"):
        print(f"  Conf            : {json.dumps(dag_run['conf'])}")

    print(f"\n  {'TASK':<40} {'STATE':<20} {'DURATION':>10}")
    print(f"  {'-'*40} {'-'*20} {'-'*10}")

    state_counts: dict[str, int] = {}
    for ti in sorted(task_instances, key=lambda t: t.get("task_id", "")):
        task_id  = ti.get("task_id", "N/A")
        state    = (ti.get("state") or "none").upper()
        duration = ti.get("duration")
        dur_str  = f"{duration:.1f}s" if duration is not None else "N/A"
        print(f"  {task_id:<40} {state:<20} {dur_str:>10}")
        state_counts[state] = state_counts.get(state, 0) + 1

    print(f"\n  Task State Counts: {state_counts}")
    print(sep)

    overall = dag_run.get("state", "").upper()
    if overall == "SUCCESS":
        print("  ✅  DAG completed SUCCESSFULLY")
    else:
        print(f"  ❌  DAG completed with state: {overall}")
    print(f"{sep}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    try:
        dag_conf = json.loads(CONF_JSON)
    except json.JSONDecodeError as e:
        raise ValueError(f"DAG_CONF is not valid JSON: {e}")

    session = build_session()

    # 1. Trigger
    trigger_dag(session, DAG_ID, DAG_RUN_ID, dag_conf)

    # 2. Poll
    log.info("Polling every %ds (timeout: %ds) ...", POLL_INTERVAL_SEC, TIMEOUT_SEC)
    dag_run = wait_for_dag_completion(
        session, DAG_ID, DAG_RUN_ID, POLL_INTERVAL_SEC, TIMEOUT_SEC
    )

    # 3. Fetch task instances
    task_instances = get_task_instances(session, DAG_ID, DAG_RUN_ID)

    # 4. Print summary
    print_summary(dag_run, task_instances)

    # Exit code 1 on failure — Harness step fails automatically
    if dag_run.get("state", "").lower() != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
