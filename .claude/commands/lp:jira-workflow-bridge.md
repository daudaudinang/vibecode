---
description: Compatibility wrapper for Jira-driven LP workflows.
---

# /lp:jira-workflow-bridge <issue_key_or_url>

## Status

Compatibility wrapper. Project đã có skill `jira-workflow-bridge`, nhưng flow này không thuộc LP canonical orchestrator.

## Purpose

Dùng làm entrypoint khi context bắt đầu từ Jira issue và cần route sang LP workflow canonical phù hợp.

## Notes

- Source of truth cho hành vi wrapper này nằm ở `.claude/skills/jira-workflow-bridge/SKILL.md`
- File này giữ command surface ổn định cho Jira intake/router; nó không phải canonical implemented workflow và không phải source of truth cho orchestration/state
- Wrapper này phải handoff sang `/lp:*` canonical commands, không tự trở thành alternative orchestrator

## Typical targets

- `/lp:plan`
- `/lp:debug-investigator`
- `/lp:implement`
