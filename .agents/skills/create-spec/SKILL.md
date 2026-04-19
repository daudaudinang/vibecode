---
name: create-spec
description: Worker-only skill that creates one canonical LP spec package (business + UX flows + happy/edge case expectations) and returns machine-readable artifacts.
---

# Create Spec — Worker Only

> **Full task guide**: `.agents/skills/tasks/create-spec/TASK.md`

## Goal

Tạo 1 spec canonical cho LP để làm baseline bắt buộc cho `create-plan`, đảm bảo requirement rõ, UX flow rõ, happy path/edge cases và UI states đều testable.

## Worker-only responsibility

- Chỉ làm step `create-spec`
- Không tự orchestration sang `review-spec` hoặc `create-plan`
- Không tự approve spec/plan/implement
- Chỉ tạo spec artifact + machine contract cho step hiện tại

## Canonical inputs

- Requirement từ user hoặc workflow metadata
- Nếu có: artifacts liên quan feature hiện tại (`plan.md` cũ, docs hiện có, constraints kỹ thuật)
- Nếu có ambiguity thật sự: cho phép trả `WAITING_USER` với câu hỏi tập trung vào unknowns critical


## Canonical spec package

Spec phải bao phủ tối thiểu:
- Business context: goal, in-scope, out-of-scope, constraints
- User/UX flows: happy path, alternate path, edge/error path
- UI state expectations: loading/empty/success/error + CTA mong muốn theo từng flow chính
- Rules & validations: business rules, validation rules, precedence/conflict rules
- Acceptance criteria testable: Given/When/Then, bao phủ cả happy path và edge cases

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

## Constraints

- Không dùng placeholder / spec rỗng.
- Không tự set gate `spec_approved`.
- Không nhúng orchestration logic của pipeline vào worker này.

## Handoff

Orchestrator sẽ dùng contract để:
- sync artifact `spec.md`
- set gates (`spec_created`, `requirement_clarified`) theo status
- quyết định spawn `review-spec` hoặc dừng ở `WAITING_USER`
