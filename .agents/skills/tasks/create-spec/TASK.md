# TASK: Create Product/UX Specification

Bạn là **Specification Worker** được orchestrator spawn cho step `create-spec`.

## Input

- `requirement`
- `plan_name` (`PLAN_*`)
- `workflow_id` (optional)
- `ticket` (optional)

## Output bắt buộc

1. `.codex/plans/<PLAN_NAME>/spec.md`
2. `.codex/pipeline/<PLAN_NAME>/00-create-spec.output.md`
3. `.codex/pipeline/<PLAN_NAME>/00-create-spec.output.contract.json`

---

# Goal

Chuyển requirement thành spec có thể thực thi: rõ business intent, rõ UX flow, rõ happy/edge cases, rõ UI state expectations, và AC testable để `create-plan` bám theo không lệch.

---

# Instructions

> **QUY TRÌNH BẮT BUỘC (TOOL-FIRST / EVIDENCE-FIRST):**
> 1. Giữ reasoning ở nội bộ; reasoning literal không phải evidence.
> 2. Đọc requirement + artifacts liên quan thực tế trước khi viết spec.
> 3. **[DỪNG LẠI SAU KHI GỌI TOOL. NGHIÊM CẤM VIẾT SPEC NẾU CHƯA CÓ KẾT QUẢ TỪ TOOL]**.
> 4. Chỉ viết spec/report/contract sau khi đã có evidence phù hợp.

---

# Mandatory flow

## Phase 0 — Load context

Phải làm:
1. Xác định `PLAN_NAME`.
2. Đọc requirement gốc từ workflow input.
3. Nếu tồn tại, đọc các artifact ảnh hưởng trực tiếp:
   - spec cũ (`.codex/plans/<PLAN_NAME>/spec.md`)
   - plan cũ (`.codex/plans/<PLAN_NAME>/plan.md`)
   - docs liên quan feature.
4. Trích xuất unknowns quan trọng (nếu có).

## Phase 1 — Build spec baseline

Spec tối thiểu phải có:
1. **Business context**
- Goal
- In-scope
- Out-of-scope
- Constraints

2. **User & UX flows**
- Happy paths
- Alternate paths
- Edge/error paths

3. **UI state expectations**
- Loading / empty / success / error cho từng flow chính
- CTA mong muốn theo từng trạng thái

4. **Rules & validations**
- Business rules
- Validation rules
- Conflict / precedence rules

5. **Acceptance criteria (testable)**
- Given / When / Then
- Bao phủ happy path và edge cases chính

## Phase 2 — Ambiguity gate

Chỉ trả `WAITING_USER` khi còn **critical unknowns** không thể suy ra từ context hiện có.

Nếu `WAITING_USER`:
- `pending_questions.questions` phải có nội dung rõ và action-oriented
- `next.recommended_skill` phải là `null`
- Không được giả vờ `PASS`

Nếu đủ rõ để tiếp tục:
- trả `PASS`
- `next.recommended_skill = review-spec`

---

# Spec template (minimum)

```markdown
# SPEC: <PLAN_NAME>

## 1. Business Context
### 1.1 Goal
### 1.2 In-scope
### 1.3 Out-of-scope
### 1.4 Constraints

## 2. User & UX Flows
### 2.1 Happy Paths
### 2.2 Alternate Paths
### 2.3 Edge/Error Paths

## 3. UI State Expectations
### 3.1 Loading
### 3.2 Empty
### 3.3 Success
### 3.4 Error

## 4. Rules & Validation
### 4.1 Business Rules
### 4.2 Validation Rules
### 4.3 Rule Precedence

## 5. Acceptance Criteria (Given/When/Then)
```

---

# Contract JSON mẫu

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
    "secondary": [
      ".codex/pipeline/<PLAN_NAME>/00-create-spec.output.md"
    ]
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

---

# Rules

- Không dùng placeholder.
- Không tự approve spec/plan/implement.
- Contract là source of truth cho orchestrator sync state.
