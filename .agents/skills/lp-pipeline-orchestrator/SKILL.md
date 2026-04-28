---
name: lp-pipeline-orchestrator
description: Canonical orchestrator for /lp:spec, /lp:plan, /lp:implement, /lp:review-implement, /lp:cook, and /lp:debug-investigator using worker skills plus the SQLite state manager.
---

# LP Pipeline Orchestrator

Orchestrator canonical duy nhất cho namespace `/lp:*`.

## Scope

Skill này là source of truth cho:

- `/lp:spec <requirement>`
- `/lp:plan <requirement>`
- `/lp:implement <plan | plan_name | workflow_id>`
- `/lp:review-implement <plan | plan_name | workflow_id>`
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
- `create-spec`
- `review-spec`
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
      00-create-spec.output.md
      00-create-spec.output.contract.json
      00-review-spec.output.md
      00-review-spec.output.contract.json
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

### Epic runtime contracts (V3)

#### Baseline resolution contract

- Priority 1: dùng `baseline_verify_command` trong frontmatter phase file.
- Priority 2: đúng 1 entry trong `Verify Commands` có label normalize về lowercase = `baseline`.
- Không có fallback ngầm ngoài plan artifact/package.

#### waiting_user one-screen contract

Mọi blocker runtime trong Epic mode phải có đủ:

```text
Error: <short reason>
Required action: <human action>
Context: <phase_id/current_step/files>
Next command: /lp:implement PLAN_<NAME>
Recovery evidence required: <what to verify before resume>
```

- Merge conflict bắt buộc có `Conflict files: <list>`.
- Worktree setup fail phải có guidance `git worktree prune` hoặc manual cleanup git/worktree state.
- Nhánh `dependency_critical = true` thiếu dependency khai báo phải chuyển `waiting_user`, không fallback tuyến tính.

#### cancel_requested safe boundary

`cancel_requested` chỉ được finalize `cancelled` tại:
- command-exit boundary
- step-transition boundary
- worker-handoff boundary

Không kill giữa command đang chạy.

#### State reconciliation

- `state_version` trong phase notes là mirror từ SQLite.
- `soft mismatch`: auto-heal từ SQLite + ghi reconciliation note.
- `hard mismatch`: dừng `waiting_user`, không auto-override.

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

## Spawn message template

Khi orchestrator spawn worker agent, spawn message **phải** chứa runtime metadata cô đọng để child agent biết ngay cần làm gì, đọc file nào. Child agent nhận metadata này qua spawn message (tin nhắn đầu tiên trong thread), kết hợp với `developer_instructions` từ `.toml`.

**Không nhét nội dung file vào spawn message.** Chỉ nhét đường dẫn + metadata. Child tự đọc file từ disk.

### Template chung

```text
## Task
[Mô tả ngắn 1-2 câu cần làm gì]

## Plan
- Plan name: PLAN_<NAME>
- Plan file: .codex/plans/PLAN_<NAME>/plan.md
- Phase files: phase-01-*.md, phase-02-*.md (nếu có)
- Spec file: .codex/plans/PLAN_<NAME>/spec.md (nếu có)

## Current Step
- Step: [create-spec | review-spec | create-plan | review-plan | implement-plan | review-implement | qa-automation]
- Review mode: [standard | fast] (chỉ cho review steps)
- Previous review output: .codex/pipeline/PLAN_<NAME>/NN-step.output.md (nếu re-review)

## Output
- Report: .codex/pipeline/PLAN_<NAME>/NN-step.output.md
- Contract: .codex/pipeline/PLAN_<NAME>/NN-step.output.contract.json
```

### Ví dụ spawn message cho standard mode review-plan (persona agent)

```text
## Task
Review plan PLAN_CHECKOUT_REDESIGN từ góc nhìn Senior Developer.
Đọc plan file, đánh giá theo 4 criteria trong developer_instructions, trả structured findings.

## Plan
- Plan name: PLAN_CHECKOUT_REDESIGN
- Plan file: .codex/plans/PLAN_CHECKOUT_REDESIGN/plan.md
- Spec file: .codex/plans/PLAN_CHECKOUT_REDESIGN/spec.md

## Current Step
- Step: review-plan (standard mode, lần đầu)
- Persona: senior_developer

## Expected Output
Trả text response với: structured findings (severity + evidence), điểm 4 criteria, verdict contribution.
Orchestrator sẽ merge output từ 4 persona agents.
```

### Ví dụ spawn message cho fast mode review-plan (1 agent)

```text
## Task
Re-review plan PLAN_CHECKOUT_REDESIGN từ cả 4 góc nhìn (PM, UX, Dev, Arch).
Tập trung vào delta changes so với review trước.

## Plan
- Plan name: PLAN_CHECKOUT_REDESIGN
- Plan file: .codex/plans/PLAN_CHECKOUT_REDESIGN/plan.md
- Spec file: .codex/plans/PLAN_CHECKOUT_REDESIGN/spec.md

## Current Step
- Step: review-plan (fast mode, re-review)
- Previous review: .codex/pipeline/PLAN_CHECKOUT_REDESIGN/02-review-plan.output.md

## Output
- Report: .codex/pipeline/PLAN_CHECKOUT_REDESIGN/02-review-plan.output.md
- Contract: .codex/pipeline/PLAN_CHECKOUT_REDESIGN/02-review-plan.output.contract.json
```

### Rules

1. **Luôn kèm file paths** — child agent không cần mò tìm
2. **Không nhét file content** — child tự đọc từ disk
3. **Nói rõ step + mode** — child biết đang ở đâu trong pipeline
4. **Nói rõ expected output** — child biết trả gì cho parent
5. **Giữ ngắn gọn** — metadata chỉ chiếm vài dòng, không phải essay


## Canonical flows

> **Global Loop Constraint:** Tất cả các luồng auto-fix (khi Worker hoặc Reviewer trả về `NEEDS_REVISION` hoặc `FAIL`) đều bị giới hạn ở **Max Retry = 3 lần**. Nếu vượt quá 3 lần lặp lại cùng một step, Orchestrator PHẢI dừng toàn bộ luồng, báo lỗi và chuyển sang trạng thái `WAITING_USER`. Hành vi này chống lặp vĩnh viễn (infinite loop).

### `/lp:spec`

1. Normalize `plan_name`
2. `start-spec`
3. Spawn `@create-spec`
4. `sync-output` từ `00-create-spec.output.contract.json`
5. Spawn step review-spec (chọn mode: Standard gọi 4 persona agents, Fast gọi `@review-spec`)
6. `sync-output` từ `00-review-spec.output.contract.json`
7. Nếu review pass, set `spec_approved = true`
8. Nếu review trả về `NEEDS_REVISION` hoặc `FAIL` và chưa chạm max retry: Quay lại bước 3 (spawn lại `@create-spec` để revise dựa trên feedback review)
9. Nếu chạm max retry hoặc dính Blocker cần user quyết định: Dừng ở `WAITING_USER`
10. Khi đã pass, dừng ở human gate, chờ `/lp:plan`

### `/lp:plan`

1. Normalize `plan_name`
2. `start-plan`
3. Nếu requirement chưa đủ rõ theo spec checklist, orchestrator auto-insert `create-spec` -> `review-spec` trước
4. Nếu đã có workflow `spec` và `create-spec = PASS` + `review-spec = PASS`, orchestrator promote cùng workflow sang lane `plan` (không tạo workflow mới)
5. Spawn `@create-plan`
6. `sync-output` từ `01-create-plan.output.contract.json`
7. Nếu state cho phép, spawn step review-plan (chọn mode: Standard gọi 4 persona agents, Fast gọi `@review-plan`)
8. `sync-output` từ `02-review-plan.output.contract.json`
9. Nếu review pass, set `plan_approved = true`
10. Nếu review trả về `NEEDS_REVISION` hoặc `FAIL` và chưa chạm max retry: Quay lại bước 5 (spawn lại `@create-plan` để revise dựa trên feedback review)
11. Nếu chạm max retry hoặc dính Blocker cần user quyết định kiến trúc: Dừng ở `WAITING_USER`
12. Khi đã pass, dừng ở human gate, chờ `/lp:implement`

### `/lp:implement`

1. Resolve workflow theo `workflow_id`, `plan_name`, hoặc `plan_file`
2. Assert `plan_approved = true`
3. `start-implement`
4. Pre-implement scope/dependency guard + baseline gate theo contract `baseline_verify_command` -> `baseline` label fallback
5. Spawn `@implement-plan`
6. Sync `03-implement-plan.output.contract.json`
7. Nếu pass, spawn step review-implement (chọn mode: Standard gọi 4 persona agents, Fast gọi `@review-implement`)
8. Sync `04-review-implement.output.contract.json`
9. Nếu review pass, spawn `@qa-automation`
10. Sync `05-qa-automation.output.contract.json`
11. Nếu worker (`implement-plan`, `qa-automation`) trả về `FAIL` hoặc review (`review-implement`) trả về `NEEDS_REVISION`/`FAIL`, và chưa chạm max retry: Quay lại bước 5 (spawn lại `@implement-plan` để auto-fix)
12. Nếu chạm max retry hoặc cần user confirm (critical/uncertain blocker): Dừng ở `WAITING_USER`
13. Khi đã pass (cả qa-automation pass), dừng ở human gate, chờ done/close task

### `/lp:cook`

1. `start-cook`
2. Chạy `create-spec` -> `review-spec` trước để chốt requirement + UX flow + happy/edge cases
3. Chạy full planning loop
4. Chỉ khi `plan_approved = true` mới vào delivery loop
5. Chạy full delivery loop
6. Nếu vượt retry budget, có blocker, hoặc cần user input thì dừng

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

- Top-level LP worker steps (`create-spec`, `review-spec`, `create-plan`, `review-plan`, `implement-plan`, `review-implement`, `qa-automation`, `debug-investigator`) bắt buộc dùng agents; parent agent là orchestrator, không tự thay worker step khi flow canonical yêu cầu agent worker.
- Mặc định spawn các top-level LP agents ngay trong current workspace, không dùng worktree isolation.
- Chỉ dùng worktree isolation nếu user explicit yêu cầu.
- Top-level LP worker steps phải chạy foreground.
- **Cấm** `run_in_background=true` cho top-level LP agents vì orchestrator cần result ngay để sync contract, set gate, và quyết định step kế tiếp.
- Background execution chỉ được xem xét ở child-job level sau này, không áp dụng cho top-level primary-run orchestration.
- Nếu user explicit yêu cầu worktree isolation, vẫn giữ top-level LP worker steps ở foreground; worktree không làm thay đổi foreground rule.
- Trước khi qua step top-level tiếp theo, orchestrator phải sync contract/state của step hiện tại.
- Với step review (`review-plan`, `review-spec`, `review-implement`), orchestrator chọn **review mode** dựa trên review history:
  - **Standard mode** (lần review đầu tiên): **BẮT BUỘC spawn 4 persona agents lẻ** (`@persona-senior-pm`, `@persona-senior-uiux`, `@persona-senior-dev`, `@persona-system-arch`) chạy song song → orchestrator merge verdict. KHÔNG spawn `@review-plan` / `@review-spec` / `@review-implement` ở mode này.
  - **Fast mode** (re-review trong loop): **BẮT BUỘC spawn 1 agent worker tương ứng** (`@review-plan`, `@review-spec`, hoặc `@review-implement`). Agent này sẽ nhận metadata và tự chạy multi-persona.
- Cách xác định mode: nếu step review hiện tại đã có ít nhất 1 lần `PASS`, `NEEDS_REVISION`, hoặc `FAIL` trước đó trong cùng workflow → fast mode. Nếu chưa có → standard mode.
- Không được bỏ qua persona nào ở cả 2 modes.
- Intent của policy này là `use agents, but no worktree by default`, không phải `avoid agents`.

## Standard Mode Merge Protocol

> Áp dụng cho **standard mode** (lần review đầu tiên) của `review-spec`, `review-plan`, `review-implement`.
> Orchestrator là người thực hiện merge — không phải worker.
> Thực hiện theo đúng 4 bước dưới đây, theo thứ tự.

### Bước 1 — Collect persona outputs

Chờ **đủ 4 persona agents** hoàn thành. Thu thập từ mỗi agent:
- Raw findings list: `[{ severity, issue, evidence }]`
- 4 criteria scores (0..10) của persona đó

> ❗ **Fail-fast**: Nếu bất kỳ persona nào không trả output hợp lệ (crash, timeout, thiếu evidence) → verdict tự động là `FAIL`. Không tiến hành merge.

### Bước 2 — Conflict normalization (finding-level)

Với mỗi issue xuất hiện từ nhiều persona, áp quy tắc sau **theo thứ tự ưu tiên**:

| Tình huống | Quy tắc xử lý |
|---|---|
| Có bất kỳ persona nào đánh `Blocker` cho issue đó | Giữ `Blocker` — không downgrade |
| ≥ 2 persona raise cùng issue, severity khác nhau | Dùng severity **cao nhất** |
| ≥ 2 persona raise cùng issue, severity bằng nhau | Merge thành 1 finding, `confidence = high` |
| Chỉ 1 persona raise, các persona khác không mention | Giữ nguyên, `confidence = medium` |
| 2 persona **mâu thuẫn** (A: Major/Blocker, B: không có issue) | Đánh `conflict_status = needs_human_confirmation` — **không được chốt `PASS`** |

Sau bước này, orchestrator có danh sách `validated_findings` và `unresolved_conflicts`.

### Bước 3 — Weighted score calculation

Tính score của từng persona = trung bình 4 criteria của persona đó.

Sau đó tính weighted score tổng:

```
weighted_score =
  senior_developer    × 0.30 +
  system_architecture × 0.30 +
  senior_pm           × 0.20 +
  senior_uiux_designer × 0.20
```

### Bước 4 — Final verdict (priority table)

Áp dụng **theo thứ tự từ trên xuống** — điều kiện nào đúng trước thì thắng:

| Priority | Điều kiện | Verdict |
|---|---|---|
| 1 | Có ≥ 1 validated `Blocker` | `FAIL` |
| 2 | Còn finding `needs_human_confirmation` chưa resolve | `NEEDS_REVISION` |
| 3 | `weighted_score < 6.0` | `FAIL` |
| 4 | `weighted_score` trong `[6.0, 8.0)` hoặc có ≥ 1 validated `Major` | `NEEDS_REVISION` |
| 5 | `weighted_score >= 8.0` + đủ 4 persona + không Blocker + không Major | `PASS` |

Sau khi có verdict, orchestrator ghi `NN-step.output.md` và `NN-step.output.contract.json`.

> **Anti-pattern**: Không dùng majority vote đơn giản ("3/4 nói PASS thì PASS"). Phải đi qua đủ 4 bước trên.

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

- `review-plan`, `review-spec`, `review-implement` là worker-only skills — chỉ trả structured findings/contract cho orchestrator gate, không tự orchestration sang step tiếp theo.
- Canonical roster 4 persona là hard requirement cho cả 2 modes.
- **Standard mode** (lần đầu): Spawn 4 agents độc lập là `@persona-senior-pm`, `@persona-senior-uiux`, `@persona-senior-dev`, và `@persona-system-arch`. Orchestrator **phải chạy đủ 4 bước trong `Standard Mode Merge Protocol`** (section bên trên) để tổng hợp verdict và ghi final contract.
- **Fast mode** (re-review): Spawn 1 agent tương ứng là `@review-plan`, `@review-spec`, hoặc `@review-implement`. Worker tự thu thập delta và trả findings. Orchestrator vẫn là người ghi contract cuối cùng.
- Findings từ review skills không được dùng để set verdict cuối nếu chưa qua conflict normalization và weighted scoring (xem `Standard Mode Merge Protocol`).

## Machine contracts

Mỗi worker step phải ghi 2 files:
- Human report: `NN-step.output.md`
- Machine contract: `NN-step.output.contract.json`

State sync ưu tiên JSON contract.
- Không được start step top-level tiếp theo trước khi contract của step hiện tại đã được sync.

## References

- `~/.agents/skills/lp-state-manager/SKILL.md` (global skill) hoặc local mirror khi đang dev skill
- `~/.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py` (global skill) hoặc local mirror khi đang dev skill
- `.agents/skills/lp-pipeline-orchestrator/references/commands.md` (command index + accessors `single-regression-check.command` / `degraded-design-drift-check.command`)
- `.agents/skills/lp-pipeline-orchestrator/references/worktree-manager.md`
- `.agents/skills/lp-pipeline-orchestrator/references/operator-waiting-user-contract.md`
- `.agents/skills/lp-pipeline-orchestrator/references/phase-notes-template.md`
- `.agents/skills/lp-pipeline-orchestrator/references/phase-report-template.md`
- `AGENTS.md (section 6: Decision Gate Policy)` — khi nào dùng `AskUserQuestion` và khi nào không
