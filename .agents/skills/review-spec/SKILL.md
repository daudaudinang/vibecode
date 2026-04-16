---
name: review-spec
description: Worker-only skill that reviews one canonical LP spec package and returns validated findings for the orchestrator spec gate.
---

# Review Spec — Worker Only

> **Full task guide**: `.agents/skills/tasks/review-spec/TASK.md`

## Goal

Review 1 canonical LP spec để chặn spec mơ hồ, thiếu happy/edge paths, thiếu UI state expectations trước khi plan bắt đầu.

## Worker-only responsibility

- Chỉ làm step `review-spec`
- Không tự orchestration sang `create-plan`
- Không tự sửa spec
- Chỉ review spec package và publish report + contract

## Canonical inputs

- `.codex/plans/PLAN_<NAME>/spec.md`
- Requirement gốc từ workflow metadata

## Output

- `.codex/pipeline/PLAN_<NAME>/00-review-spec.output.md`
- `.codex/pipeline/PLAN_<NAME>/00-review-spec.output.contract.json`

## Mandatory review model

- Bắt buộc chạy đủ 4 persona: `senior_pm`, `senior_uiux_designer`, `senior_developer`, `system_architecture`
- Chỉ verdict: `PASS | NEEDS_REVISION | FAIL`
- Mọi finding dùng cho verdict phải có evidence + validation

## Contract status

- `PASS | NEEDS_REVISION | FAIL`
- `next.recommended_skill = create-plan | create-spec | null`
