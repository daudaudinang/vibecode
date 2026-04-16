# vibecode

Canonical workspace for the LittlePea (`/lp:*`) workflow, with Codex-ready `.codex/` and `.agents/skills/` runtime layout.

## LittlePea in one screen

```text
Main chat orchestrator
→ spawn top-level worker agents
→ workers publish human report + machine contract
→ orchestrator syncs state/gates
→ orchestrator decides next step or stops at WAITING_USER
```

## What this repository contains

- `.codex/`: Codex config, AGENTS, custom agents, runtime artifacts
- `.agents/skills/`: orchestration + worker skills for Codex skill discovery
- `CODEX_GLOBAL_ARCHITECTURE.md`: Codex global structure and migration notes

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
- Canonical top-level outputs publish vào `.codex/pipeline/PLAN_<NAME>/NN-step.output.*`
- `RUN_<WORKFLOW_ID>` vẫn tồn tại như runtime identity trong state/contracts, không phải canonical top-level output folder

## Source of truth

- Global/runtime rules: `.codex/AGENTS.md`
- Orchestrator: `.agents/skills/lp-pipeline-orchestrator/SKILL.md`
- State backbone: `.agents/skills/lp-state-manager/SKILL.md`

## Global sync contract

- Sync `.codex/config.toml`, `.codex/AGENTS.md`, `.codex/agents/*.toml`, `.codex/scripts/*` into `~/.codex/`
- Sync reusable skills from `.agents/skills/*` into `~/.agents/skills/`
- Keep runtime artifacts in project scope: `<repo>/.codex/plans/`, `<repo>/.codex/pipeline/`, `<repo>/.codex/state/`
- Run LP commands from inside target git repo; global install does not change project-scoped runtime paths
- `agents/openai.yaml` is optional per skill, not required for baseline skill discovery

## Documentation notes

- Prefer `/lp:*` notation in all new docs.
- Treat `/lp-plan`, `/lp-implement`, `/lp-cook` as compatibility wrappers only.
- `lp:index.md` is intentional; the `:` may look unusual, but it maps directly to the `/lp:*` command namespace.
- Artifact model canonical là: plan-scoped output paths + run-scoped identity trong state/contracts.
- `/lp:init-project` và `/lp:jira-workflow-bridge` là compatibility helpers có skill riêng, nhưng không phải source of truth cho orchestration.
- `/lp:sync-agents-context` hiện vẫn chỉ là namespace placeholder, không phải source of truth cho orchestration.
