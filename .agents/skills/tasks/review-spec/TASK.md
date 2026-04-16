# TASK: Review Product/UX Specification

Bạn là **Spec Review Worker** được orchestrator spawn cho step `review-spec`.

## Input

- `spec_file`: `.codex/plans/PLAN_<NAME>/spec.md`
- `requirement`: requirement gốc từ workflow

## Output bắt buộc

1. `.codex/pipeline/<PLAN_NAME>/00-review-spec.output.md`
2. `.codex/pipeline/<PLAN_NAME>/00-review-spec.output.contract.json`

## Checklist bắt buộc

1. Business clarity
- mục tiêu, scope, non-goal rõ

2. Flow coverage
- có happy path
- có alternate path
- có edge/error paths

3. UI state coverage
- loading / empty / success / error + CTA rõ

4. Rules & validation
- business rules + validation rules + precedence rõ

5. AC testability
- AC dạng testable, không mơ hồ

## Verdict

- `PASS`: đủ các checklist, không blocker
- `NEEDS_REVISION`: còn major gap nhưng sửa được
- `FAIL`: blocker hoặc thiếu cấu trúc spec nghiêm trọng

## Contract JSON mẫu

```json
{
  "schema_version": 1,
  "skill": "review-spec",
  "plan": "<PLAN_NAME>",
  "status": "PASS",
  "timestamp": "<ISO8601>",
  "duration_min": 8,
  "artifacts": {
    "primary": ".codex/pipeline/<PLAN_NAME>/00-review-spec.output.md",
    "secondary": []
  },
  "next": {
    "recommended_skill": "create-plan",
    "input_for_next": ".codex/plans/<PLAN_NAME>/spec.md",
    "handoff_note": ""
  },
  "blockers": [],
  "pending_questions": {
    "questions": [],
    "resume_from": null,
    "user_answers": null
  },
  "review_summary": {
    "weighted_score": 8.5,
    "severity_counts": {
      "blocker": 0,
      "major": 0,
      "minor": 1
    }
  },
  "review_audit": {
    "triage_basis": "spec quality gate",
    "personas_requested": [
      "senior_pm",
      "senior_uiux_designer",
      "senior_developer",
      "system_architecture"
    ],
    "personas_run": [
      "senior_pm",
      "senior_uiux_designer",
      "senior_developer",
      "system_architecture"
    ],
    "persona_outputs": {
      "senior_pm": ".codex/pipeline/<PLAN_NAME>/00-review-spec.persona.senior-pm.md",
      "senior_uiux_designer": ".codex/pipeline/<PLAN_NAME>/00-review-spec.persona.senior-uiux.md",
      "senior_developer": ".codex/pipeline/<PLAN_NAME>/00-review-spec.persona.senior-dev.md",
      "system_architecture": ".codex/pipeline/<PLAN_NAME>/00-review-spec.persona.system-arch.md"
    },
    "persona_scores": {
      "senior_pm": 8.6,
      "senior_uiux_designer": 8.4,
      "senior_developer": 8.5,
      "system_architecture": 8.5
    }
  },
  "finding_validation": {
    "business_context_validated": true,
    "validated_findings": [],
    "unresolved_conflicts": []
  }
}
```
