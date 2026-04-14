---
name: review-implement
description: Review implemented code with 4 mandatory personas, validated evidence, and strict orchestrator-ready machine verdicts.
---

# Review Implement

> **Full task guide**: `.claude/skills/tasks/review-implement/TASK.md`

## Usage

```
/review-implement <plan_file_path>
```

## What It Does

1. **Boundary Check** — Verify no `Do NOT Modify` files were changed
2. **Implementation Coverage Check** — Verify delivered code still matches business scope + plan ACs
3. **4-Persona Code Review** — Parallel review từ 4 góc nhìn bắt buộc
4. **Finding Validation** — Chỉ findings có evidence + context validation mới được dùng cho verdict
5. **Scoring & Findings** — Chấm điểm định lượng và xuất machine status chuẩn

## Mandatory persona model

Canonical `review-implement` bắt buộc spawn **4 agents độc lập**, mỗi agent giữ đúng 1 persona, chạy **song song** rồi mới được orchestrator tổng hợp:

| Persona | Persona ID | Focus |
|---------|------------|-------|
| **Senior PM** | `senior_pm` | Feature completeness, business scope adherence, missing requirements |
| **Senior UI/UX Designer** | `senior_uiux_designer` | UX fidelity so với plan, clarity, consistency, regression risk |
| **Senior Developer** | `senior_developer` | Logic correctness, tests/evidence, edge cases, touched-files/scope violations |
| **System Architecture** | `system_architecture` | Coupling, architecture impact, maintainability, technical-debt risk |

Không được bỏ qua persona nào trong canonical flow.

## Quantitative verdict model

- Mỗi persona chấm đúng 4 criteria cốt lõi, mỗi criteria `0..10`
- Điểm persona = trung bình 4 criteria
- Điểm tổng = weighted average:
  - `senior_developer`: 30%
  - `system_architecture`: 30%
  - `senior_pm`: 20%
  - `senior_uiux_designer`: 20%
- Machine status chỉ dùng: `PASS | NEEDS_REVISION | FAIL`

## Fail-fast gates

Phải `FAIL` hoặc reject contract ngay nếu có một trong các lỗi sau:
- thiếu bất kỳ mandatory persona nào
- finding không có evidence tối thiểu
- thiếu business-context validation
- có `Do NOT Modify` scope violation
- findings conflict nhưng chưa normalize/xác thực xong mà vẫn chốt `PASS`

## Output

- Review report: `.claude/pipeline/<PLAN_NAME>/04-review-implement.output.md`
- Output contract: `.claude/pipeline/<PLAN_NAME>/04-review-implement.output.contract.json`

## Main Chat Reference

When Main Chat receives `/review-implement`, orchestrator phải coi đây là worker review step canonical.

Mandatory roster:
- Task file: `.claude/skills/tasks/review-implement/TASK.md`
- Personas bắt buộc: `senior_pm`, `senior_uiux_designer`, `senior_developer`, `system_architecture`

Decision authority:
- Orchestrator vẫn giữ quyền quyết định cách spawn chi tiết.
- Nhưng canonical flow không được bỏ qua persona nào trong 4 persona bắt buộc.
- Nếu LP top-level flow gọi review step này, worker phải chạy qua agent trong current workspace theo policy của `lp-pipeline-orchestrator`, không mặc định isolate bằng worktree.

## Notes

- Skill này mô tả canonical review model cho `review-implement`, không phải roster gợi ý mềm.
- Source of truth cho top-level LP spawn policy vẫn là `.claude/skills/lp-pipeline-orchestrator/SKILL.md`.
- Human report có thể dùng wording dễ đọc, nhưng machine source of truth chỉ là `PASS | NEEDS_REVISION | FAIL`.