---
description: Alias /lp:qa-automation -> qa-automation skill. Thin wrapper for LP-facing QA workflow.
---

# /lp:qa-automation <AC_LIST_OR_TICKET>

## Purpose

Chạy QA như một LP namespace wrapper khi cần verify AC độc lập hoặc chạy nghiệm thu rõ ràng ngoài delivery loop chính.

## Source of truth

- `.claude/skills/qa-automation/SKILL.md`
- Nếu QA được gọi trong LP delivery loop: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Notes

- Đây là LP namespace wrapper cho `qa-automation`
- Có thể dùng riêng khi user muốn chạy QA độc lập
- Trong canonical delivery loop, QA vẫn thường được gọi từ `/lp:implement` hoặc `/lp:cook`
- Không dùng tên `/lp:qa-auto`; command canonical là `/lp:qa-automation`
