---
name: review-spec
description: Worker-only skill that reviews one canonical LP spec package (dual-mode: standard/fast) and returns validated findings for the orchestrator spec gate.
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

## Execution model: Dual-mode review

Orchestrator chọn review mode dựa trên review history trong workflow:

### Standard mode (lần review đầu tiên)

Spawn **4 agents độc lập**, mỗi agent giữ đúng 1 persona, chạy song song:

| Persona | Persona ID | Focus |
|---------|------------|-------|
| **Senior PM** | `senior_pm` | Business completeness, goal/scope clarity, testable ACs |
| **Senior UI/UX Designer** | `senior_uiux_designer` | UX flow completeness, UI states, friction/gap risk |
| **Senior Developer** | `senior_developer` | Technical feasibility, edge cases, validation rules |
| **System Architecture** | `system_architecture` | Integration points, dependency clarity, scalability |

Orchestrator validate evidence, normalize conflicts, tổng hợp verdict cuối.

### Fast mode (re-review trong loop)

**1 agent duy nhất chạy multi-persona** — đánh giá lần lượt từ 4 góc nhìn trong cùng 1 pass. Tập trung vào delta changes.

### Khi nào dùng mode nào?

- Chưa có lần review nào trước đó → **standard mode**
- Đã có ít nhất 1 lần review trước đó → **fast mode**
- Không được bỏ qua persona nào ở cả 2 modes

## Output

- `.codex/pipeline/PLAN_<NAME>/00-review-spec.output.md`
- `.codex/pipeline/PLAN_<NAME>/00-review-spec.output.contract.json`

## Contract status

- `PASS | NEEDS_REVISION | FAIL`
- `next.recommended_skill = create-plan | create-spec | null`
