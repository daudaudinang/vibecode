#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


VALID_STATUSES_BY_SKILL = {
    'create-plan': {'PASS', 'WAITING_USER'},
    'debug-investigator': {'PASS', 'FAIL', 'WAITING_USER'},
    'review-plan': {'PASS', 'FAIL', 'NEEDS_REVISION'},
    'implement-plan': {'PASS', 'FAIL', 'WAITING_USER'},
    'review-implement': {'PASS', 'FAIL', 'NEEDS_REVISION'},
    'qa-automation': {'PASS', 'FAIL'},
    'close-task': {'PASS', 'FAIL'},
}

REQUIRED_NEXT_BY_SKILL = {
    'create-plan': {'review-plan', None},
    'debug-investigator': {'create-plan', None},
    'review-plan': {'implement-plan', 'create-plan', None},
    'implement-plan': {'review-implement', None},
    'review-implement': {'qa-automation', 'implement-plan', None},
    'qa-automation': {'close-task', 'implement-plan', None},
    'close-task': {None},
}

REVIEW_SKILLS = {'review-plan', 'review-implement'}
REQUIRED_REVIEW_PERSONAS = {
    'senior_pm',
    'senior_uiux_designer',
    'senior_developer',
    'system_architecture',
}
ALLOWED_FINDING_SEVERITIES = {'blocker', 'major', 'minor', 'info'}
ALLOWED_FINDING_CONFIDENCE = {'low', 'medium', 'high'}
ALLOWED_CONFLICT_STATUS = {'resolved', 'unresolved', 'not_applicable'}


class ContractValidationError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ContractValidationError(f'Contract file not found: {path}') from exc
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f'Invalid JSON in {path}: {exc}') from exc
    if not isinstance(data, dict):
        raise ContractValidationError('Top-level contract must be a JSON object')
    return data


def require(data: dict[str, Any], key: str, expected_type: type | tuple[type, ...] | None = None) -> Any:
    if key not in data:
        raise ContractValidationError(f'Missing required field: {key}')
    value = data[key]
    if expected_type is not None and value is not None and not isinstance(value, expected_type):
        raise ContractValidationError(f'Field {key} must be of type {expected_type}, got {type(value)}')
    return value


def require_list_of_strings(data: dict[str, Any], key: str) -> list[str]:
    value = require(data, key, list)
    if not all(isinstance(item, str) for item in value):
        raise ContractValidationError(f'{key} must be a list of strings')
    return value


def validate_common(contract: dict[str, Any]) -> None:
    schema_version = require(contract, 'schema_version', int)
    if schema_version != 1:
        raise ContractValidationError(f'Unsupported schema_version: {schema_version}')

    skill = require(contract, 'skill', str)
    if skill not in VALID_STATUSES_BY_SKILL:
        raise ContractValidationError(f'Unsupported skill: {skill}')

    require(contract, 'plan', str)
    status = require(contract, 'status', str)
    if status not in VALID_STATUSES_BY_SKILL[skill]:
        raise ContractValidationError(f'Invalid status {status} for skill {skill}')

    require(contract, 'timestamp', str)

    duration = contract.get('duration_min')
    if duration is not None and not isinstance(duration, (int, float)):
        raise ContractValidationError('duration_min must be a number when provided')

    artifacts = require(contract, 'artifacts', dict)
    require(artifacts, 'primary')
    secondary = require(artifacts, 'secondary', list)
    if not all(isinstance(item, str) for item in secondary):
        raise ContractValidationError('artifacts.secondary must be a list of strings')

    next_block = require(contract, 'next', dict)
    next_skill = next_block.get('recommended_skill')
    if next_skill not in REQUIRED_NEXT_BY_SKILL[skill]:
        raise ContractValidationError(
            f'Invalid next.recommended_skill={next_skill!r} for skill {skill}; '
            f'expected one of {sorted(REQUIRED_NEXT_BY_SKILL[skill], key=lambda x: "" if x is None else x)}'
        )
    if 'input_for_next' not in next_block:
        raise ContractValidationError('Missing next.input_for_next')
    if 'handoff_note' not in next_block:
        raise ContractValidationError('Missing next.handoff_note')

    blockers = require(contract, 'blockers', list)
    if not all(isinstance(item, str) for item in blockers):
        raise ContractValidationError('blockers must be a list of strings')

    pending = require(contract, 'pending_questions', dict)
    questions = require(pending, 'questions', list)
    if not all(isinstance(item, str) for item in questions):
        raise ContractValidationError('pending_questions.questions must be a list of strings')
    if 'resume_from' not in pending or 'user_answers' not in pending:
        raise ContractValidationError('pending_questions must contain resume_from and user_answers')


def validate_status_specific(contract: dict[str, Any]) -> None:
    status = contract['status']
    blockers = contract['blockers']
    questions = contract['pending_questions']['questions']

    if status in {'FAIL', 'NEEDS_REVISION'} and not blockers:
        raise ContractValidationError(f'{status} contract must include at least one blocker')
    if status == 'WAITING_USER' and not questions:
        raise ContractValidationError('WAITING_USER contract must include at least one pending question')


def validate_review_summary(contract: dict[str, Any]) -> None:
    if contract['skill'] not in REVIEW_SKILLS:
        return

    review_summary = require(contract, 'review_summary', dict)
    weighted_score = require(review_summary, 'weighted_score', (int, float))
    if not 0 <= weighted_score <= 10:
        raise ContractValidationError('review_summary.weighted_score must be between 0 and 10')

    severity_counts = require(review_summary, 'severity_counts', dict)
    for severity in ['blocker', 'major', 'minor']:
        count = require(severity_counts, severity, int)
        if count < 0:
            raise ContractValidationError(f'review_summary.severity_counts.{severity} must be >= 0')


def validate_review_audit(contract: dict[str, Any]) -> None:
    if contract['skill'] not in REVIEW_SKILLS:
        return

    review_audit = require(contract, 'review_audit', dict)
    triage_basis = require(review_audit, 'triage_basis', str)
    if not triage_basis.strip():
        raise ContractValidationError('review_audit.triage_basis must be non-empty')

    requested = require_list_of_strings(review_audit, 'personas_requested')
    run = require_list_of_strings(review_audit, 'personas_run')
    outputs = require(review_audit, 'persona_outputs', dict)
    persona_scores = require(review_audit, 'persona_scores', dict)

    requested_set = set(requested)
    run_set = set(run)
    if requested_set != REQUIRED_REVIEW_PERSONAS:
        raise ContractValidationError(
            'review_audit.personas_requested must contain exactly the 4 mandatory personas: '
            'senior_pm, senior_uiux_designer, senior_developer, system_architecture'
        )
    if run_set != REQUIRED_REVIEW_PERSONAS:
        raise ContractValidationError(
            'review_audit.personas_run must contain exactly the 4 mandatory personas: '
            'senior_pm, senior_uiux_designer, senior_developer, system_architecture'
        )
    if requested_set != run_set:
        raise ContractValidationError('review_audit.personas_run must match personas_requested exactly')

    if set(outputs.keys()) != REQUIRED_REVIEW_PERSONAS:
        raise ContractValidationError('review_audit.persona_outputs keys must match the 4 mandatory personas exactly')
    if not all(isinstance(path, str) and path for path in outputs.values()):
        raise ContractValidationError('review_audit.persona_outputs values must be non-empty strings')

    if set(persona_scores.keys()) != REQUIRED_REVIEW_PERSONAS:
        raise ContractValidationError('review_audit.persona_scores keys must match the 4 mandatory personas exactly')
    for persona, score in persona_scores.items():
        if not isinstance(score, (int, float)) or not 0 <= score <= 10:
            raise ContractValidationError(f'review_audit.persona_scores.{persona} must be a number between 0 and 10')


def validate_validated_finding(item: Any, index: int) -> None:
    if not isinstance(item, dict):
        raise ContractValidationError(f'finding_validation.validated_findings[{index}] must be an object')

    finding_id = require(item, 'id', str)
    if not finding_id.strip():
        raise ContractValidationError(f'finding_validation.validated_findings[{index}].id must be non-empty')

    severity = require(item, 'severity', str)
    if severity not in ALLOWED_FINDING_SEVERITIES:
        raise ContractValidationError(
            f'finding_validation.validated_findings[{index}].severity must be one of {sorted(ALLOWED_FINDING_SEVERITIES)}'
        )

    summary = require(item, 'summary', str)
    if not summary.strip():
        raise ContractValidationError(f'finding_validation.validated_findings[{index}].summary must be non-empty')

    evidence = require(item, 'evidence', list)
    if not evidence or not all(isinstance(entry, str) and entry.strip() for entry in evidence):
        raise ContractValidationError(f'finding_validation.validated_findings[{index}].evidence must be a non-empty list of strings')

    validation_note = require(item, 'validation_note', str)
    if not validation_note.strip():
        raise ContractValidationError(
            f'finding_validation.validated_findings[{index}].validation_note must be non-empty'
        )

    confidence = require(item, 'confidence', str)
    if confidence not in ALLOWED_FINDING_CONFIDENCE:
        raise ContractValidationError(
            f'finding_validation.validated_findings[{index}].confidence must be one of {sorted(ALLOWED_FINDING_CONFIDENCE)}'
        )

    conflict_status = require(item, 'conflict_status', str)
    if conflict_status not in ALLOWED_CONFLICT_STATUS:
        raise ContractValidationError(
            f'finding_validation.validated_findings[{index}].conflict_status must be one of {sorted(ALLOWED_CONFLICT_STATUS)}'
        )


def validate_finding_validation(contract: dict[str, Any]) -> None:
    if contract['skill'] not in REVIEW_SKILLS:
        return

    finding_validation = require(contract, 'finding_validation', dict)
    business_context_validated = require(finding_validation, 'business_context_validated', bool)
    validated_findings = require(finding_validation, 'validated_findings', list)
    unresolved_conflicts = require(finding_validation, 'unresolved_conflicts', list)

    for index, item in enumerate(validated_findings):
        validate_validated_finding(item, index)

    if not all(isinstance(item, str) and item.strip() for item in unresolved_conflicts):
        raise ContractValidationError('finding_validation.unresolved_conflicts must be a list of non-empty strings')

    status = contract['status']
    blockers = contract['blockers']
    severity_counts = contract['review_summary']['severity_counts']

    if not business_context_validated:
        raise ContractValidationError('finding_validation.business_context_validated must be true for review contracts')
    if status == 'PASS' and unresolved_conflicts:
        raise ContractValidationError('PASS review contracts cannot contain finding_validation.unresolved_conflicts')
    if status == 'PASS' and any(item['conflict_status'] == 'unresolved' for item in validated_findings):
        raise ContractValidationError('PASS review contracts cannot contain unresolved validated findings')
    if status == 'PASS' and severity_counts['blocker'] > 0:
        raise ContractValidationError('PASS review contracts cannot report blocker findings')
    if status == 'PASS' and blockers:
        raise ContractValidationError('PASS review contracts must not contain blockers')
    if status == 'PASS' and contract['review_summary']['weighted_score'] < 8.0:
        raise ContractValidationError('PASS review contracts require review_summary.weighted_score >= 8.0')
    if status == 'PASS' and severity_counts['major'] > 0:
        raise ContractValidationError('PASS review contracts cannot report major findings')
    if status == 'NEEDS_REVISION' and not (
        6.0 <= contract['review_summary']['weighted_score'] <= 7.9
        or severity_counts['major'] > 0
        or unresolved_conflicts
    ):
        raise ContractValidationError(
            'NEEDS_REVISION review contracts require weighted_score in 6.0..7.9, at least one major finding, or unresolved conflicts'
        )
    if status == 'FAIL' and contract['review_summary']['weighted_score'] >= 6.0 and severity_counts['blocker'] == 0:
        raise ContractValidationError('FAIL review contracts require weighted_score < 6.0 or at least one blocker finding')


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    validate_common(contract)
    validate_status_specific(contract)
    validate_review_summary(contract)
    validate_review_audit(contract)
    validate_finding_validation(contract)
    return {
        'ok': True,
        'skill': contract['skill'],
        'status': contract['status'],
        'plan': contract['plan'],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate LP pipeline machine contract JSON files.')
    parser.add_argument('contract_file', nargs='?', help='Path to *.output.contract.json')
    args = parser.parse_args()

    if not args.contract_file:
        parser.print_help(sys.stderr)
        return 0

    try:
        payload = validate_contract(read_json(Path(args.contract_file)))
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write('\n')
        return 0
    except ContractValidationError as exc:
        json.dump({'ok': False, 'error': str(exc)}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write('\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
