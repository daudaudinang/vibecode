---
name: lp-pipeline-orchestrator
description: Canonical orchestrator for /lp:plan, /lp:implement, /lp:cook, and /lp:debug-investigator using worker skills plus the SQLite state manager.
---

# LP Pipeline Orchestrator

Orchestrator canonical duy nhất cho namespace `/lp:*`.

## Scope

Skill này là source of truth cho:

- `/lp:plan <requirement>`
- `/lp:implement <plan | plan_name | workflow_id>`
- `/lp:cook <requirement>`
- `/lp:debug-investigator <symptom>`

Wrapper skills và wrapper commands khác chỉ được phép trỏ về file này.

Skill này chỉ áp đặt orchestration model cho namespace `/lp:*` và các wrapper/worker liên quan của LP. Nó không tự động áp đặt execution model đó cho các task ngoài LP hoặc các yêu cầu thông thường trong main conversation.

## Canonical responsibilities

- Điều phối worker skills theo state machine
- Dùng SQLite state manager làm workflow backbone
- Enforce artifact layout duy nhất dưới `.codex/`
- Enforce human gates, runtime transition guards, và delivery fail-loop policy (retry budget + stop-on-confirmation conditions)
- Sync machine contracts vào state để resume chính xác

## Worker roster

- `create-plan`
- `review-plan`
- `implement-plan`
- `review-implement`
- `qa-automation`
- `debug-investigator`

## Canonical artifact layout

```text
.codex/
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

`.codex/active-plan` được phép tồn tại như pointer, nhưng phải trỏ về `.codex/plans/PLAN_<NAME>/`.

## Plan profiles

### Standard plan

Dùng cho task thường:
- Goal
- Acceptance Criteria
- Execution Boundary
- Implementation Order
- Risks
- Verify Commands

### Parallel-ready plan

Chỉ bật khi task đủ lớn hoặc user yêu cầu parallel. Ngoài standard plan, bắt buộc có:
- dependency graph
- parallel groups
- file ownership matrix
- conflict prevention notes
- phase prerequisites

## Core policies

### Runtime domain model

- `plan` = logical work package + canonical plan artifact package dưới `.codex/plans/PLAN_<NAME>/`
- `primary run` = phiên điều phối chính duy nhất của một plan tại một thời điểm
- `child job` = đơn vị worker/subagent được primary run spawn để xử lý phase/task con
- `reviewer conversation` = conversation chỉ đọc/review/phối hợp, không có quyền writer mặc định
- `event log` = lớp audit/rebuild để reconcile khi DB state lệch với artifact reality

### Source-of-truth hierarchy

1. Plan content và execution boundary: `plan.md` + phase files
2. Runtime evidence: published artifacts / contracts
3. Materialized coordination state: SQLite state manager
4. Convenience pointer: `.codex/active-plan`

Nếu DB state và published artifact mâu thuẫn nhau, published artifact + reconcile result thắng DB snapshot cũ.

### Non-negotiable invariants

- Một plan chỉ có **một primary controller** hợp lệ tại một thời điểm.
- `WAITING_USER` không giữ exclusive execution lease.
- Reviewer conversations không tự trở thành primary writer nếu chưa resume/takeover rõ ràng.
- Không step nào được `PASS` nếu chưa có published artifact/contract hợp lệ.
- Parallelism chỉ nằm ở child jobs dưới primary run, không nằm ở nhiều top-level conversations cùng active write.
- State phải reconcile/rebuild được sau crash, timeout, duplicate callback, hoặc stale owner revival.

### Single source of orchestration

- Flow đầy đủ chỉ nằm ở file này
- `lp-plan`, `lp-implement`, `lp-cook` là thin wrappers
- Worker skills là worker-only, không tự chuyển step tiếp theo

### Runtime guard model

Hiện runtime enforce chủ yếu các transition/gate checks (`plan_approved`, follow-up prerequisites, workflow status).

Ownership/dependency/scope policies vẫn là canonical expectations ở layer docs/contracts, nhưng chưa được enforce đầy đủ trong script runtime hiện tại. Nếu worker report blocker hoặc cần user input, workflow phải dừng đúng gate.

### Delivery loop

`/lp:implement` chỉ hoàn tất khi:
- `implement-plan = PASS`
- `review-implement = PASS`
- `qa-automation = PASS`
- không còn blocker hoặc `scope_violation`

### Retry policy

- Delivery fail loop quay lại `implement-plan` khi `implement-plan`/`review-implement`/`qa-automation` trả fail cần sửa.
- Retry budget runtime: tối đa `3` vòng sửa.
- Dừng và chuyển `WAITING_USER` khi gặp một trong các điều kiện:
  - vượt retry budget
  - có tín hiệu critical impact tới pipeline/thiết kế plan
  - LLM chưa chắc chắn hoặc có nhiều hướng sửa cần user confirm
- Nếu pass sau 1-2 vòng sửa, orchestrator vẫn phải phản hồi rõ là đã recover sau retry.

## Canonical flows

### `/lp:plan`

1. Normalize `plan_name`
2. `start-plan`
3. Spawn `create-plan`
4. `sync-output` từ `01-create-plan.output.contract.json`
5. Nếu state cho phép, spawn `review-plan`
6. `sync-output` từ `02-review-plan.output.contract.json`
7. Nếu review pass, set `plan_approved = true`
8. Dừng ở human gate, chờ `/lp:implement`

### `/lp:implement`

1. Resolve workflow theo `workflow_id`, `plan_name`, hoặc `plan_file`
2. Assert `plan_approved = true`
3. `start-implement`
4. Pre-implement scope/dependency guard
5. Spawn `implement-plan`
6. Sync `03-implement-plan.output.contract.json`
7. Nếu pass, spawn `review-implement`
8. Sync `04-review-implement.output.contract.json`
9. Nếu review pass, spawn `qa-automation`
10. Sync `05-qa-automation.output.contract.json`
11. Nếu `implement-plan`/`review-implement`/`qa-automation` fail và chưa chạm điều kiện dừng, quay lại `implement-plan`
12. Nếu chạm max retry hoặc cần user confirm (critical/uncertain), dừng ở `WAITING_USER`

### `/lp:cook`

1. `start-cook`
2. Chạy full planning loop
3. Chỉ khi `plan_approved = true` mới vào delivery loop
4. Chạy full delivery loop
5. Nếu vượt retry budget, có blocker, hoặc cần user input thì dừng

### `/lp:debug-investigator`

1. `start-debug`
2. Spawn `debug-investigator`
3. Ghi output artifacts
4. Sync state nếu có machine contract
5. Nếu cần fix scope đủ lớn, gợi ý `/lp:plan <fix-scope>`

## Auto proceed policy

Chỉ auto proceed khi đồng thời đúng tất cả điều kiện:
1. step trước pass
2. `resolve-next` trả `can_proceed = true`
3. không có blocker unresolved từ contract
4. workflow không ở trạng thái `WAITING_USER` / `BLOCKED` / `FAILED`
5. command hiện tại đúng mode

> **`AskUserQuestion` policy:** Pipeline tự chạy tiếp theo default. Chỉ dùng `AskUserQuestion` tại **decision gate** (ambiguity / blocker / scope change / confirm rủi ro cao). Không pop question sau mọi bước. → Chi tiết: `AGENTS.md (section 6: Decision Gate Policy)`

## Workspace model

- Worktree là isolation tùy chọn, không phải bắt buộc
- Direct edit trong codebase hiện tại được support
- Repo root cho runtime resolve theo thứ tự: `--repo-root` -> git root từ cwd hiện tại -> fail rõ ràng nếu không suy ra được
- Default state DB là `<repo-root>/.codex/state/pipeline_state.db`
- Nếu chạy nhiều LP workflows song song trong cùng workspace, `.codex/state/` và `.codex/pipeline/` là shared resources nên cần tránh reuse cùng `plan_name`
- Các worktree khác nhau tự nhiên được isolate vì mỗi worktree có `.codex/` riêng

> **Global-scope deployment note (khi skill ở `~/.agents/skills/`):**
> Tất cả `.codex/` paths trong skill này **luôn resolve về project root** của project hiện tại,
> **KHÔNG phải `~/.codex/`** toàn cục. Scripts dùng `git rev-parse --show-toplevel` từ CWD
> của agent để xác định đúng project root.
> Nếu git root không resolve được, `lp_pipeline.py` sẽ fail fast với lỗi rõ ràng thay vì fallback sang path depth mơ hồ.
> Luôn chạy LP pipeline từ trong project directory để đảm bảo path resolution đúng.


## Agent execution policy

- Top-level LP worker steps (`create-plan`, `review-plan`, `implement-plan`, `review-implement`, `qa-automation`, `debug-investigator`) bắt buộc dùng agents; parent agent là orchestrator, không tự thay worker step khi flow canonical yêu cầu agent worker.
- Mặc định spawn các top-level LP agents ngay trong current workspace, không dùng worktree isolation.
- Chỉ dùng worktree isolation nếu user explicit yêu cầu.
- Top-level LP worker steps phải chạy foreground.
- **Cấm** `run_in_background=true` cho top-level LP agents vì orchestrator cần result ngay để sync contract, set gate, và quyết định step kế tiếp.
- Background execution chỉ được xem xét ở child-job level sau này, không áp dụng cho top-level primary-run orchestration.
- Nếu user explicit yêu cầu worktree isolation, vẫn giữ top-level LP worker steps ở foreground; worktree không làm thay đổi foreground rule.
- Trước khi qua step top-level tiếp theo, orchestrator phải sync contract/state của step hiện tại.
- Với `review-plan` và `review-implement`, canonical execution model là spawn 4 agents độc lập theo 4 persona bắt buộc, chạy song song trong current workspace, sau đó orchestrator mới validate evidence, normalize conflicts, và tổng hợp verdict cuối; không được bỏ qua persona nào trong flow chuẩn.
- Intent của policy này là `use agents, but no worktree by default`, không phải `avoid agents`.

## Top-level worker spawn standard

1. Orchestrator nhận LP command canonical và giữ vai trò orchestrator
2. Orchestrator spawn đúng worker agent cho step hiện tại
3. Worker agent chạy foreground trong current workspace
4. Không dùng worktree isolation trừ khi user explicit yêu cầu
5. Worker ghi human report + machine contract
6. Orchestrator sync contract/state
7. Chỉ sau đó mới quyết định step kế tiếp hoặc dừng ở human gate

Flow ngắn:

```text
Orchestrator (parent agent)
→ spawn top-level worker agent
→ run foreground in current workspace
→ publish output + contract
→ sync state
→ decide next step
```

Anti-misread:
- Đúng: dùng agents trong current workspace
- Sai: bỏ agent và để orchestrator tự làm hết worker step
- Sai: mặc định isolate mọi worker bằng worktree
- Sai: cho top-level LP worker chạy background rồi sync sau

## Review skill autonomy note

- `review-plan` là worker-only skill; nó chỉ trả structured findings/contract cho orchestrator gate, không tự orchestration sang step tiếp theo.
- `review-implement` là worker-only skill; nó chỉ trả structured findings/contract cho orchestrator gate, không tự orchestration sang step tiếp theo.
- Với 2 review skills này, canonical roster 4 persona là hard requirement của review model và canonical execution model là 4 agents độc lập chạy song song.
- Orchestrator không dùng "depth level" để giả lập multi-review; phải thực sự spawn đủ 4 agents persona rồi mới validate/tổng hợp.
- Findings từ review skills không được dùng để set verdict cuối nếu chưa qua validation về evidence, business context, và conflict normalization.

## Machine contracts

Mỗi worker step phải ghi 2 files:
- Human report: `NN-step.output.md`
- Machine contract: `NN-step.output.contract.json`

State sync ưu tiên JSON contract.
- Không được start step top-level tiếp theo trước khi contract của step hiện tại đã được sync.

## References

- `~/.agents/skills/lp-state-manager/SKILL.md` (global skill) hoặc local mirror khi đang dev skill
- `~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py` (global skill) hoặc local mirror khi đang dev skill
- `skill `lp-pipeline-orchestrator` (command index)`
- `AGENTS.md (section 6: Decision Gate Policy)` — khi nào dùng `AskUserQuestion` và khi nào không
