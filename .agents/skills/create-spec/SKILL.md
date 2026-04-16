---
name: create-spec
description: Worker-only skill that creates one canonical LP spec package (business + UX flows + happy/edge case expectations) and returns machine-readable artifacts.
---

# Create Spec — Worker Only

## Goal

Tạo 1 spec canonical cho LP để làm baseline cho `create-plan`.

## Worker-only responsibility

- Chỉ làm step `create-spec`
- Không tự orchestration sang `create-plan`
- Không tự approve plan/implement
- Chỉ tạo spec artifact + machine contract

## Canonical artifacts

- `.codex/plans/PLAN_<NAME>/spec.md`
- `.codex/pipeline/PLAN_<NAME>/00-create-spec.output.md`
- `.codex/pipeline/PLAN_<NAME>/00-create-spec.output.contract.json`

## Output contract expectations

- `skill = create-spec`
- `status = PASS | WAITING_USER`
- `artifacts.primary = .codex/plans/PLAN_<NAME>/spec.md`
- `next.recommended_skill = review-spec | null`
- `pending_questions.questions` phải có dữ liệu khi status = `WAITING_USER`
