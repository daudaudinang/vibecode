# PLAN: PIPELINE_AUTOFIX_VALIDATOR

> **Tier**: L (cross-cutting: orchestrator, state manager, worker instructions, reviewer instructions, validator, runtime docs)
> **Phases**: 4
> **Design basis**: Approved pipeline revision design v2 + review decisions chốt ngày 2026-04-21.
> **Self-contained note**: Plan này là nguồn triển khai đầy đủ; không phụ thuộc section ID kiểu `E16/E19` hay `file://...` ngoài repo.

---

## Mục tiêu

Triển khai pipeline auto-fix mới cho LP namespace với 5 mục tiêu cụ thể:
1. Fix retry tracking bug cho spec/plan loops
2. Đóng kín runtime loop cho `review-spec` / `review-plan` để có thể revision nhiều vòng trước khi dừng
3. Giữ mô hình **orchestrator self-coordinate, worker self-write** cho spec/plan revision
4. Thêm Validator agent dùng **structured JSON handoff** làm input chính
5. Update `/lp:cook` và runtime docs để phản ánh ownership, retry budgets, và validator flow mới

---

## Canonical decisions đã chốt

### Decision A — Spec/Plan self-fix ownership

- **Không** cho orchestrator tự viết trực tiếp `spec.md` hoặc `plan.md`
- Orchestrator chỉ:
  - quyết định có cần revise hay không
  - spawn worker đúng mode
  - sync state / gate / artifacts
- Worker `create-spec` và `create-plan` sẽ được **reuse ở `Mode: Revise`** để ghi artifact revision

### Decision B — Validator input source

- Validator **không** parse raw text review output làm source chính
- Validator đọc từ:
  1. artifact path đang được review
  2. file **Validator Judgment Handoff (VJH) JSON** do orchestrator hoặc fast-review agent tạo
- Human report vẫn tồn tại để người đọc, nhưng **JSON là source of truth cho validator**

---

## Acceptance Criteria

| AC | Mô tả | Verify |
|---|---|---|
| AC-1 | `spec_loop_fail_count` được track trên `review-spec` khi status = `FAIL` hoặc `NEEDS_REVISION`, reset về `0` khi `review-spec = PASS` | VC-1, VC-2 |
| AC-2 | `plan_loop_fail_count` được track trên `review-plan` khi status = `FAIL` hoặc `NEEDS_REVISION`, reset về `0` khi `review-plan = PASS` | VC-1, VC-2 |
| AC-3 | `resolve-next` cho mode `spec` trả `next_step = create-spec` khi `review-spec ∈ {FAIL, NEEDS_REVISION}`, fail count `< max`, và không có pause flag | VC-2 |
| AC-4 | `resolve-next` cho mode `plan` trả `next_step = create-plan` khi `review-plan ∈ {FAIL, NEEDS_REVISION}`, fail count `< max`, và không có pause flag | VC-2 |
| AC-5 | `review-spec FAIL` và `review-plan FAIL` không còn mặc định đẩy workflow sang `FAILED`; chỉ `WAITING_USER`/stop khi chạm max retry hoặc contract yêu cầu pause | VC-1, VC-2 |
| AC-6 | `create-spec` hỗ trợ `Revision Mode` nhất quán ở `TASK.md`, `SKILL.md`, và `.codex/agents/create-spec.toml` | VC-1, VC-3 |
| AC-7 | `create-plan` hỗ trợ `Revision Mode` nhất quán ở `TASK.md`, `SKILL.md`, và `.codex/agents/create-plan.toml` | VC-1, VC-3 |
| AC-8 | `implement-plan` `Revision Mode` được giữ lại nhưng wording không còn mâu thuẫn với rule “phải đọc boundary/dependencies trước khi sửa” | VC-1, VC-3 |
| AC-9 | `validator.toml`, `validator/SKILL.md`, `tasks/validator/TASK.md` tồn tại và định nghĩa input chính là **artifact path + VJH JSON path** | VC-1, VC-4 |
| AC-10 | Fast-mode reviewer agents (`review-spec`, `review-plan`, `review-implement`) yêu cầu trả thêm VJH JSON có schema rõ ràng | VC-1, VC-4 |
| AC-11 | Orchestrator SKILL mô tả rõ 2 artifact phụ cho validator: `*.validator-handoff.json` và `*.validator-judgment.json` | VC-1, VC-4 |
| AC-12 | `/lp:spec`, `/lp:plan`, `/lp:implement`, `/lp:cook` trong orchestrator doc phản ánh đúng ownership mới: orchestrator coordinate, worker revise, validator đọc JSON handoff | VC-1, VC-4 |
| AC-13 | Verify commands trong plan dùng canonical repo-relative paths `.agents/...` và command surface thật của CLI hiện tại | VC-1 |
| AC-14 | `sync-global.sh` không còn là bước bắt buộc sau mỗi phase; chỉ chạy sau khi toàn bộ implementation pass verify hoặc khi user explicit yêu cầu rollout global | VC-1, VC-4 |
| AC-15 | Plan có verify flow cụ thể, tái lập được cho retry logic của `spec` và `plan`; không còn ghi chung chung kiểu “manual verify bằng mock state” | VC-2 |
| AC-16 | `/lp:cook` có AC riêng cho revised retry budgets + validator/revision ownership | VC-1, VC-4 |

---

## Non-goals

- Không rewrite toàn bộ `lp_pipeline.py` hay `state_manager.py`
- Không thêm test framework mới cho Python scripts
- Không sửa persona agent `.toml` files
- Không thay đổi canonical Standard Mode Merge Protocol ngoài phần bổ sung VJH/validator handoff
- Không biến validator thành top-level workflow step trong SQLite state machine

---

## Dependencies / Prerequisites

- Approved design v2 đã tồn tại
- Hai quyết định ở mục **Canonical decisions đã chốt** là hard requirement
- Dùng canonical runtime paths của repo này:
  - `.agents/skills/`
  - `.codex/agents/`
  - `.codex/pipeline/`
  - `.codex/state/`
  - `.codex/tmp/`

---

## Execution Boundary

### Allowed Files

| File | Action |
|---|---|
| `.agents/skills/lp-pipeline-orchestrator/SKILL.md` | MODIFY — update canonical flows, VJH artifacts, validator flow, retry ownership, `/lp:cook` |
| `.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py` | MODIFY — add spec/plan retry metadata patch + gate transitions cho revision loop |
| `.agents/skills/lp-state-manager/scripts/state_manager.py` | MODIFY — close retry loop logic trong `resolve-next` |
| `.agents/skills/create-spec/SKILL.md` | MODIFY — add `Revision Mode` source-of-truth wording |
| `.agents/skills/create-plan/SKILL.md` | MODIFY — add `Revision Mode` source-of-truth wording |
| `.agents/skills/implement-plan/SKILL.md` | MODIFY — align `Revision Mode` wording với boundary/dependency rules |
| `.agents/skills/tasks/create-spec/TASK.md` | MODIFY — add `Revision Mode` section |
| `.agents/skills/tasks/create-plan/TASK.md` | MODIFY — add `Revision Mode` section |
| `.agents/skills/tasks/implement-plan/TASK.md` | MODIFY — refine `Revision Mode` section |
| `.codex/agents/create-spec.toml` | MODIFY — add `Revision Mode` instructions |
| `.codex/agents/create-plan.toml` | MODIFY — add `Revision Mode` instructions |
| `.codex/agents/implement-plan.toml` | MODIFY — align `Revision Mode` wording |
| `.codex/agents/review-spec.toml` | MODIFY — require VJH JSON output in fast mode |
| `.codex/agents/review-plan.toml` | MODIFY — require VJH JSON output in fast mode |
| `.codex/agents/review-implement.toml` | MODIFY — require VJH JSON output in fast mode |
| `.codex/agents/validator.toml` | CREATE |
| `.agents/skills/validator/SKILL.md` | CREATE |
| `.agents/skills/tasks/validator/TASK.md` | CREATE |

### Do NOT Modify

- `.agents/skills/tasks/review-spec/TASK.md`
- `.agents/skills/tasks/review-plan/TASK.md`
- `.agents/skills/tasks/review-implement/TASK.md`
- `.agents/skills/persona-reviewer/SKILL.md`
- `.codex/agents/persona-*.toml`
- `.agents/skills/lp-state-manager/SKILL.md`
- `.agents/skills/lp-state-manager/scripts/state_manager.py` schema DDL / table structure
- `.codex/scripts/sync-global.sh` implementation logic (plan chỉ đổi cách **khi nào chạy**, không sửa script)

---

## Implementation Order

```text
Phase 1: Runtime loop closure
    ↓ (verify: AC-1, AC-2, AC-3, AC-4, AC-5, AC-15)
Phase 2: Worker revision-mode source-of-truth
    ↓ (verify: AC-6, AC-7, AC-8)
Phase 3: Validator + VJH JSON integration
    ↓ (verify: AC-9, AC-10, AC-11)
Phase 4: Orchestrator docs + /lp:cook + final verify strategy
    ↓ (verify: AC-12, AC-13, AC-14, AC-16)
```

---

## Phase 1: Runtime Loop Closure

### 1.1 `lp_pipeline.py` — add spec/plan retry metadata patch

Thêm helper mới, tách riêng khỏi delivery loop:

```python
SPEC_REVIEW_SKILLS = {'review-spec'}
PLAN_REVIEW_SKILLS = {'review-plan'}
SPEC_LOOP_MAX_RETRIES = 3
PLAN_LOOP_MAX_RETRIES = 3
```

Thêm function mới:

```python
def build_spec_plan_loop_metadata_patch(snapshot, skill, status, contract):
    ...
```

Rules:
- Chỉ track retry trên **review step**, không track trên `create-spec` / `create-plan`
- `review-spec`:
  - `FAIL` / `NEEDS_REVISION` → `spec_loop_fail_count += 1`
  - `PASS` → reset `spec_loop_fail_count = 0`
- `review-plan`:
  - `FAIL` / `NEEDS_REVISION` → `plan_loop_fail_count += 1`
  - `PASS` → reset `plan_loop_fail_count = 0`
- Patch metadata phải chứa tối thiểu:
  - `spec_loop_fail_count`
  - `spec_loop_max_retries`
  - `spec_loop_pause_for_user`
  - `spec_loop_pause_reason_code`
  - `spec_loop_pause_reason`
  - `plan_loop_fail_count`
  - `plan_loop_max_retries`
  - `plan_loop_pause_for_user`
  - `plan_loop_pause_reason_code`
  - `plan_loop_pause_reason`

### 1.2 `lp_pipeline.py` — close gate transitions for loopable review FAIL/NEEDS_REVISION

Update `sync_gates_for_skill()` cho `review-spec` và `review-plan`:

#### `review-spec`
- `PASS`:
  - giữ behavior publish/approval như hiện tại
  - merge metadata patch để reset fail count
- `NEEDS_REVISION`:
  - **không** dừng cứng
  - workflow status = `ACTIVE`
  - current step vẫn ở lane `spec`
  - merge metadata patch
- `FAIL`:
  - nếu contract yêu cầu pause user hoặc fail count đã chạm max → `WAITING_USER`
  - ngược lại vẫn để workflow `ACTIVE` để quay lại `create-spec` revision loop
  - **không** set `FAILED` mặc định cho loopable review fail

#### `review-plan`
- áp dụng logic tương tự `review-spec`
- `FAIL` chỉ chuyển sang `WAITING_USER` khi có blocker/user-confirmation/max retry; không hard-fail mặc định

#### Metadata merge requirement
Không được truyền `metadata_json=None` cho các nhánh review-spec/review-plan nói trên.
Bắt buộc dùng `merge_metadata_payload(...)` để không làm rơi fail-count patch.

### 1.3 `state_manager.py` — update `resolve-next`

#### Spec mode
Trong block `if mode == 'spec':`
- Nếu `review-spec.status in {'FAIL', 'NEEDS_REVISION'}`:
  - đọc `spec_loop_fail_count`, `spec_loop_max_retries`, `spec_loop_pause_for_user`
  - nếu `spec_loop_pause_for_user = true` hoặc `fail_count >= max`:
    - `can_proceed = false`
    - `workflow_status = 'WAITING_USER'`
    - `next_step = None`
  - ngược lại:
    - `can_proceed = true`
    - `next_step = 'create-spec'`
    - `reason = 'review-spec requested revision; rerun create-spec in Revision Mode'`

#### Plan mode
Trong block `review-plan`:
- áp dụng logic tương tự cho `plan_loop_fail_count`
- khi loop được:
  - `can_proceed = true`
  - `next_step = 'create-plan'`
  - `reason = 'review-plan requested revision; rerun create-plan in Revision Mode'`

#### Generic fail guard
Đảm bảo generic guard ở đầu `resolve-next` **không chặn nhầm** `review-spec FAIL` / `review-plan FAIL` khi các fail này còn nằm trong retry budget và không có pause flag.
Có thể xử lý theo một trong hai cách, nhưng phải chọn **một** cách rõ ràng trong code:
1. dời mode-specific logic lên trước generic `FAIL` guard, hoặc
2. loại trừ `review-spec` / `review-plan` khỏi generic `FAIL` guard khi loopable

### Verify Phase 1

- Xem **VC-1** cho static source checks
- Xem **VC-2** cho runtime fixture checks bằng `create-workflow` + `upsert-step` + `resolve-next`

---

## Phase 2: Worker Revision-Mode Source-of-Truth

### 2.1 `create-spec` — add `Revision Mode`

Cập nhật nhất quán ở 3 nơi:
- `.agents/skills/create-spec/SKILL.md`
- `.agents/skills/tasks/create-spec/TASK.md`
- `.codex/agents/create-spec.toml`

Required behavior:
- Nếu spawn message có `Mode: Revise`:
  - đọc review findings đã được orchestrator xác nhận
  - đọc spec hiện tại nếu có
  - chỉ sửa phần liên quan findings
  - vẫn phải đọc boundary/context trước khi ghi
  - vẫn publish `00-create-spec.output.*` như worker bình thường
- Không dùng wording kiểu “spawn-once” nữa

### 2.2 `create-plan` — add `Revision Mode`

Cập nhật nhất quán ở 3 nơi:
- `.agents/skills/create-plan/SKILL.md`
- `.agents/skills/tasks/create-plan/TASK.md`
- `.codex/agents/create-plan.toml`

Required behavior:
- Nếu spawn message có `Mode: Revise`:
  - đọc plan hiện tại + spec baseline + review findings đã normalize
  - revise targeted, không rewrite vô cớ
  - vẫn giữ output paths canonical `01-create-plan.output.*`
- Không dùng wording kiểu “spawn-once” nữa

### 2.3 `implement-plan` — refine existing `Revision Mode`

Cập nhật nhất quán ở 3 nơi:
- `.agents/skills/implement-plan/SKILL.md`
- `.agents/skills/tasks/implement-plan/TASK.md`
- `.codex/agents/implement-plan.toml`

Required wording fix:
- Có thể “focus fix phần bị flag”, nhưng **không** được mâu thuẫn với rule hiện tại rằng worker vẫn phải:
  - đọc `plan_file`
  - đọc execution boundary
  - đọc dependencies / prerequisites liên quan
- Thay câu “không đọc lại toàn bộ plan” bằng wording an toàn hơn như:
  - “được phép ưu tiên phần liên quan findings sau khi đã nạp boundary/dependency context bắt buộc”

### Verify Phase 2

- Xem **VC-3**

---

## Phase 3: Validator + VJH JSON Integration

### 3.1 `validator` worker package

Tạo mới:
- `.codex/agents/validator.toml`
- `.agents/skills/validator/SKILL.md`
- `.agents/skills/tasks/validator/TASK.md`

Canonical role:
- read-only verifier
- không edit artifact
- không phải top-level workflow step
- input chính là:
  1. artifact path under review
  2. `validator-handoff.json`

### 3.2 VJH (Validator Judgment Handoff) JSON

Mỗi review step có validator phải dùng artifact phụ sau:

| Review step | Handoff artifact | Judgment artifact |
|---|---|---|
| `review-spec` | `.codex/pipeline/PLAN_<NAME>/00-review-spec.validator-handoff.json` | `.codex/pipeline/PLAN_<NAME>/00-review-spec.validator-judgment.json` |
| `review-plan` | `.codex/pipeline/PLAN_<NAME>/02-review-plan.validator-handoff.json` | `.codex/pipeline/PLAN_<NAME>/02-review-plan.validator-judgment.json` |
| `review-implement` | `.codex/pipeline/PLAN_<NAME>/04-review-implement.validator-handoff.json` | `.codex/pipeline/PLAN_<NAME>/04-review-implement.validator-judgment.json` |

### 3.3 VJH schema tối thiểu

```json
{
  "schema_version": 1,
  "review_step": "review-plan",
  "plan": "PLAN_X",
  "artifact_under_review": ".codex/plans/PLAN_X/plan.md",
  "review_mode": "standard | fast",
  "findings": [
    {
      "id": "F-001",
      "persona": "senior_developer",
      "severity": "major",
      "summary": "...",
      "evidence": ["file:line"],
      "business_context": "..."
    }
  ],
  "review_summary": {
    "weighted_score": 7.4,
    "severity_counts": {
      "blocker": 0,
      "major": 1,
      "minor": 2,
      "info": 0
    }
  }
}
```

### 3.4 Validator judgment schema tối thiểu

```json
{
  "schema_version": 1,
  "skill": "validator",
  "review_step": "review-plan",
  "plan": "PLAN_X",
  "confirmed_findings": [],
  "false_positives": [],
  "conflicts_unresolved": [],
  "notes": []
}
```

Rules:
- `Blocker` không được validator tự reject nếu evidence thật sự có mặt; nếu bất đồng diễn giải thì đẩy vào `conflicts_unresolved`
- Text report chỉ để người đọc; validator **không** dùng text report làm source chính

### 3.5 Fast-mode reviewer output update

Update 3 agent `.toml` files:
- `.codex/agents/review-spec.toml`
- `.codex/agents/review-plan.toml`
- `.codex/agents/review-implement.toml`

Required output change:
- vẫn trả human-readable review text
- **đồng thời** phải trả structured VJH JSON block để orchestrator có thể persist thành `*.validator-handoff.json`

### 3.6 Standard mode ownership

- Standard mode vẫn spawn 4 persona agents như cũ
- Sau bước conflict normalization + weighted scoring, orchestrator tạo `*.validator-handoff.json`
- Validator đọc file này + artifact thật
- Orchestrator dùng validator judgment để finalize contract cuối

### Verify Phase 3

- Xem **VC-4**

---

## Phase 4: Orchestrator Docs, `/lp:cook`, and Final Verify Strategy

### 4.1 `lp-pipeline-orchestrator/SKILL.md`

Cập nhật các flow canonical:

#### `/lp:spec`
1. Spawn `@create-spec`
2. Review spec
3. Persist `00-review-spec.validator-handoff.json`
4. Spawn `@validator`
5. Nếu validator + retry budget cho phép revise → spawn lại `@create-spec` với `Mode: Revise`
6. Nếu chạm max retry hoặc cần user quyết định → `WAITING_USER`
7. `PASS` thì dừng human gate chờ `/lp:plan`

#### `/lp:plan`
1. Spawn `@create-plan`
2. Review plan
3. Persist `02-review-plan.validator-handoff.json`
4. Spawn `@validator`
5. Nếu validator + retry budget cho phép revise → spawn lại `@create-plan` với `Mode: Revise`
6. Nếu chạm max retry hoặc cần user quyết định → `WAITING_USER`
7. `PASS` thì dừng human gate chờ `/lp:implement`

#### `/lp:implement`
- giữ delivery loop hiện có
- validator cũng dùng VJH JSON path, không dựa vào raw text
- `implement-plan` tiếp tục là worker rewrite/revise chính trong delivery loop

#### `/lp:cook`
Phải nêu rõ 3 retry budgets độc lập:
- spec loop retries
- plan loop retries
- delivery loop retries

### 4.2 Sync policy update

Bỏ rule “chạy `sync-global.sh` sau mỗi phase`”.
Thay bằng:
- chỉ sync global sau khi toàn bộ thay đổi pass verify, hoặc
- khi user explicit yêu cầu rollout global ngay lúc đó

### 4.3 Verify command paths

Tất cả verify examples trong plan phải dùng canonical repo-relative paths kiểu:
- `.agents/skills/...`
- `.codex/agents/...`
- `.codex/pipeline/...`
- `.codex/tmp/...`

Không dùng path rút gọn mơ hồ kiểu `tasks/create-spec/TASK.md` khi plan đang đứng ở repo root.

### Verify Phase 4

- Xem **VC-1** và **VC-4**

---

## Verify Commands

> Các command dưới đây là verify plan-level bắt buộc. Chúng dùng CLI thật đã verify bằng `--help` trong repo hiện tại.

### VC-1 — Static source checks

```bash
# Runtime loop code paths
rg -n "build_spec_plan_loop_metadata_patch|spec_loop_fail_count|plan_loop_fail_count|merge_metadata_payload|validator-handoff|validator-judgment" \
  .agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py \
  .agents/skills/lp-state-manager/scripts/state_manager.py \
  .agents/skills/lp-pipeline-orchestrator/SKILL.md

# Revision Mode surfaces
rg -n "Revision Mode|Mode: Revise|validator-handoff|validator-judgment" \
  .agents/skills/create-spec/SKILL.md \
  .agents/skills/create-plan/SKILL.md \
  .agents/skills/implement-plan/SKILL.md \
  .agents/skills/tasks/create-spec/TASK.md \
  .agents/skills/tasks/create-plan/TASK.md \
  .agents/skills/tasks/implement-plan/TASK.md \
  .codex/agents/create-spec.toml \
  .codex/agents/create-plan.toml \
  .codex/agents/implement-plan.toml \
  .codex/agents/review-spec.toml \
  .codex/agents/review-plan.toml \
  .codex/agents/review-implement.toml \
  .codex/agents/validator.toml \
  .agents/skills/validator/SKILL.md \
  .agents/skills/tasks/validator/TASK.md
```

### VC-2 — Reproducible runtime fixture checks for `resolve-next`

#### Spec loop below max retry

```bash
TMP_DB=.codex/tmp/pipeline_autofix_validator_spec.db
mkdir -p .codex/tmp
rm -f "$TMP_DB"

python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" create-workflow \
  --workflow-id WF_AUTOFIX_SPEC \
  --plan-name PLAN_AUTOFIX_SPEC \
  --mode spec \
  --status ACTIVE \
  --current-phase spec \
  --current-step review-spec \
  --steps create-spec,review-spec \
  --metadata-json '{"spec_loop_fail_count":2,"spec_loop_max_retries":3}'

python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" upsert-step \
  --workflow-id WF_AUTOFIX_SPEC \
  --step create-spec \
  --order 1 \
  --status PASS

python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" upsert-step \
  --workflow-id WF_AUTOFIX_SPEC \
  --step review-spec \
  --order 2 \
  --status NEEDS_REVISION

python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" resolve-next \
  --workflow-id WF_AUTOFIX_SPEC
```

Expected result:
- `can_proceed = true`
- `next_step = create-spec`
- reason nói rõ revision loop

#### Spec loop at max retry

```bash
python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" update-workflow \
  --workflow-id WF_AUTOFIX_SPEC \
  --metadata-json '{"spec_loop_fail_count":3,"spec_loop_max_retries":3}'

python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" resolve-next \
  --workflow-id WF_AUTOFIX_SPEC
```

Expected result:
- `can_proceed = false`
- `workflow_status = WAITING_USER`

#### Plan loop below max retry

```bash
TMP_DB=.codex/tmp/pipeline_autofix_validator_plan.db
mkdir -p .codex/tmp
rm -f "$TMP_DB"

python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" create-workflow \
  --workflow-id WF_AUTOFIX_PLAN \
  --plan-name PLAN_AUTOFIX_PLAN \
  --mode plan \
  --status ACTIVE \
  --current-phase plan \
  --current-step review-plan \
  --steps create-plan,review-plan \
  --metadata-json '{"plan_loop_fail_count":1,"plan_loop_max_retries":3}'

python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" upsert-step \
  --workflow-id WF_AUTOFIX_PLAN \
  --step create-plan \
  --order 1 \
  --status PASS

python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" upsert-step \
  --workflow-id WF_AUTOFIX_PLAN \
  --step review-plan \
  --order 2 \
  --status FAIL

python .agents/skills/lp-state-manager/scripts/state_manager.py \
  --db-path "$TMP_DB" resolve-next \
  --workflow-id WF_AUTOFIX_PLAN
```

Expected result:
- `can_proceed = true`
- `next_step = create-plan`
- workflow **không** bị hard-stop chỉ vì `review-plan = FAIL`

### VC-3 — Revision Mode instruction consistency

```bash
rg -n "Revision Mode|Mode: Revise|focus.*findings|boundary|dependencies" \
  .agents/skills/create-spec/SKILL.md \
  .agents/skills/create-plan/SKILL.md \
  .agents/skills/implement-plan/SKILL.md \
  .agents/skills/tasks/create-spec/TASK.md \
  .agents/skills/tasks/create-plan/TASK.md \
  .agents/skills/tasks/implement-plan/TASK.md \
  .codex/agents/create-spec.toml \
  .codex/agents/create-plan.toml \
  .codex/agents/implement-plan.toml
```

Expected result:
- `create-spec` và `create-plan` có `Revision Mode`
- `implement-plan` vẫn nhắc boundary/dependency context bắt buộc
- không còn wording `spawn-once`

### VC-4 — Validator + VJH integration checks

```bash
rg -n "validator-handoff|validator-judgment|structured JSON|artifact_under_review|confirmed_findings|false_positives|conflicts_unresolved|/lp:cook|sync-global" \
  .agents/skills/lp-pipeline-orchestrator/SKILL.md \
  .codex/agents/review-spec.toml \
  .codex/agents/review-plan.toml \
  .codex/agents/review-implement.toml \
  .codex/agents/validator.toml \
  .agents/skills/validator/SKILL.md \
  .agents/skills/tasks/validator/TASK.md \
  README.md
```

Expected result:
- validator docs nói rõ JSON là input chính
- orchestrator docs có artifact paths `*.validator-handoff.json` + `*.validator-judgment.json`
- `/lp:cook` docs reflect revised retry ownership
- plan không còn yêu cầu sync global sau mỗi phase

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Logic retry mới vô tình phá generic `FAIL` guard | High | Phase 1 phải verify bằng VC-2 cho cả `NEEDS_REVISION` và `FAIL` |
| Drift giữa worker skill / task / agent instructions | High | Phase 2 bắt buộc sửa đủ 3 surfaces cho mỗi worker |
| Validator JSON schema bị drift giữa orchestrator và fast reviewer | Medium | Phase 3 định nghĩa 1 schema tối thiểu duy nhất trong plan + docs |
| Validator artifact tăng số file trong `.codex/pipeline/` | Low | Chấp nhận để đổi lấy auditability và deterministic input |
| Sync global quá sớm làm ảnh hưởng repo khác | Medium | Chỉ sync sau full verify hoặc khi user explicit yêu cầu |

---

## Post-implementation

1. Chạy đầy đủ `VC-1` → `VC-4`
2. Chỉ khi tất cả verify pass mới cân nhắc:
   ```bash
   bash .codex/scripts/sync-global.sh
   ```
3. Sau khi code thay đổi ổn định, gợi ý user chạy lại `$review-plan` hoặc `/lp:review-implement` tùy phase tiếp theo
