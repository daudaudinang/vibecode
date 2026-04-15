# vibecode

Canonical workspace for the LittlePea (`/lp:*`) workflow on Claude Code.

## LittlePea in one screen

```text
Main chat orchestrator
→ spawn top-level worker agents
→ workers publish human report + machine contract
→ orchestrator syncs state/gates
→ orchestrator decides next step or stops at WAITING_USER
```

## What this repository contains

- `.claude/commands/`: slash command entrypoints
- `.claude/skills/`: orchestration + worker skills
- `.claude/ARCHITECTURE.md`: high-level architecture overview

## Canonical command surface

Use these commands as the public LP namespace:

- `/lp:plan <requirement>`
- `/lp:implement <plan_file | plan_name | workflow_id>`
- `/lp:cook <requirement>`
- `/lp:debug-investigator <symptom>`

Utility wrappers:

- `/lp:qa-automation <AC_LIST_OR_TICKET>`
- `/lp:close-task <ticket_key>`
- `/lp:lesson-capture`
- `/lp:pipeline`

## Runtime model

- Main chat = orchestrator
- Top-level LP workers = foreground agents trong current workspace
- Worker skills là worker-only; không tự orchestration sang step kế tiếp
- `review-plan` và `review-implement` dùng 4 persona bắt buộc
- Canonical top-level outputs publish vào `.claude/pipeline/PLAN_<NAME>/NN-step.output.*`
- `RUN_<WORKFLOW_ID>` vẫn tồn tại như runtime identity trong state/contracts, không phải canonical top-level output folder

## Source of truth

- Command index: `.claude/commands/lp:index.md`
- Orchestrator: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
- State backbone: `.claude/skills/lp-state-manager/SKILL.md`

## Documentation notes

- Prefer `/lp:*` notation in all new docs.
- Treat `/lp-plan`, `/lp-implement`, `/lp-cook` as compatibility wrappers only.
- `lp:index.md` is intentional; the `:` may look unusual, but it maps directly to the `/lp:*` command namespace.
- Artifact model canonical là: plan-scoped output paths + run-scoped identity trong state/contracts.
- `/lp:init-project` và `/lp:jira-workflow-bridge` là compatibility helpers có skill riêng, nhưng không phải source of truth cho orchestration.
- `/lp:sync-agents-context` hiện vẫn chỉ là namespace placeholder, không phải source of truth cho orchestration.
