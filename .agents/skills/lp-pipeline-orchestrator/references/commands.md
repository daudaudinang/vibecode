# LP Pipeline Commands

> **⚠️ Scope quan trọng:** Tất cả lệnh trong file này dùng `.codex/` là path tương đối với **project root**.
> - Luôn chạy từ bên trong project directory (nơi có `.git/` và `.codex/config.toml`).
> - Scripts tự detect project root qua `git rev-parse --show-toplevel` — không dùng cwd mơ hồ.
> - State DB, plans, pipeline artifacts lưu trong **project scope**; không bao giờ lưu lên `~/.codex/`.
> - Nếu chạy ngoài project dir, script sẽ fail rõ ràng (không silently dùng global path).

## Script

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py <command> ...
```

> Nếu repo có local mirror để dev skill thì local path có thể tồn tại, nhưng canonical global-ready invocation vẫn là `~/.agents/skills/...`.

## Contract validator

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/validate_contract.py \
  .codex/pipeline/PLAN_MERCHANT_BULK_IMPORT/01-create-plan.output.contract.json
```

## Commands

Root resolution policy:

- `--db-path` nếu user explicit truyền
- `--repo-root` nếu user explicit truyền
- fallback sang git root của cwd hiện tại
- nếu vẫn không suy ra được thì fail rõ ràng

## Operational guardrails

Before calling any project-specific CLI:
1. Run `--help` nếu command/flags chưa được verify trong chính repo hiện tại.
2. Nếu command ghi state, verify rõ DB path canonical trước khi gọi.
3. Nếu command ghi contract, đọc validator hoặc passing artifact mẫu trước khi gọi.
4. Nếu skill path có thể mơ hồ, resolve `.codex/config.toml` trước rồi mới thao tác.

### Workspace / writer policy

- Direct edit trong workspace hiện tại là mode canonical cho LP ở repo này.
- Không auto spawn agent trong worktree.
- Chỉ dùng worktree khi user explicit yêu cầu isolation bằng worktree.
- Top-level LP agents phải chạy foreground; **cấm** `run_in_background` cho `create-spec`, `review-spec`, `create-plan`, `review-plan`, `implement-plan`, `review-implement`, `qa-automation`, `debug-investigator`.
- `status` và `resume` phải surface rõ `workspace_policy` + `entry_decision`; không bắt orchestrator phải đoán writer authority.

### `start-plan`

Tạo workflow mới cho `/lp:plan`.
Nếu requirement chưa đủ rõ (business/flow/happy/edge/UI/AC), command này sẽ auto-insert `create-spec` -> `review-spec` trước `create-plan`.
Nếu đã có workflow `spec` cho cùng `plan_name` và `create-spec = PASS` + `review-spec = PASS`, command sẽ promote cùng workflow sang lane `plan`.

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-plan \
  --plan-name PLAN_MERCHANT_BULK_IMPORT \
  --requirement "Create reviewed plan for merchant bulk import"
```

### `start-spec`

Tạo workflow mới cho `/lp:spec`.

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-spec \
  --plan-name PLAN_MERCHANT_BULK_IMPORT \
  --requirement "Clarify business rules, UX flow, happy path, and edge cases for merchant bulk import"
```

### `start-cook`

Tạo workflow mới cho `/lp:cook`, chạy từ `create-spec` -> `review-spec`, đồng thời set gate `user_approved_implementation = true`.

### `start-debug`

Tạo workflow debug mới cho `/lp:debug-investigator`.

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-debug \
  --plan-name DEBUG_CHECKOUT_TIMEOUT \
  --requirement "Checkout timeout when creating payment session"
```

### `start-implement`

Chuẩn bị workflow đã approved để chạy delivery loop từ `implement-plan`.

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-implement \
  --plan-name PLAN_MERCHANT_BULK_IMPORT \
  --plan-file .codex/plans/PLAN_MERCHANT_BULK_IMPORT/plan.md
```

### `start-review-implement`

Wrapper trực tiếp cho `/lp:review-implement`, tương đương `start-followup --step review-implement`.
Command này chỉ hợp lệ khi `implementation_done = true`.

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-review-implement \
  --workflow-id WF_20260409_000001
```

### `start-followup`

Khởi chạy các bước follow-up trong delivery loop với transition guard.

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py start-followup \
  --workflow-id WF_20260409_000001 \
  --step review-implement
```

### `sync-output`

Ưu tiên đọc machine contract JSON; fallback sang markdown frontmatter nếu chưa có JSON.

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py sync-output \
  --workflow-id WF_20260409_000001 \
  --output-file .codex/pipeline/PLAN_MERCHANT_BULK_IMPORT/01-create-plan.output.md \
  --contract-file .codex/pipeline/PLAN_MERCHANT_BULK_IMPORT/01-create-plan.output.contract.json \
  --plan-file .codex/plans/PLAN_MERCHANT_BULK_IMPORT/plan.md
```

#### Correct examples

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py next \
  --workflow-id WF_20260409_000001
```

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/validate_contract.py \
  .codex/pipeline/PLAN_MERCHANT_BULK_IMPORT/04-review-implement.output.contract.json
```

#### Wrong examples

```text
--step-id   # invalid for lp_pipeline.py next
--db        # invalid short alias here
sync-output without validator/artifact awareness for contract-writing flows
```

Dùng `python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py --print-examples` để xem examples canonical mới nhất.
Dùng `python ~/.agents/skills/lp-pipeline-orchestrator/scripts/validate_contract.py --print-schema` để in schema validator hiện hành.

### `next`

Xem bước kế tiếp.

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py next \
  --workflow-id WF_20260409_000001
```

### `status`

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py status \
  --workflow-id WF_20260409_000001 \
  --include-events
```

### `resume`

```bash
python ~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py resume \
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

Stop conditions cho fail-loop:

- Tối đa 3 vòng sửa
- Dừng `WAITING_USER` nếu có critical impact tới pipeline/thiết kế plan
- Dừng `WAITING_USER` nếu LLM không chắc chắn hoặc có nhiều lựa chọn cần user confirm

`delivery_next` trong output của `status` / `resume` là nguồn khuyến nghị chính cho orchestrator.
