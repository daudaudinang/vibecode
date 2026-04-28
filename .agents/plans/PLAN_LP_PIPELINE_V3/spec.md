# SPEC: PLAN_LP_PIPELINE_V3

> **LP Pipeline v3 — Epic/Single Classification + Git-Native Phase Management**

---

## 1. Business Context

### 1.1 Goal

Redesign LP pipeline architecture để giải quyết 3 vấn đề kiến trúc cùng gốc:
1. **Không có execution isolation** — hiện tại không có worktree hay branch strategy, mọi thay đổi trực tiếp trên working directory → không thể làm việc song song hoặc rollback sạch. V3 xây infrastructure (worktree + branch per phase) làm nền tảng cho parallel execution ở iteration sau.
2. **Spec drift cho task lớn** — state quản lý per-plan, không per-phase, dẫn đến implement xa dần spec khi task có nhiều phases
3. **Artifact bloat** — pipeline artifacts (`.codex/pipeline/`) tích lũy không dọn, tốn token + context LLM

**Giải pháp V3 (safe incremental)**: Tạo 2 modes (Single / Epic), thêm complexity assessment riêng, và dùng git branches + worktrees làm execution isolation cho **Epic mode**. Để giảm migration risk, V3 **giữ `.codex/` làm canonical runtime artifact root** và **giữ SQLite làm orchestration backbone**. Phase notes + phase reports được thêm như human-readable artifacts cho Epic workflows; chúng hỗ trợ phase-level context, reviewability, và resume clarity nhưng **không thay thế** runtime coordination layer trong V3. Artifact đang review trong `.agents/plans/PLAN_LP_PIPELINE_V3/` chỉ là **design workspace** cho initiative này; khi triển khai runtime thật, artifacts bắt buộc publish dưới `.codex/*`.

> **Scope note**: V3 xây foundation cho parallelism (worktree infra + phase isolation) nhưng chưa enable parallel phase execution. Các phases chạy **tuần tự** trong V3. Parallel execution là mục tiêu của V3.1+.

### 1.2 In-scope

1. **Complexity assessment framework** — 6 chiều đánh giá để agent recommend Single vs Epic mode
2. **`assess-complexity` step riêng** — tách khỏi `create-plan`
3. **Epic plan template** — template chuẩn cho epic-level planning (invariants, constraints, phase boundaries)
4. **Phase notes structure** — file riêng per phase, living document cập nhật sau mỗi bước pipeline
5. **Phase report** — summary tổng hợp sau khi phase hoàn thành, lưu trên main sau merge
6. **Worktree management** — tạo/dọn worktree + branch cho Epic phases
7. **Orchestrator refactor** — thêm mode classification + Epic implement flow tuần tự
8. **`.codex/AGENTS.md` update** — cập nhật global instruction chain
9. **Worker SKILL.md + TASK.md update** — sync behavior mới cho toàn bộ workers
10. **`vibecode-doctor` update** — phản ánh đúng runtime state mới

### 1.3 Out-of-scope

- ❌ Tối ưu pipeline strategy bên trong phase (differentiated review per phase size) — sẽ làm ở iteration sau
- ❌ **Parallel phase execution** — V3 chạy phases tuần tự. Parallel cần worktree foundation (V3) + ownership matrix enforcement (V3.1)
- ❌ Model selection guidance cho subagents (từ Superpowers)
- ❌ Migration tool cho old plans — old plans giữ nguyên, flow cũ vẫn chạy cho chúng
- ❌ Path migration từ `.codex/*` sang `.agents/plans/*`
- ❌ Xóa `state_manager.py` — V3 vẫn giữ làm runtime backbone
- ❌ Xóa `.codex/` directory — giữ cho backward compat

> **Backward compat strategy**: V3 giữ `.codex/plans/` + `.codex/pipeline/` làm canonical runtime layout. Existing Single workflows tiếp tục chạy theo flow hiện tại. Epic support được thêm dần trên cùng runtime surface để tránh full rewrite trong một đợt.

### 1.4 Constraints

- **Backward compatible**: Single mode phải giữ nguyên behavior cho existing workflows — KHÔNG regression
- **`.codex/*` canonical trong V3**: Không đổi runtime artifact root trong V3
- **SQLite vẫn là orchestration backbone trong V3**: Giữ runtime coordination cho backward compatibility
- **Agent only recommends mode**: Quyết định Single vs Epic thuộc user, agent chỉ recommend + evidence
- **Phase notes = per-file**: Mỗi phase có file notes riêng (Option A) để parallel phases không conflict
- **Epic phases chạy tuần tự**: Chưa enable parallel phase execution trong V3
- **Pipeline bên trong Epic phase chỉ là delivery loop**:
  - `implement-plan`
  - `review-implement`
  - `qa-automation`
- **`.codex/AGENTS.md` phải đồng bộ**: Mọi thay đổi behavior phải reflect trong global instruction chain

---

## 2. User & UX Flows

> **Note**: Đây là agent infrastructure, không có human UI. "User" = developer sử dụng LP commands. "UX" = developer experience khi tương tác với pipeline.

### 2.1 Happy Paths

#### Flow A: Single Pipeline (task nhỏ-vừa)

```
1. User: "/lp:plan - Add validation to checkout form"
2. Agent: create-spec → spec.md
3. Agent: review-spec (4-persona)
4. Agent: assess-complexity
   ├── Chạy complexity assessment (6 chiều)
   ├── Score: 6/18 → Recommend Single
   └── Trình bày assessment + recommendation
5. User: Confirm "Single pipeline"
6. Agent: create-plan → plan.md (standard template, không phases section)
7. Agent: review-plan (4-persona)
8. User: Approve plan
9. Agent: implement → review-implement → QA (flow giữ nguyên hiện tại)
10. Done → report.md

Artifacts:
  .codex/plans/PLAN_CHECKOUT_VALIDATION/
    spec.md
    plan.md
    report.md
```

#### Flow B: Epic Pipeline (task lớn)

```
1. User: "/lp:plan - Build authentication system with JWT + refresh + session"
2. Agent: create-spec → spec.md (epic-level)
3. Agent: review-spec (4-persona)
4. Agent: assess-complexity
   ├── Chạy complexity assessment (6 chiều)
   ├── Score: 15/18 → Strongly Recommend Epic
   ├── D1 (Domain crossing) = 3: auth + API + session + frontend
   ├── D5 (Risk) = 3: public API change + DB migration
   ├── D6 (Context) = 3: >500 LOC, >2000 LOC context
   └── Trình bày assessment + phase decomposition proposal
5. User: Confirm "Epic" mode
6. Agent: create-plan → plan.md (epic template)
   ├── Invariants section (constraints cho ALL phases)
   ├── Phase list (3 phases + dependencies)
   └── phases/ folder reference
7. Agent: review-plan (4-persona)
8. User: Approve epic plan + phase breakdown chính thức
9. User: "/lp:implement PLAN_AUTH_SYSTEM"
10. Agent: đọc epic plan → phase 1 (JWT middleware)
    ├── Tạo branch: lp/PLAN_AUTH_SYSTEM/phase-01-jwt
    ├── Tạo worktree: .worktrees/phase-01-jwt/
    ├── Tạo phase notes: .codex/plans/PLAN_AUTH_SYSTEM/phases/phase-01-jwt-notes.md
    ├── Chạy pre-flight `baseline-verify`, rồi vào delivery loop bên trong worktree:
    │   implement-plan → review-implement → qa-automation
    ├── Sau MỖI step ở trên (`baseline-verify`/`implement-plan`/`review-implement`/`qa-automation`): update phase notes ngay (status/current_step/retry_count + decisions/debt nếu có)
    ├── Generate phase report: .codex/plans/PLAN_AUTH_SYSTEM/phases/phase-01-jwt-report.md
    ├── Merge branch vào main
    └── Cleanup worktree + delete branch
11. Agent: phase 2 (refresh token) — tương tự step 10
    ├── Đọc phase-01 report + Notes for Later Phases trước khi bắt đầu
    └── Biết phase 1 đã chốt gì, debt gì
12. Agent: phase 3 (session management) — tương tự
13. Agent: Final integration QA trên main (sau khi merge tất cả phases)
14. Done → epic report

Artifacts:
  .codex/plans/PLAN_AUTH_SYSTEM/
    spec.md
    plan.md
    phases/
      phase-01-jwt-notes.md
      phase-01-jwt-report.md
      phase-02-refresh-notes.md
      phase-02-refresh-report.md
      phase-03-session-notes.md
      phase-03-session-report.md
    report.md
```

### 2.2 Alternate Paths

#### Alt A: User overrides agent recommendation

```
Agent recommends Epic (score 14) → User says "Chạy single thôi, deadline gấp"
→ Agent: OK, tạo single plan
→ Flow tiếp tục như Flow A
```

#### Alt B: User changes mind mid-epic

```
Đang implement phase 2 → User: "Merge phase 2 thôi, phase 3 cancel"
→ Agent: merge phase 2, update epic plan (phase 3 = CANCELLED)
→ Chạy final QA trên main
```

#### Alt C: Phase fails after 3 retries

```
Phase 1 implement → review fails 3 times
→ Rollback Protocol kích hoạt
→ Agent: báo user, dừng epic
→ User quyết định: retry / skip phase / abandon epic
```

#### Alt D: Single plan cần thêm spec trước

```
User: "/lp:plan ..." → Agent: requirement chưa đủ rõ
→ Auto-insert create-spec → review-spec trước create-plan
→ (Giữ nguyên behavior hiện tại)
```

### 2.3 Edge/Error Paths

#### Edge 1: Worktree creation fails

```
git worktree add fails (unclean state, locked worktree)
→ Agent: report error + suggest "git worktree prune" hoặc manual cleanup
→ Agent dùng recovery prompt chuẩn:
   - Error: <worktree creation failure reason>
   - Required action: cleanup worktree state / fix git state
   - Next command: `/lp:implement PLAN_<NAME>` sau khi fix xong
→ `waiting_user`
```

#### Edge 2: Merge conflict khi merge phase branch

```
Phase 1 merge OK → Phase 2 merge → conflict
→ Agent: report conflicting files
→ Agent dùng recovery prompt chuẩn:
   - Error: merge conflict
   - Required action: resolve conflicts + commit merge result
   - Conflict files: <list>
   - Next command: `/lp:implement PLAN_<NAME>`
→ `waiting_user` (agent KHÔNG tự resolve merge conflicts)
```

#### Edge 3: Phase dependency not met

```
Phase 2 depends on phase 1, nhưng phase 1 chưa PASS
→ Agent: block phase 2, báo dependency chưa met
→ Default: `waiting_user`
→ Chỉ auto-start dependency phase khi user đã explicit bật `auto_start_dependencies = true` trong epic plan
→ Nếu phase được đánh dấu `dependency_critical = true` mà dependency chưa khai báo rõ trong plan: KHÔNG fallback tuyến tính, chuyển `waiting_user` để user/reviewer bổ sung dependency graph
```

#### Edge 4: Worktree already exists

```
User retry phase 1 → worktree .worktrees/phase-01-jwt/ đã tồn tại
→ Agent: detect existing worktree
→ Option A: resume (nếu branch vẫn đúng)
→ Option B: cleanup + recreate (nếu stale)
→ Agent dùng recovery prompt chuẩn:
   - Error: stale/existing worktree detected
   - Required action: chọn resume hoặc cleanup
   - Next command: `/lp:implement PLAN_<NAME>` sau khi quyết định xong
→ `waiting_user` để user chọn
```

#### Edge 5: Git branch name collision

```
Branch lp/PLAN_AUTH/phase-01-jwt đã tồn tại (từ run trước)
→ Agent: detect branch collision
→ Agent dùng recovery prompt chuẩn:
   - Error: branch name collision
   - Required action: confirm cleanup branch cũ hoặc chọn branch name khác
   - Next command: `/lp:implement PLAN_<NAME>` sau khi quyết định xong
→ Nếu branch cũ đã merged: hỏi user confirm cleanup branch cũ rồi mới delete + recreate
→ Nếu branch cũ chưa merged hoặc user không confirm: chuyển `waiting_user`
```

#### Edge 6: .worktrees/ not in .gitignore

```
Trước khi tạo worktree → check .gitignore
→ Nếu .worktrees/ chưa ignored: dừng flow + yêu cầu repo setup fix
→ Agent dùng recovery prompt chuẩn:
   - Error: `.worktrees/` chưa được ignore
   - Required action: thêm `.worktrees/` vào `.gitignore` rồi commit/persist repo setup
   - Next command: `/lp:implement PLAN_<NAME>` sau khi fix xong
→ Phase chuyển `waiting_user` cho tới khi repo setup được fix
→ KHÔNG auto-commit ngầm trong lúc implement epic
```

---

## 3. Agent Behavior Expectations

> Thay vì UI states, section này mô tả expected agent behavior cho từng tình huống.

### 3.0 Execution Model Summary

- `assess-complexity` là step riêng, chạy trước `create-plan`
- Single mode giữ flow hiện tại
- Epic mode chỉ thêm phase decomposition + worktree isolation
- Trong V3, mỗi Epic phase **không** chạy lại `create-spec` / `review-spec` / `create-plan` / `review-plan`
- Trong V3, mỗi Epic phase có 1 bước pre-flight bắt buộc: `baseline-verify`
- Sau `baseline-verify`, phase mới vào delivery loop chính thức:
  1. `implement-plan`
  2. `review-implement`
  3. `qa-automation`

### 3.1 Complexity Assessment Output

Agent PHẢI trình bày structured table khi recommend mode:

**Recommendation mapping (canonical trong V3):**

| Điều kiện | Recommendation |
|---|---|
| Có bất kỳ veto rule nào trigger | Epic |
| Total score `0-6` | Single |
| Total score `7-11` | User decides |
| Total score `12-18` | Epic |

**Veto rules:**
- `D6 (Context pressure) = 3` → luôn recommend Epic

**Rubric tối thiểu cho từng chiều (để review/implementation tái lập kết quả):**
- D1 Domain crossing: `0 = 1 module`, `1 = 2 modules cùng bounded context`, `2 = >=2 modules khác bounded context`, `3 = backend + frontend + shared contract/data`
- D2 Interface surface: `0 = internal-only`, `1 = 1 internal contract`, `2 = nhiều internal contracts hoặc 1 public API`, `3 = nhiều public/external interfaces`
- D3 Dependency chain: `0 = độc lập`, `1 = 1 dependency trực tiếp`, `2 = chuỗi 2-3 bước hoặc cần sequencing rõ`, `3 = DAG nhiều nhánh / dependency-critical`
- D4 Decision ambiguity: `0 = spec rõ`, `1 = còn 1-2 decision nhỏ`, `2 = còn decision ảnh hưởng thiết kế`, `3 = nhiều decision mở cần user chốt`
- D5 Risk surface: `0 = low-risk refactor`, `1 = thay đổi cục bộ`, `2 = đổi logic ảnh hưởng flow chính`, `3 = DB/public API/security/runtime risk`
- D6 Context pressure: `0 = <150 LOC / ít file`, `1 = 150-300 LOC hoặc vài file`, `2 = 300-500 LOC hoặc context rộng`, `3 = >500 LOC hoặc >2000 LOC context`

Nếu score nằm trong vùng `User decides`, agent PHẢI nêu trade-off cụ thể giữa Single vs Epic cho case đó. Chi tiết examples/rubric đầy đủ được chuẩn hóa thêm tại `.agents/skills/lp-pipeline-orchestrator/references/complexity-assessment.md`, nhưng bảng trên là minimum contract bắt buộc để re-score được ngay trong spec.

```markdown
## Complexity Assessment

| Chiều | Score | Evidence |
|---|---|---|
| D1 Domain crossing | 2 | Sửa auth module + API layer |
| D2 Interface surface | 1 | 1 shared type thay đổi |
| D3 Dependency chain | 2 | Phase 2 phụ thuộc phase 1 |
| D4 Decision ambiguity | 1 | Spec đã rõ ràng |
| D5 Risk surface | 3 | DB schema change + public API |
| D6 Context pressure | 2 | ~350 LOC sửa |

**Total: 11/18 → Recommend: User quyết định**

[Explain trade-offs giữa Single vs Epic cho case này]
```

### 3.2 Phase Notes Update Behavior

Sau MỖI bước pipeline trong 1 phase, agent PHẢI update phase notes file.

**Phase notes PHẢI có YAML frontmatter** để agent parser xác định chính xác current state:

```markdown
---
phase: phase-01-jwt
epic: PLAN_AUTH_SYSTEM
status: in_progress  # pending | in_progress | waiting_user | completed | failed | cancelled
current_step: review-implement  # baseline-verify | implement-plan | review-implement | qa-automation | merge-phase
retry_count: 1
state_version: 7  # increment mỗi lần sync state transition thành công
last_updated: 2026-04-23T18:00:00+07:00
---

## Pipeline Progress
- [x] implement-plan (PASS)
- [ ] review-implement (IN_PROGRESS, retry 1)
- [ ] qa-automation
- [ ] merge-phase

## Decisions Log
- [2026-04-23T16:00] Dùng JWT RS256 thay HS256 (source: user)
- [2026-04-23T17:00] Skip rate limiting, để phase-02 (source: review)

## Technical Debt
- Token refresh endpoint chưa có integration test

## Notes for Later Phases
- Phase-02 cần đọc JWT_SECRET config từ env
```

**Resume rule**: Khi agent resume:
- đọc frontmatter để lấy phase-local context + mirror status
- dùng SQLite để lấy authoritative phase status set (`waiting_user` / `in_progress` / `pending`) + `current_step` / `resume_point` chính xác
- dùng SQLite để validate `retry_count`/`state_version`, và dùng phase notes cho phase-local context + human-readable mirrors
- nếu có nhiều candidate phases: chọn theo thứ tự deterministic từ SQLite status `waiting_user` → `in_progress` → `pending` đã satisfied dependencies, tie-break bằng phase index nhỏ nhất
- chỉ resume phase khi `phase_notes.state_version` khớp với state snapshot/version do SQLite publish ở lần sync gần nhất; nếu lệch mà không auto-heal được → `waiting_user`

**Status semantics**:
- `failed`: step fail nhưng chưa cần user action
- `waiting_user`: blocked, cần user decision hoặc manual intervention

**Retry contract (deterministic):**
- `retry_count` tính theo **phase delivery step đang active** (`implement-plan` hoặc `review-implement` hoặc `qa-automation`)
- `retry_count` authoritative nằm trong SQLite machine state; phase notes chỉ mirror để human đọc nhanh
- Mỗi lần cùng step trả `FAIL`/`NEEDS_REVISION` và loop quay lại step đó: tăng `retry_count += 1` trong cùng SQLite transition
- Khi phase chuyển sang step kế tiếp thành công: reset `retry_count = 0` cho step mới trong cùng SQLite transition
- Ngưỡng `3 retries` áp dụng **per-phase per-step**, không cộng dồn toàn epic
- Chạm ngưỡng 3: phase chuyển `waiting_user`, publish rollback/recovery note, không auto thử lần 4

**State authority matrix (canonical trong V3)**:

| Field / concern | Authority |
|---|---|
| `current_step` / `resume_point` | SQLite |
| `retry_count` | SQLite authoritative, phase notes mirror |
| `state_version` (phase-level sync token) | SQLite publish -> phase notes mirror |
| `status` (phase-level resume status) | SQLite authoritative, phase notes mirror |
| `current_step` mirror trong phase notes | derived from SQLite, non-authoritative |
| Decisions Log / Technical Debt / Notes for Later Phases | phase notes |
| branch/worktree existence | Git state |
| reviewable outputs / contracts | published artifacts |

**Conflict handling**:
- Nếu SQLite `current_step` và phase-notes mirror của `current_step` mâu thuẫn nhau:
  - soft mismatch: nếu evidence cho thấy SQLite vừa được persist thành công và phase notes chỉ stale mirror (ví dụ crash giữa bước 2 và 3), orchestrator được phép auto-heal phase-notes mirror theo SQLite + publish reconciliation note
  - hard mismatch: nếu không chứng minh được đó chỉ là stale mirror, orchestrator PHẢI chuyển `waiting_user` + publish reconciliation note
- Không có chế độ “SQLite tự thắng và tiếp tục im lặng” khi đã detect mismatch.

**State commit protocol (canonical cho mỗi step transition)**:
1. Compute next authoritative `current_step` + phase `status` trong SQLite
2. Persist `current_step` + `status` + `state_version` trong **một SQLite transaction atomic duy nhất**
   - transaction write PHẢI dùng optimistic concurrency guard với `expected_state_version`
   - nếu `expected_state_version` không khớp snapshot hiện tại: abort transition + chuyển `waiting_user` hoặc retry reconcile
3. Sync phase-notes mirror (`status`, `retry_count`, `state_version`, `current_step` mirror, notes) từ snapshot SQLite vừa persist
4. Nếu bước liên quan Git state thì mới thực hiện Git mutation
5. Nếu crash giữa step 2 và 4:
   - resume dựa trên SQLite
   - phase notes được coi là mirror có thể stale
6. Mọi transition PHẢI idempotent theo `(plan, phase, current_step, state_version)`

### 3.3 Phase Report Generation

Sau khi phase PASS, agent PHẢI generate immutable report:

```markdown
# Phase Report: phase-01-jwt

## Summary
- Files modified: 5
- LOC added: 230, removed: 15
- Tests: 8 passed, 0 failed

## Key Decisions
(Extracted from phase notes)

## Technical Debt
(Carried forward items)

## Notes for Next Phases
(Critical context)
```

**Dependency-aware context rule**:
- Nếu epic plan khai báo `dependencies` theo graph/DAG, phase mới PHẢI đọc report của **tất cả direct dependencies**
- Nếu phase không khai báo dependencies riêng và phase đó không được đánh dấu `dependency_critical`, fallback mặc định là phase ngay trước đó (`N-1`)
- Nếu phase được đánh dấu `dependency_critical = true` mà dependencies còn thiếu: chuyển `waiting_user`, không fallback tuyến tính
- `Notes for Later Phases` chỉ được đọc từ:
  - direct dependency phases
  - hoặc phase ngay trước đó trong linear flow

### 3.4 Worktree Lifecycle

```
CREATE:  git worktree add .worktrees/phase-<NN>-<name> -b lp/<plan>/phase-<NN>-<name>
         → verify .gitignore → project setup → baseline test
         
WORK:    pipeline runs inside worktree
         → phase notes committed vào phase branch để resume được
         → phase report generate ở phase branch trước merge

MERGE:   git checkout main → git merge lp/<plan>/phase-<NN>-<name>
         → if conflict → `waiting_user`
         → if clean → phase notes/report xuất hiện trên main sau merge
         → update epic plan status

CLEANUP: git worktree remove .worktrees/phase-<NN>-<name>
         → git branch -d lp/<plan>/phase-<NN>-<name>
```

---

## 4. Rules & Validation

### 4.1 Business Rules

| # | Rule | Enforcement |
|---|---|---|
| BR1 | Single mode PHẢI backward compatible với flow hiện tại | Regression test |
| BR2 | Epic mode PHẢI có invariants section trong plan | create-plan template validation |
| BR3 | Phase notes PHẢI được update sau mỗi pipeline step | Orchestrator enforcement |
| BR4 | Phase report PHẢI được generate trước merge | Merge precondition check |
| BR5 | Worktree PHẢI được cleanup sau merge | close-task / orchestrator |
| BR6 | Agent chỉ RECOMMEND mode, user DECIDE | Complexity assessment output format |
| BR7 | D6 (Context pressure) = 3 → luôn recommend Epic | Veto rule trong assessment |
| BR8 | `.codex/*` vẫn là canonical runtime root trong V3 | Runtime path validation |
| BR9 | SQLite vẫn là orchestration backbone trong V3 | Runtime command validation |
| BR10 | Mỗi Epic phase chỉ chạy delivery loop | Phase step validation |
| BR11 | Nếu dependency phase chưa PASS thì default là `waiting_user`, trừ khi plan explicit cho phép auto-start dependencies | Dependency gate validation |
| BR12 | Nếu một phase bị `cancelled` và là dependency bắt buộc của phase khác, downstream phase PHẢI bị block ở `waiting_user` cho tới khi user re-plan hoặc cancel downstream | Cancel dependency validation |

### 4.2 Validation Rules

| # | Rule | When |
|---|---|---|
| VR1 | `.gitignore` PHẢI chứa `.worktrees/` | Trước khi tạo worktree |
| VR2 | Branch name PHẢI theo pattern `lp/<plan>/phase-<NN>-<name>` | create-phase |
| VR3 | Phase notes file PHẢI tồn tại trước khi bắt đầu pipeline | create-phase |
| VR4 | Phase dependencies PHẢI satisfied trước khi start phase | implement-phase |
| VR5 | Baseline test PHẢI pass trong worktree trước implement | post-worktree-setup |
| VR6 | No unmerged changes trên main trước khi merge phase | pre-merge check |
| VR7 | Tất cả SKILL.md + TASK.md + AGENTS.md PHẢI consistent về `.codex/*` paths trong V3 | Cross-reference verify |
| VR8 | `assess-complexity` PHẢI chạy trước `create-plan` | plan flow validation |
| VR9 | Baseline verification command PHẢI lấy theo thứ tự ưu tiên đã định nghĩa | post-worktree-setup |
| VR10 | `current_step` và phase `status` PHẢI biểu diễn được merge/resume states | resume-state validation |
| VR11 | Nếu dùng dependency graph, context propagation PHẢI đọc direct dependencies thay vì giả định tuyến tính | dependency-context validation |
| VR12 | `No unmerged changes trên main` nghĩa là: working tree clean, không có merge in progress, không có conflict markers chưa resolve | pre-merge git-state validation |
| VR13 | Baseline verification fail PHẢI sync SQLite `current_step = baseline-verify` trước khi chuyển `waiting_user` | baseline-failure validation |
| VR14 | Phase report lifecycle PHẢI nhất quán: generate ở phase branch trước merge, visible trên main sau merge sạch | phase-report lifecycle validation |

### 4.3 Rule Precedence

1. **User decision > Agent recommendation** (mode selection)
2. **Plan file = source of truth cho invariants / dependencies / execution boundaries**
3. **Phase notes = source of truth cho phase-local notes/debt/decisions; `retry_count`/`status`/`state_version` chỉ là mirrors từ SQLite**
4. **Git branch + worktree state = source of truth cho branch/worktree existence**
5. **SQLite state = source of truth cho machine-level orchestration / current_step / resume point trong V3**
6. **Published reports/contracts = source of truth cho reviewable output evidence**

Nếu phase notes và SQLite mâu thuẫn:
- SQLite là authority cho `current_step` và phase `status`
- phase notes là authority cho phase-local detail (notes, debt, decisions); `retry_count`/`status`/`state_version` chỉ là mirrors từ SQLite
- soft mismatch do stale mirror được phép auto-heal từ SQLite + publish reconciliation note
- hard mismatch hoặc conflict không tự chứng minh được mới buộc `waiting_user`
- orchestrator phải publish reconciliation note trước khi resume hoặc yêu cầu user quyết định

---

## 5. Acceptance Criteria (Given/When/Then)

### AC1: Single Pipeline — No Regression

```
GIVEN: User chạy "/lp:plan" cho task có complexity score 0-6
WHEN:  Agent completes create-plan
THEN:  
  - `assess-complexity` chạy trước `create-plan`
  - Plan file ở `.codex/plans/PLAN_<NAME>/plan.md`
  - Plan KHÔNG có phases section
  - Flow tiếp tục theo same canonical delivery loop hiện tại: `implement-plan → review-implement → qa-automation`
  - KHÔNG tạo worktree, KHÔNG tạo phase notes
  - Vẫn dùng SQLite runtime coordination hiện tại
  - Verification contract tối thiểu cho backward compat:
    1. chạy **canonical single regression fixture** được khai báo trong `.agents/skills/lp-pipeline-orchestrator/references/commands.md` dưới accessor duy nhất `single-regression-check.command`, và accessor này PHẢI resolve thành **đúng 1 command deterministic**
    2. nếu fixture reference thiếu / rỗng / malformed / multi-candidate → AC1 = FAIL
    3. fixture trên PHẢI có expected evidence rõ: exit code = 0, không tạo artifact mới dưới `.worktrees/` và `.codex/plans/PLAN_<NAME>/phases/`
    4. assert top-level outputs vẫn publish đúng runtime shape bất biến của single flow: `.codex/pipeline/PLAN_<NAME>/03-implement-plan.output.*`, `04-review-implement.output.*`, `05-qa-automation.output.*`
    5. required contract fields tối thiểu cho mỗi output contract: `schema_version`, `skill`, `status`, `artifacts.primary`
```

### AC2: Complexity Assessment Visible

```
GIVEN: User chạy "/lp:plan" cho bất kỳ task nào
WHEN:  Agent hoàn thành `assess-complexity`
THEN:  
  - Output chứa bảng 6 chiều (D1-D6) với score + evidence
  - Output chứa recommendation (Single / User decides / Epic)
  - Output áp dụng đúng recommendation mapping:
    - `0-6` → Single
    - `7-11` → User decides
    - `12-18` → Epic
    - `D6 = 3` → Epic override
  - Output chứa câu hỏi cho user confirm mode
  - User response xác định mode tiếp theo
```

### AC3: Epic Plan Template

```
GIVEN: User confirm "Epic" mode
WHEN:  Agent tạo plan
THEN:  
  - plan.md chứa Invariants section (constraints cho ALL phases)
  - plan.md chứa Phase list (name + goal + owned modules + dependencies)
  - plan.md chứa reference tới phases/ folder
  - Tạo `.codex/plans/PLAN_<NAME>/phases/` directory
```

### AC4: Phase Worktree Lifecycle

```
GIVEN: Epic plan approved, user chạy "/lp:implement"
WHEN:  Agent bắt đầu phase 1
THEN:
  - .worktrees/ được check trong .gitignore
  - Branch lp/<plan>/phase-01-<name> được tạo từ main
  - Worktree .worktrees/phase-01-<name>/ được tạo
  - Phase notes file `.codex/plans/PLAN_<NAME>/phases/phase-01-<name>-notes.md` được tạo
  - SQLite `current_step` được khởi tạo tại `baseline-verify` trước khi vào implement
  - Pipeline chạy bên trong worktree
  - Phase chỉ chạy delivery loop: `implement-plan → review-implement → qa-automation`
  - `current_step` support đầy đủ cho resume, gồm cả `merge-phase`
```

### AC5: Phase Notes Updated

```
GIVEN: Pipeline đang chạy trong worktree cho phase 1
WHEN:  Mỗi bước pipeline hoàn thành (`baseline-verify` / `implement-plan` / `review-implement` / `qa-automation` / post-delivery `merge-phase`)
THEN:  
  - Phase notes YAML frontmatter được update:
    - status, current_step, retry_count, last_updated
  - Pipeline Progress checklist được update
  - Decisions Log, Technical Debt, Notes for Later Phases (if any)
```

### AC6: Phase Merge + Cleanup

```
GIVEN: Phase 1 pipeline hoàn thành (implement + review + QA = PASS)
WHEN:  Agent merge phase
THEN:
  - Phase report phases/phase-01-<name>-report.md được generate trên phase branch trước merge
  - Sau merge sạch, phase report xuất hiện trên main
  - Branch lp/<plan>/phase-01-<name> được merge vào main
  - Worktree .worktrees/phase-01-<name>/ được remove
  - Branch lp/<plan>/phase-01-<name> được delete
  - Epic plan trên main updated (phase 1 status = COMPLETED)
```

### AC7: Phase Context Propagation

```
GIVEN: Phase N completed, phase N+1 starting (N >= 1)
WHEN:  Agent bắt đầu phase N+1
THEN:
  - Agent đọc mặc định:
    1. Epic plan invariants (bắt buộc)
    2. Report của tất cả direct dependency phases
    3. `Notes for Later Phases` của direct dependency phases
  - Agent KHÔNG đọc raw notes của phases 1..N-1
  - Phase N+1 plan KHÔNG vi phạm epic invariants

Context budget rule:
  - Nếu flow linear và không khai báo dependency riêng: direct dependency mặc định là phase ngay trước đó (`N-1`)
  - Mặc định chỉ đọc epic invariants + report/notes của direct dependency phases
  - Chỉ khi epic plan explicit bật `broad_context_reports = true` và tổng số phase ≤ 5: được đọc thêm report của các phase completed trước đó theo thứ tự phase index tăng dần
  - Dù có `broad_context_reports = true`, agent vẫn KHÔNG đọc raw notes ngoài direct dependency phases
```

### AC8: V3 Runtime Coordination Compatibility

```
GIVEN: Bất kỳ flow nào trong v3
WHEN:  Pipeline chạy (single hoặc epic)
THEN:
  - `.codex/*` vẫn là canonical runtime artifact root
  - `state_manager.py` / SQLite vẫn được giữ cho machine-level orchestration trong V3
  - State được tách theo concern:
    - plan.md: invariants / phase definitions / execution boundaries
    - phase notes frontmatter: retry_count / human-readable mirrors / phase-local notes
    - SQLite: workflow coordination / authoritative phase selection status / authoritative `current_step` / machine resume metadata
  - Agent resume sau crash dùng:
    - phase notes để lấy mirror/context
    - SQLite để xác định phase nào cần resume + `current_step` / `resume_point`
  - Nếu SQLite và phase-notes mirror conflict: soft mismatch thì auto-heal, hard mismatch thì `waiting_user`
```

### AC9: Cross-Reference Consistency

```
GIVEN: Tất cả files đã được update
WHEN:  Chạy cross-reference verify trên `.agents/skills/` và `.codex/AGENTS.md`
THEN:
  - Verify command/check phải bao phủ cả `.agents/skills/**/*.md` lẫn `.codex/AGENTS.md`
  - Trong giai đoạn degraded design review trước khi publish runtime: chạy supplementary check được khai báo tại accessor duy nhất `degraded-design-drift-check.command` trong `.agents/skills/lp-pipeline-orchestrator/references/commands.md`
  - Command này PHẢI là negative-grep trên **forbidden patterns** đã khai báo rõ trong cùng reference; semantics bắt buộc: exit `0` = FAIL (phát hiện drift), exit `1` = PASS (không phát hiện drift)
  - Các active references trong V3 phải consistent với `.codex/*`
  - Các references tới `state_manager.py` phải phản ánh đúng vai trò runtime backbone trong V3
  - Tất cả artifact paths consistent giữa SKILL.md, TASK.md, và `.codex/AGENTS.md`
```

### AC10: Merge Conflict Handling + Resume Hook

```
GIVEN: Phase branch có changes conflict với main
WHEN:  Agent thử merge
THEN:
  - Agent KHÔNG tự resolve conflicts
  - Agent report conflicting files
  - Agent sync SQLite `status = waiting_user`, `current_step = merge-phase`, `state_version = state_version + 1` trước
  - Agent update phase-notes mirrors (`status`, `current_step`, `state_version`) sau khi SQLite persist thành công
  - Agent hướng dẫn user:
    1. Resolve conflicts manually
    2. Commit merge result
    3. Chạy `/lp:implement PLAN_<NAME>` để resume
  - Agent dùng template recovery prompt chuẩn:
    - `Error: merge conflict`
    - `Required action: resolve conflicts + commit merge result`
    - `Conflict files: <list>`
    - `Next command: /lp:implement PLAN_<NAME>`

Resume behavior (specialization của AC13 trong merge-conflict context):
  - `/lp:implement` đọc plan.md → detect epic mode
  - Đọc phase notes frontmatter để lấy mirror/context
  - Xác định phase resume từ SQLite authoritative status = `waiting_user`
  - Kiểm tra merge đã resolved (no conflict markers + no merge in progress)
  - Lấy `current_step` authoritative từ SQLite
  - Tiếp tục pipeline từ `current_step` đó
```

### AC11: Epic Partial Cancel

```
GIVEN: Epic đang chạy và user quyết định cancel một phase chưa bắt đầu hoặc chưa complete
WHEN:  Orchestrator nhận explicit user decision
THEN:
  - Epic plan được update với phase status = `cancelled`
  - Nếu phase đang `in_progress`: orchestrator KHÔNG được kill giữa command đang chạy; chỉ mark `cancel_requested` rồi dừng ở boundary an toàn tiếp theo
  - Khi command hiện tại kết thúc hoặc step boundary gần nhất đạt được: phase chuyển `cancelled`, giữ nguyên worktree/branch để user có thể inspect hoặc cleanup sau
  - Dependencies downstream được re-evaluate
  - Nếu phase bị cancel là dependency bắt buộc của phase downstream:
    - downstream phase KHÔNG được auto-start
    - downstream phase chuyển `waiting_user`
    - user phải chọn re-plan hoặc cancel downstream phase
  - Final QA scope chỉ còn các phase đã complete/merged
  - Epic report phải ghi rõ cancelled phases, adjusted scope, và phase nào bị cancel khi đang `in_progress`
```

### AC12: Final Integration QA

```
GIVEN: Tất cả phases đã merge vào main
WHEN:  Agent chạy final QA
THEN:
  - QA chạy trên main (integrated code)
  - QA verify epic-level ACs (không chỉ per-phase ACs)
  - Section `Final Integration Verify Commands` PHẢI tồn tại, không rỗng, và parse được theo schema machine-readable: danh sách có thứ tự, mỗi entry = `{ label: <string>, command: <non-empty string> }`; nếu thiếu / rỗng / malformed => final QA = FAIL
  - QA phải chạy **toàn bộ** commands theo đúng thứ tự khai báo trong section `Final Integration Verify Commands`
  - Fail-fast: dừng ngay tại command đầu tiên có exit != 0 và mark final QA = FAIL
  - Nếu có bất kỳ command nào exit != 0 hoặc có epic-level AC nào chưa được map sang evidence, final QA = FAIL
  - Epic report generated, kèm command list + exit status + AC-to-evidence mapping
```

### AC13: Resume After `waiting_user`

```
GIVEN: Pipeline đã dừng ở `waiting_user` (merge conflict, max retry, user input needed)
WHEN:  User chạy `/lp:implement PLAN_<NAME>` lại
THEN:
  - Orchestrator đọc plan.md → detect mode (single/epic)
  - Đọc phase notes frontmatter để lấy mirror/context
  - Liệt kê candidate phases từ SQLite authoritative status `waiting_user`, `in_progress`, hoặc `pending`
  - Chọn phase resume theo thứ tự deterministic: `waiting_user` → `in_progress` → `pending` đã satisfied dependencies; nếu hòa thì lấy phase index nhỏ nhất
  - Validate `state_version` của phase notes với snapshot/version từ SQLite; mismatch không auto-heal được thì chuyển `waiting_user`
  - Lấy `current_step` / `resume_point` authoritative từ SQLite cho phase đã chọn
  - KHÔNG chạy lại từ đầu
  - Nếu chỉ còn phases `pending` nhưng dependencies chưa satisfied: giữ `waiting_user` và báo rõ dependency blocker
  - Nếu không còn candidate phase → báo "Pipeline already completed"
```

### AC14: Baseline Verification Command Resolution

```
GIVEN: Epic phase vừa tạo worktree xong
WHEN:  Agent chuẩn bị chạy baseline verification
THEN:
  - Ưu tiên 1: dùng `baseline_verify_command` khai báo trong YAML frontmatter của phase file, với schema machine-readable: `{ command: <non-empty string>, expected_artifact?: <string> }`
  - Ưu tiên 2: dùng đúng 1 entry có label normalize về lowercase = `baseline` trong section `Verify Commands` của `plan.md`; whitespace đầu/cuối bị trim trước khi so khớp
  - Nếu có nhiều hơn 1 baseline candidate hợp lệ, label malformed, field thiếu `command`, hoặc phase file không đúng schema/frontmatter chuẩn → chuyển `waiting_user`
  - Nếu plan không khai báo baseline command rõ ràng → chuyển `waiting_user`
  - Không có fallback ngầm sang command repo-level không được khai báo trong plan artifact
```

### AC15: Baseline Verification Failure Handling

```
GIVEN: Agent đã resolve được baseline verification command
WHEN:  Baseline verification fail trước khi implement
THEN:
  - Agent KHÔNG bắt đầu `implement-plan`
  - Agent sync SQLite `current_step = baseline-verify`
  - Agent update phase-notes `current_step` mirror = `baseline-verify`
  - Agent publish failure summary + failed command output
  - Agent chuyển `waiting_user`
  - Agent dùng recovery prompt chuẩn:
    - `Error: baseline verification failed`
    - `Required action: fix baseline environment/test failure`
    - `Next command: /lp:implement PLAN_<NAME>`
```

### AC16: Rollout Success Metrics for V3

```
GIVEN: V3 implementation hoàn tất và được thử nghiệm nội bộ
WHEN:  Team đánh giá rollout outcome
THEN:
  - Có tối thiểu 1 metric cho execution isolation readiness, với baseline + target + owner + công thức + data source + 30-day measurement window
  - Có tối thiểu 1 metric cho spec-drift reduction, với baseline + target + owner + công thức + data source + 30-day measurement window
  - Có tối thiểu 1 metric cho artifact/runtime hygiene, với baseline + target + owner + công thức + data source + 30-day measurement window

Suggested starter metrics (contract đủ đo được):
  - `resume_success_rate = successful_epic_resumes / total_epic_resume_attempts`
    - baseline: đo từ 5 internal dry-runs đầu tiên của V3
    - target: `>= 0.80` trong cửa sổ 30 ngày
    - data source: workflow event log + SQLite resume records
    - owner: orchestration maintainer
  - `spec_drift_reopen_rate = epic_phases_reopened_due_to_spec_gap / total_epic_phases_started`
    - baseline: đo từ 5 internal dry-runs đầu tiên của V3
    - target: `<= 0.15` trong cửa sổ 30 ngày
    - data source: review-spec/review-plan/review-implement outputs + workflow state
    - owner: spec/process maintainer
  - `stale_phase_artifact_count = leftover_phase_worktrees + leftover_phase_branches + stale_phase_notes_after_completed_runs`
    - baseline: đo từ 5 internal dry-runs đầu tiên của V3
    - target: `= 0` tại mỗi weekly audit trong 30 ngày đầu
    - data source: git state + `.worktrees/` + `.codex/plans/PLAN_<NAME>/phases/` audit
    - owner: repo maintainer
```

### AC17: Mode Decision Audit Trail

```
GIVEN: Agent hoàn tất `assess-complexity`
WHEN:  User confirm hoặc override Single/Epic recommendation
THEN:
  - Quyết định mode cuối cùng PHẢI được persist vào plan artifact như source of truth
  - Workflow metadata chỉ được mirror lại mode decision để resume/search, không được override plan artifact
  - Nếu user override recommendation, phải lưu `override_reason`
  - Reviewers/implementers có thể truy vết được final mode decision từ plan artifact
```

---

## 6. Affected Components

### Files cần tạo mới (7)

> Guardrail: `.agents/plans/PLAN_LP_PIPELINE_V3/*` chỉ là design workspace cho initiative này. Runtime artifacts của LP V3 không được publish vào `.agents/plans/*`; chúng phải publish vào `.codex/*`.

| File | Purpose |
|---|---|
| `.agents/skills/lp-pipeline-orchestrator/references/complexity-assessment.md` | 6-chiều assessment framework + rubric examples |
| `.agents/skills/create-plan/references/epic-plan-template.md` | Epic plan template |
| `.agents/skills/lp-pipeline-orchestrator/references/worktree-manager.md` | Worktree operations guide |
| `.agents/plans/PLAN_LP_PIPELINE_V3/spec.md` | Design-spec source file cho initiative này, không phải runtime artifact path |
| `.agents/skills/lp-pipeline-orchestrator/references/phase-notes-template.md` | Versioned phase notes template |
| `.agents/skills/lp-pipeline-orchestrator/references/phase-report-template.md` | Versioned phase report template |
| `.agents/plans/PLAN_LP_PIPELINE_V3/plan.md` | Design plan cho initiative này, không phải runtime artifact path |

### Files cần sửa (focused scope cho phương án A)

| File | Primary changes |
|---|---|
| `.codex/AGENTS.md` | Section 8: update LP pipeline rules để Single = direct-edit, Epic = worktree mặc định |
| `.agents/skills/lp-pipeline-orchestrator/SKILL.md` | Add `assess-complexity`, Epic sequential phases, worktree lifecycle |
| `.agents/skills/lp-pipeline-orchestrator/references/commands.md` | Add Epic/worktree commands, giữ `.codex/*` paths |
| `.agents/skills/create-plan/SKILL.md` | Epic plan template support |
| `.agents/skills/lp-plan/SKILL.md` | Trigger `assess-complexity` trước `create-plan` |
| `.agents/skills/lp-implement/SKILL.md` | Epic implement flow = phase delivery loop |
| `.agents/skills/lp-cook/SKILL.md` | Epic support theo phased rollout |
| `.agents/skills/review-plan/SKILL.md` | Review Epic plan sections (invariants, phases, dependencies) |
| `.agents/skills/implement-plan/SKILL.md` | Epic phase execution contract |
| `.agents/skills/review-implement/SKILL.md` | Review scope cho Epic phase delivery loop |
| `.agents/skills/qa-automation/SKILL.md` hoặc TASK liên quan | Epic phase QA + final integration QA guidance |
| `.agents/skills/vibecode-doctor/SKILL.md` | Runtime state checks phản ánh V3 safe incremental |
| `.agents/skills/close-task/SKILL.md` | Worktree cleanup awareness |
| `.agents/skills/lp-state-manager/SKILL.md` | Clarify vẫn canonical trong V3, chưa deprecate khỏi runtime |
| TASK.md liên quan tới LP plan/implement/review/qa | Sync behavior changes, không đổi `.codex/*` |
| `.gitignore` | Add `.worktrees/` |

### Files deferred to later phase (không xử lý trong phương án A)

| File | Status |
|---|---|
| Path migration sang `.agents/plans/*` | Deferred |
| Full removal của `state_manager.py` | Deferred |
| Full removal của `.codex/state/pipeline_state.db` | Deferred |
