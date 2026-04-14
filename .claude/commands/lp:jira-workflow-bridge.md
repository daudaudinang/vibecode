---
description: Compatibility wrapper for Jira-driven LP workflows.
---

# /lp:jira-workflow-bridge <issue_key_or_url>

## Status

Namespace placeholder. Chưa có project-scope skill implementation.

## Purpose

Dùng làm entrypoint khi context bắt đầu từ Jira issue và cần route sang LP workflow phù hợp.

## Notes

- Hiện project `.claude/skills/` chưa có skill `jira-workflow-bridge`
- File này giữ namespace ổn định để migration tiếp theo không vỡ command surface
- Khi cần implement đầy đủ, nên tạo canonical skill `.claude/skills/jira-workflow-bridge/SKILL.md`

## Typical targets

- `/lp:plan`
- `/lp:debug-investigator`
- `/lp:implement`
