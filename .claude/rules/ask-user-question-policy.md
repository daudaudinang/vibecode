---
alwaysApply: true
---

# AskUserQuestion — Decision Gate Policy

> Rule này áp dụng cho **tất cả LP commands** và mọi flow dùng `AskUserQuestion` (hoặc tương đương như `mcp__ide__showInputPrompt`, form prompt, interactive confirmation dialog).
> **`AskUserQuestion` là cổng quyết định — không phải UI mặc định cho mọi bước.**

---

## Nguyên tắc cốt lõi

**Default: pipeline tự chạy tiếp. Chỉ hỏi khi có quyết định thật sự cần user.**

```text
Đúng:  tự chạy tiếp → chỉ hỏi tại decision gate
Sai:   hỏi sau mỗi bước → biến pipeline thành chuỗi popup wizard
```

---

## Khi nào ĐƯỢC dùng `AskUserQuestion`

Chỉ bật khi đáp ứng ít nhất 1 trong các điều kiện sau:

| Điều kiện | Ví dụ |
|-----------|-------|
| **Có hơn 1 hướng hợp lý** và không thể tự quyết | Approach A (minimal) vs B (refactor sạch) |
| **Có rủi ro nếu tự quyết** | Thay đổi ảnh hưởng nhiều module, khó rollback |
| **Scope thay đổi** so với plan ban đầu | Cần sửa file ngoài Execution Boundary |
| **Có Blocker / Ambiguity** | Business rule chưa rõ, missing requirement |
| **Confirm hành động khó đảo ngược** | Delete, migrate data, thay đổi cấu trúc DB |
| **Mức fix cần user chọn** | Review xong: fix critical only / fix all? |

**Tiêu chí nhanh:** Nếu câu trả lời của mình dùng được và rủi ro thấp → tự chạy tiếp. Nếu có hơn 1 hướng hợp lý hoặc có rủi ro → hỏi.

---

## Khi nào CẤM dùng `AskUserQuestion`

| Tình huống | Lý do |
|-----------|-------|
| Sau **mọi bước** đều hỏi "làm tiếp gì?" | Vỡ flow, mỏi user, phá nhịp autopilot |
| Chỉ để báo tiến độ / status | Dùng text inline ngắn gọn |
| Câu hỏi hiển nhiên — kết quả không thay đổi flow | "Mình vừa đọc file xong, tiếp nhé?" |
| Xin phép những hành động agent đã được authorize | "Mình chạy test được không?" |
| Câu trả lời mở và cần nhiều context | Dùng conversational text thay vì form |

---

## Pattern đúng vs sai

### ✅ Pattern đúng

```text
[Bước hoàn thành]
→ text ngắn: kết quả + điểm chú ý
→ đề xuất next step rõ ràng
→ chỉ AskUserQuestion nếu gặp decision gate thật sự
```

Ví dụ:
> "Plan xong. Có 2 điểm cần chốt trước khi implement: ..."  
> `→ AskUserQuestion: Chọn approach A hay B?`

> "Implement xong phase 1. Tiếp theo: test + review."  
> *(không hỏi — tự chạy tiếp)*

> "Review xong. Có 3 lỗi critical. Fix luôn hay chỉ tổng hợp?"  
> `→ AskUserQuestion: Fix ngay / Chỉ report`

### ❌ Pattern sai

```text
Bước 1 xong → popup hỏi
Bước 2 xong → popup hỏi
Bước 3 xong → popup hỏi
```

---

## Rule theo từng stage trong LP pipeline

### `create-plan`

Hợp dùng `AskUserQuestion` khi discovery xong và có câu hỏi thật:
- Scope mức nào (minimal change / refactor sạch)?
- Có bao gồm test/docs không?
- Ưu tiên approach A hay B?

Không hỏi khi có thể suy ra từ codebase hoặc yêu cầu đã đủ rõ.

### `implement-plan`

Dùng **có chọn lọc**. Chỉ hỏi khi:
- Phát hiện ambiguity không thể tự resolve
- Có 2 cách fix tương đương, không tự quyết được
- Đụng file ngoài Execution Boundary — dừng và hỏi trước khi tiếp
- Hành động có blast radius lớn cần confirm

Không hỏi ở từng bước nhỏ trong implementation.

### `review-plan` / `review-implement`

Hợp dùng sau review để user chốt:
- Fix luôn hay chỉ output report?
- Fix critical only hay toàn bộ findings?
- Output dạng checklist hay patch-ready?

### `qa-automation`

Hỏi khi:
- Server chưa lên và cần user start
- Missing auth credentials sau khi đã lookup
- Mode `e2e-spec` cần install browser lớn

Không hỏi khi server đã up và AC đủ rõ.

### Sau mỗi bước pipeline

Ưu tiên text inline + đề xuất next step. Chỉ bật `AskUserQuestion` nếu cần chốt thật sự:

```text
✅ "Review xong. PASS. Tiếp: qa-automation. Chạy luôn?"
❌ "Review xong. Bước tiếp là gì?" ← không cần hỏi, tự quyết được
```

---

## Áp dụng vào WAITING_USER gate

Khi pipeline phải dừng ở `WAITING_USER`, orchestrator nên:
1. Tóm tắt ngắn: đã làm gì, tại sao dừng
2. Liệt kê rõ các lựa chọn (có đề xuất mặc định)
3. **Dùng `AskUserQuestion`** để user chọn nhanh — không dùng conversational text khi có form options

---

## Non-negotiable: đừng biến pipeline thành wizard

Cứ sau mỗi step popup lên hỏi là:
- phá nhịp autopilot của `/lp:cook`
- làm user mệt mỏi với UX hỏi liên tục
- giảm hiệu quả của toàn pipeline

Rule gốc: **pipeline tự chạy → dừng đúng gate → hỏi đúng điểm.**
