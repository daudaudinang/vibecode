# Architecture v2 — LittlePea `/lp:*` Orchestrator

> Updated: 2026-04-15  
> Canonical model: Main chat orchestrates, worker skills execute.

## Canonical entrypoints

Public LP namespace:

- `/lp:plan <requirement>`
- `/lp:implement <plan_file | plan_name | workflow_id>`
- `/lp:cook <requirement>`
- `/lp:debug-investigator <symptom>`

Utility wrappers:

- `/lp:qa-automation`
- `/lp:close-task`
- `/lp:lesson-capture`
- `/lp:pipeline`

Compatibility wrappers (non-canonical): `/lp-plan`, `/lp-implement`, `/lp-cook`.

## Source-of-truth hierarchy

1. `/home/runner/work/vibecode/vibecode/.claude/skills/lp-pipeline-orchestrator/SKILL.md`
2. `/home/runner/work/vibecode/vibecode/.claude/skills/lp-state-manager/SKILL.md`
3. `/home/runner/work/vibecode/vibecode/.claude/commands/lp:index.md`

Thin wrappers must defer to these files; they are not orchestration truth.

## Runtime model

### Main chat (orchestrator)

- Chooses next phase by workflow state.
- Calls worker skills via agent/tool execution.
- Syncs output contracts into pipeline state.
- Enforces gates (`WAITING_USER`, review/QA pass, boundary guards).

### Worker skills

- Produce phase output + machine-readable contract.
- Do not self-advance global orchestration state.

## Canonical artifact layout

```text
.claude/
  plans/
    PLAN_<NAME>/
      plan.md
      phase-01-*.md
      phase-02-*.md
      manifests/
        ownership.json
        dependency-graph.json
        benchmark.json
  pipeline/
    PLAN_<NAME>/
      01-create-plan.output.md
      01-create-plan.output.contract.json
      02-review-plan.output.md
      02-review-plan.output.contract.json
      03-implement-plan.output.md
      03-implement-plan.output.contract.json
      04-review-implement.output.md
      04-review-implement.output.contract.json
      05-qa-automation.output.md
      05-qa-automation.output.contract.json
```

`.claude/active-plan` may exist as a pointer to `.claude/plans/PLAN_<NAME>/`.

## Operational policies (current)

- Use `/lp:*` command notation in all new docs.
- Keep top-level LP phase execution in foreground agent runs.
- Do not assume auto-worktree isolation unless user explicitly requests it.
- Do not mark step `PASS` without valid published artifact/contract.
- Keep single primary controller for a plan at any given time.

## Example canonical flow (`/lp:plan`)

1. Main chat receives `/lp:plan <requirement>`
2. Orchestrator starts/loads workflow state
3. Spawn planner worker (`create-plan`)
4. Sync `01-create-plan.output.*`
5. Resolve next step (`review-plan`)
6. Spawn review workers/personas
7. Merge + validate findings at orchestrator
8. Sync `02-review-plan.output.*`
9. Pause at user gate for implementation decision

## Documentation anti-drift checklist

- [x] Canonical commands use `/lp:*` notation
- [x] `lp-pipeline-orchestrator` is documented as orchestration source of truth
- [x] `lp-state-manager` is documented as state backbone
- [x] Compatibility wrappers are marked non-canonical
- [x] Artifact layout matches current `.claude/plans` + `.claude/pipeline` model
