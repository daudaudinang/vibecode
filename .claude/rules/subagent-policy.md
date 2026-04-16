---
alwaysApply: true
---

# Subagent Usage Policy — LP/Vibecode Project Override

> Rule này **override global `subagent-policy.md`** cho repo này.
> Global rule: ưu tiên main conversation. Project override: giữ nguyên — nhưng thêm exception bắt buộc cho `/lp:*`.

---

## LP Pipeline: Bắt buộc dùng agent

Trong canonical `/lp:*` workflows, **bắt buộc** spawn worker agents theo flow:

| Command | Worker bắt buộc dùng agent |
|---------|---------------------------|
| `/lp:plan` | `create-plan`, `review-plan` |
| `/lp:implement` | `implement-plan`, `review-implement`, `qa-automation` |
| `/lp:cook` | Toàn bộ pipeline |
| `/lp:debug-investigator` | `debug-investigator` |

> Main chat là **orchestrator**, không tự làm thay worker. Chi tiết: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

---

## Ngoài LP Pipeline: Cực kỳ tiết chế

Ngoài `/lp:*` flow, áp dụng policy nghiêm hơn global:

```text
Default ngoài LP → main chat + tools trực tiếp
KHÔNG spawn subagent trừ khi lợi ích rõ ràng và không thể thay thế
```

**Cấm spawn khi:**
- Task có thể làm trong main conversation trong < 5 bước tool
- Chỉ đọc/sửa file đã biết path
- Hỏi đáp, review, explain, một lần chỉnh sửa nhỏ
- Không chắc có nên spawn không

**Cho phép spawn khi:**
- Parallel research thật sự cần độc lập
- Codebase exploration rộng (>10 files, nhiều vòng search)
- Task rõ ràng hưởng lợi từ isolated context

---

## Tổng hợp

| Bối cảnh | Rule |
|----------|------|
| `/lp:*` canonical step | **Bắt buộc agent** |
| `/lp:*` orchestrator gate | **Main chat** |
| Ngoài LP — task nhỏ/rõ | **Main chat** (cấm spawn) |
| Ngoài LP — parallel lớn | **Có thể spawn** |
| Ngoài LP — không chắc | **Main chat** |

---

## Kết nối với các rule khác

- `ask-user-question-policy.md` — nếu cần user chốt nhanh ngoài LP: main chat + AskUserQuestion, không spawn agent
- `lp-pipeline-orchestrator/SKILL.md` — chi tiết về khi nào orchestrator spawn worker
