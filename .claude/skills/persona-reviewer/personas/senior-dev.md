# Legacy Persona Mapping: senior-dev

> ⚠️ Legacy compatibility file.
> File này **không còn là source of truth canonical** cho review flow trong repo này.

## Canonical mapping

Legacy `senior-dev` tương ứng với canonical persona:
- `senior_developer`

## Canonical responsibility

`senior_developer` tập trung vào:
- logic / implementation correctness
- test or verification evidence strength
- edge-case coverage
- boundary / touched-files correctness

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

Nếu cần chạy 1 persona agent riêng, dùng persona ID canonical `senior_developer`, không dùng `senior-dev` trong flow review canonical mới.
