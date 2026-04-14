---
description: Deprecated worker alias. Prefer /lp:plan for the canonical LP planning flow.
---

# /lp:create-plan <requirement>

## Status

Deprecated compatibility wrapper.

## Preferred command

```text
/lp:plan <requirement>
```

## Source of truth

- Worker skill: `.claude/skills/create-plan/SKILL.md`
- Canonical orchestration: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Notes

- Alias này chỉ gọi worker-level planning step
- Có thể bypass planning orchestration nếu dùng như public flow chính
- Chỉ nên dùng khi thật sự cần gọi trực tiếp worker `create-plan`
