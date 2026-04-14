# Legacy Persona Mapping: security

> ⚠️ Legacy compatibility file.
> File này **không còn là source of truth canonical** cho review flow trong repo này.

## Status

Legacy `security` **không thuộc canonical 4-agent roster** của `review-plan` / `review-implement` hiện tại.

Canonical roster hiện dùng:
- `senior_pm`
- `senior_uiux_designer`
- `senior_developer`
- `system_architecture`

## Why

Repo này đã chốt review canonical theo 4 persona ở chuẩn vibe-coding SSS hiện tại.
Security review có thể vẫn hữu ích ở một số ngữ cảnh riêng, nhưng không còn là persona bắt buộc trong canonical review flow mới.

## Canonical orchestration model

```text
Agent 1 → senior_pm
Agent 2 → senior_uiux_designer
Agent 3 → senior_developer
Agent 4 → system_architecture
→ wait for all
→ validate evidence
→ normalize conflicts
→ merge findings
→ final verdict
```

## Source of truth

- `.claude/skills/review-plan/SKILL.md`
- `.claude/skills/review-implement/SKILL.md`
- `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
- `.claude/skills/tasks/persona-review/TASK.md`

## Note

Không dùng `security` để override canonical roster của `review-plan` hoặc `review-implement`.
Nếu sau này cần security review riêng, nên coi đó là lane bổ sung/optional, không phải 1 trong 4 persona canonical hiện tại.
