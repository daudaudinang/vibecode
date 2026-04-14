---
description: Alias /lp:close-task -> close-task skill. Thin wrapper for task finalization workflow.
---

# /lp:close-task <ticket_key>

## Purpose

Đóng task theo workflow cuối: selective commit, transition ticket, worklog, và lesson capture nếu applicable.

## Source of truth

- `.claude/skills/close-task/SKILL.md`

## Notes

- Đây là LP namespace wrapper cho `close-task`
- Chỉ nên dùng khi implementation/review/QA đã xong và user muốn finalize task
