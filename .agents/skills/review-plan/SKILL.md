---
name: review-plan
description: Worker-only skill that reviews one canonical LP plan package with 4 mandatory personas (dual-mode: standard/fast) and returns validated findings for the orchestrator gate.
---

# Review Plan — Worker Only

## Goal

Review 1 canonical LP plan để chặn plan mơ hồ, lệch nghiệp vụ, lệch UX intent, thiếu edge cases, hoặc tạo rủi ro kiến trúc trước khi implementation bắt đầu.

## Worker-only responsibility

- Chỉ làm step `review-plan`
- Không tự orchestration sang `implement-plan`
- Không tự approve plan ngoài contract verdict
- Không tự sửa plan
- Chỉ review plan package được giao và publish report + contract

## Canonical inputs

- `.codex/plans/PLAN_<NAME>/plan.md`
- `.codex/plans/PLAN_<NAME>/spec.md` nếu tồn tại
- `phase-XX-*.md` nếu có
- `.codex/plans/PLAN_<NAME>/manifests/ownership.json` nếu có
- `.codex/plans/PLAN_<NAME>/manifests/dependency-graph.json` nếu có

## Execution model: Dual-mode review

Orchestrator chọn review mode dựa trên review history trong workflow:

### Standard mode (lần review đầu tiên)

Spawn **4 agents độc lập**, mỗi agent giữ đúng 1 persona, chạy song song:

| Persona | Persona ID | Focus |
|---------|------------|-------|
| **Senior PM** | `senior_pm` | Business intent, AC completeness, clarity để implement không hiểu sai |
| **Senior UI/UX Designer** | `senior_uiux_designer` | UX flow, wording/UI intent, design consistency, friction risk |
| **Senior Developer** | `senior_developer` | Risks, edge cases, scope/file-path correctness, verify-command feasibility |
| **System Architecture** | `system_architecture` | Dependency logic, decomposition quality, coupling, scalability risk |

Orchestrator validate evidence, normalize conflicts, tổng hợp verdict cuối. Đảm bảo full independence, tránh anchoring/confirmation bias.

### Fast mode (re-review trong loop)

**1 agent duy nhất chạy multi-persona** — đánh giá lần lượt từ 4 góc nhìn trong cùng 1 pass.

- Tập trung vào **delta changes** so với review trước
- Đọc previous review output từ `.codex/pipeline/PLAN_<NAME>/` để biết findings cũ
- Nhanh hơn vì chỉ spawn 1 agent thay vì 4

### Khi nào dùng mode nào?

- Chưa có lần review nào trước đó trong workflow → **standard mode**
- Đã có ít nhất 1 lần review (`NEEDS_REVISION` hoặc `FAIL`) trước đó → **fast mode**
- Không được bỏ qua persona nào ở cả 2 modes

## Review focus

### Runtime model checks cho mọi plan

Luôn review thêm các câu hỏi này:
- plan có bám đúng requirement gốc không?
- execution boundary có rõ và dùng được không?
- review findings có đủ evidence để downstream implement/review không tranh cãi mơ hồ không?
- source-of-truth hierarchy có rõ giữa plan files, artifacts, DB state, và active-plan pointer không?
- runtime invariants có nhất quán giữa orchestrator doc, worker skills, plan text, và manifests không?
- nếu có drift giữa các artifact trên, review có chặn pass rõ ràng không?
- plan có mô tả rõ phase runtime enum lowercase (`pending | in_progress | waiting_user | completed | failed | cancelled`) khi bật Epic mode không?
- branch `dependency_critical = true` có behavior explicit `waiting_user` (không fallback tuyến tính) không?
- branch `broad_context_reports = true` có nêu rõ guard `phase-count <= 5` và ordering tăng dần không?

### Với standard plan

Phải check tối thiểu:
- context accuracy
- AC completeness
- execution boundary clarity
- implementation order logic
- risk coverage
- verify command feasibility

### Với parallel-ready plan

Ngoài các mục trên, phải check thêm:
- phase decomposition có hợp lý không
- ownership matrix có rõ và không overlap không
- dependency graph có hợp lệ không
- parallel groups có conflict risk không
- phase prerequisites có đủ để tránh race/conflict không

## Quantitative verdict model

- Mỗi persona chấm đúng 4 criteria cốt lõi, mỗi criteria `0..10`
- Điểm persona = trung bình 4 criteria
- Điểm tổng = weighted average:
  - `senior_developer`: 30%
  - `system_architecture`: 30%
  - `senior_pm`: 20%
  - `senior_uiux_designer`: 20%
- Machine status chỉ dùng: `PASS | NEEDS_REVISION | FAIL`

### Fail-fast gates

Phải `FAIL` hoặc reject contract ngay nếu có một trong các lỗi sau:
- thiếu bất kỳ mandatory persona nào trong output
- finding không có evidence tối thiểu
- thiếu business-context validation
- plan thiếu execution boundary rõ ràng
- findings conflict nhưng chưa normalize/xác thực xong mà vẫn chốt `PASS`

## Output expectations

Pipeline output:
- `.codex/pipeline/PLAN_<NAME>/02-review-plan.output.md`
- `.codex/pipeline/PLAN_<NAME>/02-review-plan.output.contract.json`

Contract phải support tối thiểu các field sau:
- `status = PASS | NEEDS_REVISION | FAIL`
- `findings`
- `blockers`
- `duration_min`
- `review_audit`
- `review_summary`
- `finding_validation`
- `next.recommended_skill = implement-plan | create-plan | null`

## Decision rules

- `PASS` khi đủ 4 persona, weighted score `>= 8.0`, không blocker, evidence đầy đủ, business context đã validate
- `NEEDS_REVISION` khi weighted score `6.0–7.9`, hoặc có Major, hoặc còn issue cần revise nhưng chưa tới mức fail nặng
- `FAIL` khi weighted score `< 6.0`, có Blocker, hoặc đụng fail-fast gates

## Constraints

- Không tự sửa plan ngoài phạm vi review step
- Không duplicate orchestration flow ở skill này
- Không assume parallel-ready là bắt buộc cho mọi task
- Không cho pass nếu ownership overlap hoặc dependency graph mâu thuẫn ở plan parallel-ready
- Không cho pass khi findings chưa được orchestrator-level validation chuẩn bị đủ trong contract

## Handoff

Orchestrator đọc contract đã validate để set `plan_reviewed`, quyết định `plan_approved`, hoặc quay lại planning loop / human gate.
