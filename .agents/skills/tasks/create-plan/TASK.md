# TASK: Create Implementation Plan

Bạn là **Planner Worker** được spawn bởi orchestrator (parent agent). Nhiệm vụ: sinh implementation plan chi tiết, actionable, đủ rõ để implement agent có thể thực hiện mà **không cần hỏi thêm** ngoài các quyết định thật sự còn mơ hồ sau khi đã khám phá codebase.

> Public LP entrypoint canonical là `/lp:plan`.
> Task này chạy ở chế độ worker-only planning.
> Alias note: `/lp:create-plan` chỉ là deprecated worker alias / compatibility wrapper.

## Input

- `requirement`: mô tả yêu cầu từ user
- `plan_name`: tên plan `PLAN_XXX` (có thể suy ra từ requirement)
- `workflow_id`: workflow ID để sync state (optional)
- `existing_plan`: path plan cũ nếu đang update (optional)

## Output

- Plan file: `.codex/plans/PLAN_<NAME>/plan.md`
- Machine contract: `.codex/pipeline/<PLAN_NAME>/01-create-plan.output.contract.json`
- Human report: `.codex/pipeline/<PLAN_NAME>/01-create-plan.output.md`

---

# Goal

Sinh implementation plan chi tiết, actionable, đủ rõ để implement agent có thể thực hiện mà **không cần hỏi thêm** ngoài các quyết định thật sự còn mơ hồ sau khi đã khám phá codebase.

---

# Instructions

> **QUY TRÌNH BẮT BUỘC (TOOL-FIRST / EVIDENCE-FIRST):**
> 1. Giữ reasoning ở nội bộ; reasoning literal không phải evidence.
> 2. Phải phân tích yêu cầu và định hình Tool calls cần gọi (`gitnexus_query`, `Read`, `Grep`, ...) trước khi kết luận.
> 3. **[DỪNG LẠI SAU KHI GỌI TOOL. NGHIÊM CẤM TỰ Ý TẠO PLAN NẾU CHƯA CÓ KẾT QUẢ TỪ TOOL QUẢN LÝ]**.
> 4. Chỉ được sinh plan hoặc hỏi user ở turn tiếp theo, sau khi Tool đã trả về log thành công.

---

# Mandatory flow

## Bước 0 — Khởi tạo

## 1. Resolve plan identity

1. Xác định `<FEATURE_NAME>` từ requirement.
2. Chuẩn hoá thành `PLAN_<FEATURE_NAME>` theo UPPERCASE + underscore.
3. Kiểm tra plan cũ tại `.codex/plans/PLAN_<FEATURE_NAME>/plan.md`.

## 2. Existing plan rules

- Nếu plan đã tồn tại:
  - hỏi user muốn **tạo mới** hay **cập nhật**
  - nếu tạo mới → archive plan cũ theo convention phù hợp
  - nếu cập nhật → áp dụng **Plan Versioning Protocol**
- Nếu chưa có → tiếp tục.

---

# S0.1 — Triage Complexity

| Tier | Tiêu chí | Workflow impact |
|------|----------|-----------------|
| **S** | `<= 3` files, 1 module, bug fix nhỏ, không cross-cutting | Plan rút gọn: mục tiêu + AC + boundary + test plan |
| **M** | 4–10 files, 2–3 modules, có edge cases | Plan đầy đủ, có thể bỏ sections không liên quan |
| **L** | `> 10` files, cross-cutting, nhiều dependencies | Plan đầy đủ + phase files |
| **P** | đủ lớn cho parallel hoặc user explicit yêu cầu parallel | plan đầy đủ + ownership + dependency graph + conflict notes |

Rules:
1. Ước lượng số files/modules bị ảnh hưởng.
2. Ghi Tier vào header plan.
3. Tier S có thể skip S3 nếu không còn câu hỏi thật sự.

---

# S0.5 — Ensure GitNexus Ready

1. Detect GitNexus config/capability trong runtime/session.
2. Nếu capability chưa sẵn sàng:
   - kiểm tra CLI/package
   - bootstrap/install/setup binding cần thiết
   - verify command cơ bản chạy được
3. Prepare index phù hợp (ví dụ `npx gitnexus analyze`) để repo queryable.
4. Verify repo usable cho query/context/impact.
5. Nếu verify pass → `HAS_GITNEXUS = true`.
6. Chỉ khi bootstrap/verify fail hoặc GitNexus không đủ thông tin → `HAS_GITNEXUS = false` và fallback `Grep` / `Read` / `Glob`.
7. Khi fallback phải nêu rõ **degraded mode** và lý do.
8. Không được bỏ qua GitNexus chỉ vì task nhỏ.

---

# S1 — Requirement intake

## Phải xác định

- loại yêu cầu: feature mới / cải tiến / bug fix / refactor
- goal: user muốn đạt gì
- non-goals: chưa làm gì ở phase này
- priority/deadline nếu user đề cập
- điểm còn mơ hồ nhưng **chưa hỏi ngay**

---

# S2 — Codebase discovery

> Đây là **cửa ải bắt buộc**. Không được viết plan hoặc hỏi user nếu chưa khám phá codebase thực tế.

## Discovery strategy

**Nếu `HAS_GITNEXUS = true`:**
- `gitnexus_query` để tìm execution flows
- `gitnexus_context` để xem callers / callees / imports / processes
- `gitnexus_impact` để xem blast radius
- `Read` khi cần xem implementation cụ thể

**Nếu `HAS_GITNEXUS = false`:**
- `Grep` cho keywords, definitions, callers
- `Glob` cho file patterns
- `Read` cho implementation chi tiết

## Phải làm

1. Tìm files/modules liên quan.
2. Đọc code có mục tiêu:
   - entrypoints
   - business logic
   - types/interfaces/schema
   - tests liên quan
3. Xác định patterns đang dùng:
   - naming / folder structure
   - state management
   - error handling
4. Xác định impacts:
   - files nào cần sửa/tạo
   - breaking changes
   - dependencies / side effects
5. Depth Check cho từng file chính:
   - callers / consumers
   - middleware / interceptors / hidden layers
   - existing tests

## Depth check format

```text
DEPTH CHECK:
- [file1]: 3 callers, 1 middleware, 2 tests
- [file2]: no callers, no tests
- Impact chain: file1 -> file3 -> file4
```

## Research persistence

- Nếu task phức tạp → có thể lưu research notes trong package plan
- Nếu task đơn giản → giữ trong context nhưng phải cite paths rõ ràng

---

# S3 — Question gate

Chỉ hỏi user sau khi đã discovery xong.

## Khi nào được hỏi

- quy tắc nghiệp vụ thiếu số liệu/quy ước cụ thể
- UX có nhiều cách hợp lý
- scope phase này chưa rõ
- kỹ thuật có nhiều trade-off thật sự và cần user chốt
- cần confirm giả định quan trọng không thể suy ra từ code

## Khi nào không được hỏi

- framework gì / file nào / pattern nào nếu đã tự đọc được
- bất kỳ điều gì có thể suy ra từ codebase hoặc docs đã verify

## Question rules

- nhóm theo chủ đề
- tối đa 5–7 câu mỗi lượt
- tối đa 2 lượt hỏi
- mỗi nhóm có: ngữ cảnh + câu hỏi + đề xuất mặc định
- ghi nhận câu trả lời và đánh dấu đã chốt trong plan

---

# S4 — Plan authoring

## Required sections by tier

| Section | Question it must answer | Required |
|---------|-------------------------|----------|
| Mục tiêu | Agent biết đang làm gì? | S/M/L |
| Acceptance Criteria | Xong là khi nào? Verify bằng gì? | S/M/L |
| Non-goals | Không làm gì ở phase này? | M/L |
| Bối cảnh | Code hiện tại ra sao? | M/L |
| Dependencies | Cần gì sẵn trước khi bắt đầu? | M/L |
| Yêu cầu nghiệp vụ | Con số/quy tắc cụ thể là gì? | M/L |
| Thiết kế | Cần tạo gì, ở đâu? | M/L, skip với S |
| Execution Boundary | Sửa gì, cấm sửa gì? | S/M/L |
| Test plan | Verify thế nào? | S/M/L |
| Decisions đã chốt | Điều gì không cần hỏi lại? | nếu có S3 |

## Internal review checklist trước khi lưu

- mọi AC đều SMART
- boundary rõ: Allowed + Do NOT Modify
- implementation order không mâu thuẫn dependency
- risks/edge cases đủ cover
- dependencies/prerequisites đủ rõ
- test plan hiện thực, không assert buggy behavior
- nếu update plan cũ → change log đã cập nhật
- đủ thông tin để implement mà không hỏi thêm ngoài unknowns hợp lệ

## Context sharding — chỉ Tier L/P

Nếu plan có `> 3` phases hoặc `> 300` dòng, chia nhỏ trong package plan canonical:

```text
.codex/plans/PLAN_<FEATURE>/
├── plan.md
├── phase-01-<name>.md
├── phase-02-<name>.md
└── phase-03-<name>.md
```

Mỗi phase file phải có:
- parent plan
- scope
- AC cụ thể cho phase
- dependencies
- execution boundary

## Naming rules

- plan file: `.codex/plans/PLAN_<FEATURE_NAME>/plan.md`
- research folder: `.codex/plans/PLAN_<FEATURE_NAME>/research/`
- phase files: `phase-XX-<name>.md`
- parallel-ready manifests: `manifests/ownership.json`, `manifests/dependency-graph.json`

---

# Plan Versioning Protocol

Áp dụng khi user yêu cầu cập nhật plan đã tồn tại.

1. Bump version:
   - minor change: `1.0 -> 1.1`
   - major scope change: `1.0 -> 2.0`
2. Cập nhật header với version + updated date.
3. Ghi Change Log cuối plan.
4. Đánh dấu AC thay đổi:
   - `[NEW]`
   - `[MODIFIED]`
   - moved to `Removed ACs` nếu xoá

---

# Constraints

## Quy trình

- không hỏi user ngay khi nhận yêu cầu; phải discovery trước
- không hỏi những gì có thể tự tìm từ code
- không quá 7 câu / lượt và không quá 2 lượt hỏi
- luôn nhóm câu hỏi theo chủ đề + có đề xuất mặc định
- nếu Phase 3 có hỏi thì phải ghi decisions đã chốt

## Chất lượng plan

- không viết plan sơ sài
- không bỏ qua Non-goals, AC, Test plan, Execution Boundary
- test phải assert **hành vi đúng/mong đợi**, không assert buggy behavior
- luôn cite file paths cụ thể
- luôn ghi file nào cần sửa/tạo trong Execution Boundary
- luôn liên kết với existing patterns trong codebase

## Recovery

- có research notes → đọc lại trong package plan
- có plan draft → tiếp tục từ draft
- không có gì → bắt đầu lại từ S1

---

# Planning Checklist

```markdown
## Checklist /lp:plan
- [ ] S0 Init: resolve feature/plan identity, check existing plan
- [ ] S0.1 Triage: classify Tier S/M/L/P
- [ ] S0.5 Ensure GitNexus: detect / bootstrap / verify / degraded fallback nếu cần
- [ ] S1 Requirement intake: parse goal / non-goals / open questions
- [ ] S2 Discovery: find files, patterns, impacts, depth check
- [ ] S3 Question gate: hỏi đúng chỗ, đúng nhóm, nếu còn ambiguity thật sự
- [ ] S4 Plan authoring: AC, boundary, risks, dependencies, test plan, decisions
- [ ] Context sharding nếu Tier L/P
- [ ] Save plan vào `.codex/plans/PLAN_<FEATURE_NAME>/plan.md`
```

---

## 📤 Output Contract

Khi hoàn thành task, **bắt buộc** ghi 2 files:

1. Human report: `.codex/pipeline/<PLAN_NAME>/01-create-plan.output.md`
2. Machine contract: `.codex/pipeline/<PLAN_NAME>/01-create-plan.output.contract.json`

**Source of truth cho state sync là file `.output.contract.json`.**

Human report markdown:

```yaml
---
skill: create-plan
plan: <PLAN_NAME>
ticket: <TICKET-KEY | null>
status: PASS | WAITING_USER
timestamp: <ISO8601>
duration_min: <số phút>
---

## Artifact
primary: .codex/plans/PLAN_<NAME>/plan.md
secondary: []

## Decision Summary
- Tier <S|M|L|P>: <X> phases, <Y> files changed
- Do NOT Modify list: <danh sách>
- Key risks: <risk chính>
- Architecture decisions chốt: <pattern đã chọn>

## Context Chain
- <file đã đọc 1>
- <file đã đọc 2>

## Next Step
recommended_skill: review-plan
input_for_next: .codex/plans/PLAN_<NAME>/plan.md
handoff_note: "<cảnh báo cho reviewer nếu có>"

## Blockers

## Pending Questions
questions:
  - "<câu hỏi 1>"
resume_from: "<step>"
user_answers: null
```

Machine contract JSON:

```json
{
  "schema_version": 1,
  "skill": "create-plan",
  "plan": "<PLAN_NAME>",
  "ticket": "<TICKET-KEY | null>",
  "status": "PASS | WAITING_USER",
  "timestamp": "<ISO8601>",
  "duration_min": 14,
  "artifacts": {
    "primary": ".codex/plans/PLAN_<NAME>/plan.md",
    "secondary": []
  },
  "next": {
    "recommended_skill": "review-plan",
    "input_for_next": ".codex/plans/PLAN_<NAME>/plan.md",
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

Sau khi ghi xong contract, báo orchestrator để sync state via orchestrator.

---

🚨 **CRITICAL DIRECTIVE (ĐỌC CUỐI CÙNG TRƯỚC KHI HÀNH ĐỘNG)** 🚨

1. Output plan bị coi là vô giá trị nếu trước đó bạn không thực hiện GitNexus / `Read` / `Grep` / `Glob` phù hợp để khám phá codebase.
2. Mọi path, symbol, scope, verify command trong plan phải khớp 100% với tool output thực tế.
3. Không được tự bịa plan, path, hay file references.