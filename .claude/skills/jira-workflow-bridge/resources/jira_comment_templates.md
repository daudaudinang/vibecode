# Jira Comment Templates — LP Write-Back

Templates cho comments ghi ngược về Jira sau khi helper này handoff hoặc sau khi LP workflow hoàn thành.

---

## 1. Sau khi `/lp:plan` hoàn thành

```markdown
🤖 **LP Agent — Plan Created**

📋 **Plan:** `PLAN_<NAME>`
📍 **Location:** `.claude/plans/PLAN_<NAME>/plan.md`

**Tóm tắt:**
- **Scope:** [N] phases, [M] tasks
- **Files ảnh hưởng:** [top files nếu có]

---
⏩ **Next:** Review artifact trong `.claude/pipeline/PLAN_<NAME>/01-create-plan.output.md`, sau đó tiếp tục LP delivery flow khi phù hợp.
```

---

## 2. Sau khi `/lp:debug-investigator` hoàn thành

```markdown
🤖 **LP Agent — Debug Investigation Complete**

🔍 **Root Cause (Confidence: [X]%)**
- [Tóm tắt nguyên nhân]
- **Location:** `[file:line]`

**Suggested Next Step:**
- Nếu cần fix có scope rõ ràng: chạy `/lp:plan <fix-scope>`

📄 **Report:** `[debug artifact path nếu có]`
```

---

## 3. Sau khi `/lp:implement` hoàn thành một delivery loop hoặc phase đáng kể

```markdown
🤖 **LP Agent — Implementation Update**

✅ **Trạng thái:** [PASS / NEEDS_REVISION / FAIL]

**Artifacts:**
- `.claude/pipeline/PLAN_<NAME>/03-implement-plan.output.md`
- `.claude/pipeline/PLAN_<NAME>/04-review-implement.output.md`
- `.claude/pipeline/PLAN_<NAME>/05-qa-automation.output.md`

**Notes:**
- [Tóm tắt ngắn về tiến độ hoặc blocker]
```

---

## 4. Khi bắt đầu làm việc

```markdown
🤖 **LP Agent — Starting Work**

- **Workflow:** `/lp:plan` | `/lp:debug-investigator` | `/lp:implement`
- **Started at:** [timestamp]
```

---

## 5. Khi cần user input

```markdown
🤖 **LP Agent — Cần Input**

**Vấn đề:**
- [Mô tả ngắn]

**Cần xác nhận:**
1. [Câu hỏi 1]
2. [Câu hỏi 2]
```

---

## 6. Khi Jira context thiếu thông tin

```markdown
🤖 **LP Agent — Cần Bổ Sung Thông Tin**

**Thiếu:**
- [Acceptance Criteria / reproduce steps / scope / business rules]

**Gợi ý:**
- Bổ sung trực tiếp trên Jira, hoặc
- mô tả thêm trong IDE chat

Template tham chiếu: `.claude/skills/jira-workflow-bridge/resources/jira_task_templates.md`
```

---

## Quy tắc viết comment

1. Ưu tiên nhắc LP canonical commands: `/lp:plan`, `/lp:debug-investigator`, `/lp:implement`
2. Ưu tiên nhắc `.claude/*` artifact paths
3. Không gợi ý `.agent/*`, `.agents/*`, `/review-plan`, `/review-implement` như public next step mặc định
4. Không paste code dài vào comment
5. Không tự transition issue nếu user chưa yêu cầu
