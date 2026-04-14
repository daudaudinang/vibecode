# Legacy Persona Mapping: architect

> ⚠️ Legacy compatibility file.
> File này **không còn là source of truth canonical** cho review flow trong repo này.

## Canonical mapping

Legacy `architect` tương ứng với canonical persona:
- `system_architecture`

## Canonical responsibility

`system_architecture` tập trung vào:
- decomposition quality
- dependency logic
- coupling / maintainability risk
- scalability / long-term architecture risk

## Canonical orchestration model

Không dùng file này để định nghĩa review flow tổng.
Canonical flow là:

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
- `.claude/skills/tasks/review-plan/TASK.md`
- `.claude/skills/tasks/review-implement/TASK.md`
- `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
- `.claude/skills/tasks/persona-review/TASK.md`

## Note

Nếu cần chạy 1 persona agent riêng, dùng persona ID canonical `system_architecture`, không dùng `architect` trong flow review canonical mới.
