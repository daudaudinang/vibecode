# Architecture — LittlePea Pipeline for Claude Code

> Updated: 2026-04-15
> Canonical model: **Main chat là orchestrator**, Claude Code spawned agents là workers, LP artifacts + state là workflow backbone.

## 1. One-screen architecture

```text
┌───────────────┐
│ User command  │
│ /lp:*         │
└──────┬────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ Main Chat Orchestrator                                      │
│ - đọc canonical LP docs/rules                               │
│ - chọn đúng top-level worker step                           │
│ - spawn agent trong current workspace                       │
│ - sync output contract + gates + workflow state             │
│ - quyết định next step hoặc dừng ở human gate               │
└──────┬───────────────────────────────────────────────────────┘
       │ spawn Agent tool
       ▼
┌──────────────────────────────────────────────────────────────┐
│ Top-level Worker Agents                                     │
│ - create-plan                                               │
│ - review-plan (4 persona agents song song)                  │
│ - implement-plan                                            │
│ - review-implement (4 persona agents song song)             │
│ - qa-automation                                             │
│ - debug-investigator                                        │
└──────┬───────────────────────────────────────────────────────┘
       │ publish report + contract
       ▼
┌──────────────────────────────────────────────────────────────┐
│ LP Runtime Backbone                                         │
│ - .claude/plans/PLAN_<NAME>/...                             │
│ - .claude/pipeline/PLAN_<NAME>/RUN_<WORKFLOW_ID>/...        │
│ - .claude/state/pipeline_state.db                           │
└──────┬───────────────────────────────────────────────────────┘
       │ resolve-next / status / resume
       ▼
┌──────────────────────────────────────────────────────────────┐
│ Main Chat Orchestrator                                      │
│ - đọc gates / artifacts / delivery_next / entry_decision    │
│ - tiếp tục step kế hoặc chờ user                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Responsibility split by layer

| Layer | Trách nhiệm | Source of truth |
|------|-------------|-----------------|
| Main chat orchestration layer | nhận `/lp:*`, spawn agent, sync state, quyết định next step | `.claude/skills/lp-pipeline-orchestrator/SKILL.md` |
| Worker skill layer | làm đúng 1 step, xuất report + machine contract, không tự orchestration sang step tiếp theo | worker `SKILL.md` + `tasks/*/TASK.md` |
| Runtime helper layer | normalize workflow, sync output, set gates, derive next step | `.claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py` |
| State layer | persist workflow state, steps, gates, artifacts, events | `.claude/skills/lp-state-manager/SKILL.md` + `references/schema.md` |
| Rules layer | ép process discipline, verify-first, anti-hallucination | `.claude/rules/*.md` |

### Điều không được hiểu sai

- `lp-plan`, `lp-implement`, `lp-cook` **không** phải source of truth orchestration.
- Worker skill **không** tự orchestration sang step tiếp theo.
- Python runtime helper **không** thay thế main chat orchestrator.
- Main chat **không** được tự làm thay top-level worker canonical step.

---

## 3. Canonical public commands

Canonical namespace là `/lp:*`:

- `/lp:plan <requirement>`
- `/lp:implement <plan_file | plan_name | workflow_id>`
- `/lp:cook <requirement>`
- `/lp:debug-investigator <symptom>`

Utility wrappers:
- `/lp:qa-automation <AC_LIST_OR_TICKET>`
- `/lp:close-task <ticket_key>`
- `/lp:lesson-capture`
- `/lp:pipeline`

Source of truth cho catalog public:
- `.claude/commands/lp:index.md`
- `.claude/commands/lp:pipeline.md`

---

## 4. Worker roster

### Top-level worker steps

| Step | Vai trò |
|------|---------|
| `create-plan` | tạo plan package canonical |
| `review-plan` | review plan qua 4 persona bắt buộc |
| `implement-plan` | implement code trong execution boundary |
| `review-implement` | review implementation qua 4 persona bắt buộc |
| `qa-automation` | kiểm AC/evidence và đưa QA verdict |
| `debug-investigator` | điều tra bug / symptom độc lập |

### Review roster bắt buộc

Hai step review canonical phải spawn **4 agents độc lập chạy song song**:

- `senior_pm`
- `senior_uiux_designer`
- `senior_developer`
- `system_architecture`

Orchestrator tổng hợp findings, validate evidence, normalize conflicts, rồi mới chốt verdict cuối.

---

## 5. Workspace and execution policy

### Canonical policy

- Top-level LP worker steps **bắt buộc dùng agents**.
- Mặc định chạy trong **current workspace**.
- **Không auto dùng worktree**.
- Chỉ dùng worktree khi user explicit yêu cầu.
- Top-level LP worker steps phải chạy **foreground**.
- Không dùng `run_in_background=true` cho top-level LP workers.
- Trước khi qua step top-level tiếp theo, orchestrator phải sync contract/state của step hiện tại.

### Vì sao policy này tồn tại

Vì `.claude/state/` và `.claude/pipeline/` là shared resources trong cùng workspace. Main chat cần result ngay để:
- set gate
- sync artifacts
- quyết định next step
- tránh drift giữa contract và workflow state

---

## 6. Canonical artifact + state model

```text
.claude/
  plans/
    PLAN_<NAME>/
      plan.md
      phase-*.md
      manifests/
        ownership.json
        dependency-graph.json
        benchmark.json

  pipeline/
    PLAN_<NAME>/
      RUN_<WORKFLOW_ID>/
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
        child-jobs/
          JOB_<ID>/
            result.md
            result.contract.json

  state/
    pipeline_state.db
```

### Source-of-truth hierarchy

1. Plan content + execution boundary trong `.claude/plans/PLAN_<NAME>/`
2. Published artifacts + machine contracts trong `.claude/pipeline/...`
3. SQLite workflow state trong `.claude/state/pipeline_state.db`
4. Convenience pointer `.claude/active-plan`

Nếu DB state và published artifact mâu thuẫn nhau, published artifact + reconcile result thắng snapshot cũ.

---

## 7. Flow overview

### `/lp:plan`

```text
/lp:plan <requirement>
→ start-plan
→ spawn create-plan
→ sync-output
→ spawn review-plan (4 persona agents)
→ orchestrator validate + merge findings
→ sync-output
→ nếu PASS thì set plan_approved = true
→ dừng ở human gate
```

### `/lp:implement`

```text
/lp:implement <plan_file | plan_name | workflow_id>
→ resolve workflow
→ assert plan_approved = true
→ start-implement
→ spawn implement-plan
→ sync-output
→ spawn review-implement (4 persona agents)
→ orchestrator validate + merge findings
→ sync-output
→ nếu review PASS thì spawn qa-automation
→ sync-output
→ nếu QA PASS thì sẵn sàng close-task
```

### `/lp:cook`

```text
/lp:cook <requirement>
→ planning loop
→ human gates khi cần
→ delivery loop
→ review / QA / retry loop
→ stop nếu blocker, WAITING_USER, hoặc cần user input
```

### `/lp:debug-investigator`

```text
/lp:debug-investigator <symptom>
→ start-debug
→ spawn debug-investigator
→ publish outputs
→ sync state
→ nếu cần fix lớn thì chuyển sang /lp:plan <fix-scope>
```

---

## 8. Delivery loop and gates

```text
implement-plan
   │ PASS
   ▼
review-implement
   ├── PASS ─────────────► qa-automation
   ├── NEEDS_REVISION ───► quay lại implement-plan
   ├── FAIL ─────────────► dừng / blocker
   └── WAITING_USER ─────► human gate

qa-automation
   ├── PASS ─────────────► close-task
   ├── FAIL ─────────────► quay lại implement-plan
   └── WAITING_USER ─────► human gate
```

Gate thường gặp:
- `plan_approved`
- `user_approved_implementation`
- `implementation_done`
- `implementation_review_passed`
- `qa_passed`

Runtime helper commands như `status` / `resume` phải surface:
- `entry_decision`
- `workspace_policy`
- `workspace_warning`
- `delivery_next`

Main chat không được đoán writer authority nếu runtime đã trả decision rõ.

---

## 9. File structure and role map

```text
.claude/
├── commands/
│   ├── lp:index.md                    # public command catalog
│   └── lp:pipeline.md                 # quick workflow catalog
│
├── rules/
│   ├── identity.md                    # global execution discipline
│   ├── doc-rule.md                    # doc/plan placement rules
│   └── response-format.md             # final response formatting
│
├── skills/
│   ├── lp-pipeline-orchestrator/      # orchestration source of truth + scripts
│   ├── lp-state-manager/              # workflow state backbone + schema refs
│   │
│   ├── lp-plan/                       # thin wrapper
│   ├── lp-implement/                  # thin wrapper
│   ├── lp-cook/                       # thin wrapper
│   │
│   ├── create-plan/                   # canonical worker-only skill
│   ├── review-plan/                   # canonical worker-only skill
│   ├── implement-plan/                # canonical worker-only skill
│   ├── review-implement/              # canonical worker-only skill
│   ├── qa-automation/                 # canonical worker-only skill
│   ├── debug-investigator/            # canonical worker-only skill
│   ├── close-task/                    # task finalization + lesson capture
│   └── lesson-capture/                # lessons learned quality-gated sink
│
└── ARCHITECTURE.md                    # overview architecture doc
```

### Naming note

- `lp-*` wrappers: public-orchestration aliases / thin wrappers
- worker skills: canonical step executors
- `close-task` và `lesson-capture`: terminal workflow / knowledge retention loop

---

## 10. Key corrections from older docs

| Sai mental model cũ | Canonical model đúng |
|---------------------|----------------------|
| `/lp-plan` là syntax chính | `/lp:plan` mới là canonical namespace |
| `lp-plan/SKILL.md` là orchestration source of truth | `lp-pipeline-orchestrator/SKILL.md` mới là source of truth |
| worker skills là legacy có thể xóa | worker skills là canonical top-level steps |
| skill tự sync state | main chat orchestrator sync state qua runtime helper |
| artifact root chỉ ở plan-level | V2 runtime foundation dùng run-level root `RUN_<WORKFLOW_ID>` |

---

## 11. Read this next

Nếu cần đi sâu hơn, đọc theo thứ tự:

1. `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
2. `.claude/skills/lp-pipeline-orchestrator/references/commands.md`
3. `.claude/skills/lp-state-manager/SKILL.md`
4. `.claude/skills/lp-state-manager/references/schema.md`
5. `.claude/commands/lp:index.md`
6. `.claude/commands/lp:pipeline.md`
