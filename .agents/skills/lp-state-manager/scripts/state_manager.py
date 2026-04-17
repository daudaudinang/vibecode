#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH_RELATIVE = Path('.codex/state/pipeline_state.db')
VALID_MODES = {'spec', 'plan', 'implement', 'cook', 'debug'}
STATE_MANAGER_EXAMPLES = {
    'upsert-step': "python ~/.agents/skills/lp-state-manager/scripts/state_manager.py --db-path \".codex/state/pipeline_state.db\" upsert-step --workflow-id \"WF_20260409_000001\" --step \"review-implement\" --order 4 --status FAIL --output \".codex/pipeline/PLAN_MERCHANT_BULK_IMPORT/04-review-implement.output.md\"",
    'resolve-next': "python ~/.agents/skills/lp-state-manager/scripts/state_manager.py resolve-next --workflow-id \"WF_20260409_000001\"",
}
VALID_WORKFLOW_STATUSES = {'ACTIVE', 'WAITING_USER', 'COMPLETED', 'FAILED', 'BLOCKED'}
VALID_STEP_STATUSES = {'PENDING', 'RUNNING', 'PASS', 'FAIL', 'NEEDS_REVISION', 'WAITING_USER', 'SKIPPED'}
PHASE_BY_STEP = {
    'jira-workflow-bridge': 'intake',
    'debug-investigator': 'debug',
    'create-spec': 'spec',
    'review-spec': 'spec_review',
    'create-plan': 'plan',
    'review-plan': 'plan_review',
    'implement-plan': 'implement',
    'review-implement': 'code_review',
    'qa-automation': 'qa',
    'close-task': 'close',
}
DEFAULT_STEPS_BY_MODE = {
    'spec': ['create-spec', 'review-spec'],
    'plan': ['create-plan', 'review-plan'],
    'implement': ['implement-plan'],
    'cook': ['create-spec', 'review-spec', 'create-plan', 'review-plan', 'implement-plan'],
    'debug': ['debug-investigator'],
}
DEFAULT_GATES = {
    'requirement_clarified': False,
    'spec_created': False,
    'spec_reviewed': False,
    'spec_approved': False,
    'plan_created': False,
    'plan_reviewed': False,
    'plan_approved': False,
    'user_approved_implementation': False,
    'implementation_done': False,
    'implementation_review_passed': False,
    'qa_passed': False,
    'user_approved_close': False,
}
SCHEMA_VERSION = 2
V2_ALLOWED_ARTIFACT_PREFIXES = ('.codex/plans/', '.codex/pipeline/', '.codex/state/')
V2_ALLOWED_PLAN_PREFIX = '.codex/plans/'
V2_ALLOWED_RUN_PREFIX = 'RUN_'
V2_ALLOWED_JOB_PREFIX = 'JOB_'
V2_PLAN_STATUSES = {'DRAFT', 'ACTIVE', 'WAITING_USER', 'COMPLETED', 'FAILED', 'BLOCKED'}
V2_PRIMARY_RUN_STATUSES = {'ACTIVE', 'WAITING_USER', 'COMPLETED', 'FAILED', 'BLOCKED', 'SUPERSEDED'}
V2_CHILD_JOB_STATUSES = {'PENDING', 'RUNNING', 'PASS', 'FAIL', 'NEEDS_REVISION', 'WAITING_USER', 'SKIPPED'}
V2_AGGREGATE_TYPES = {'plan', 'primary_run', 'child_job'}
V2_DEFAULT_PLAN_STATUS = 'DRAFT'
V2_DEFAULT_PRIMARY_RUN_STATUS = 'ACTIVE'
V2_DEFAULT_CHILD_JOB_STATUS = 'PENDING'
V2_DEFAULT_LEASE_TTL_SECONDS = 900
V2_DEFAULT_ATTEMPT_NO = 1
V2_DEFAULT_LEASE_REVISION = 1
V2_SCHEMA_NOTES = {
    'artifact_root_pattern': '.codex/pipeline/<PLAN_NAME>/',
    'child_job_root_pattern': '.codex/pipeline/<PLAN_NAME>/RUN_<ID>/child-jobs/JOB_<ID>/',
}


def normalize_relative_artifact_path(path: str) -> str:
    candidate = path.strip()
    if not candidate:
        raise V2StateValidationError('Artifact path must not be empty')
    pure = Path(candidate)
    if pure.is_absolute():
        raise V2StateValidationError(f'Artifact path must be repo-relative: {path}')
    normalized = pure.as_posix()
    if normalized.startswith('../') or '/..' in normalized or normalized == '..':
        raise V2StateValidationError(f'Artifact path must not escape repo root: {path}')
    if not normalized.startswith(V2_ALLOWED_ARTIFACT_PREFIXES):
        raise V2StateValidationError(
            f'Artifact path must stay under one of {V2_ALLOWED_ARTIFACT_PREFIXES}: {path}'
        )
    return normalized


def normalize_plan_path(path: str) -> str:
    normalized = normalize_relative_artifact_path(path)
    if not normalized.startswith(V2_ALLOWED_PLAN_PREFIX):
        raise V2StateValidationError(f'Plan path must stay under {V2_ALLOWED_PLAN_PREFIX}: {path}')
    return normalized


def infer_v2_artifact_identity(path: str) -> dict[str, str | None]:
    normalized = normalize_relative_artifact_path(path)
    parts = Path(normalized).parts
    plan_name = None
    run_id = None
    job_id = None
    for index, part in enumerate(parts):
        if part == 'pipeline' and index + 1 < len(parts):
            plan_name = parts[index + 1]
        if part == 'plans' and index + 1 < len(parts):
            plan_name = parts[index + 1]
        if part.startswith(V2_ALLOWED_RUN_PREFIX):
            run_id = part
        if part.startswith(V2_ALLOWED_JOB_PREFIX):
            job_id = part
    return {
        'normalized_path': normalized,
        'plan_name': plan_name,
        'run_id': run_id,
        'job_id': job_id,
    }


def validate_v2_table_enums() -> dict[str, list[str]]:
    return {
        'plan_statuses': sorted(V2_PLAN_STATUSES),
        'primary_run_statuses': sorted(V2_PRIMARY_RUN_STATUSES),
        'child_job_statuses': sorted(V2_CHILD_JOB_STATUSES),
        'aggregate_types': sorted(V2_AGGREGATE_TYPES),
    }


def default_v2_schema_metadata() -> dict[str, Any]:
    return {
        'notes': V2_SCHEMA_NOTES,
        'enums': validate_v2_table_enums(),
        'lease_ttl_seconds': V2_DEFAULT_LEASE_TTL_SECONDS,
        'default_attempt_no': V2_DEFAULT_ATTEMPT_NO,
        'default_lease_revision': V2_DEFAULT_LEASE_REVISION,
    }


class StateManagerError(RuntimeError):
    pass


class V2StateValidationError(StateManagerError):
    pass


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec='seconds')


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {'1', 'true', 'yes', 'y', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'n', 'off'}:
        return False
    raise StateManagerError(f'Invalid boolean value: {value}')


def coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def validate_mode(mode: str) -> str:
    if mode not in VALID_MODES:
        raise StateManagerError(f'Invalid mode: {mode}. Expected one of {sorted(VALID_MODES)}')
    return mode


def validate_workflow_status(status: str) -> str:
    if status not in VALID_WORKFLOW_STATUSES:
        raise StateManagerError(
            f'Invalid workflow status: {status}. Expected one of {sorted(VALID_WORKFLOW_STATUSES)}'
        )
    return status


def validate_step_status(status: str) -> str:
    if status not in VALID_STEP_STATUSES:
        raise StateManagerError(f'Invalid step status: {status}. Expected one of {sorted(VALID_STEP_STATUSES)}')
    return status


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def detect_git_repo_root(cwd: Path | None = None) -> Path | None:
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else None,
        )
        root = result.stdout.strip()
        if root:
            return Path(root).resolve()
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # Fallback to manual traversal looking for markers
    current = Path(cwd).resolve() if cwd else Path.cwd().resolve()
    for parent in [current] + list(current.parents):
        if parent == Path.home():
            break  # Stop at home dir to avoid confusing ~/.codex global config with project root
        if (parent / '.codex').is_dir() or (parent / 'config.toml').is_file() or (parent / '.git').is_dir():
            return parent

    return None


def resolve_repo_root(repo_root_arg: str | None = None, cwd: Path | None = None) -> Path:
    if repo_root_arg:
        return Path(repo_root_arg).expanduser().resolve()

    detected = detect_git_repo_root(cwd)
    if detected is not None:
        return detected

    raise StateManagerError('Cannot infer repo root. Pass --repo-root explicitly or run the command inside a git repository.')


def resolve_db_path(db_path_arg: str | None = None, repo_root_arg: str | None = None, cwd: Path | None = None) -> Path:
    if db_path_arg:
        return Path(db_path_arg).expanduser().resolve()

    repo_root = resolve_repo_root(repo_root_arg=repo_root_arg, cwd=cwd)
    return (repo_root / DEFAULT_DB_PATH_RELATIVE).resolve()


def normalize_step_list(raw_steps: str | None, mode: str) -> list[str]:
    if not raw_steps:
        return DEFAULT_STEPS_BY_MODE[mode][:]
    steps = [step.strip() for step in raw_steps.split(',') if step.strip()]
    if not steps:
        raise StateManagerError('Step list is empty')
    return steps


def generate_workflow_id(conn: sqlite3.Connection) -> str:
    date_prefix = datetime.now().strftime('WF_%Y%m%d')
    for _ in range(5):
        candidate = f"{date_prefix}_{uuid.uuid4().hex[:8].upper()}"
        exists = conn.execute(
            'SELECT 1 FROM workflows WHERE workflow_id = ?',
            (candidate,),
        ).fetchone()
        if not exists:
            return candidate
    raise StateManagerError('Unable to generate unique workflow_id after 5 attempts')


def phase_for_step(step: str | None) -> str | None:
    if not step:
        return None
    return PHASE_BY_STEP.get(step, 'custom')


def infer_workflow_status_from_step(step_status: str) -> str | None:
    if step_status == 'WAITING_USER':
        return 'WAITING_USER'
    if step_status == 'FAIL':
        return 'FAILED'
    if step_status == 'RUNNING':
        return 'ACTIVE'
    return None


def terminal_step_status(status: str) -> bool:
    return status in {'PASS', 'FAIL', 'NEEDS_REVISION', 'WAITING_USER', 'SKIPPED'}


def workflow_status_for_business_state(snapshot: dict[str, Any]) -> str:
    mode = snapshot['mode']
    gates = snapshot['gates']
    steps = snapshot['steps']
    current_status = snapshot['status']

    if current_status in {'FAILED', 'BLOCKED'}:
        return current_status
    if any(step['status'] == 'RUNNING' for step in steps):
        return 'ACTIVE'
    if any(step['status'] == 'WAITING_USER' for step in steps):
        return 'WAITING_USER'
    if any(step['status'] in {'FAIL', 'NEEDS_REVISION'} for step in steps):
        return 'ACTIVE'

    if mode == 'debug':
        debug_step = next((step for step in steps if step['skill'] == 'debug-investigator'), None)
        if debug_step and debug_step['status'] == 'PASS':
            return 'COMPLETED'
        return 'ACTIVE'

    if mode == 'spec':
        if gates.get('spec_approved'):
            return 'WAITING_USER'
        return 'ACTIVE'

    if mode == 'plan' and gates.get('plan_approved') and not gates.get('user_approved_implementation'):
        return 'WAITING_USER'
    if gates.get('user_approved_implementation') and not gates.get('qa_passed'):
        return 'ACTIVE'
    if mode in {'implement', 'cook'} and gates.get('qa_passed'):
        return 'COMPLETED'
    if mode == 'plan' and steps and all(step['status'] in {'PASS', 'SKIPPED'} for step in steps):
        return 'COMPLETED'
    if steps and all(step['status'] in {'PASS', 'SKIPPED'} for step in steps):
        return 'COMPLETED'
    return 'ACTIVE'


@contextmanager
def connect(db_path: Path) -> sqlite3.Connection:
    ensure_parent_dir(db_path)
    retries = 3
    for attempt in range(retries):
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            break
        except sqlite3.OperationalError as exc:
            if 'locked' not in str(exc).lower() or attempt == retries - 1:
                raise
            time.sleep(0.2 * (attempt + 1))
    else:
        raise StateManagerError(f'Unable to connect to SQLite DB: {db_path}')

    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    conn.execute('PRAGMA synchronous = NORMAL')
    conn.execute('PRAGMA busy_timeout = 5000')
    try:
        current_version = conn.execute('PRAGMA user_version').fetchone()[0]
        if current_version < SCHEMA_VERSION:
            ensure_schema(conn)
            conn.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        '''
        CREATE TABLE IF NOT EXISTS workflows (
          workflow_id TEXT PRIMARY KEY,
          plan_name TEXT NOT NULL,
          mode TEXT NOT NULL,
          ticket TEXT,
          requirement TEXT,
          status TEXT NOT NULL,
          current_phase TEXT,
          current_step TEXT,
          started_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          schema_version INTEGER NOT NULL DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_workflows_plan_name ON workflows(plan_name);
        CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
        CREATE INDEX IF NOT EXISTS idx_workflows_mode ON workflows(mode);

        CREATE TABLE IF NOT EXISTS workflow_steps (
          workflow_id TEXT NOT NULL,
          step_order INTEGER NOT NULL,
          skill TEXT NOT NULL,
          status TEXT NOT NULL,
          output TEXT,
          started_at TEXT,
          completed_at TEXT,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          PRIMARY KEY (workflow_id, skill),
          FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_workflow_steps_order ON workflow_steps(workflow_id, step_order);

        CREATE TABLE IF NOT EXISTS workflow_gates (
          workflow_id TEXT NOT NULL,
          gate_name TEXT NOT NULL,
          gate_value INTEGER NOT NULL,
          updated_at TEXT NOT NULL,
          PRIMARY KEY (workflow_id, gate_name),
          FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS workflow_artifacts (
          workflow_id TEXT NOT NULL,
          artifact_key TEXT NOT NULL,
          artifact_path TEXT NOT NULL,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          updated_at TEXT NOT NULL,
          PRIMARY KEY (workflow_id, artifact_key),
          FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS workflow_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          workflow_id TEXT NOT NULL,
          ts TEXT NOT NULL,
          actor TEXT NOT NULL,
          event_type TEXT NOT NULL,
          payload_json TEXT NOT NULL DEFAULT '{}',
          FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_workflow_events_workflow_id ON workflow_events(workflow_id, id);

        CREATE TABLE IF NOT EXISTS v2_plans (
          plan_id TEXT PRIMARY KEY,
          plan_name TEXT NOT NULL UNIQUE,
          plan_path TEXT NOT NULL,
          status TEXT NOT NULL,
          current_primary_run_id TEXT,
          plan_version INTEGER NOT NULL DEFAULT 1,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_v2_plans_status ON v2_plans(status);

        CREATE TABLE IF NOT EXISTS v2_primary_runs (
          run_id TEXT PRIMARY KEY,
          plan_id TEXT NOT NULL,
          workflow_id TEXT NOT NULL UNIQUE,
          mode TEXT NOT NULL,
          status TEXT NOT NULL,
          owner_session_id TEXT NOT NULL,
          lease_revision INTEGER NOT NULL DEFAULT 1,
          lease_expires_at TEXT,
          last_heartbeat_at TEXT,
          supersedes_run_id TEXT,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          updated_at TEXT NOT NULL,
          FOREIGN KEY (plan_id) REFERENCES v2_plans(plan_id) ON DELETE CASCADE,
          FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE,
          FOREIGN KEY (supersedes_run_id) REFERENCES v2_primary_runs(run_id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_v2_primary_runs_plan_id ON v2_primary_runs(plan_id, updated_at);
        CREATE INDEX IF NOT EXISTS idx_v2_primary_runs_status ON v2_primary_runs(status);

        CREATE TABLE IF NOT EXISTS v2_child_jobs (
          job_id TEXT PRIMARY KEY,
          run_id TEXT NOT NULL,
          phase_id TEXT,
          workflow_id TEXT NOT NULL,
          status TEXT NOT NULL,
          attempt_no INTEGER NOT NULL DEFAULT 1,
          artifact_path TEXT,
          artifact_hash TEXT,
          idempotency_key TEXT NOT NULL,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          updated_at TEXT NOT NULL,
          FOREIGN KEY (run_id) REFERENCES v2_primary_runs(run_id) ON DELETE CASCADE,
          FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_v2_child_jobs_idempotency_key ON v2_child_jobs(idempotency_key);
        CREATE INDEX IF NOT EXISTS idx_v2_child_jobs_run_id ON v2_child_jobs(run_id, updated_at);

        CREATE TABLE IF NOT EXISTS v2_run_events (
          event_id INTEGER PRIMARY KEY AUTOINCREMENT,
          aggregate_type TEXT NOT NULL,
          aggregate_id TEXT NOT NULL,
          workflow_id TEXT NOT NULL,
          event_type TEXT NOT NULL,
          payload_json TEXT NOT NULL DEFAULT '{}',
          ts TEXT NOT NULL,
          FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_v2_run_events_aggregate ON v2_run_events(aggregate_type, aggregate_id, event_id);
        '''
    )
    conn.execute(
        '''
        UPDATE workflows
        SET schema_version = ?
        WHERE schema_version <> ?
        ''',
        (SCHEMA_VERSION, SCHEMA_VERSION),
    )
    conn.execute(
        '''
        UPDATE workflows
        SET metadata_json = json_patch(COALESCE(metadata_json, '{}'), ?)
        WHERE schema_version = ?
        ''',
        (json_dumps(default_v2_schema_metadata()), SCHEMA_VERSION),
    )
    conn.execute(
        '''
        INSERT INTO workflow_events (workflow_id, ts, actor, event_type, payload_json)
        SELECT workflow_id, ?, 'state-manager', 'schema_upgraded_to_v2', ?
        FROM workflows
        WHERE NOT EXISTS (
          SELECT 1 FROM workflow_events
          WHERE workflow_events.workflow_id = workflows.workflow_id
            AND workflow_events.event_type = 'schema_upgraded_to_v2'
        )
        ''',
        (now_iso(), json_dumps(default_v2_schema_metadata())),
    )
    conn.execute(
        '''
        INSERT OR IGNORE INTO v2_plans (
          plan_id, plan_name, plan_path, status, current_primary_run_id, plan_version, metadata_json, updated_at
        )
        SELECT
          plan_name,
          plan_name,
          CASE
            WHEN json_extract(metadata_json, '$.plan_root') IS NOT NULL
              THEN json_extract(metadata_json, '$.plan_root') || '/plan.md'
            ELSE '.codex/plans/' || plan_name || '/plan.md'
          END,
          COALESCE(json_extract(metadata_json, '$.plan_status'), 'DRAFT'),
          COALESCE(json_extract(metadata_json, '$.current_primary_run_id'), 'RUN_' || workflow_id),
          1,
          json_patch(COALESCE(metadata_json, '{}'), ?),
          updated_at
        FROM workflows
        ''',
        (json_dumps({'migrated_from_v1': True}),),
    )
    conn.execute(
        '''
        INSERT OR IGNORE INTO v2_primary_runs (
          run_id, plan_id, workflow_id, mode, status, owner_session_id,
          lease_revision, lease_expires_at, last_heartbeat_at, supersedes_run_id,
          metadata_json, updated_at
        )
        SELECT
          COALESCE(json_extract(metadata_json, '$.current_primary_run_id'), 'RUN_' || workflow_id),
          plan_name,
          workflow_id,
          mode,
          COALESCE(json_extract(metadata_json, '$.primary_run_status'), status),
          'session:' || workflow_id,
          COALESCE(json_extract(metadata_json, '$.lease_revision'), 1),
          updated_at,
          updated_at,
          NULL,
          json_patch(COALESCE(metadata_json, '{}'), ?),
          updated_at
        FROM workflows
        ''',
        (json_dumps({'migrated_from_v1': True}),),
    )
    conn.execute(
        '''
        INSERT OR IGNORE INTO v2_run_events (aggregate_type, aggregate_id, workflow_id, event_type, payload_json, ts)
        SELECT 'plan', plan_name, workflow_id, 'v1_workflow_imported', ?, started_at
        FROM workflows
        ''',
        (json_dumps({'source': 'workflows'}),),
    )
    conn.execute(
        '''
        INSERT OR IGNORE INTO v2_run_events (event_id, aggregate_type, aggregate_id, workflow_id, event_type, payload_json, ts)
        SELECT event_id, aggregate_type, aggregate_id, workflow_id, event_type, payload_json, ts
        FROM (
          SELECT
            id AS event_id,
            'primary_run' AS aggregate_type,
            COALESCE(json_extract(w.metadata_json, '$.current_primary_run_id'), 'RUN_' || w.workflow_id) AS aggregate_id,
            e.workflow_id,
            e.event_type,
            e.payload_json,
            e.ts
          FROM workflow_events e
          JOIN workflows w ON w.workflow_id = e.workflow_id
        )
        ''',
    )
    conn.execute(
        '''
        UPDATE workflow_artifacts
        SET artifact_path = CASE
          WHEN instr(artifact_path, '.codex/pipeline/') = 1 THEN artifact_path
          WHEN instr(artifact_path, '.codex/plans/') = 1 THEN artifact_path
          ELSE artifact_path
        END
        '''
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET plan_path = ?
        WHERE plan_path NOT LIKE '.codex/plans/%'
        ''',
        ('.codex/plans/UNKNOWN/plan.md',),
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET plan_path = '.codex/plans/' || plan_name || '/plan.md'
        WHERE plan_path = '.codex/plans/UNKNOWN/plan.md'
        ''',
    )
    conn.execute(
        '''
        UPDATE v2_primary_runs
        SET metadata_json = json_patch(COALESCE(metadata_json, '{}'), ?)
        ''',
        (json_dumps({'artifact_root_pattern': V2_SCHEMA_NOTES['artifact_root_pattern']}),),
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET metadata_json = json_patch(COALESCE(metadata_json, '{}'), ?)
        ''',
        (json_dumps({'child_job_root_pattern': V2_SCHEMA_NOTES['child_job_root_pattern']}),),
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET current_primary_run_id = 'RUN_' || substr(current_primary_run_id, 5)
        WHERE current_primary_run_id NOT LIKE 'RUN_%'
        '''
    )
    conn.execute(
        '''
        INSERT OR IGNORE INTO v2_child_jobs (
          job_id, run_id, phase_id, workflow_id, status, attempt_no, artifact_path, artifact_hash, idempotency_key, metadata_json, updated_at
        )
        SELECT
          'JOB_' || s.workflow_id || '_' || replace(s.skill, '-', '_'),
          COALESCE(json_extract(w.metadata_json, '$.current_primary_run_id'), 'RUN_' || w.workflow_id),
          s.skill,
          s.workflow_id,
          s.status,
          1,
          s.output,
          NULL,
          s.workflow_id || ':' || s.skill,
          s.metadata_json,
          COALESCE(s.completed_at, s.started_at, w.updated_at)
        FROM workflow_steps s
        JOIN workflows w ON w.workflow_id = s.workflow_id
        WHERE s.output IS NOT NULL
        '''
    )
    conn.execute(
        '''
        UPDATE v2_child_jobs
        SET artifact_path = REPLACE(artifact_path, '//', '/')
        WHERE artifact_path IS NOT NULL
        '''
    )
    conn.execute(
        '''
        UPDATE workflow_artifacts
        SET metadata_json = json_patch(COALESCE(metadata_json, '{}'), ?)
        ''',
        (json_dumps({'schema_version': SCHEMA_VERSION}),),
    )
    conn.execute(
        '''
        UPDATE workflows
        SET metadata_json = json_patch(COALESCE(metadata_json, '{}'), ?)
        ''',
        (json_dumps({'schema_version': SCHEMA_VERSION}),),
    )
    conn.execute(
        '''
        UPDATE v2_child_jobs
        SET metadata_json = json_patch(COALESCE(metadata_json, '{}'), ?)
        ''',
        (json_dumps({'schema_version': SCHEMA_VERSION}),),
    )
    conn.execute(
        '''
        UPDATE v2_run_events
        SET payload_json = json_patch(COALESCE(payload_json, '{}'), ?)
        WHERE event_type = 'v1_workflow_imported'
        ''',
        (json_dumps({'schema_version': SCHEMA_VERSION}),),
    )
    conn.execute(
        '''
        UPDATE workflow_steps
        SET metadata_json = json_patch(COALESCE(metadata_json, '{}'), ?)
        ''',
        (json_dumps({'schema_version': SCHEMA_VERSION}),),
    )
    conn.execute(
        '''
        UPDATE v2_primary_runs
        SET lease_expires_at = updated_at
        WHERE lease_expires_at IS NULL
        ''',
    )
    conn.execute(
        '''
        UPDATE v2_primary_runs
        SET last_heartbeat_at = updated_at
        WHERE last_heartbeat_at IS NULL
        ''',
    )
    conn.execute(
        '''
        UPDATE v2_child_jobs
        SET idempotency_key = job_id
        WHERE idempotency_key = ''
        '''
    )
    conn.execute(
        '''
        UPDATE v2_child_jobs
        SET artifact_path = NULL
        WHERE artifact_path = ''
        '''
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET status = 'ACTIVE'
        WHERE status = 'DRAFT' AND current_primary_run_id IS NOT NULL
        '''
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET status = 'WAITING_USER'
        WHERE status = 'ACTIVE' AND plan_id IN (
          SELECT plan_id FROM v2_primary_runs WHERE status = 'WAITING_USER'
        )
        '''
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET status = 'COMPLETED'
        WHERE status IN ('ACTIVE', 'WAITING_USER') AND plan_id IN (
          SELECT plan_id FROM v2_primary_runs WHERE status = 'COMPLETED'
        )
        '''
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET status = 'FAILED'
        WHERE plan_id IN (
          SELECT plan_id FROM v2_primary_runs WHERE status = 'FAILED'
        )
        '''
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET status = 'BLOCKED'
        WHERE plan_id IN (
          SELECT plan_id FROM v2_primary_runs WHERE status = 'BLOCKED'
        )
        '''
    )
    conn.execute(
        '''
        UPDATE v2_plans
        SET metadata_json = json_patch(COALESCE(metadata_json, '{}'), ?)
        ''',
        (json_dumps(default_v2_schema_metadata()),),
    )
    conn.execute(
        '''
        UPDATE v2_primary_runs
        SET metadata_json = json_patch(COALESCE(metadata_json, '{}'), ?)
        ''',
        (json_dumps(default_v2_schema_metadata()),),
    )


def ensure_workflow_exists(conn: sqlite3.Connection, workflow_id: str) -> None:
    row = conn.execute('SELECT workflow_id FROM workflows WHERE workflow_id = ?', (workflow_id,)).fetchone()
    if not row:
        raise StateManagerError(f'Workflow not found: {workflow_id}')


def ensure_no_active_workflow_for_plan(conn: sqlite3.Connection, plan_name: str, workflow_id: str | None = None) -> None:
    rows = conn.execute(
        '''
        SELECT workflow_id, status
        FROM workflows
        WHERE plan_name = ? AND status IN ('ACTIVE', 'WAITING_USER', 'BLOCKED')
        ORDER BY updated_at DESC
        ''',
        (plan_name,),
    ).fetchall()
    active_ids = [row['workflow_id'] for row in rows if row['workflow_id'] != workflow_id]
    if active_ids:
        raise StateManagerError(
            f'Active workflow already exists for plan_name={plan_name}: {active_ids[0]}. '
            'Use --workflow-id explicitly or finish the existing run before starting another in the same workspace'
        )


def append_event_record(
    conn: sqlite3.Connection,
    workflow_id: str,
    actor: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    ts: str | None = None,
) -> None:
    ensure_workflow_exists(conn, workflow_id)
    conn.execute(
        '''
        INSERT INTO workflow_events (workflow_id, ts, actor, event_type, payload_json)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (workflow_id, ts or now_iso(), actor, event_type, json_dumps(payload or {})),
    )


def set_updated_at(conn: sqlite3.Connection, workflow_id: str) -> None:
    conn.execute('UPDATE workflows SET updated_at = ? WHERE workflow_id = ?', (now_iso(), workflow_id))


def recompute_workflow_status(conn: sqlite3.Connection, workflow_id: str) -> None:
    snapshot = get_workflow_snapshot(conn, workflow_id, include_events=False)
    business_status = workflow_status_for_business_state(snapshot)
    conn.execute(
        'UPDATE workflows SET status = ?, updated_at = ? WHERE workflow_id = ?',
        (business_status, now_iso(), workflow_id),
    )


def create_workflow(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    mode = validate_mode(args.mode)
    steps = normalize_step_list(args.steps, mode)
    workflow_id = args.workflow_id or generate_workflow_id(conn)
    started_at = args.started_at or now_iso()
    status = validate_workflow_status(args.status or 'ACTIVE')
    ensure_no_active_workflow_for_plan(conn, args.plan_name, workflow_id=workflow_id)
    current_step = args.current_step or (steps[0] if steps else None)
    current_phase = args.current_phase or phase_for_step(current_step)
    metadata = default_v2_schema_metadata()
    if args.metadata_json:
        metadata.update(json_loads(args.metadata_json, {}))
    metadata.setdefault('plan_name', args.plan_name)
    metadata.setdefault('workflow_id', workflow_id)
    metadata.setdefault('artifact_root', f'.codex/pipeline/{args.plan_name}')
    metadata.setdefault('plan_root', f'.codex/plans/{args.plan_name}')
    metadata.setdefault('current_primary_run_id', f'RUN_{workflow_id}')
    metadata.setdefault('plan_status', V2_DEFAULT_PLAN_STATUS)
    metadata.setdefault('primary_run_status', V2_DEFAULT_PRIMARY_RUN_STATUS)
    metadata.setdefault('lease_revision', V2_DEFAULT_LEASE_REVISION)
    metadata.setdefault('lease_ttl_seconds', V2_DEFAULT_LEASE_TTL_SECONDS)
    metadata.setdefault('attempt_no', V2_DEFAULT_ATTEMPT_NO)
    metadata.setdefault('idempotency_key_scope', {'workflow': workflow_id, 'plan': args.plan_name})

    conn.execute(
        '''
        INSERT INTO workflows (
          workflow_id, plan_name, mode, ticket, requirement, status,
          current_phase, current_step, started_at, updated_at, metadata_json, schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            workflow_id,
            args.plan_name,
            mode,
            args.ticket,
            args.requirement,
            status,
            current_phase,
            current_step,
            started_at,
            started_at,
            json_dumps(metadata),
            SCHEMA_VERSION,
        ),
    )

    conn.execute(
        '''
        INSERT OR IGNORE INTO v2_plans (
          plan_id, plan_name, plan_path, status, current_primary_run_id, plan_version, metadata_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            args.plan_name,
            args.plan_name,
            normalize_plan_path(f'.codex/plans/{args.plan_name}/plan.md'),
            metadata['plan_status'],
            metadata['current_primary_run_id'],
            1,
            json_dumps({'workflow_id': workflow_id, 'mode': mode}),
            started_at,
        ),
    )
    conn.execute(
        '''
        INSERT OR IGNORE INTO v2_primary_runs (
          run_id, plan_id, workflow_id, mode, status, owner_session_id,
          lease_revision, lease_expires_at, last_heartbeat_at, supersedes_run_id,
          metadata_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            metadata['current_primary_run_id'],
            args.plan_name,
            workflow_id,
            mode,
            metadata['primary_run_status'],
            f'session:{workflow_id}',
            metadata['lease_revision'],
            started_at,
            started_at,
            None,
            json_dumps({'artifact_root': metadata['artifact_root']}),
            started_at,
        ),
    )

    append_event_record(
        conn,
        workflow_id=workflow_id,
        actor=args.actor,
        event_type='v2_primary_run_initialized',
        payload={
            'run_id': metadata['current_primary_run_id'],
            'artifact_root': metadata['artifact_root'],
            'lease_revision': metadata['lease_revision'],
        },
    )

    for index, step in enumerate(steps, start=1):
        conn.execute(
            '''
            INSERT INTO workflow_steps (
              workflow_id, step_order, skill, status, output, started_at, completed_at, metadata_json
            ) VALUES (?, ?, ?, 'PENDING', NULL, NULL, NULL, '{}')
            ''',
            (workflow_id, index, step),
        )

    for gate_name, gate_value in DEFAULT_GATES.items():
        conn.execute(
            '''
            INSERT INTO workflow_gates (workflow_id, gate_name, gate_value, updated_at)
            VALUES (?, ?, ?, ?)
            ''',
            (workflow_id, gate_name, int(gate_value), started_at),
        )

    append_event_record(
        conn,
        workflow_id=workflow_id,
        actor=args.actor,
        event_type='workflow_created',
        payload={
            'mode': mode,
            'plan_name': args.plan_name,
            'steps': steps,
            'ticket': args.ticket,
        },
    )
    return get_workflow_snapshot(conn, workflow_id, include_events=args.include_events)


def update_workflow(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    ensure_workflow_exists(conn, args.workflow_id)
    updates: list[str] = []
    params: list[Any] = []
    event_payload = {
        k: v
        for k, v in vars(args).items()
        if k not in {'db_path', 'command', 'actor', 'handler'} and v is not None
    }

    if getattr(args, 'mode', None) is not None:
        updates.append('mode = ?')
        params.append(validate_mode(args.mode))
    if args.status is not None:
        updates.append('status = ?')
        params.append(validate_workflow_status(args.status))
    if args.current_phase is not None:
        updates.append('current_phase = ?')
        params.append(args.current_phase)
    if args.current_step is not None:
        updates.append('current_step = ?')
        params.append(args.current_step)
        if args.current_phase is None:
            updates.append('current_phase = ?')
            params.append(phase_for_step(args.current_step))
    if args.requirement is not None:
        updates.append('requirement = ?')
        params.append(args.requirement)
    if args.ticket is not None:
        updates.append('ticket = ?')
        params.append(args.ticket)
    if args.metadata_json is not None:
        current_row = conn.execute(
            'SELECT metadata_json FROM workflows WHERE workflow_id = ?',
            (args.workflow_id,),
        ).fetchone()
        current_metadata = json_loads(current_row['metadata_json'], {}) if current_row else {}
        patch_metadata = json_loads(args.metadata_json, {})
        merged_metadata = current_metadata.copy()
        merged_metadata.update(patch_metadata)
        updates.append('metadata_json = ?')
        params.append(json_dumps(merged_metadata))
        event_payload['metadata_json'] = merged_metadata

    if not updates:
        raise StateManagerError('No updates provided')

    updates.append('updated_at = ?')
    params.append(now_iso())
    params.append(args.workflow_id)
    conn.execute(f'UPDATE workflows SET {", ".join(updates)} WHERE workflow_id = ?', params)
    append_event_record(
        conn,
        workflow_id=args.workflow_id,
        actor=args.actor,
        event_type='workflow_updated',
        payload=event_payload,
    )
    return get_workflow_snapshot(conn, args.workflow_id, include_events=args.include_events)


def upsert_step(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    ensure_workflow_exists(conn, args.workflow_id)
    status = validate_step_status(args.status)
    existing = conn.execute(
        'SELECT * FROM workflow_steps WHERE workflow_id = ? AND skill = ?',
        (args.workflow_id, args.step),
    ).fetchone()

    started_at = args.started_at
    completed_at = args.completed_at
    metadata_json = json_dumps(json_loads(args.metadata_json, {})) if args.metadata_json else '{}'

    if existing:
        step_order = args.order if args.order is not None else existing['step_order']
        if status == 'RUNNING' and not started_at:
            started_at = existing['started_at'] or now_iso()
        else:
            started_at = started_at or existing['started_at']

        if status in {'PASS', 'FAIL', 'SKIPPED'} and not completed_at:
            completed_at = now_iso()
        else:
            completed_at = completed_at or existing['completed_at']

        conn.execute(
            '''
            UPDATE workflow_steps
            SET step_order = ?, status = ?, output = ?, started_at = ?, completed_at = ?, metadata_json = ?
            WHERE workflow_id = ? AND skill = ?
            ''',
            (
                step_order,
                status,
                args.output if args.output is not None else existing['output'],
                started_at,
                completed_at,
                metadata_json if args.metadata_json is not None else existing['metadata_json'],
                args.workflow_id,
                args.step,
            ),
        )
    else:
        if args.order is None:
            row = conn.execute(
                'SELECT COALESCE(MAX(step_order), 0) + 1 AS next_order FROM workflow_steps WHERE workflow_id = ?',
                (args.workflow_id,),
            ).fetchone()
            step_order = int(row['next_order'])
        else:
            step_order = args.order
        if status == 'RUNNING' and not started_at:
            started_at = now_iso()
        if status in {'PASS', 'FAIL', 'SKIPPED'} and not completed_at:
            completed_at = now_iso()
        conn.execute(
            '''
            INSERT INTO workflow_steps (
              workflow_id, step_order, skill, status, output, started_at, completed_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                args.workflow_id,
                step_order,
                args.step,
                status,
                args.output,
                started_at,
                completed_at,
                metadata_json,
            ),
        )

    workflow_updates = {'current_step': args.step, 'current_phase': phase_for_step(args.step)}
    if args.workflow_status is not None:
        workflow_updates['status'] = validate_workflow_status(args.workflow_status)
    else:
        inferred_status = infer_workflow_status_from_step(status)
        if inferred_status is not None:
            workflow_updates['status'] = inferred_status

    conn.execute(
        '''
        UPDATE workflows
        SET current_step = ?, current_phase = ?, status = COALESCE(?, status), updated_at = ?
        WHERE workflow_id = ?
        ''',
        (
            workflow_updates['current_step'],
            workflow_updates['current_phase'],
            workflow_updates.get('status'),
            now_iso(),
            args.workflow_id,
        ),
    )

    append_event_record(
        conn,
        workflow_id=args.workflow_id,
        actor=args.actor,
        event_type='step_upserted',
        payload={
            'step': args.step,
            'status': status,
            'output': args.output,
        },
    )
    if args.workflow_status is None:
        recompute_workflow_status(conn, args.workflow_id)
    return get_workflow_snapshot(conn, args.workflow_id, include_events=args.include_events)


def start_step(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    ensure_workflow_exists(conn, args.workflow_id)
    snapshot = get_workflow_snapshot(conn, args.workflow_id, include_events=False)
    transition = validate_workflow_transition(snapshot, args.step)
    if not transition['ok']:
        raise StateManagerError(f"Cannot start {args.step}: {transition['reason']}")

    return upsert_step(
        conn,
        argparse.Namespace(
            workflow_id=args.workflow_id,
            step=args.step,
            order=args.order,
            status='RUNNING',
            output=args.output,
            started_at=args.started_at or now_iso(),
            completed_at=None,
            metadata_json=args.metadata_json,
            workflow_status='ACTIVE',
            actor=args.actor,
            include_events=args.include_events,
        ),
    )


def set_gate(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    ensure_workflow_exists(conn, args.workflow_id)
    gate_value = int(parse_bool(args.value))
    ts = now_iso()
    conn.execute(
        '''
        INSERT INTO workflow_gates (workflow_id, gate_name, gate_value, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(workflow_id, gate_name)
        DO UPDATE SET gate_value = excluded.gate_value, updated_at = excluded.updated_at
        ''',
        (args.workflow_id, args.gate, gate_value, ts),
    )
    set_updated_at(conn, args.workflow_id)
    append_event_record(
        conn,
        workflow_id=args.workflow_id,
        actor=args.actor,
        event_type='gate_updated',
        payload={'gate': args.gate, 'value': bool(gate_value)},
    )
    recompute_workflow_status(conn, args.workflow_id)
    return get_workflow_snapshot(conn, args.workflow_id, include_events=args.include_events)


def set_artifact(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    ensure_workflow_exists(conn, args.workflow_id)
    metadata = json_loads(args.metadata_json, {}) if args.metadata_json else {}
    identity = infer_v2_artifact_identity(args.path)
    normalized_path = identity['normalized_path']
    workflow = conn.execute(
        'SELECT plan_name, metadata_json FROM workflows WHERE workflow_id = ?',
        (args.workflow_id,),
    ).fetchone()
    if workflow is None:
        raise StateManagerError(f'Workflow not found: {args.workflow_id}')
    workflow_plan_name = workflow['plan_name']
    workflow_metadata = json_loads(workflow['metadata_json'], {})
    expected_run_id = workflow_metadata.get('current_primary_run_id') or f'RUN_{args.workflow_id}'

    if identity['plan_name'] and identity['plan_name'] != workflow_plan_name:
        raise StateManagerError(
            f'Artifact path plan mismatch for workflow {args.workflow_id}: '
            f'expected {workflow_plan_name}, got {identity["plan_name"]}'
        )
    if identity['run_id'] and identity['run_id'] != expected_run_id:
        raise StateManagerError(
            f'Artifact path run mismatch for workflow {args.workflow_id}: '
            f'expected {expected_run_id}, got {identity["run_id"]}'
        )

    ts = now_iso()
    conn.execute(
        '''
        INSERT INTO workflow_artifacts (workflow_id, artifact_key, artifact_path, metadata_json, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(workflow_id, artifact_key)
        DO UPDATE SET artifact_path = excluded.artifact_path, metadata_json = excluded.metadata_json, updated_at = excluded.updated_at
        ''',
        (args.workflow_id, args.key, normalized_path, json_dumps(metadata), ts),
    )
    if identity['run_id']:
        updated = conn.execute(
            '''
            UPDATE v2_primary_runs
            SET updated_at = ?, metadata_json = json_set(COALESCE(metadata_json, '{}'), '$.last_artifact_path', ?)
            WHERE run_id = ? AND workflow_id = ?
            ''',
            (ts, normalized_path, identity['run_id'], args.workflow_id),
        )
        if updated.rowcount == 0:
            raise StateManagerError(
                f'Primary run not found for workflow {args.workflow_id} and run_id {identity["run_id"]}'
            )
    if identity['job_id']:
        conn.execute(
            '''
            INSERT INTO v2_child_jobs (
              job_id, run_id, phase_id, workflow_id, status, attempt_no, artifact_path, artifact_hash, idempotency_key, metadata_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id)
            DO UPDATE SET artifact_path = excluded.artifact_path, metadata_json = excluded.metadata_json, updated_at = excluded.updated_at
            ''',
            (
                identity['job_id'],
                expected_run_id,
                metadata.get('phase_id'),
                args.workflow_id,
                metadata.get('status', V2_DEFAULT_CHILD_JOB_STATUS),
                int(metadata.get('attempt_no', V2_DEFAULT_ATTEMPT_NO)),
                normalized_path,
                metadata.get('artifact_hash'),
                metadata.get('idempotency_key', f"{args.workflow_id}:{args.key}:{identity['job_id']}"),
                json_dumps({'artifact_key': args.key, 'plan_name': workflow_plan_name}),
                ts,
            ),
        )
    set_updated_at(conn, args.workflow_id)
    append_event_record(
        conn,
        workflow_id=args.workflow_id,
        actor=args.actor,
        event_type='artifact_set',
        payload={'key': args.key, 'path': normalized_path, 'run_id': identity['run_id'], 'job_id': identity['job_id']},
    )
    return get_workflow_snapshot(conn, args.workflow_id, include_events=args.include_events)


def append_event(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    payload = json_loads(args.payload_json, {}) if args.payload_json else {}
    append_event_record(
        conn,
        workflow_id=args.workflow_id,
        actor=args.actor,
        event_type=args.event_type,
        payload=payload,
        ts=args.ts,
    )
    set_updated_at(conn, args.workflow_id)
    return get_workflow_snapshot(conn, args.workflow_id, include_events=args.include_events)


def get_workflow_snapshot(conn: sqlite3.Connection, workflow_id: str, include_events: bool = False) -> dict[str, Any]:
    workflow = conn.execute('SELECT * FROM workflows WHERE workflow_id = ?', (workflow_id,)).fetchone()
    if not workflow:
        raise StateManagerError(f'Workflow not found: {workflow_id}')

    gates_rows = conn.execute(
        'SELECT gate_name, gate_value, updated_at FROM workflow_gates WHERE workflow_id = ? ORDER BY gate_name',
        (workflow_id,),
    ).fetchall()
    artifact_rows = conn.execute(
        '''
        SELECT artifact_key, artifact_path, metadata_json, updated_at
        FROM workflow_artifacts
        WHERE workflow_id = ?
        ORDER BY artifact_key
        ''',
        (workflow_id,),
    ).fetchall()
    step_rows = conn.execute(
        '''
        SELECT step_order, skill, status, output, started_at, completed_at, metadata_json
        FROM workflow_steps
        WHERE workflow_id = ?
        ORDER BY step_order, skill
        ''',
        (workflow_id,),
    ).fetchall()

    snapshot = {
        'schema_version': workflow['schema_version'],
        'workflow_id': workflow['workflow_id'],
        'plan_name': workflow['plan_name'],
        'mode': workflow['mode'],
        'ticket': workflow['ticket'],
        'requirement': workflow['requirement'],
        'status': workflow['status'],
        'current_phase': workflow['current_phase'],
        'current_step': workflow['current_step'],
        'started_at': workflow['started_at'],
        'updated_at': workflow['updated_at'],
        'metadata': json_loads(workflow['metadata_json'], {}),
        'gates': {row['gate_name']: bool(row['gate_value']) for row in gates_rows},
        'artifacts': {
            row['artifact_key']: {
                'path': row['artifact_path'],
                'metadata': json_loads(row['metadata_json'], {}),
                'updated_at': row['updated_at'],
            }
            for row in artifact_rows
        },
        'steps': [
            {
                'order': row['step_order'],
                'skill': row['skill'],
                'status': row['status'],
                'output': row['output'],
                'started_at': row['started_at'],
                'completed_at': row['completed_at'],
                'metadata': json_loads(row['metadata_json'], {}),
            }
            for row in step_rows
        ],
    }

    if include_events:
        event_rows = conn.execute(
            '''
            SELECT id, ts, actor, event_type, payload_json
            FROM workflow_events
            WHERE workflow_id = ?
            ORDER BY id
            ''',
            (workflow_id,),
        ).fetchall()
        snapshot['events'] = [
            {
                'id': row['id'],
                'ts': row['ts'],
                'actor': row['actor'],
                'event_type': row['event_type'],
                'payload': json_loads(row['payload_json'], {}),
            }
            for row in event_rows
        ]
    return snapshot


def validate_workflow_transition(snapshot: dict[str, Any], target_step: str) -> dict[str, Any]:
    steps = snapshot['steps']
    workflow_status = snapshot['status']
    if workflow_status in {'FAILED', 'BLOCKED'}:
        return {
            'ok': False,
            'reason': f'workflow is {workflow_status}',
        }

    target = None
    for step in steps:
        if step['skill'] == target_step:
            target = step
            break

    if target is None:
        return {
            'ok': False,
            'reason': f'step {target_step} not registered in workflow',
        }

    if target['status'] == 'RUNNING':
        return {
            'ok': False,
            'reason': f'step {target_step} is already RUNNING',
        }
    if target['status'] in {'PASS', 'SKIPPED'}:
        return {
            'ok': False,
            'reason': f'step {target_step} is already {target["status"]}',
        }

    if target_step == 'implement-plan':
        if not snapshot['gates'].get('plan_approved'):
            return {
                'ok': False,
                'reason': 'plan_approved gate is false',
            }
        if not snapshot['gates'].get('user_approved_implementation'):
            return {
                'ok': False,
                'reason': 'user_approved_implementation gate is false',
            }
    if target_step in {'create-plan', 'review-plan', 'implement-plan'}:
        if snapshot['gates'].get('spec_created') and not snapshot['gates'].get('spec_approved'):
            return {
                'ok': False,
                'reason': 'spec_approved gate is false',
            }

    for step in steps:
        if step['order'] >= target['order']:
            continue
        if step['status'] in {'PASS', 'SKIPPED'}:
            continue
        return {
            'ok': False,
            'reason': f"previous step {step['skill']} is {step['status']}",
        }

    return {
        'ok': True,
        'reason': 'transition allowed',
    }


def get_workflow(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    workflow_id = resolve_workflow_id(conn, workflow_id=args.workflow_id, plan_name=args.plan_name)
    return get_workflow_snapshot(conn, workflow_id, include_events=args.include_events)


def find_workflows(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    where_clauses: list[str] = []
    params: list[Any] = []
    if args.plan_name:
        where_clauses.append('plan_name = ?')
        params.append(args.plan_name)
    if args.status:
        where_clauses.append('status = ?')
        params.append(validate_workflow_status(args.status))
    if args.mode:
        where_clauses.append('mode = ?')
        params.append(validate_mode(args.mode))
    if args.ticket:
        where_clauses.append('ticket = ?')
        params.append(args.ticket)
    if args.query:
        where_clauses.append('(plan_name LIKE ? OR requirement LIKE ? OR workflow_id LIKE ?)')
        like = f'%{args.query}%'
        params.extend([like, like, like])

    where_sql = f'WHERE {" AND ".join(where_clauses)}' if where_clauses else ''
    rows = conn.execute(
        f'''
        SELECT workflow_id, plan_name, mode, status, current_phase, current_step, ticket, updated_at
        FROM workflows
        {where_sql}
        ORDER BY updated_at DESC
        LIMIT ?
        ''',
        (*params, args.limit),
    ).fetchall()
    return {
        'count': len(rows),
        'results': [dict(row) for row in rows],
    }


def resolve_workflow_id(conn: sqlite3.Connection, workflow_id: str | None, plan_name: str | None) -> str:
    if workflow_id:
        ensure_workflow_exists(conn, workflow_id)
        return workflow_id
    if not plan_name:
        raise StateManagerError('Either --workflow-id or --plan-name is required')
    rows = conn.execute(
        '''
        SELECT workflow_id, status, updated_at
        FROM workflows
        WHERE plan_name = ?
        ORDER BY updated_at DESC
        LIMIT 20
        ''',
        (plan_name,),
    ).fetchall()
    if not rows:
        raise StateManagerError(f'No workflow found for plan_name={plan_name}')
    if len(rows) > 1:
        non_terminal = [row for row in rows if row['status'] in {'ACTIVE', 'WAITING_USER', 'BLOCKED'}]
        if len(non_terminal) == 1:
            return non_terminal[0]['workflow_id']

        summary = ', '.join(f"{row['workflow_id']}[{row['status']}]" for row in rows[:5])
        raise StateManagerError(
            f'Multiple workflows found for plan_name={plan_name}; '
            f'candidates: {summary}. Pass --workflow-id explicitly'
        )
    return rows[0]['workflow_id']


def resolve_next(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    workflow_id = resolve_workflow_id(conn, workflow_id=args.workflow_id, plan_name=args.plan_name)
    snapshot = get_workflow_snapshot(conn, workflow_id, include_events=False)
    steps = snapshot['steps']
    workflow_status = snapshot['status']
    gates = snapshot['gates']
    mode = snapshot['mode']
    metadata = snapshot.get('metadata') or {}
    steps_by_skill = {step['skill']: step for step in steps}
    delivery_loop_skills = {'implement-plan', 'review-implement', 'qa-automation'}
    delivery_fail_count = coerce_int(metadata.get('delivery_loop_fail_count'), 0)
    delivery_max_retries = coerce_int(metadata.get('delivery_loop_max_retries'), 3)
    delivery_pause_for_user = bool(metadata.get('delivery_loop_pause_for_user'))
    delivery_pause_reason = metadata.get('delivery_loop_pause_reason')
    has_delivery_failure = any(
        step['skill'] in delivery_loop_skills and step['status'] in {'FAIL', 'NEEDS_REVISION'}
        for step in steps
    )

    if workflow_status in {'WAITING_USER', 'BLOCKED', 'FAILED'}:
        reason = f'workflow is {workflow_status}'
        if workflow_status == 'WAITING_USER' and delivery_pause_for_user and delivery_pause_reason:
            reason = delivery_pause_reason
        return {
            'workflow_id': workflow_id,
            'can_proceed': False,
            'reason': reason,
            'next_step': None,
            'workflow_status': workflow_status,
        }

    for step in steps:
        if step['status'] == 'RUNNING':
            return {
                'workflow_id': workflow_id,
                'can_proceed': False,
                'reason': f"step {step['skill']} is RUNNING",
                'next_step': None,
                'workflow_status': workflow_status,
            }
        if step['status'] == 'WAITING_USER':
            return {
                'workflow_id': workflow_id,
                'can_proceed': False,
                'reason': f"step {step['skill']} is {step['status']}",
                'next_step': None,
                'workflow_status': workflow_status,
            }
        if step['status'] == 'FAIL' and step['skill'] not in delivery_loop_skills:
            return {
                'workflow_id': workflow_id,
                'can_proceed': False,
                'reason': f"step {step['skill']} is FAIL",
                'next_step': None,
                'workflow_status': workflow_status,
            }

    if mode == 'debug':
        debug_step = steps_by_skill.get('debug-investigator')
        if debug_step and debug_step['status'] == 'PENDING':
            return {
                'workflow_id': workflow_id,
                'can_proceed': True,
                'reason': 'debug-investigator pending',
                'next_step': 'debug-investigator',
                'workflow_status': workflow_status,
            }
        return {
            'workflow_id': workflow_id,
            'can_proceed': False,
            'reason': 'debug workflow requires manual follow-up after investigation',
            'next_step': None,
            'workflow_status': workflow_status,
        }

    if mode == 'spec':
        create_spec = steps_by_skill.get('create-spec')
        review_spec = steps_by_skill.get('review-spec')
        if review_spec and review_spec['status'] in {'FAIL', 'NEEDS_REVISION'}:
            return {
                'workflow_id': workflow_id,
                'can_proceed': False,
                'reason': 'review-spec requested revisions',
                'next_step': None,
                'workflow_status': workflow_status,
            }
        if create_spec and create_spec['status'] == 'PENDING':
            return {
                'workflow_id': workflow_id,
                'can_proceed': True,
                'reason': 'create-spec pending',
                'next_step': 'create-spec',
                'workflow_status': workflow_status,
            }
        if review_spec and review_spec['status'] == 'PENDING' and create_spec and create_spec['status'] == 'PASS':
            return {
                'workflow_id': workflow_id,
                'can_proceed': True,
                'reason': 'create-spec passed; review-spec pending',
                'next_step': 'review-spec',
                'workflow_status': workflow_status,
            }
        if review_spec and review_spec['status'] == 'PASS':
            return {
                'workflow_id': workflow_id,
                'can_proceed': False,
                'reason': 'spec finalized; waiting for /lp:plan',
                'next_step': None,
                'workflow_status': 'WAITING_USER',
            }
        return {
            'workflow_id': workflow_id,
            'can_proceed': False,
            'reason': 'spec workflow requires manual follow-up',
            'next_step': None,
            'workflow_status': workflow_status,
        }

    review_plan = steps_by_skill.get('review-plan')
    create_spec = steps_by_skill.get('create-spec')
    review_spec = steps_by_skill.get('review-spec')
    implement = steps_by_skill.get('implement-plan')
    review_implement = steps_by_skill.get('review-implement')
    qa = steps_by_skill.get('qa-automation')

    if mode in {'implement', 'cook'} and delivery_pause_for_user and has_delivery_failure:
        return {
            'workflow_id': workflow_id,
            'can_proceed': False,
            'reason': delivery_pause_reason or 'delivery loop paused for user confirmation',
            'next_step': None,
            'workflow_status': 'WAITING_USER',
        }
    if mode in {'implement', 'cook'} and has_delivery_failure and delivery_fail_count >= delivery_max_retries:
        return {
            'workflow_id': workflow_id,
            'can_proceed': False,
            'reason': f'delivery fix loop reached max retries ({delivery_max_retries})',
            'next_step': None,
            'workflow_status': 'WAITING_USER',
        }

    if review_plan and review_plan['status'] == 'NEEDS_REVISION':
        return {
            'workflow_id': workflow_id,
            'can_proceed': False,
            'reason': 'review-plan requested revisions',
            'next_step': None,
            'workflow_status': workflow_status,
        }
    if implement and implement['status'] == 'FAIL':
        return {
            'workflow_id': workflow_id,
            'can_proceed': True,
            'reason': 'implement-plan failed; retry implementation loop',
            'next_step': 'implement-plan',
            'workflow_status': workflow_status,
        }
    if review_implement and review_implement['status'] in {'NEEDS_REVISION', 'FAIL'}:
        return {
            'workflow_id': workflow_id,
            'can_proceed': True,
            'reason': 'review-implement requested code changes',
            'next_step': 'implement-plan',
            'workflow_status': workflow_status,
        }
    if qa and qa['status'] == 'FAIL':
        return {
            'workflow_id': workflow_id,
            'can_proceed': True,
            'reason': 'qa-automation failed; return to implementation loop',
            'next_step': 'implement-plan',
            'workflow_status': workflow_status,
        }

    if review_plan and review_plan['status'] == 'PENDING':
        create_plan = steps_by_skill.get('create-plan')
        if create_plan and create_plan['status'] == 'PASS':
            return {
                'workflow_id': workflow_id,
                'can_proceed': True,
                'reason': 'create-plan passed; review-plan pending',
                'next_step': 'review-plan',
                'workflow_status': workflow_status,
            }
    if implement and implement['status'] == 'PENDING' and gates.get('plan_approved') and gates.get('user_approved_implementation'):
        return {
            'workflow_id': workflow_id,
            'can_proceed': True,
            'reason': 'implement-plan pending and implementation approved',
            'next_step': 'implement-plan',
            'workflow_status': workflow_status,
        }
    if gates.get('implementation_done') and not gates.get('implementation_review_passed'):
        if review_implement is None or review_implement['status'] == 'PENDING':
            return {
                'workflow_id': workflow_id,
                'can_proceed': True,
                'reason': 'implementation done; review-implement required',
                'next_step': 'review-implement',
                'workflow_status': workflow_status,
            }
    if gates.get('implementation_review_passed') and not gates.get('qa_passed'):
        if qa is None or qa['status'] == 'PENDING':
            return {
                'workflow_id': workflow_id,
                'can_proceed': True,
                'reason': 'review passed; qa-automation required',
                'next_step': 'qa-automation',
                'workflow_status': workflow_status,
            }
    if gates.get('qa_passed'):
        close_task = steps_by_skill.get('close-task')
        if close_task is None or close_task['status'] == 'PENDING':
            return {
                'workflow_id': workflow_id,
                'can_proceed': True,
                'reason': 'qa passed; close-task ready',
                'next_step': 'close-task',
                'workflow_status': workflow_status,
            }

    for step in steps:
        if step['status'] == 'PENDING':
            return {
                'workflow_id': workflow_id,
                'can_proceed': True,
                'reason': 'next pending step available',
                'next_step': step['skill'],
                'workflow_status': workflow_status,
            }

    return {
        'workflow_id': workflow_id,
        'can_proceed': False,
        'reason': 'no pending step left',
        'next_step': None,
        'workflow_status': 'COMPLETED' if workflow_status == 'COMPLETED' else workflow_status,
    }


def validate_transition(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    workflow_id = resolve_workflow_id(conn, workflow_id=args.workflow_id, plan_name=args.plan_name)
    snapshot = get_workflow_snapshot(conn, workflow_id, include_events=False)
    result = validate_workflow_transition(snapshot, args.step)
    result['workflow_id'] = workflow_id
    result['step'] = args.step
    return result


def print_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write('\n')


def print_examples() -> None:
    print_json({'examples': STATE_MANAGER_EXAMPLES})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='SQLite-backed workflow state manager for LittlePea pipeline.')
    parser.add_argument('--print-examples', action='store_true', help='Print machine-friendly command examples and exit')
    parser.add_argument(
        '--db-path',
        help='Explicit path to SQLite DB file. If omitted, resolve to <repo-root>/.codex/state/pipeline_state.db',
    )
    parser.add_argument(
        '--repo-root',
        help='Explicit project root. If omitted, detect via git from the current working directory.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    create = subparsers.add_parser('create-workflow')
    create.add_argument('--workflow-id')
    create.add_argument('--plan-name', required=True)
    create.add_argument('--mode', required=True)
    create.add_argument('--ticket')
    create.add_argument('--requirement')
    create.add_argument('--status')
    create.add_argument('--current-phase')
    create.add_argument('--current-step')
    create.add_argument('--steps', help='Comma-separated ordered steps')
    create.add_argument('--started-at')
    create.add_argument('--metadata-json')
    create.add_argument('--actor', default='orchestrator')
    create.add_argument('--include-events', action='store_true')
    create.set_defaults(handler=create_workflow)

    get = subparsers.add_parser('get-workflow')
    get.add_argument('--workflow-id')
    get.add_argument('--plan-name')
    get.add_argument('--include-events', action='store_true')
    get.set_defaults(handler=get_workflow)

    find = subparsers.add_parser('find-workflows')
    find.add_argument('--query')
    find.add_argument('--plan-name')
    find.add_argument('--status')
    find.add_argument('--mode')
    find.add_argument('--ticket')
    find.add_argument('--limit', type=int, default=20)
    find.set_defaults(handler=find_workflows)

    update = subparsers.add_parser('update-workflow')
    update.add_argument('--workflow-id', required=True)
    update.add_argument('--mode')
    update.add_argument('--status')
    update.add_argument('--current-phase')
    update.add_argument('--current-step')
    update.add_argument('--ticket')
    update.add_argument('--requirement')
    update.add_argument('--metadata-json')
    update.add_argument('--actor', default='orchestrator')
    update.add_argument('--include-events', action='store_true')
    update.set_defaults(handler=update_workflow)

    upsert = subparsers.add_parser('upsert-step')
    upsert.add_argument('--example', action='store_true', help='Print canonical example for this command and exit')
    upsert.add_argument('--workflow-id', required=True)
    upsert.add_argument('--step', required=True)
    upsert.add_argument('--order', type=int)
    upsert.add_argument('--status', required=True)
    upsert.add_argument('--output')
    upsert.add_argument('--started-at')
    upsert.add_argument('--completed-at')
    upsert.add_argument('--metadata-json')
    upsert.add_argument('--workflow-status')
    upsert.add_argument('--actor', default='orchestrator')
    upsert.add_argument('--include-events', action='store_true')
    upsert.set_defaults(handler=upsert_step)

    start = subparsers.add_parser('start-step')
    start.add_argument('--workflow-id', required=True)
    start.add_argument('--step', required=True)
    start.add_argument('--order', type=int)
    start.add_argument('--output')
    start.add_argument('--started-at')
    start.add_argument('--metadata-json')
    start.add_argument('--actor', default='orchestrator')
    start.add_argument('--include-events', action='store_true')
    start.set_defaults(handler=start_step)

    gate = subparsers.add_parser('set-gate')
    gate.add_argument('--workflow-id', required=True)
    gate.add_argument('--gate', required=True)
    gate.add_argument('--value', required=True)
    gate.add_argument('--actor', default='orchestrator')
    gate.add_argument('--include-events', action='store_true')
    gate.set_defaults(handler=set_gate)

    artifact = subparsers.add_parser('set-artifact')
    artifact.add_argument('--workflow-id', required=True)
    artifact.add_argument('--key', required=True)
    artifact.add_argument('--path', required=True)
    artifact.add_argument('--metadata-json')
    artifact.add_argument('--actor', default='orchestrator')
    artifact.add_argument('--include-events', action='store_true')
    artifact.set_defaults(handler=set_artifact)

    event = subparsers.add_parser('append-event')
    event.add_argument('--workflow-id', required=True)
    event.add_argument('--event-type', required=True)
    event.add_argument('--payload-json')
    event.add_argument('--ts')
    event.add_argument('--actor', default='orchestrator')
    event.add_argument('--include-events', action='store_true')
    event.set_defaults(handler=append_event)

    nxt = subparsers.add_parser('resolve-next')
    nxt.add_argument('--workflow-id')
    nxt.add_argument('--plan-name')
    nxt.set_defaults(handler=resolve_next)

    validate = subparsers.add_parser('validate-transition')
    validate.add_argument('--workflow-id')
    validate.add_argument('--plan-name')
    validate.add_argument('--step', required=True)
    validate.set_defaults(handler=validate_transition)

    return parser


def main() -> int:
    argv = sys.argv[1:]
    if '--print-examples' in argv:
        print_examples()
        return 0
    if argv and argv[0] == 'upsert-step' and '--example' in argv[1:]:
        print_json({'command': 'upsert-step', 'example': STATE_MANAGER_EXAMPLES['upsert-step']})
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        db_path = resolve_db_path(db_path_arg=args.db_path, repo_root_arg=args.repo_root)
        with connect(db_path) as conn:
            payload = args.handler(conn, args)
        print_json(payload)
        return 0
    except StateManagerError as exc:
        print_json({'error': str(exc)})
        return 2
    except sqlite3.Error as exc:
        print_json({'error': f'SQLite error: {exc}'})
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
