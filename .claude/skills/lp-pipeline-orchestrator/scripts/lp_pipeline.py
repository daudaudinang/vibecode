#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parents[4]
STATE_MANAGER_PATH = SCRIPT_ROOT / '.claude/skills/lp-state-manager/scripts/state_manager.py'
CONTRACT_VALIDATOR_PATH = SCRIPT_ROOT / '.claude/skills/lp-pipeline-orchestrator/scripts/validate_contract.py'


def load_state_manager():
    spec = importlib.util.spec_from_file_location('lp_state_manager', STATE_MANAGER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load state manager from {STATE_MANAGER_PATH}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sm = load_state_manager()


def load_contract_validator():
    spec = importlib.util.spec_from_file_location('lp_contract_validator', CONTRACT_VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load contract validator from {CONTRACT_VALIDATOR_PATH}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cv = load_contract_validator()


def print_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write('\n')


def normalize_plan_name(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise sm.StateManagerError('plan name is empty')
    if value.startswith('PLAN_'):
        return value
    normalized = re.sub(r'[^A-Za-z0-9]+', '_', value).strip('_').upper()
    return f'PLAN_{normalized}'


def infer_plan_name(plan_name: str | None, plan_file: str | None, fallback: str | None = None) -> str:
    if plan_name:
        return normalize_plan_name(plan_name)
    if plan_file:
        plan_path = Path(plan_file)
        if plan_path.stem.lower() == 'plan' and plan_path.parent.name:
            return normalize_plan_name(plan_path.parent.name)
        return normalize_plan_name(plan_path.stem)
    if fallback:
        return normalize_plan_name(fallback)
    raise sm.StateManagerError('Unable to infer plan name')


def detect_git_repo_root(cwd: Path | None = None) -> Path | None:
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else None,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    root = result.stdout.strip()
    return Path(root).resolve() if root else None


def resolve_project_root(repo_root_arg: str | None = None, cwd: Path | None = None) -> Path:
    if repo_root_arg:
        return Path(repo_root_arg).expanduser().resolve()

    detected = detect_git_repo_root(cwd)
    if detected is not None:
        return detected

    raise sm.StateManagerError('Cannot infer repo root. Pass --repo-root explicitly or run the command inside a git repository.')


def resolve_db_path(args: argparse.Namespace) -> Path:
    return sm.resolve_db_path(db_path_arg=args.db_path, repo_root_arg=args.repo_root)


def ensure_pipeline_dir(project_root: Path, plan_name: str) -> Path:
    path = project_root / '.claude/pipeline' / plan_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_workflow_id(conn, workflow_id: str | None, plan_name: str | None, plan_file: str | None) -> str:
    inferred = infer_plan_name(plan_name, plan_file) if (plan_name or plan_file) else None
    return sm.resolve_workflow_id(conn, workflow_id=workflow_id, plan_name=inferred)


def workspace_policy(plan_name: str) -> dict[str, Any]:
    return {
        'direct_edit_supported': True,
        'worktree_canonical': False,
        'agent_worktree_policy': 'forbidden-unless-user-explicitly-asks',
        'top_level_agent_background_policy': 'forbidden',
        'reason': 'This repo uses repo-local .claude state/artifacts as the canonical LP runtime surface.',
        'conflict_rule': f'Avoid concurrent active runs sharing the same plan_name ({plan_name}) in one workspace.',
    }


def warn_same_workspace_concurrency(plan_name: str) -> str:
    return (
        'Direct edit in the current workspace is the canonical LP mode for this repo. '
        'Do not auto-launch LP agents in a worktree unless the user explicitly asks for worktree isolation. '
        f'Concurrent runs sharing the same plan_name ({plan_name}) will conflict on repo-local .claude state/artifacts.'
    )


def derive_entry_decision(snapshot: dict[str, Any]) -> dict[str, Any]:
    metadata = snapshot.get('metadata', {})
    run_id = metadata.get('current_primary_run_id')
    if not run_id and snapshot.get('schema_version', 1) >= 2 and snapshot.get('workflow_id'):
        run_id = f"RUN_{snapshot['workflow_id']}"
    status = snapshot.get('status')

    if not run_id:
        return {
            'current_state': 'NO_PRIMARY_RUN',
            'expected_action': 'start-primary-run',
            'allowed_writer': True,
            'silent_takeover_allowed': False,
            'reason': 'No current_primary_run_id exists for this plan yet.',
        }
    if status == 'ACTIVE':
        return {
            'current_state': 'PRIMARY_ACTIVE',
            'expected_action': 'inspect-only-or-explicit-takeover',
            'allowed_writer': False,
            'silent_takeover_allowed': False,
            'reason': 'A primary run is already ACTIVE; do not silently take over from another conversation.',
        }
    if status == 'WAITING_USER':
        return {
            'current_state': 'WAITING_USER',
            'expected_action': 'resume-existing-run',
            'allowed_writer': True,
            'silent_takeover_allowed': False,
            'reason': 'WAITING_USER releases exclusive execution lease but keeps the same primary run canonical until superseded.',
        }
    if status == 'COMPLETED':
        return {
            'current_state': 'COMPLETED',
            'expected_action': 'start-new-run-superseding-completed',
            'allowed_writer': True,
            'silent_takeover_allowed': False,
            'reason': 'Completed runs are read-only history; follow-up work should start a fresh primary run.',
        }
    if status in {'FAILED', 'BLOCKED'}:
        return {
            'current_state': status,
            'expected_action': 'explicit-repair-or-new-run',
            'allowed_writer': True,
            'silent_takeover_allowed': False,
            'reason': 'Failed/blocked runs require explicit operator intent; do not guess whether to repair or supersede.',
        }
    return {
        'current_state': status or 'UNKNOWN',
        'expected_action': 'manual-inspection',
        'allowed_writer': False,
        'silent_takeover_allowed': False,
        'reason': 'State is not mapped to a deterministic writer action yet.',
    }


def parse_frontmatter(output_path: Path) -> dict[str, str]:
    text = output_path.read_text(encoding='utf-8')
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        raise sm.StateManagerError(f'Output contract missing frontmatter: {output_path}')

    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == '---':
            break
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        result[key.strip()] = value.strip()
    return result


def load_contract(output_file: str, contract_file: str | None) -> dict[str, Any]:
    if contract_file:
        contract_path = Path(contract_file)
    else:
        out_path = Path(output_file)
        contract_path = out_path.with_suffix('.contract.json')

    if contract_path.exists():
        payload = json.loads(contract_path.read_text(encoding='utf-8'))
        payload['_contract_source'] = str(contract_path)
        payload['_contract_format'] = 'json'
        return payload

    output_path = Path(output_file)
    frontmatter = parse_frontmatter(output_path)
    frontmatter['_contract_source'] = str(output_path)
    frontmatter['_contract_format'] = 'frontmatter'
    return frontmatter


def command_start_plan(conn, args: argparse.Namespace) -> dict[str, Any]:
    plan_name = infer_plan_name(args.plan_name, None, args.requirement if args.allow_requirement_name else None)
    ensure_pipeline_dir(resolve_project_root(args.repo_root), plan_name)

    create_args = argparse.Namespace(
        workflow_id=args.workflow_id,
        plan_name=plan_name,
        mode='plan',
        ticket=args.ticket,
        requirement=args.requirement,
        status='ACTIVE',
        current_phase='plan',
        current_step='create-plan',
        steps='create-plan,review-plan',
        started_at=args.started_at,
        metadata_json=args.metadata_json,
        actor=args.actor,
        include_events=args.include_events,
    )
    payload = sm.create_workflow(conn, create_args)
    sm.start_step(
        conn,
        argparse.Namespace(
            workflow_id=payload['workflow_id'],
            step='create-plan',
            order=1,
            output=None,
            started_at=args.started_at,
            metadata_json=json.dumps({'source_command': '/lp:plan'}),
            actor=args.actor,
            include_events=False,
        ),
    )
    payload = sm.get_workflow_snapshot(conn, payload['workflow_id'], include_events=args.include_events)
    payload['recommended_next'] = {
        'agent': 'create-plan',
        'command': f'/lp:plan {args.requirement}' if args.requirement else f'/lp:plan {plan_name}',
    }
    payload['workspace_warning'] = warn_same_workspace_concurrency(plan_name)
    payload['workspace_policy'] = workspace_policy(plan_name)
    return payload


def command_start_cook(conn, args: argparse.Namespace) -> dict[str, Any]:
    plan_name = infer_plan_name(args.plan_name, None, args.requirement if args.allow_requirement_name else None)
    ensure_pipeline_dir(resolve_project_root(args.repo_root), plan_name)

    create_args = argparse.Namespace(
        workflow_id=args.workflow_id,
        plan_name=plan_name,
        mode='cook',
        ticket=args.ticket,
        requirement=args.requirement,
        status='ACTIVE',
        current_phase='plan',
        current_step='create-plan',
        steps='create-plan,review-plan,implement-plan',
        started_at=args.started_at,
        metadata_json=args.metadata_json,
        actor=args.actor,
        include_events=args.include_events,
    )
    payload = sm.create_workflow(conn, create_args)
    sm.set_gate(
        conn,
        argparse.Namespace(
            workflow_id=payload['workflow_id'],
            gate='user_approved_implementation',
            value='true',
            actor=args.actor,
            include_events=False,
        ),
    )
    sm.start_step(
        conn,
        argparse.Namespace(
            workflow_id=payload['workflow_id'],
            step='create-plan',
            order=1,
            output=None,
            started_at=args.started_at,
            metadata_json=json.dumps({'source_command': '/lp:cook'}),
            actor=args.actor,
            include_events=False,
        ),
    )
    payload = sm.get_workflow_snapshot(conn, payload['workflow_id'], include_events=args.include_events)
    payload['workspace_warning'] = warn_same_workspace_concurrency(plan_name)
    payload['workspace_policy'] = workspace_policy(plan_name)
    return payload


def command_start_implement(conn, args: argparse.Namespace) -> dict[str, Any]:
    workflow_id = resolve_workflow_id(conn, args.workflow_id, args.plan_name, args.plan_file)
    snapshot = sm.get_workflow_snapshot(conn, workflow_id, include_events=False)
    if not snapshot['gates'].get('plan_approved'):
        raise sm.StateManagerError(f'Workflow {workflow_id} is not plan-approved yet')

    plan_name = snapshot['plan_name']
    ensure_pipeline_dir(resolve_project_root(args.repo_root), plan_name)
    if args.plan_file:
        sm.set_artifact(
            conn,
            argparse.Namespace(
                workflow_id=workflow_id,
                key='final_plan_path',
                path=args.plan_file,
                metadata_json=None,
                actor=args.actor,
                include_events=False,
            ),
        )

    sm.set_gate(
        conn,
        argparse.Namespace(
            workflow_id=workflow_id,
            gate='user_approved_implementation',
            value='true',
            actor=args.actor,
            include_events=False,
        ),
    )

    existing_steps = {step['skill'] for step in snapshot['steps']}
    if 'implement-plan' not in existing_steps:
        sm.upsert_step(
            conn,
            argparse.Namespace(
                workflow_id=workflow_id,
                step='implement-plan',
                order=None,
                status='PENDING',
                output=None,
                started_at=None,
                completed_at=None,
                metadata_json=None,
                workflow_status='ACTIVE',
                actor=args.actor,
                include_events=False,
            ),
        )

    sm.update_workflow(
        conn,
        argparse.Namespace(
            workflow_id=workflow_id,
            status='ACTIVE',
            current_phase='implement',
            current_step='implement-plan',
            ticket=None,
            requirement=None,
            metadata_json=None,
            actor=args.actor,
            include_events=args.include_events,
        ),
    )
    sm.start_step(
        conn,
        argparse.Namespace(
            workflow_id=workflow_id,
            step='implement-plan',
            order=None,
            output=None,
            started_at=None,
            metadata_json=json.dumps({'source_command': '/lp:implement'}),
            actor=args.actor,
            include_events=False,
        ),
    )
    payload = sm.get_workflow_snapshot(conn, workflow_id, include_events=args.include_events)
    payload['workspace_warning'] = warn_same_workspace_concurrency(plan_name)
    payload['workspace_policy'] = workspace_policy(plan_name)
    payload['entry_decision'] = derive_entry_decision(payload)
    return payload


def extract_review_validation_summary(contract: dict[str, Any]) -> dict[str, Any]:
    review_summary = contract.get('review_summary', {})
    finding_validation = contract.get('finding_validation', {})
    return {
        'weighted_score': review_summary.get('weighted_score'),
        'severity_counts': review_summary.get('severity_counts'),
        'business_context_validated': finding_validation.get('business_context_validated'),
        'unresolved_conflicts': finding_validation.get('unresolved_conflicts', []),
        'validated_findings_count': len(finding_validation.get('validated_findings', [])),
    }


def sync_gates_for_skill(conn, workflow_id: str, skill: str, status: str, actor: str, contract: dict[str, Any] | None = None) -> None:
    if skill == 'create-plan':
        if status == 'PASS':
            sm.set_gate(conn, argparse.Namespace(workflow_id=workflow_id, gate='plan_created', value='true', actor=actor, include_events=False))
        elif status == 'WAITING_USER':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='WAITING_USER',
                    current_phase='plan',
                    current_step='create-plan',
                    ticket=None,
                    requirement=None,
                    metadata_json=None,
                    actor=actor,
                    include_events=False,
                ),
            )
    elif skill == 'debug-investigator':
        if status == 'WAITING_USER':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='WAITING_USER',
                    current_phase='debug',
                    current_step='debug-investigator',
                    ticket=None,
                    requirement=None,
                    metadata_json=None,
                    actor=actor,
                    include_events=False,
                ),
            )
        elif status == 'FAIL':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='FAILED',
                    current_phase='debug',
                    current_step='debug-investigator',
                    ticket=None,
                    requirement=None,
                    metadata_json=None,
                    actor=actor,
                    include_events=False,
                ),
            )
    elif skill == 'review-plan':
        validation = extract_review_validation_summary(contract or {})
        metadata_json = json.dumps({'review_validation': validation})
        sm.set_gate(conn, argparse.Namespace(workflow_id=workflow_id, gate='plan_reviewed', value='true' if status in {'PASS', 'FAIL', 'NEEDS_REVISION'} else 'false', actor=actor, include_events=False))
        sm.set_gate(conn, argparse.Namespace(workflow_id=workflow_id, gate='plan_approved', value='true' if status == 'PASS' else 'false', actor=actor, include_events=False))
        if status == 'PASS':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='WAITING_USER',
                    current_phase='plan_review',
                    current_step='review-plan',
                    ticket=None,
                    requirement=None,
                    metadata_json=metadata_json,
                    actor=actor,
                    include_events=False,
                ),
            )
        elif status == 'NEEDS_REVISION':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='ACTIVE',
                    current_phase='plan',
                    current_step='review-plan',
                    ticket=None,
                    requirement=None,
                    metadata_json=metadata_json,
                    actor=actor,
                    include_events=False,
                ),
            )
        elif status == 'FAIL':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='FAILED',
                    current_phase='plan_review',
                    current_step='review-plan',
                    ticket=None,
                    requirement=None,
                    metadata_json=metadata_json,
                    actor=actor,
                    include_events=False,
                ),
            )
    elif skill == 'implement-plan':
        if status == 'PASS':
            sm.set_gate(conn, argparse.Namespace(workflow_id=workflow_id, gate='implementation_done', value='true', actor=actor, include_events=False))
        elif status == 'WAITING_USER':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='WAITING_USER',
                    current_phase='implement',
                    current_step='implement-plan',
                    ticket=None,
                    requirement=None,
                    metadata_json=None,
                    actor=actor,
                    include_events=False,
                ),
            )
        elif status == 'FAIL':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='FAILED',
                    current_phase='implement',
                    current_step='implement-plan',
                    ticket=None,
                    requirement=None,
                    metadata_json=None,
                    actor=actor,
                    include_events=False,
                ),
            )
    elif skill == 'review-implement':
        if not contract:
            raise sm.StateManagerError('review-implement gate sync requires validated contract payload')

        validation = extract_review_validation_summary(contract)
        metadata_json = json.dumps({'review_validation': validation})
        severity_counts = validation.get('severity_counts') or {}
        weighted_score = validation.get('weighted_score')
        business_context_validated = validation.get('business_context_validated') is True
        unresolved_conflicts = validation.get('unresolved_conflicts') or []

        if status in {'PASS', 'NEEDS_REVISION', 'FAIL'}:
            validation_artifact_path = str(Path('.claude/pipeline') / contract['plan'] / 'review-implement.validation.json')
            sm.set_artifact(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    key='review_implement_validation',
                    path=validation_artifact_path,
                    metadata_json=metadata_json,
                    actor=actor,
                    include_events=False,
                ),
            )

        if weighted_score is None:
            raise sm.StateManagerError('review-implement review contracts require weighted_score for gate decisions')
        if not business_context_validated:
            raise sm.StateManagerError('review-implement review contracts require validated business context')
        if status == 'PASS' and unresolved_conflicts:
            raise sm.StateManagerError('review-implement PASS contract cannot contain unresolved conflicts after validation')
        if status == 'PASS' and severity_counts.get('major', 0) > 0:
            raise sm.StateManagerError('review-implement PASS contract cannot keep validated major findings')
        if status == 'PASS' and severity_counts.get('blocker', 0) > 0:
            raise sm.StateManagerError('review-implement PASS contract cannot keep validated blocker findings')
        if status == 'PASS' and weighted_score < 8.0:
            raise sm.StateManagerError('review-implement PASS contract requires weighted_score >= 8.0')
        if status == 'NEEDS_REVISION' and severity_counts.get('blocker', 0) > 0:
            raise sm.StateManagerError('review-implement NEEDS_REVISION contract cannot include blocker findings; use FAIL instead')
        if status == 'NEEDS_REVISION' and weighted_score < 6.0:
            raise sm.StateManagerError('review-implement NEEDS_REVISION contract cannot have weighted_score < 6.0')

        if status == 'PASS':
            sm.append_event_record(
                conn,
                workflow_id=workflow_id,
                actor=actor,
                event_type='review_findings_validated',
                payload=validation,
            )
        else:
            sm.append_event_record(
                conn,
                workflow_id=workflow_id,
                actor=actor,
                event_type='review_findings_blocked',
                payload=validation,
            )

        sm.set_gate(
            conn,
            argparse.Namespace(
                workflow_id=workflow_id,
                gate='implementation_review_validated',
                value='true',
                actor=actor,
                include_events=False,
            ),
        )
        sm.set_gate(
            conn,
            argparse.Namespace(
                workflow_id=workflow_id,
                gate='implementation_review_ready_for_qa',
                value='true' if status == 'PASS' else 'false',
                actor=actor,
                include_events=False,
            ),
        )
        sm.set_gate(
            conn,
            argparse.Namespace(
                workflow_id=workflow_id,
                gate='implementation_review_passed',
                value='true' if status == 'PASS' else 'false',
                actor=actor,
                include_events=False,
            ),
        )

        if status == 'PASS':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='ACTIVE',
                    current_phase='code_review',
                    current_step='review-implement',
                    ticket=None,
                    requirement=None,
                    metadata_json=metadata_json,
                    actor=actor,
                    include_events=False,
                ),
            )
        elif status == 'NEEDS_REVISION':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='ACTIVE',
                    current_phase='code_review',
                    current_step='review-implement',
                    ticket=None,
                    requirement=None,
                    metadata_json=metadata_json,
                    actor=actor,
                    include_events=False,
                ),
            )
        elif status == 'FAIL':
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='FAILED',
                    current_phase='code_review',
                    current_step='review-implement',
                    ticket=None,
                    requirement=None,
                    metadata_json=metadata_json,
                    actor=actor,
                    include_events=False,
                ),
            )

        return
    elif skill == 'qa-automation':
        if status == 'PASS':
            sm.set_gate(conn, argparse.Namespace(workflow_id=workflow_id, gate='qa_passed', value='true', actor=actor, include_events=False))
        elif status == 'FAIL':
            sm.set_gate(conn, argparse.Namespace(workflow_id=workflow_id, gate='qa_passed', value='false', actor=actor, include_events=False))
            sm.update_workflow(
                conn,
                argparse.Namespace(
                    workflow_id=workflow_id,
                    status='ACTIVE',
                    current_phase='qa',
                    current_step='qa-automation',
                    ticket=None,
                    requirement=None,
                    metadata_json=None,
                    actor=actor,
                    include_events=False,
                ),
            )
    elif skill == 'close-task':
        if status == 'PASS':
            sm.set_gate(conn, argparse.Namespace(workflow_id=workflow_id, gate='user_approved_close', value='true', actor=actor, include_events=False))


def command_sync_output(conn, args: argparse.Namespace) -> dict[str, Any]:
    output_path = Path(args.output_file)
    if not output_path.exists():
        raise sm.StateManagerError(f'Output file not found: {output_path}')

    contract = load_contract(args.output_file, args.contract_file)
    if contract.get('_contract_format') == 'json':
        cv.validate_contract({k: v for k, v in contract.items() if not k.startswith('_')})
    skill = contract.get('skill')
    status = contract.get('status')
    if not skill or not status:
        raise sm.StateManagerError(f'Output contract missing skill/status: {output_path}')

    workflow_id = resolve_workflow_id(conn, args.workflow_id, args.plan_name or contract.get('plan'), args.plan_file)
    snapshot = sm.get_workflow_snapshot(conn, workflow_id, include_events=False)
    target_step = next((step for step in snapshot['steps'] if step['skill'] == skill), None)
    if target_step is None:
        raise sm.StateManagerError(f'Cannot sync {skill}: step not registered in workflow')
    if skill == 'implement-plan':
        if not snapshot['gates'].get('plan_approved'):
            raise sm.StateManagerError('Cannot sync implement-plan: plan_approved gate is false')
        if not snapshot['gates'].get('user_approved_implementation'):
            raise sm.StateManagerError('Cannot sync implement-plan: user_approved_implementation gate is false')
    for step in snapshot['steps']:
        if step['order'] < target_step['order'] and step['status'] != 'PASS':
            raise sm.StateManagerError(f"Cannot sync {skill}: previous step {step['skill']} is {step['status']}")

    sm.upsert_step(
        conn,
        argparse.Namespace(
            workflow_id=workflow_id,
            step=skill,
            order=None,
            status=status,
            output=str(output_path),
            started_at=None,
            completed_at=contract.get('timestamp') if status in {'PASS', 'FAIL', 'SKIPPED'} else None,
            metadata_json=json.dumps(
                {
                    'contract_source': contract.get('_contract_source'),
                    'contract_format': contract.get('_contract_format'),
                }
            ),
            workflow_status=None,
            actor=args.actor,
            include_events=False,
        ),
    )

    if args.plan_file:
        sm.set_artifact(
            conn,
            argparse.Namespace(
                workflow_id=workflow_id,
                key='final_plan_path',
                path=args.plan_file,
                metadata_json=None,
                actor=args.actor,
                include_events=False,
            ),
        )
    elif skill == 'create-plan' and contract.get('plan'):
        plan_path = str(Path('.claude/plans') / contract['plan'] / 'plan.md')
        sm.set_artifact(
            conn,
            argparse.Namespace(
                workflow_id=workflow_id,
                key='final_plan_path',
                path=plan_path,
                metadata_json=None,
                actor=args.actor,
                include_events=False,
            ),
        )

    sync_gates_for_skill(conn, workflow_id, skill, status, args.actor, contract={k: v for k, v in contract.items() if not k.startswith('_')})
    sm.append_event_record(
        conn,
        workflow_id=workflow_id,
        actor=args.actor,
        event_type='output_synced',
        payload={
            'skill': skill,
            'status': status,
            'output_file': str(output_path),
            'contract_source': contract.get('_contract_source'),
            'contract_format': contract.get('_contract_format'),
            'run_id': args.run_id,
            'source_command': args.source_command,
        },
    )
    return sm.get_workflow_snapshot(conn, workflow_id, include_events=args.include_events)


def command_next(conn, args: argparse.Namespace) -> dict[str, Any]:
    workflow_id = resolve_workflow_id(conn, args.workflow_id, args.plan_name, args.plan_file)
    result = sm.resolve_next(
        conn,
        argparse.Namespace(workflow_id=workflow_id, plan_name=None),
    )
    if result['next_step']:
        result['recommended_agent'] = result['next_step']
    return result


def command_start_followup(conn, args: argparse.Namespace) -> dict[str, Any]:
    workflow_id = resolve_workflow_id(conn, args.workflow_id, args.plan_name, args.plan_file)
    snapshot = sm.get_workflow_snapshot(conn, workflow_id, include_events=False)

    if args.step == 'review-implement' and not snapshot['gates'].get('implementation_done'):
        raise sm.StateManagerError('Cannot start review-implement before implementation_done=true')
    if args.step == 'qa-automation' and not snapshot['gates'].get('implementation_review_passed'):
        raise sm.StateManagerError('Cannot start qa-automation before implementation_review_passed=true')
    if args.step == 'close-task' and not snapshot['gates'].get('qa_passed'):
        raise sm.StateManagerError('Cannot start close-task before qa_passed=true')

    existing_steps = {step['skill'] for step in snapshot['steps']}
    if args.step not in existing_steps:
        sm.upsert_step(
            conn,
            argparse.Namespace(
                workflow_id=workflow_id,
                step=args.step,
                order=None,
                status='PENDING',
                output=None,
                started_at=None,
                completed_at=None,
                metadata_json=None,
                workflow_status='ACTIVE',
                actor=args.actor,
                include_events=False,
            ),
        )

    sm.start_step(
        conn,
        argparse.Namespace(
            workflow_id=workflow_id,
            step=args.step,
            order=None,
            output=None,
            started_at=None,
            metadata_json=json.dumps({'source_command': args.source_command}),
            actor=args.actor,
            include_events=False,
        ),
    )
    return sm.get_workflow_snapshot(conn, workflow_id, include_events=args.include_events)


def command_start_debug(conn, args: argparse.Namespace) -> dict[str, Any]:
    plan_name = infer_plan_name(args.plan_name, None, args.requirement if args.allow_requirement_name else None)
    ensure_pipeline_dir(resolve_project_root(args.repo_root), plan_name)

    create_args = argparse.Namespace(
        workflow_id=args.workflow_id,
        plan_name=plan_name,
        mode='debug',
        ticket=args.ticket,
        requirement=args.requirement,
        status='ACTIVE',
        current_phase='debug',
        current_step='debug-investigator',
        steps='debug-investigator',
        started_at=args.started_at,
        metadata_json=args.metadata_json,
        actor=args.actor,
        include_events=args.include_events,
    )
    payload = sm.create_workflow(conn, create_args)
    sm.start_step(
        conn,
        argparse.Namespace(
            workflow_id=payload['workflow_id'],
            step='debug-investigator',
            order=1,
            output=None,
            started_at=args.started_at,
            metadata_json=json.dumps({'source_command': '/lp:debug-investigator'}),
            actor=args.actor,
            include_events=False,
        ),
    )
    return sm.get_workflow_snapshot(conn, payload['workflow_id'], include_events=args.include_events)


def command_status(conn, args: argparse.Namespace) -> dict[str, Any]:
    workflow_id = resolve_workflow_id(conn, args.workflow_id, args.plan_name, args.plan_file)
    snapshot = sm.get_workflow_snapshot(conn, workflow_id, include_events=args.include_events)
    next_info = sm.resolve_next(conn, argparse.Namespace(workflow_id=workflow_id, plan_name=None))
    delivery_next = compute_delivery_next(snapshot)
    return {
        'workflow': snapshot,
        'next': next_info,
        'delivery_next': delivery_next,
        'entry_decision': derive_entry_decision(snapshot),
        'workspace_policy': workspace_policy(snapshot['plan_name']),
        'workspace_warning': warn_same_workspace_concurrency(snapshot['plan_name']),
    }


def command_resume(conn, args: argparse.Namespace) -> dict[str, Any]:
    workflow_id = resolve_workflow_id(conn, args.workflow_id, args.plan_name, args.plan_file)
    snapshot = sm.get_workflow_snapshot(conn, workflow_id, include_events=False)
    next_info = sm.resolve_next(conn, argparse.Namespace(workflow_id=workflow_id, plan_name=None))
    delivery_next = compute_delivery_next(snapshot)

    result: dict[str, Any] = {
        'workflow_id': workflow_id,
        'workflow_status': snapshot['status'],
        'current_step': snapshot['current_step'],
        'can_resume': next_info['can_proceed'],
        'reason': next_info['reason'],
        'next_step': next_info['next_step'],
        'delivery_next': delivery_next,
        'entry_decision': derive_entry_decision(snapshot),
        'workspace_policy': workspace_policy(snapshot['plan_name']),
        'workspace_warning': warn_same_workspace_concurrency(snapshot['plan_name']),
    }
    if next_info['next_step']:
        result['recommended_agent'] = next_info['next_step']
        result['recommended_command'] = {
            'create-plan': '@create-plan or /lp:plan',
            'review-plan': '@review-plan',
            'implement-plan': '@implement-plan or /lp:implement',
            'review-implement': '@review-implement',
            'qa-automation': '@qa-automation',
            'close-task': '@close-task',
        }.get(next_info['next_step'], next_info['next_step'])
    return result


def compute_delivery_next(snapshot: dict[str, Any]) -> dict[str, Any]:
    steps = {step['skill']: step for step in snapshot['steps']}
    gates = snapshot['gates']

    if 'debug-investigator' in steps:
        debug_step = steps['debug-investigator']
        if debug_step['status'] == 'PASS':
            return {
                'action': None,
                'reason': 'debug-investigator is a standalone investigation lane; decide next action manually',
                'recommended_command': '/lp:plan <fix_scope>',
            }
        if debug_step['status'] in {'RUNNING', 'WAITING_USER', 'FAIL'}:
            return {
                'action': 'debug-investigator',
                'reason': f'debug-investigator is {debug_step["status"]}',
                'recommended_command': None,
            }

    def response(action: str | None, reason: str, command: str | None = None) -> dict[str, Any]:
        return {
            'action': action,
            'reason': reason,
            'recommended_command': command,
        }

    for step_name in ['implement-plan', 'review-implement', 'qa-automation', 'close-task']:
        step = steps.get(step_name)
        if step and step['status'] in {'RUNNING', 'WAITING_USER'}:
            return response(step_name, f'{step_name} is {step["status"]}', None)

    review = steps.get('review-implement')
    qa = steps.get('qa-automation')

    if review and review['status'] in {'FAIL', 'NEEDS_REVISION'}:
        return response('implement-plan', 'review-implement requested code changes', '/lp:implement <plan_file>')
    if qa and qa['status'] == 'FAIL':
        return response('implement-plan', 'qa-automation failed; return to implementation loop', '/lp:implement <plan_file>')
    if gates.get('implementation_done') and not gates.get('implementation_review_passed'):
        return response('review-implement', 'implementation done; review required', '@review-implement')
    if gates.get('implementation_review_passed') and not gates.get('qa_passed'):
        return response('qa-automation', 'review passed; QA required', '@qa-automation')
    if gates.get('qa_passed'):
        return response('close-task', 'QA passed; ready to close task', '@close-task')
    if steps.get('implement-plan') and steps['implement-plan']['status'] == 'PASS':
        return response('review-implement', 'implementation finished; start review loop', '@review-implement')
    if steps.get('implement-plan'):
        return response('implement-plan', 'implementation step pending or not completed', '/lp:implement <plan_file>')
    return response(None, 'delivery loop not initialized', None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='High-level LP pipeline orchestration helpers.')
    parser.add_argument(
        '--db-path',
        help='Explicit path to SQLite DB file. If omitted, resolve to <repo-root>/.claude/state/pipeline_state.db',
    )
    parser.add_argument(
        '--repo-root',
        help='Explicit project root. If omitted, detect via git from the current working directory.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    start_plan = subparsers.add_parser('start-plan')
    start_plan.add_argument('--workflow-id')
    start_plan.add_argument('--plan-name')
    start_plan.add_argument('--ticket')
    start_plan.add_argument('--requirement', required=True)
    start_plan.add_argument('--metadata-json')
    start_plan.add_argument('--started-at')
    start_plan.add_argument('--actor', default='orchestrator')
    start_plan.add_argument('--include-events', action='store_true')
    start_plan.add_argument('--allow-requirement-name', action='store_true')
    start_plan.set_defaults(handler=command_start_plan)

    start_cook = subparsers.add_parser('start-cook')
    start_cook.add_argument('--workflow-id')
    start_cook.add_argument('--plan-name')
    start_cook.add_argument('--ticket')
    start_cook.add_argument('--requirement', required=True)
    start_cook.add_argument('--metadata-json')
    start_cook.add_argument('--started-at')
    start_cook.add_argument('--actor', default='orchestrator')
    start_cook.add_argument('--include-events', action='store_true')
    start_cook.add_argument('--allow-requirement-name', action='store_true')
    start_cook.set_defaults(handler=command_start_cook)

    start_debug = subparsers.add_parser('start-debug')
    start_debug.add_argument('--workflow-id')
    start_debug.add_argument('--plan-name')
    start_debug.add_argument('--ticket')
    start_debug.add_argument('--requirement', required=True)
    start_debug.add_argument('--metadata-json')
    start_debug.add_argument('--started-at')
    start_debug.add_argument('--actor', default='orchestrator')
    start_debug.add_argument('--include-events', action='store_true')
    start_debug.add_argument('--allow-requirement-name', action='store_true')
    start_debug.set_defaults(handler=command_start_debug)

    start_implement = subparsers.add_parser('start-implement')
    start_implement.add_argument('--workflow-id')
    start_implement.add_argument('--plan-name')
    start_implement.add_argument('--plan-file')
    start_implement.add_argument('--actor', default='orchestrator')
    start_implement.add_argument('--include-events', action='store_true')
    start_implement.set_defaults(handler=command_start_implement)

    follow = subparsers.add_parser('start-followup')
    follow.add_argument('--workflow-id')
    follow.add_argument('--plan-name')
    follow.add_argument('--plan-file')
    follow.add_argument('--step', required=True, choices=['review-implement', 'qa-automation', 'close-task'])
    follow.add_argument('--actor', default='orchestrator')
    follow.add_argument('--source-command', default='lp-pipeline-orchestrator')
    follow.add_argument('--include-events', action='store_true')
    follow.set_defaults(handler=command_start_followup)

    sync = subparsers.add_parser('sync-output')
    sync.add_argument('--workflow-id')
    sync.add_argument('--plan-name')
    sync.add_argument('--plan-file')
    sync.add_argument('--output-file', required=True)
    sync.add_argument('--contract-file')
    sync.add_argument('--actor', default='orchestrator')
    sync.add_argument('--run-id')
    sync.add_argument('--source-command')
    sync.add_argument('--include-events', action='store_true')
    sync.set_defaults(handler=command_sync_output)

    nxt = subparsers.add_parser('next')
    nxt.add_argument('--workflow-id')
    nxt.add_argument('--plan-name')
    nxt.add_argument('--plan-file')
    nxt.set_defaults(handler=command_next)

    status = subparsers.add_parser('status')
    status.add_argument('--workflow-id')
    status.add_argument('--plan-name')
    status.add_argument('--plan-file')
    status.add_argument('--include-events', action='store_true')
    status.set_defaults(handler=command_status)

    resume = subparsers.add_parser('resume')
    resume.add_argument('--workflow-id')
    resume.add_argument('--plan-name')
    resume.add_argument('--plan-file')
    resume.set_defaults(handler=command_resume)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        db_path = resolve_db_path(args)
        with sm.connect(db_path) as conn:
            payload = args.handler(conn, args)
        print_json(payload)
        return 0
    except sm.StateManagerError as exc:
        print_json({'error': str(exc)})
        return 2
    except Exception as exc:  # noqa: BLE001
        print_json({'error': str(exc)})
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
