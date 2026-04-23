# TASK: Review Product/UX Specification

Bạn là **Spec Review Worker** được orchestrator spawn cho step `review-spec`.

## Input

- `spec_file`: `.codex/plans/PLAN_<NAME>/spec.md`
- `requirement`: requirement gốc từ workflow
- `workflow_id` (optional)

## Output bắt buộc

1. `.codex/pipeline/<PLAN_NAME>/00-review-spec.output.md`
2. `.codex/pipeline/<PLAN_NAME>/00-review-spec.output.contract.json`

---

# Goal

Đánh giá spec như một quality gate trước planning: spec phải rõ business intent, đủ flow/happy/edge coverage, có UI state expectations rõ và AC testable để giảm lệch khi vào `create-plan`/`implement-plan`.

---

# Instructions

> **QUY TRÌNH BẮT BUỘC (TOOL-FIRST / EVIDENCE-FIRST):**
> 1. Giữ reasoning ở nội bộ; reasoning literal không phải evidence.
> 2. Phải đọc spec + context liên quan bằng tool trước khi kết luận.
> 3. **[DỪNG LẠI SAU KHI GỌI TOOL. NGHIÊM CẤM TỰ TẠO FINDINGS/SCORE/VERDICT NẾU CHƯA CÓ TOOL RESULT]**.
> 4. Chỉ chốt findings/score/verdict ở turn tiếp theo sau khi có evidence.

---

# Non-negotiable review model

## A. Mandatory personas

Canonical `review-spec` **phải chạy đủ 4 persona**:

| Persona | Persona ID | Focus |
|---------|------------|-------|
| Senior PM | `senior_pm` | business intent, scope clarity, AC completeness |
| Senior UI/UX Designer | `senior_uiux_designer` | user flow clarity, UI state expectations, friction risk |
| Senior Developer | `senior_developer` | edge/error coverage, validation logic, testability |
| System Architecture | `system_architecture` | rule coupling, dependency assumptions, maintainability risk |

Rules:
- Không bỏ qua persona nào.
- Canonical execution model: **Dual-mode review**:
  - **Standard mode** (lần đầu): 4 agents độc lập, mỗi agent 1 persona, chạy song song → orchestrator tổng hợp verdict theo **Standard Mode Merge Protocol** trong `lp-pipeline-orchestrator/SKILL.md`.
  - **Fast mode** (re-review trong loop): 1 agent duy nhất chạy multi-persona, tập trung delta changes.
- Orchestrator chọn mode dựa trên review history. Nếu chưa có review trước → standard. Đã có → fast.
- Contract cuối phải thể hiện đủ `personas_requested` và `personas_run`.

## B. Machine statuses duy nhất

Chỉ dùng:
- `PASS`
- `NEEDS_REVISION`
- `FAIL`

## C. Review-only worker

- Chỉ review.
- Không tự sửa spec.
- Không tự orchestration sang step khác (ngoài recommendation trong contract).

---

# Mandatory process

## Phase 0 — Load and normalize context

Phải làm:
1. Đọc `spec_file`.
2. Đối chiếu requirement gốc.
3. Nếu có, đọc context bổ sung (plan cũ/docs liên quan) để xác thực business intent.

## Phase 1 — Structural quality checks

Checklist bắt buộc:
1. **Business clarity**: goal/scope/non-goal/constraints rõ.
2. **Flow coverage**: có happy + alternate + edge/error paths.
3. **UI state coverage**: loading/empty/success/error + CTA rõ cho flow chính.
4. **Rules & validation**: business rules + validation + precedence rõ.
5. **AC testability**: AC không mơ hồ, đo được bằng Given/When/Then.

## Phase 2 — Persona scoring

Mỗi persona chấm 4 criteria, mỗi criteria `0..10`.

| Persona | Criteria |
|---------|----------|
| Senior PM | requirement fidelity, scope clarity, AC completeness, business value clarity |
| Senior UI/UX Designer | flow clarity, UI state clarity, wording/intent consistency, friction risk |
| Senior Developer | edge/error completeness, validation consistency, AC testability, ambiguity risk |
| System Architecture | rule coupling risk, dependency assumptions, extensibility risk, maintainability |

## Phase 3 — Finding validation

Mỗi finding dùng cho verdict phải có:
- `evidence` cụ thể (spec section/path hoặc artifact reference)
- `business_context_validation`
- `validation_status`

Nếu còn `needs_human_confirmation` hoặc unresolved conflict:
- Không được chốt `PASS`.

## Phase 4 — Decision rules

| Verdict | Điều kiện |
|---------|-----------|
| `PASS` | đủ 4 persona, không blocker, findings cho verdict đều validated |
| `NEEDS_REVISION` | có major gaps nhưng sửa được |
| `FAIL` | blocker hoặc thiếu cấu trúc spec nghiêm trọng |

---

# Contract JSON mẫu

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
      "minor": 1,
      "info": 0
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
