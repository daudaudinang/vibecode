# Tài liệu Tham chiếu Kiến trúc: LittlePea vs Superpowers

> **Mục đích**: Baseline chính xác để review spec PLAN_LP_PIPELINE_V3.
> **Nguồn**: Đọc trực tiếp từ source files (23/04/2026). LOC verified bằng `wc -l`.

---

# PHẦN 1: LITTLEPEA (LP) — KIẾN TRÚC HIỆN TẠI

## 1.1 Tổng quan

LP là pipeline orchestration framework cho AI agent development workflows.
Triết lý: **process-heavy, multi-persona review, state-machine driven**.

### Thành phần chính

| Thành phần | File | LOC | Vai trò |
|---|---|---|---|
| **Orchestrator** | `lp-pipeline-orchestrator/SKILL.md` | 452 | Source of truth `/lp:*` |
| **State Manager** | `lp-state-manager/scripts/state_manager.py` | 1945 | SQLite workflow state |
| **State Schema** | `lp-state-manager/references/schema.md` | 189 | DB schema docs |
| **State Guide** | `lp-state-manager/SKILL.md` | 175 | State manager usage |
| **Global Rules** | `.codex/AGENTS.md` | 418 | Global instruction chain (9 sections) |

### Worker Skills

| Skill | LOC | Vai trò |
|---|---|---|
| `create-spec` | 62 | Spec creation worker |
| `create-plan` | 112 | Plan creation worker |
| `review-spec` | 61 | Spec review (dual-mode) |
| `review-plan` | 142 | Plan review (dual-mode) |
| `review-implement` | 97 | Impl review (dual-mode) |
| `implement-plan` | 70 | Implementation worker |
| `qa-automation` | 53 | E2E testing (Playwright) |
| `persona-reviewer` | 67 | 4-persona definitions |
| `debug-investigator` | 56 | Debug workflow |
| `close-task` | 46 | Post-pipeline commit+Jira |
| `vibecode-doctor` | 58 | Runtime health check |

### Wrapper Skills (thin → orchestrator)

| Skill | LOC |
|---|---|
| `lp-spec` | 41 |
| `lp-plan` | 46 |
| `lp-implement` | 40 |
| `lp-cook` | 33 |

### Task Files (detailed worker instructions)

| File | LOC |
|---|---|
| `tasks/debug-investigator/TASK.md` | 569 |
| `tasks/implement-plan/TASK.md` | 411 |
| `tasks/qa-automation/TASK.md` | 404 |
| `tasks/create-plan/TASK.md` | 388 |
| `tasks/review-plan/TASK.md` | 331 |
| `tasks/review-implement/TASK.md` | 328 |
| `tasks/close-task/TASK.md` | 328 |
| `tasks/review-spec/TASK.md` | 186 |
| `tasks/persona-review/TASK.md` | 161 |
| `tasks/create-spec/TASK.md` | 160 |
| **Tổng TASK.md** | **3266** |

### Auxiliary Skills (không thuộc pipeline core)

| Skill | LOC | Vai trò |
|---|---|---|
| `skill-generator-main` | 1106 | Tạo skill mới |
| `playwright-skill` | 455 | Browser automation |
| `playwright-cli` | 344 | Playwright CLI |
| `ui-ux-pro-max` | 377 | UI/UX design |
| `lesson-capture` | 242 | Bài học kinh nghiệm |
| `jira-workflow-bridge` | 187 | Jira integration |
| `init-project` | 146 | Project bootstrap |
| `vercel-react-best-practices` | 136 | React perf guide |
| `web-design-guidelines` | 39 | Web UI review |
| `gitnexus-*` (5 skills) | 510 | Code intelligence |

## 1.2 `.codex/AGENTS.md` — Global Instruction Chain (9 sections)

| Section | Lines | Nội dung |
|---|---|---|
| **Header** | 1-47 | Purpose, communication style, core workflow |
| **§1 Agentic Workflow** | 48-149 | Core directive, Trust-but-Verify, Anti-placeholder, ReAct loop, Rollback Protocol |
| **§2 Verification** | 151-197 | Red flags, evidence-based completion, lint/test discipline |
| **§3 Communication** | 199-252 | Ngôn ngữ (Việt), confidence disclosure, structured output |
| **§4 File Placement** | 254-281 | File location rules, cleanup, naming conventions |
| **§5 Subagent Policy** | 283-329 | LP pipeline bắt buộc agent, ngoài LP tiết chế |
| **§6 Decision Gate** | 331-356 | Khi nào được/cấm hỏi user |
| **§7 Documentation** | 358-368 | Doc rules |
| **§8 LP Pipeline** | 370-418 | Pipeline-specific rules, verification discipline, orchestration discipline, scope control |

## 1.3 Canonical Flows

### Flow `/lp:spec`

```
1. Normalize plan_name
2. start-spec (state manager)
3. Spawn @create-spec → spec.md + contract JSON
4. sync-output
5. Spawn review-spec (standard: 4 persona | fast: 1 agent)
6. sync-output
7. Pass → spec_approved = true → DỪNG chờ /lp:plan
8. NEEDS_REVISION (chưa max retry) → quay bước 3
9. Max retry / Blocker → WAITING_USER
```

### Flow `/lp:plan`

```
1. Normalize plan_name
2. start-plan (state)
3. Chưa có spec → auto-insert create-spec → review-spec
4. Spec PASS → promote workflow sang lane plan
5. Spawn @create-plan → plan.md + contract
6. sync-output
7. Spawn review-plan (standard/fast)
8. sync-output
9. Pass → plan_approved = true → DỪNG chờ /lp:implement
10. NEEDS_REVISION → retry (max 3)
11. Max retry / Blocker → WAITING_USER
```

### Flow `/lp:implement`

```
1. Resolve workflow (workflow_id, plan_name, plan_file)
2. Assert plan_approved = true
3. start-implement (state)
4. Pre-implement scope/dependency guard
5. Spawn @implement-plan → contract
6. Pass → spawn review-implement (standard/fast)
7. Review pass → spawn @qa-automation
8. Bất kỳ FAIL → retry (max 3, quay bước 5)
9. Max retry / critical → WAITING_USER
10. All pass → DỪNG chờ close-task
```

### Flow `/lp:cook` (autopilot)

```
1. create-spec → review-spec (spec loop)
2. create-plan → review-plan (plan loop)
3. plan_approved → implement → review → QA (delivery loop)
4. Retry budget / blocker → dừng
```

## 1.4 Review System — 4-Persona Dual-Mode

### Standard Mode (lần đầu): 4 agents song song

| Persona | Weight | Focus |
|---|---|---|
| Senior PM | 20% | Business intent, AC completeness |
| Senior UI/UX | 20% | UX flow, design consistency |
| Senior Developer | 30% | Logic, edge cases, tests |
| System Architecture | 30% | Coupling, scalability |

### Fast Mode (re-review): 1 agent multi-persona, focus delta

### Merge Protocol

```
1. Collect 4 persona outputs
2. Conflict normalization:
   - Blocker từ bất kỳ → giữ Blocker
   - ≥2 cùng issue khác severity → severity cao nhất
   - Mâu thuẫn → needs_human_confirmation
3. Weighted score: dev×0.30 + arch×0.30 + pm×0.20 + ux×0.20
4. Verdict:
   - Blocker → FAIL
   - needs_human_confirmation → NEEDS_REVISION
   - Score < 6.0 → FAIL
   - Score [6.0, 8.0) hoặc Major → NEEDS_REVISION
   - Score ≥ 8.0 + no Blocker/Major → PASS
```

## 1.5 State Management

### SQLite State Manager (1945 LOC)

- **DB**: `.codex/state/pipeline_state.db`
- **Schema**: V1 tables + V2 runtime migration bridge
- **Commands**: workflow CRUD, step status, gate management, artifact tracking
- **Source-of-Truth Hierarchy**:
  1. Plan content (plan.md + phase files)
  2. Published artifacts/contracts
  3. SQLite state (materialized)
  4. `.codex/active-plan` (pointer)

### Vấn đề

- State per-plan, KHÔNG per-phase → spec drift khi task lớn
- V1/V2 migration phức tạp
- DB state có thể mâu thuẫn với published artifacts
- Không support worktree → không parallel

## 1.6 Artifact Layout

```
.codex/
  plans/PLAN_<NAME>/
    spec.md
    plan.md
    phase-01-*.md, phase-02-*.md
    manifests/ (ownership.json, dependency-graph.json, benchmark.json)
  pipeline/PLAN_<NAME>/
    00-create-spec.output.md + .contract.json
    00-review-spec.output.md + .contract.json
    01-create-plan.output.md + .contract.json
    02-review-plan.output.md + .contract.json
    03-implement-plan.output.md + .contract.json
    04-review-implement.output.md + .contract.json
    05-qa-automation.output.md + .contract.json
  state/pipeline_state.db
  active-plan (pointer)
```

## 1.7 Machine Contracts

Mỗi step ghi: report `.output.md` + contract `.output.contract.json`.
Fields: `schema_version`, `skill`, `plan`, `status`, `artifacts`, `next`, `blockers`, `pending_questions`, `duration_min`.
State sync ưu tiên JSON contract.

## 1.8 Policies

| Policy | Rule |
|---|---|
| Retry | Max 3. Vượt → WAITING_USER |
| Agent execution | Top-level LP steps BẮT BUỘC dùng agents |
| Worktree | Chỉ khi user explicit. Default = direct edit |
| Foreground | LP agents PHẢI foreground. Cấm background |
| Auto-proceed | Chỉ khi step pass + can_proceed + no blocker |
| Decision gate | Chỉ hỏi khi ambiguity/blocker |

## 1.9 Plan Profiles

- **Standard**: Goal, AC, Execution Boundary, Implementation Order, Risks, Verify Commands
- **Parallel-ready**: + dependency graph, parallel groups, ownership matrix, conflict prevention, phase prerequisites

---

# PHẦN 2: SUPERPOWERS — KIẾN TRÚC

## 2.1 Tổng quan

Skills-as-code methodology. Triết lý: **TDD-first, Git-native, YAGNI, evidence-based**.

### 14 Skills (LOC verified)

| Skill | LOC | Vai trò |
|---|---|---|
| `writing-skills` | 655 | Skill authoring guide |
| `test-driven-development` | 371 | RED-GREEN-REFACTOR |
| `systematic-debugging` | 296 | 4-phase root cause |
| `subagent-driven-development` | 277 | Fresh subagent/task + 2-stage review |
| `using-git-worktrees` | 218 | Worktree management |
| `receiving-code-review` | 213 | Handle review feedback |
| `finishing-a-development-branch` | 200 | Branch completion (4 options) |
| `dispatching-parallel-agents` | 182 | Parallel agent dispatch |
| `brainstorming` | 164 | Idea → Design → Spec |
| `writing-plans` | 152 | Spec → TDD Plan |
| `verification-before-completion` | 139 | Evidence before claims |
| `using-superpowers` | 117 | Entry point, skill discovery |
| `requesting-code-review` | 105 | Dispatch reviewer |
| `executing-plans` | 70 | Plan execution (separate session) |
| **Total SKILL.md** | **3159** | |

### Supporting files (non-SKILL.md)

| Skill folder | Extra files |
|---|---|
| `subagent-driven-development/` | `implementer-prompt.md`, `spec-reviewer-prompt.md`, `code-quality-reviewer-prompt.md` |
| `systematic-debugging/` | `root-cause-tracing.md`, `defense-in-depth.md`, `condition-based-waiting.md`, `find-polluter.sh`, 3 test-pressure files |
| `brainstorming/` | `visual-companion.md`, `spec-document-reviewer-prompt.md`, `scripts/` |
| Root | `README.md` (199 LOC), `CLAUDE.md` (86 LOC) |

## 2.2 Full Pipeline Flow

```
User request
  → [using-superpowers] Scan skill applicability
  → [brainstorming] HARD GATE — no code before design
      1. Explore context
      2. Questions (1 at a time, prefer multiple choice)
      3. Propose 2-3 approaches + recommend
      4. Present design → user approve per section
      5. Write spec → docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md
      6. Self-review (placeholders, consistency, scope, ambiguity)
      7. User review gate
  → [writing-plans] Spec → Plan
      File structure mapping (decomposition first)
      Bite-sized tasks (2-5 min/step)
      TDD: Write test → Run fail → Implement → Run pass → Commit
      No placeholders (code blocks required)
      Self-review (spec coverage, type consistency)
      Save → docs/superpowers/plans/YYYY-MM-DD-<feature>.md
  → [using-git-worktrees] Isolation
      Priority: .worktrees/ → CLAUDE.md → ask user
      Safety: git check-ignore → .gitignore auto-fix
      Create worktree + run project setup + baseline tests
  → [subagent-driven-development] OR [executing-plans]
  → [finishing-a-development-branch]
      Verify tests → 4 options → Execute → Cleanup
```

## 2.3 Subagent-Driven Development

```
FOR each Task:
  1. Dispatch implementer subagent (fresh context, model selection)
  2. Handle status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
  3. Dispatch spec-reviewer → pass/fail loop
  4. Dispatch code-quality-reviewer → pass/fail loop
  5. Mark complete

AFTER all tasks:
  Final code-reviewer (entire impl)
  → finishing-a-development-branch
```

### Model Selection

| Complexity | Model tier | Signal |
|---|---|---|
| 1-2 files, clear spec | Cheap/fast | Mechanical |
| Multi-file, coordination | Standard | Integration |
| Architecture, review | Most capable | Judgment |

### Review: LP vs Superpowers

| Dimension | LP | Superpowers |
|---|---|---|
| Reviewers | 4 personas (PM, UX, Dev, Arch) | 2 stages (spec + quality) |
| Scope | Toàn bộ plan/impl | Per-task |
| Merge | Weighted scoring + conflict | Binary pass/fail |
| Final | QA automation (Playwright) | Final code reviewer |

## 2.4 TDD Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

RED → Verify RED → GREEN → Verify GREEN → REFACTOR → Repeat.
Violations: code before test → DELETE, start over.

## 2.5 Systematic Debugging (4 phases)

1. **Root Cause**: Read errors, reproduce, check changes, gather evidence, trace data flow
2. **Pattern Analysis**: Find working examples, compare, identify differences
3. **Hypothesis**: Form 1 hypothesis, test minimally, verify
4. **Implementation**: Create failing test, single fix, verify. 3+ fails → STOP, question architecture

## 2.6 Git & Worktree Model

- Feature = branch in worktree. **Không code trên main** (cần consent)
- Locations: `.worktrees/` (project-local) or `~/.config/superpowers/worktrees/` (global)
- Finishing: 4 options (merge local, PR, keep, discard)
- Safety: `.worktrees/` in `.gitignore`, baseline tests pass

## 2.7 State Management

**KHÔNG CÓ DB hay coordinator.** State = Git branches + TodoWrite + plan checkboxes + commits.
Resume = read plan file + git log.

## 2.8 Artifact Layout

```
docs/superpowers/
  specs/YYYY-MM-DD-<topic>-design.md
  plans/YYYY-MM-DD-<feature>.md
.worktrees/<name>/  (gitignored)
Git: main, feature/<name>
```

No pipeline folder, no contract JSON, no machine state files.

## 2.9 Verification Before Completion

```
1. IDENTIFY what command proves claim
2. RUN full command (fresh)
3. READ full output + exit code
4. VERIFY output confirms claim
5. ONLY THEN make claim
```

Banned phrases: "should be fine", "probably works", "I believe this fixes it".

---

# PHẦN 3: SO SÁNH TRỰC TIẾP

## 3.1 Triết lý

| | LP | Superpowers |
|---|---|---|
| Core identity | Process Execution Engine | Skills-as-Code Methodology |
| Quality gate | 4-persona weighted review | TDD + 2-stage review/task |
| State | SQLite + machine contracts | Git + plan checkboxes |
| Isolation | Direct edit (default) | Worktree (bắt buộc) |
| Granularity | Pipeline-level | Task-level (2-5 min) |
| Token strategy | Không tối ưu | Model selection/task |

## 3.2 Flow Mapping

| Superpowers | LittlePea | Note |
|---|---|---|
| brainstorming | create-spec | SP dialogue vs LP template |
| writing-plans | create-plan | SP TDD-oriented vs LP phase-oriented |
| spec-reviewer | review-spec/plan | SP binary vs LP 4-persona weighted |
| code-quality-reviewer | review-implement | SP binary vs LP 4-persona weighted |
| using-git-worktrees | *(chưa có)* | LP = direct edit |
| finishing-branch | close-task | Partial match |
| subagent-driven-dev | orchestrator | SP subagent/task vs LP state machine |
| test-driven-development | *(không có)* | LP chỉ verify commands |
| systematic-debugging | debug-investigator | Tương tự (4 vs 8 steps) |
| verification-before-completion | AGENTS.md §2 | Similar intent |
| dispatching-parallel-agents | *(chưa có)* | LP tuần tự |
| model selection | *(không có)* | LP dùng model mặc định |

## 3.3 Ưu điểm riêng

### LP (Superpowers không có)

1. **4-persona review** — 4 góc nhìn, weighted scoring, conflict normalization
2. **QA automation** — Playwright E2E tích hợp pipeline
3. **Machine contracts** — JSON output cho state sync
4. **Structured spec template** — business context, UX flows, UI states, ACs
5. **Retry policy** — explicit max 3 + WAITING_USER fallback

### Superpowers (LP không có)

1. **TDD bắt buộc** — RED-GREEN-REFACTOR trước mọi production code
2. **Git-native isolation** — worktree bắt buộc
3. **Stateless** — không DB, resume từ git + plan file
4. **Model selection** — cheap model cho mechanical tasks
5. **Bite-sized tasks** — 2-5 min/step
6. **Brainstorming dialogue** — natural conversation
7. **Parallel dispatch** — independent problems song song

## 3.4 Điểm yếu

| | LP | Superpowers |
|---|---|---|
| Token cost | Cao (4 persona × mỗi review) | Thấp hơn nhưng nhiều subagent calls |
| Complexity | Rất cao (~6600 LOC pipeline core) | Thấp (~3159 LOC skills) |
| Parallel | Không | Có (worktree + dispatch) |
| Resume | SQLite (có thể stale) | Git (luôn accurate) |

---

# PHẦN 4: LOC SUMMARY

## LP Pipeline Core

| Category | LOC |
|---|---|
| Orchestrator SKILL.md | 452 |
| State Manager (Python) | 1945 |
| State Schema + Guide | 364 |
| `.codex/AGENTS.md` | 418 |
| Worker SKILL.md (11 files) | 824 |
| Wrapper SKILL.md (4 files) | 160 |
| TASK.md (10 files) | 3266 |
| **Total pipeline core** | **~7429** |

## Superpowers

| Category | LOC |
|---|---|
| SKILL.md (14 files) | 3159 |
| Supporting docs/prompts | ~800 |
| README + CLAUDE.md | 285 |
| **Total** | **~4244** |

---

# PHẦN 5: KIẾN TRÚC LƯU TRỮ SO SÁNH

```
=== LITTLEPEA ===                          === SUPERPOWERS ===

.codex/                                    docs/superpowers/
  AGENTS.md (418 LOC)                        specs/YYYY-MM-DD-*.md
  plans/PLAN_<NAME>/                         plans/YYYY-MM-DD-*.md
    spec.md
    plan.md                                .worktrees/
    phase-01-*.md                            <feature>/  (gitignored)
    manifests/*.json
  pipeline/PLAN_<NAME>/                    Git branches:
    NN-step.output.md                        main
    NN-step.output.contract.json             feature/<name>
  state/pipeline_state.db
  active-plan (pointer)                    [No DB, no pipeline folder,
                                            no contracts, no state files]
.agents/
  skills/  (32 skill folders)
  plans/   (plan packages)
```
