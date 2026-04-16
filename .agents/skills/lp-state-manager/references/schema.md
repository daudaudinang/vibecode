# SQLite schema và command contract

Source of truth mặc định:

```text
.codex/state/pipeline_state.db
```

Notes:

- Default DB path được resolve thành `<repo-root>/.codex/state/pipeline_state.db`, không neo theo vị trí script.
- Repo root resolve theo thứ tự: `--repo-root` -> git root từ cwd hiện tại -> fail rõ ràng nếu không suy ra được.
- Vì vậy mỗi repo hoặc worktree có DB riêng nếu command chạy với đúng project root.
- First run sẽ tự tạo file DB và bootstrap schema khi script mở connection.
- Chỉ override `--db-path` khi debug/test hoặc migration có chủ đích; tránh trỏ nhiều project vào cùng một SQLite file.

## Schema layers

### V1 compatibility layer

- `workflows`
  - workflow shell theo orchestration hiện tại, gồm cả mode `debug`
- `workflow_steps`
  - trạng thái theo từng step/skill
- `workflow_gates`
  - các cờ gate như `plan_approved`
- `workflow_artifacts`
  - artifact registry theo `workflow_id`
- `workflow_events`
  - append-only event log theo workflow

### V2 runtime model layer

- `v2_plans`
  - identity của logical plan + canonical plan path + current primary run pointer
- `v2_primary_runs`
  - primary controller hiện hành cho mỗi plan, kèm lease/fencing metadata
- `v2_child_jobs`
  - child-job identity, idempotency key, artifact path, status/attempt
- `v2_run_events`
  - append-only events theo aggregate (`plan`, `primary_run`, `child_job`)

## V2 status model

### Plan status

- `DRAFT`
- `ACTIVE`
- `WAITING_USER`
- `COMPLETED`
- `FAILED`
- `BLOCKED`

### Primary run status

- `ACTIVE`
- `WAITING_USER`
- `COMPLETED`
- `FAILED`
- `BLOCKED`
- `SUPERSEDED`

### Child job status

- `PENDING`
- `RUNNING`
- `PASS`
- `FAIL`
- `NEEDS_REVISION`
- `WAITING_USER`
- `SKIPPED`

## Artifact layout v2

```text
.codex/plans/PLAN_<NAME>/
  plan.md
  phase-*.md
  manifests/

.codex/pipeline/PLAN_<NAME>/
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

Notes:

- Layout canonical hiện là plan-scoped cho top-level step outputs.
- `RUN_<WORKFLOW_ID>` vẫn giữ vai trò runtime identity trong state metadata/V2 tables.
- Artifact legacy hoặc child-job paths vẫn có thể chứa `RUN_<WORKFLOW_ID>` cho compatibility và runtime forensics, nhưng đó không còn là canonical top-level output root mặc định.

## Path and identity rules

- Artifact path phải là repo-relative, không được là absolute path.
- Artifact path không được escape repo root bằng `..`.
- Artifact path chỉ được nằm dưới một trong các root:
  - `.codex/plans/`
  - `.codex/pipeline/`
  - `.codex/state/`
- `plan_path` canonical: `.codex/plans/PLAN_<NAME>/plan.md`
- `run_id` canonical: `RUN_<WORKFLOW_ID>`
- `job_id` canonical: `JOB_<ID>`

## Lease / fencing defaults

- `lease_revision`: bắt đầu từ `1`
- `lease_ttl_seconds`: mặc định `900`
- `attempt_no`: mặc định `1`
- `idempotency_key`: required cho child jobs

## JSON shape của `get-workflow`

```json
{
  "schema_version": 2,
  "workflow_id": "WF_20260414_AB12CD34",
  "plan_name": "PLAN_MERCHANT_BULK_IMPORT",
  "mode": "plan",
  "status": "ACTIVE",
  "current_phase": "plan",
  "current_step": "create-plan",
  "metadata": {
    "current_primary_run_id": "RUN_WF_20260414_AB12CD34",
    "artifact_root": ".codex/pipeline/PLAN_MERCHANT_BULK_IMPORT",
    "plan_root": ".codex/plans/PLAN_MERCHANT_BULK_IMPORT"
  },
  "gates": {
    "plan_approved": false
  },
  "artifacts": {
    "final_plan_path": {
      "path": ".codex/plans/PLAN_MERCHANT_BULK_IMPORT/plan.md",
      "metadata": {}
    }
  },
  "steps": [
    {
      "order": 1,
      "skill": "create-plan",
      "status": "PASS",
      "output": ".codex/pipeline/PLAN_MERCHANT_BULK_IMPORT/01-create-plan.output.md"
    }
  ],
  "events": []
}
```

## Commands

- `create-workflow`
- `get-workflow`
- `find-workflows`
- `update-workflow`
- `upsert-step`
- `set-gate`
- `set-artifact`
- `append-event`
- `resolve-next`
- `validate-transition`

## Gợi ý dùng

- Agent orchestration chỉ nên gọi script với tham số rõ ràng
- Không cập nhật DB bằng SQL tay trừ khi đang debug script
- Nếu cần thay đổi schema, tăng `schema_version` trong script và thêm migration/reconcile logic
- Khi persist artifact path, luôn normalize/validate path trước khi ghi DB
- Ưu tiên dùng V2 tables cho plan/run/job semantics; V1 layer giữ vai trò compatibility + bridge trong giai đoạn migrate

## Mapping tối thiểu V1 → V2

- `workflows.plan_name` → `v2_plans.plan_id`, `v2_plans.plan_name`
- `workflows.workflow_id` → `v2_primary_runs.workflow_id`
- `RUN_<workflow_id>` → `v2_primary_runs.run_id`
- `workflow_steps.output` → `v2_child_jobs.artifact_path` khi step có output cụ thể
- `workflow_events` → `v2_run_events` aggregate `primary_run`
- `workflow_artifacts.final_plan_path` → `v2_plans.plan_path`

## Current limitation

- Runtime hiện đã có schema/layout v2 foundation trong state manager, nhưng orchestration layer khác vẫn cần follow-up phases để dùng đầy đủ `v2_primary_runs`, `v2_child_jobs`, và `v2_run_events` trong decision flow thực tế.
