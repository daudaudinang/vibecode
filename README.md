# vibecode

Canonical workspace for the LittlePea (`/lp:*`) workflow on Claude Code.

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

## Source of truth

- Command index: `.claude/commands/lp:index.md`
- Orchestrator: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
- State backbone: `.claude/skills/lp-state-manager/SKILL.md`

## Documentation notes

- Prefer `/lp:*` notation in all new docs.
- Treat `lp-plan`, `lp-implement`, `lp-cook` as compatibility wrappers only.
