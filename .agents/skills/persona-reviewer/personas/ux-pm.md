# Legacy Persona Mapping: ux-pm

> ⚠️ Legacy compatibility file.
> File này **không còn là source of truth canonical** cho review flow trong repo này.

## Canonical mapping

Legacy `ux-pm` tương ứng với canonical persona:
- `senior_uiux_designer`

## Canonical responsibility

`senior_uiux_designer` tập trung vào:
- user-flow clarity
- wording / UI intent clarity
- design consistency
- friction / regression risk

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

- `.agents/skills/review-plan/SKILL.md`
- `.agents/skills/review-implement/SKILL.md`
- `.agents/skills/tasks/review-plan/TASK.md`
- `.agents/skills/tasks/review-implement/TASK.md`
- `.agents/skills/lp-pipeline-orchestrator/SKILL.md`
- `.agents/skills/tasks/persona-review/TASK.md`

## Note

Nếu cần chạy 1 persona agent riêng, dùng persona ID canonical `senior_uiux_designer`, không dùng `ux-pm` trong flow review canonical mới.
