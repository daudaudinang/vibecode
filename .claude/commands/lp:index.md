---
description: Canonical namespace index for LittlePea slash commands in Claude Code.
---

# /lp:index

## Canonical public commands

- `/lp:plan <requirement>`
- `/lp:implement <plan_file | plan_name | workflow_id>`
- `/lp:cook <requirement>`
- `/lp:debug-investigator <symptom>`

## Utility wrappers

- `/lp:qa-automation <AC_LIST_OR_TICKET>`
- `/lp:close-task <ticket_key>`
- `/lp:lesson-capture`
- `/lp:pipeline`

## Source of truth

- Orchestrator: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
- State backbone: `.claude/skills/lp-state-manager/SKILL.md`

## Worker aliases

Các command dưới đây chỉ là compatibility/deprecated wrappers:
- `/lp:create-plan`
- `/lp:review-plan`
- `/lp:implement-plan`

## Rules

- Ưu tiên dùng namespace `/lp:*` trong docs mới
- Không đặt orchestration logic đầy đủ trong command files
- Command files chỉ là thin wrappers; skill files mới là source of truth
- LP canonical flow dùng artifact layout dưới `.claude/plans/PLAN_<NAME>/` và `.claude/pipeline/PLAN_<NAME>/`
- Model state/artifact canonical là: plan-scoped top-level output paths + run-scoped identity trong state/contracts
- Canonical public commands: `/lp:plan`, `/lp:implement`, `/lp:cook`, `/lp:debug-investigator`
- Utility wrappers: `/lp:qa-automation`, `/lp:close-task`, `/lp:lesson-capture`, `/lp:pipeline`
- Non-canonical helper surfaces: `/lp:init-project`, `/lp:jira-workflow-bridge`
- Namespace placeholder chưa có project-scope skill thật: `/lp:sync-agents-context`
