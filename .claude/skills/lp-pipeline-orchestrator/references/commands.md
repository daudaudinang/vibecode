# LP Pipeline Commands

## Script

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py <command> ...
```

## Contract validator

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/validate_contract.py \
  .claude/pipeline/PLAN_MERCHANT_BULK_IMPORT/01-create-plan.output.contract.json
```

## Commands

Root resolution policy:

- `--db-path` nếu user explicit truyền
- `--repo-root` nếu user explicit truyền
- fallback sang git root của cwd hiện tại
- nếu vẫn không suy ra được thì fail rõ ràng


### Workspace / writer policy

- Direct edit trong workspace hiện tại là mode canonical cho LP ở repo này.
- Không auto spawn agent trong worktree.
- Chỉ dùng worktree khi user explicit yêu cầu isolation bằng worktree.
- Top-level LP agents phải chạy foreground; **cấm** `run_in_background` cho `create-plan`, `review-plan`, `implement-plan`, `review-implement`, `qa-automation`, `debug-investigator`.
- `status` và `resume` phải surface rõ `workspace_policy` + `entry_decision`; không bắt main chat phải đoán writer authority.

### `start-plan`

Tạo workflow mới cho `/lp:plan`.

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-plan \
  --plan-name PLAN_MERCHANT_BULK_IMPORT \
  --requirement "Create reviewed plan for merchant bulk import"
```

### `start-cook`

Tạo workflow mới cho `/lp:cook`, đồng thời set gate `user_approved_implementation = true`.

### `start-debug`

Tạo workflow debug mới cho `/lp:debug-investigator`.

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-debug \
  --plan-name DEBUG_CHECKOUT_TIMEOUT \
  --requirement "Checkout timeout when creating payment session"
```

### `start-implement`

Chuẩn bị workflow đã approved để chạy delivery loop từ `implement-plan`.

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-implement \
  --plan-name PLAN_MERCHANT_BULK_IMPORT \
  --plan-file .claude/plans/PLAN_MERCHANT_BULK_IMPORT/plan.md
```

### `start-followup`

Khởi chạy các bước follow-up trong delivery loop với transition guard.

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-followup \
  --workflow-id WF_20260409_000001 \
  --step review-implement
```

### `sync-output`

Ưu tiên đọc machine contract JSON; fallback sang markdown frontmatter nếu chưa có JSON.

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py sync-output \
  --workflow-id WF_20260409_000001 \
  --output-file .claude/pipeline/PLAN_MERCHANT_BULK_IMPORT/01-create-plan.output.md \
  --contract-file .claude/pipeline/PLAN_MERCHANT_BULK_IMPORT/01-create-plan.output.contract.json \
  --plan-file .claude/plans/PLAN_MERCHANT_BULK_IMPORT/plan.md
```

### `next`

Xem bước kế tiếp.

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py next \
  --workflow-id WF_20260409_000001
```

### `status`

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py status \
  --workflow-id WF_20260409_000001 \
  --include-events
```

### `resume`

```bash
python .claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py resume \
  --workflow-id WF_20260409_000001
```

`resume` phải trả về tối thiểu:
- `entry_decision`: quyết định deterministic cho conversation hiện tại (`resume-existing-run`, `inspect-only-or-explicit-takeover`, ...)
- `workspace_policy`: direct-edit canonical, worktree không auto dùng
- `workspace_warning`: cảnh báo collision nếu cùng `plan_name` trong một workspace

## Delivery loop usage

Sau mỗi lần sync output, gọi `resume` hoặc `status` để biết bước loop tiếp theo. Delivery loop mặc định là:

- `implement-plan`
- `review-implement`
- quay lại `implement-plan` nếu review yêu cầu sửa
- `qa-automation`
- quay lại `implement-plan` nếu QA fail
- `close-task` khi QA PASS

`delivery_next` trong output của `status` / `resume` là nguồn khuyến nghị chính cho main chat.
