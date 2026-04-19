---
name: review-implement
description: Review implemented code with 4 mandatory personas (dual-mode: standard/fast), validated evidence, and strict orchestrator-ready machine verdicts.
---

# Review Implement

> **Full task guide**: `.agents/skills/tasks/review-implement/TASK.md`

## Usage

```
/review-implement <plan_file_path>
```

## What It Does

1. **Boundary Check** — Verify no `Do NOT Modify` files were changed
2. **Implementation Coverage Check** — Verify delivered code still matches spec baseline + plan ACs
3. **Multi-Persona Code Review** — Review từ 4 góc nhìn bắt buộc trong 1 pass
4. **Finding Validation** — Chỉ findings có evidence + context validation mới được dùng cho verdict
5. **Scoring & Findings** — Chấm điểm định lượng và xuất machine status chuẩn

## Execution model: Dual-mode review

Orchestrator chọn review mode dựa trên review history trong workflow:

### Standard mode (lần review đầu tiên)

Spawn **4 agents độc lập**, mỗi agent giữ đúng 1 persona, chạy song song:

| Persona | Persona ID | Focus |
|---------|------------|-------|
| **Senior PM** | `senior_pm` | Feature completeness, business scope adherence, missing requirements |
| **Senior UI/UX Designer** | `senior_uiux_designer` | UX fidelity so với plan, clarity, consistency, regression risk |
| **Senior Developer** | `senior_developer` | Logic correctness, tests/evidence, edge cases, touched-files/scope violations |
| **System Architecture** | `system_architecture` | Coupling, architecture impact, maintainability, technical-debt risk |

Orchestrator validate evidence, normalize conflicts, tổng hợp verdict cuối.

### Fast mode (re-review trong loop)

**1 agent duy nhất chạy multi-persona** — đánh giá lần lượt từ 4 góc nhìn trong cùng 1 pass.

- Tập trung vào **delta changes** so với review trước
- Đọc previous review output từ `.codex/pipeline/PLAN_<NAME>/` để biết findings cũ
- Nhanh hơn vì chỉ spawn 1 agent thay vì 4

### Khi nào dùng mode nào?

- Chưa có lần review nào trước đó trong workflow → **standard mode**
- Đã có ít nhất 1 lần review (`NEEDS_REVISION` hoặc `FAIL`) trước đó → **fast mode**
- Không được bỏ qua persona nào ở cả 2 modes

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
- thiếu bất kỳ mandatory persona nào trong output
- finding không có evidence tối thiểu
- thiếu business-context validation
- có `Do NOT Modify` scope violation
- findings conflict nhưng chưa normalize/xác thực xong mà vẫn chốt `PASS`

## Output

- Review report: `.codex/pipeline/<PLAN_NAME>/04-review-implement.output.md`
- Output contract: `.codex/pipeline/<PLAN_NAME>/04-review-implement.output.contract.json`

## Orchestrator Reference

When Orchestrator receives `/review-implement`, orchestrator phải coi đây là worker review step canonical.

Mandatory roster:
- Task file: `.agents/skills/tasks/review-implement/TASK.md`
- Personas bắt buộc: `senior_pm`, `senior_uiux_designer`, `senior_developer`, `system_architecture`

Decision authority:
- Orchestrator vẫn giữ quyền quyết định cách spawn chi tiết.
- Nhưng canonical flow không được bỏ qua persona nào trong 4 persona bắt buộc.
- Nếu LP top-level flow gọi review step này, worker phải chạy qua agent trong current workspace theo policy của `lp-pipeline-orchestrator`, không mặc định isolate bằng worktree.

## Notes

- Skill này mô tả canonical review model cho `review-implement`, không phải roster gợi ý mềm.
- Source of truth cho top-level LP spawn policy vẫn là `.agents/skills/lp-pipeline-orchestrator/SKILL.md`.
- Human report có thể dùng wording dễ đọc, nhưng machine source of truth chỉ là `PASS | NEEDS_REVISION | FAIL`.
