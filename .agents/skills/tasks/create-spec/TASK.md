# TASK: Create Product/UX Specification

Bạn là **Specification Worker** được orchestrator spawn cho step `create-spec`.

## Input

- `requirement`
- `plan_name` (PLAN_*)
- `workflow_id` (optional)

## Output bắt buộc

1. `.codex/plans/<PLAN_NAME>/spec.md`
2. `.codex/pipeline/<PLAN_NAME>/00-create-spec.output.md`
3. `.codex/pipeline/<PLAN_NAME>/00-create-spec.output.contract.json`

## Spec tối thiểu phải có

1. **Business Context**
- Goal
- In-scope / Out-of-scope
- Constraints

2. **User & UX Flows**
- Happy paths
- Alternate paths
- Edge/error paths

3. **UI State Expectations**
- Loading / empty / success / error cho từng flow chính
- CTA mong muốn cho từng trạng thái

4. **Rules & Validation**
- Business rules
- Validation rules
- Conflict/priority rules

5. **Acceptance Criteria (testable)**
- Given/When/Then
- Bao phủ cả happy path và edge cases

## Contract JSON mẫu

```json
{
  "schema_version": 1,
  "skill": "create-spec",
  "plan": "<PLAN_NAME>",
  "ticket": null,
  "status": "PASS",
  "timestamp": "<ISO8601>",
  "duration_min": 12,
  "artifacts": {
    "primary": ".codex/plans/<PLAN_NAME>/spec.md",
    "secondary": []
  },
  "next": {
    "recommended_skill": "review-spec",
    "input_for_next": ".codex/plans/<PLAN_NAME>/spec.md",
    "handoff_note": ""
  },
  "blockers": [],
  "pending_questions": {
    "questions": [],
    "resume_from": null,
    "user_answers": null
  }
}
```

## Rules

- Không dùng placeholder.
- Nếu còn ambiguity thật sự, dùng `WAITING_USER` + điền `pending_questions.questions`.
- Contract là source of truth cho sync state.
