# Epic Plan Template (LP Pipeline V3)

## Header

- Plan: `PLAN_<NAME>`
- Plan profile: `standard` hoặc `parallel-ready`
- Tier: `L` hoặc `P`
- Canonical runtime root: `.codex/`

## Invariants

- Runtime publish path canonical là `.codex/*`
- SQLite (`state_manager.py`) là authority cho state transitions
- Phase notes/report là human-readable artifacts, không thay thế state authority
- Canonical status enum cho phase runtime: `pending | in_progress | waiting_user | completed | failed | cancelled`

## Mode Decision

- `mode_decision`: `single | epic`
- `mode_recommendation`: `single | user-decides | epic`
- `override_reason`: null hoặc mô tả cụ thể

## Goal

Mô tả mục tiêu nghiệp vụ và technical outcome cần đạt.

## Acceptance Criteria

Liệt kê AC theo format `AC1..ACn`.

## Phase list

Mỗi phase phải có:
- `id`
- `title`
- `owned_files`
- `ac_primary`
- `ac_secondary`
- verify commands riêng

## dependencies

- Liệt kê dependencies theo graph `from -> to`
- Nếu phase có `dependency_critical = true`, phải khai báo dependencies explicit

## Execution Boundary

- Allowed files
- Do NOT Modify

## Verify Commands

- Command ở level phase
- Command ở level plan
- Baseline command resolution contract:
  - priority 1: `baseline_verify_command` trong phase frontmatter
  - priority 2: đúng 1 label `baseline` trong plan Verify Commands

## Final Integration Verify Commands

Phải là JSON parseable:

```json
[
  {
    "label": "example-check",
    "command": "echo ok"
  }
]
```

## Risks

Nêu risk + mitigation + rollback conditions.
