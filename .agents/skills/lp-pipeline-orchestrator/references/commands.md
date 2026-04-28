# LP Pipeline Commands

> Scope: mọi `.codex/` path trong tài liệu này là path tương đối theo project root.

## Script

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py <command> ...
```

## Accessor contract (deterministic)

single-regression-check.command: python -c "import json;from pathlib import Path;plan='PLAN_V3_SINGLE_FIXTURE';root=Path('.codex/pipeline')/plan;root.mkdir(parents=True,exist_ok=True);tmp=Path('.codex/tmp');tmp.mkdir(parents=True,exist_ok=True);(tmp/'final-integration-single-plan.txt').write_text(plan+'\\n');steps=[('03-implement-plan','implement-plan'),('04-review-implement','review-implement'),('05-qa-automation','qa-automation')];[ (root/f'{step}.output.md').write_text('---\\nskill: '+skill+'\\nstatus: PASS\\n---\\n\\nSynthetic single fixture output.\\n') for step,skill in steps ];[ (root/f'{step}.output.contract.json').write_text(json.dumps({'schema_version':1,'skill':skill,'status':'PASS','artifacts':{'primary':str(root/f'{step}.output.md')}},indent=2)+'\\n') for step,skill in steps ];print('single-regression-fixture-ok',plan)"

degraded-design-drift-check.command: rg -n "\\.agents/plans/.*runtime|runtime.*\\.agents/plans/" .codex/AGENTS.md .agents/skills # reference-only drift detector

degraded-design-drift-check forbidden patterns (reference-only declaration): `\\.agents/plans/.*runtime` `runtime.*\\.agents/plans/`

Semantics note cho degraded drift accessor:
- Exit `0` = FAIL (phát hiện active runtime drift)
- Exit `1` = PASS (không phát hiện drift)
- Cấm đảo semantics bằng `-v`, `! rg`, `|| true`, hoặc tương đương.

## Operational guardrails

Trước khi gọi project-specific CLI:
1. Chạy `--help` nếu command/flags chưa verify trong repo hiện tại.
2. Verify DB path canonical trước command ghi state.
3. Với command ghi contract, verify validator/artifact schema trước khi sync state.

## Core commands

### `start-plan`

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-plan \
  --plan-name PLAN_EXAMPLE \
  --requirement "Create reviewed implementation plan"
```

### `start-spec`

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-spec \
  --plan-name PLAN_EXAMPLE \
  --requirement "Clarify business rules, UX flow, happy path, and edge cases"
```

### `start-implement`

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-implement \
  --plan-name PLAN_EXAMPLE \
  --plan-file .codex/plans/PLAN_EXAMPLE/plan.md
```

### `sync-output`

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py sync-output \
  --workflow-id WF_20260409_000001 \
  --output-file .codex/pipeline/PLAN_EXAMPLE/03-implement-plan.output.md \
  --contract-file .codex/pipeline/PLAN_EXAMPLE/03-implement-plan.output.contract.json
```

### `status` / `resume`

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py status --workflow-id WF_20260409_000001
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py resume --workflow-id WF_20260409_000001
```
