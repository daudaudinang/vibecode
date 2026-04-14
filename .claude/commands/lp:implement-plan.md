---
description: Deprecated worker alias. Prefer /lp:implement for the canonical LP delivery loop.
---

# /lp:implement-plan <plan_file>

## Status

Deprecated compatibility wrapper.

## Preferred command

```text
/lp:implement <plan_file | plan_name | workflow_id>
```

## Source of truth

- Worker skill: `.claude/skills/implement-plan/SKILL.md`
- Canonical orchestration: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Notes

- Alias này chỉ gọi worker-level implement step
- Không enforce full delivery loop như command canonical
- Chỉ nên dùng khi thật sự cần direct worker execution
