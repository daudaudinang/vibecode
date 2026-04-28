---
name: lp-state-manager
description: Quản lý workflow state cho pipeline LittlePea bằng SQLite qua script chuẩn, thay cho grep/sửa JSON thủ công. Dùng khi agent cần tạo workflow, tìm workflow theo plan name, đọc state hiện tại, cập nhật step/gate/artifact/event, hoặc suy ra bước kế tiếp trong /lp:spec, /lp:plan, /lp:implement, /lp:cook.
---

# LP State Manager

Skill này chuẩn hoá state management cho pipeline LittlePea.

## Khi nào dùng

- Cần tạo workflow state mới cho `/lp:plan`, `/lp:implement`, `/lp:cook`, `/lp:debug-investigator`
- Cần tạo workflow state mới cho `/lp:spec`, `/lp:plan`, `/lp:implement`, `/lp:cook`, `/lp:debug-investigator`
- Cần tìm workflow theo `workflow_id`, `plan_name`, `ticket`, `status`
- Cần cập nhật step status, gate, artifact, top-level workflow status
- Cần append event log hoặc resolve bước tiếp theo

## ⚠️ Scope Rules — Đọc trước khi chạy bất kỳ lệnh nào

> **Tất cả `.codex/` paths trong file này là tương đối với PROJECT ROOT**, không phải `~/` hay global.
> - Scripts tự resolve project root qua `git rev-parse --show-toplevel`.
> - State DB (`pipeline_state.db`), plans, pipeline artifacts đều lưu trong **project scope**.
> - **Tuyệt đối không chạy các lệnh này ngoài project directory** — sẽ không tìm được git root và fail.
> - `--db-path` chỉ dùng để override khi debug/test; không dùng global DB path cho nhiều project.
>
> **Global-scope deployment note:**
> Khi skill này được cài ở `~/.agents/skills/` (global), `.codex/` vẫn resolve về **project root** của
> project mà agent đang làm việc — **KHÔNG phải `~/.codex/`**.
> Scripts dùng `git rev-parse --show-toplevel` từ CWD của agent để tìm đúng project root.
> Nếu muốn override thủ công: `python state_manager.py --repo-root /path/to/project <command>`.

## Rule bắt buộc

- **KHÔNG** grep rồi sửa `.json` state thủ công
- **KHÔNG** tự tạo schema ad-hoc
- **LUÔN** dùng script global skill path khi chạy global install:

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py <command> ...
```

- Nếu repo có local mirror của skill để dev/test thì local path có thể tồn tại, nhưng **không phải canonical invocation model** cho global deployment.

- Source of truth mặc định: `<repo-root>/.codex/state/pipeline_state.db`
- Repo root resolve theo thứ tự: `--repo-root` -> git root từ cwd hiện tại -> fail rõ ràng nếu không suy ra được
- First run sẽ tự bootstrap DB + schema khi gọi script; không cần migrate tay riêng cho LP state DB
- `--db-path` chỉ nên dùng cho debug/test hoặc migration có chủ đích; không dùng shared/global DB path cho nhiều project
- Nếu cần hiểu schema/commands chi tiết, đọc `references/schema.md`

## Commands cốt lõi

### 1) Tạo workflow

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py create-workflow \
  --plan-name PLAN_MERCHANT_BULK_IMPORT \
  --mode plan \
  --requirement "Create and review plan for merchant bulk import"
```

### 2) Đọc workflow

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py get-workflow \
  --workflow-id WF_20260409_000001
```

### 3) Tìm workflow

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py find-workflows \
  --plan-name PLAN_MERCHANT_BULK_IMPORT
```

### 4) Cập nhật step

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py upsert-step \
  --workflow-id WF_20260409_000001 \
  --step create-plan \
  --status PASS \
  --output .codex/pipeline/PLAN_MERCHANT_BULK_IMPORT/01-create-plan.output.md
```

#### Correct examples

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path ".codex/state/pipeline_state.db" \
  upsert-step \
  --workflow-id "WF_20260409_000001" \
  --step "review-implement" \
  --order 4 \
  --status FAIL \
  --output ".codex/pipeline/PLAN_MERCHANT_BULK_IMPORT/04-review-implement.output.md"
```

#### Wrong examples

```text
--step-id   # invalid flag
--db        # invalid flag
--workflow  # invalid flag
```

Dùng `python ~/.agents/skills/lp-state-manager/scripts/state_manager.py upsert-step --example` để in example canonical mới nhất.

Trước khi gọi command ghi state:
- verify DB path canonical
- chạy `--help` nếu flags chưa được verify trong repo hiện tại
- không dùng path suy đoán nếu chưa đọc manifest/source-of-truth hiện hành

Dùng `python ~/.agents/skills/lp-state-manager/scripts/state_manager.py --print-examples` để xem examples machine-friendly cho các command chính.

### 5) Cập nhật gate

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py set-gate \
  --workflow-id WF_20260409_000001 \
  --gate plan_approved \
  --value true
```

### 6) Gắn artifact

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py set-artifact \
  --workflow-id WF_20260409_000001 \
  --key final_plan_path \
  --path .codex/plans/PLAN_MERCHANT_BULK_IMPORT/plan.md
```

### 7) Suy ra bước tiếp theo

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py resolve-next \
  --workflow-id WF_20260409_000001
```

## Pattern dùng trong pipeline

### `/lp:spec`
1. `create-workflow --mode spec`
2. `upsert-step create-spec --status RUNNING`
3. create-spec xong → `upsert-step ... PASS`, `set-gate requirement_clarified true`
4. `upsert-step review-spec --status RUNNING`
5. review-spec xong:
   - PASS -> `set-gate spec_approved true`
   - NEEDS_REVISION/FAIL -> `set-gate spec_approved false`

### `/lp:plan`
1. `create-workflow --mode plan`
2. `upsert-step create-plan --status RUNNING`
3. create-plan xong → `upsert-step ... PASS`, `set-artifact final_plan_path ...`
4. review-plan xong → `upsert-step ... PASS|NEEDS_REVISION|FAIL`
5. nếu PASS → `set-gate plan_approved true`

### `/lp:implement`
1. `find-workflows` hoặc `get-workflow`
2. xác nhận `plan_approved = true`
3. `upsert-step implement-plan --status RUNNING`
4. implement xong → `upsert-step ... PASS`, set artifacts/gates cần thiết
5. nếu `implementation_done = true` nhưng `implementation_review_passed = false` → bước tiếp theo là `review-implement`
6. nếu `qa_passed = false` sau review PASS → bước tiếp theo là `qa-automation`
7. nếu `implement-plan`/review/QA fail → quay lại `implement-plan`
8. fail-loop tối đa 3 lần; nếu critical impact hoặc cần user confirm do uncertainty/multiple options thì dừng `WAITING_USER`

### `/lp:cook`
- Dùng cùng workflow record
- Chỉ auto nhảy bước khi `resolve-next` trả về `can_proceed = true`

### `/lp:debug-investigator`
1. `create-workflow --mode debug`
2. `upsert-step debug-investigator --status RUNNING|PASS|WAITING_USER|FAIL`
3. lane này là standalone investigation; sau khi PASS thì orchestrator tự quyết định bước tiếp theo

## Epic phase runtime helpers

Các command bổ sung cho phase-level state (Epic mode):

```bash
python ~/.agents/skills/lp-state-manager/scripts/state_manager.py upsert-phase-state \
  --workflow-id WF_20260409_000001 \
  --phase-id P02 \
  --status in_progress \
  --current-step implement-plan \
  --state-version 3

python ~/.agents/skills/lp-state-manager/scripts/state_manager.py list-phase-states \
  --workflow-id WF_20260409_000001

python ~/.agents/skills/lp-state-manager/scripts/state_manager.py resolve-phase-resume \
  --workflow-id WF_20260409_000001
```

Quy tắc deterministic resume selector:
- Ưu tiên `waiting_user` -> `in_progress` -> `pending`
- Chỉ chọn phase có dependencies satisfied
- Nếu `dependency_critical = true` mà dependencies thiếu/không rõ -> trả `waiting_user`, không fallback tuyến tính

Reconciliation semantics:
- `state_version` trong phase notes chỉ là mirror từ SQLite authority
- `soft mismatch` => auto-heal mirror
- `hard mismatch` => dừng `waiting_user` để operator xử lý
