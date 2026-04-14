---
description: Deprecated worker alias. Prefer /lp:plan for the canonical LP reviewed-plan flow.
---

# /lp:review-plan <plan_file>

## Status

Deprecated compatibility wrapper.

## Preferred command

```text
/lp:plan <requirement>
```

## Source of truth

- Worker skill: `.claude/skills/review-plan/SKILL.md`
- Canonical orchestration: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Notes

- Alias này chỉ gọi worker-level review step
- Không phải public entrypoint canonical cho planning flow mới
- Chỉ nên dùng khi thật sự cần review trực tiếp một plan package
