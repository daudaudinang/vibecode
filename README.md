# LittlePea Pipeline for Claude Code

README này mô tả **pipeline LittlePea** khi bộ `.claude/` được copy vào **global `.claude`** và chạy bằng **Claude Code**.

Nó không phải prompt pack đơn lẻ. Nó là workflow có:
- **main chat orchestrator**
- **spawned worker agents/subagents**
- **machine contracts + artifacts**
- **SQLite workflow state**
- **lesson / memory loop**

---

## 1. TL;DR

### LittlePea trong 1 màn hình

```text
User dùng /lp:*
→ Main chat orchestrator
→ spawn top-level worker agent
→ worker tạo report + machine contract
→ orchestrator sync state / gates / artifacts
→ orchestrator quyết định next step hoặc dừng ở human gate
```

### Nếu chỉ nhớ 4 ý, nhớ 4 ý này

1. **Main chat là orchestrator**
2. **Worker chỉ làm đúng 1 step**
3. **Contracts + state là source of truth runtime**
4. **Top-level workers chạy foreground trong current workspace**

---

## 2. Architecture overview

### 2.1. System map

```text
┌───────────────┐
│ User command  │
│ /lp:*         │
└──────┬────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ Main Chat Orchestrator                                      │
│ - đọc rules + canonical docs                                │
│ - chọn đúng worker step                                     │
│ - spawn Claude Code agent/subagent                          │
│ - sync contract + gate + workflow state                     │
│ - quyết định next step / stop                               │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ Top-level Worker Agents                                     │
│ create-plan / review-plan / implement-plan                  │
│ review-implement / qa-automation / debug-investigator       │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ Runtime Backbone                                            │
│ - .claude/plans/PLAN_<NAME>/...                             │
│ - .claude/pipeline/PLAN_<NAME>/RUN_<WORKFLOW_ID>/...        │
│ - .claude/state/pipeline_state.db                           │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ Next step                                                   │
│ resume / status / delivery_next / human gate                │
└──────────────────────────────────────────────────────────────┘
```

### 2.2. Layer model

| Layer | Vai trò | Source of truth |
|------|---------|-----------------|
| Main chat orchestration | nhận `/lp:*`, spawn agents, sync state, quyết định flow | `.claude/skills/lp-pipeline-orchestrator/SKILL.md` |
| Worker skills | làm đúng 1 step, xuất report + contract | worker `SKILL.md` + `tasks/*/TASK.md` |
| Runtime helper | sync-output, set gates, derive next step | `.claude/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py` |
| State layer | persist workflow, steps, gates, artifacts, events | `.claude/skills/lp-state-manager/SKILL.md` |
| Rules layer | ép discipline, verify-first, anti-hallucination | `.claude/rules/*.md` |

---

## 3. Canonical commands

### 3.1. Public commands

| Command | Dùng khi nào | Output / mục tiêu |
|---------|--------------|-------------------|
| `/lp:plan <requirement>` | cần plan trước khi code | plan package + reviewed plan |
| `/lp:implement <plan_file \| plan_name \| workflow_id>` | đã có plan approved | delivery loop implement → review → QA |
| `/lp:cook <requirement>` | muốn chạy gần full flow | planning + delivery với human gates |
| `/lp:debug-investigator <symptom>` | cần điều tra bug trước | debug artifacts + next suggestion |

### 3.2. Utility wrappers

- `/lp:qa-automation <AC_LIST_OR_TICKET>`
- `/lp:close-task <ticket_key>`
- `/lp:lesson-capture`
- `/lp:pipeline`

### 3.3. Compatibility aliases

- `/lp:create-plan`
- `/lp:review-plan`
- `/lp:implement-plan`

> 📌 Canonical namespace là `/lp:*`. Wrapper/alias không phải source of truth orchestration.

### 3.4. Quick command map

| Command | Worker path chính | Dừng ở đâu |
|---------|-------------------|------------|
| `/lp:plan` | `create-plan → review-plan` | human gate sau reviewed plan |
| `/lp:implement` | `implement-plan → review-implement → qa-automation` | QA pass hoặc WAITING_USER / blocker |
| `/lp:cook` | planning loop + delivery loop | blocker / WAITING_USER / done |
| `/lp:debug-investigator` | `debug-investigator` | debug verdict + next suggestion |

```text
/lp:plan                → create-plan → review-plan → stop at gate
/lp:implement           → implement → review → QA → close-task
/lp:cook                → plan → review → implement → review → QA
/lp:debug-investigator  → debug → analyze → recommend next flow
```

---

## 4. Worker roster

### 4.1. Top-level worker steps

| Worker | Vai trò |
|--------|---------|
| `create-plan` | tạo plan package canonical |
| `review-plan` | review plan |
| `implement-plan` | implement code theo boundary |
| `review-implement` | review implementation |
| `qa-automation` | validate AC và evidence |
| `debug-investigator` | điều tra bug / symptom |

### 4.2. Review model bắt buộc

Hai step review canonical phải spawn **4 persona agents song song**:

| Persona | Focus |
|---------|-------|
| `senior_pm` | business scope, AC completeness |
| `senior_uiux_designer` | UX flow, wording, clarity |
| `senior_developer` | logic, tests, evidence, edge cases |
| `system_architecture` | dependency, coupling, architecture risk |

```text
review-plan / review-implement
→ spawn 4 persona agents
→ thu findings riêng
→ orchestrator validate evidence + normalize conflicts
→ mới chốt verdict cuối
```

---

## 5. Core flows

### 5.1. `/lp:plan`

```text
/lp:plan <requirement>
→ start-plan
→ spawn create-plan
→ sync-output
→ spawn review-plan
→ run 4 persona review song song
→ orchestrator merge + validate findings
→ sync-output
→ nếu PASS thì set plan_approved = true
→ dừng ở human gate
```

### 5.2. `/lp:implement`

```text
/lp:implement <plan_file | plan_name | workflow_id>
→ resolve workflow
→ assert plan_approved = true
→ start-implement
→ spawn implement-plan
→ sync-output
→ spawn review-implement
→ run 4 persona review song song
→ orchestrator merge + validate findings
→ sync-output
→ nếu review PASS thì spawn qa-automation
→ sync-output
→ nếu QA PASS thì ready for close-task
```

### 5.3. `/lp:cook`

```text
/lp:cook <requirement>
→ planning loop
→ plan review
→ implement loop
→ implementation review
→ QA
→ stop nếu blocker / WAITING_USER / cần user input
```

### 5.4. `/lp:debug-investigator`

```text
/lp:debug-investigator <symptom>
→ start-debug
→ spawn debug-investigator
→ publish outputs
→ sync state
→ nếu fix scope đủ lớn thì chuyển sang /lp:plan <fix-scope>
```

---

## 6. Delivery loop visual

```text
implement-plan
   │ PASS
   ▼
review-implement
   ├── PASS ─────────────► qa-automation
   ├── NEEDS_REVISION ───► quay lại implement-plan
   ├── FAIL ─────────────► blocker / fail gate
   └── WAITING_USER ─────► human gate

qa-automation
   ├── PASS ─────────────► close-task
   ├── FAIL ─────────────► quay lại implement-plan
   └── WAITING_USER ─────► human gate
```

### Gate quan trọng

- `plan_approved`
- `user_approved_implementation`
- `implementation_done`
- `implementation_review_passed`
- `qa_passed`

> 📌 Không được sang step top-level tiếp theo nếu contract step hiện tại chưa sync.

---

## 7. Artifact layout

### 7.1. Visual tree

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

### 7.2. Ý nghĩa từng vùng

| Path | Ý nghĩa |
|------|--------|
| `.claude/plans/PLAN_<NAME>/` | canonical plan package |
| `.claude/pipeline/PLAN_<NAME>/RUN_<WORKFLOW_ID>/` | outputs/contracts theo từng run |
| `.claude/state/pipeline_state.db` | workflow state, gates, artifacts, events |

### 7.3. Source-of-truth ladder

```text
Plan files + execution boundary
            │
            ▼
Published artifacts + machine contracts
            │
            ▼
SQLite workflow state
            │
            ▼
.active-plan pointer / convenience hints
```

> 📌 Nếu DB state lệch artifact đã publish, artifact + reconcile result thắng snapshot cũ.

---

## 8. State management

State manager là backbone để workflow không phụ thuộc vào chat memory.

### Nó quản lý gì?

- workflow identity
- step status
- gates
- artifacts
- event log
- resolve-next / resume / status

### Script chuẩn

```bash
python .claude/skills/lp-state-manager/scripts/state_manager.py <command> ...
```

### Vì sao quan trọng?

```text
Không có state manager
→ flow dễ drift
→ resume khó
→ pass/fail dễ dựa vào chat feeling

Có state manager
→ workflow deterministic hơn
→ gates rõ hơn
→ artifacts và next-step kiểm được
```

---

## 9. Memory và lesson loop

LittlePea không chỉ chạy task. Nó còn có loop giữ tri thức đã verify.

### 9.1. Hai loại memory quan trọng

| Loại | Vai trò |
|------|---------|
| Runtime memory | workflow state, gates, events, artifacts |
| Knowledge memory | lessons learned, gotchas, decisions, patterns |

### 9.2. Lesson loop

```text
Implement / Review / QA xong
→ /lp:close-task
→ lesson-capture
→ quality gates
→ chỉ ghi lesson nếu có evidence + user approve
```

### 9.3. Vì sao lesson-capture đáng giá

Lesson không được ghi bừa. Nó đi qua quality gates:
- Eligibility
- Classification
- Verification
- User Approval

Điều này giúp tránh:
- ghi workaround tạm
- ghi noise
- ghi thói quen xấu
- ghi kết luận chưa verify

---

## 10. Execution policy

### Canonical policy

- Top-level LP worker steps **bắt buộc dùng agents**
- Mặc định dùng **current workspace**
- **Không auto dùng worktree**
- Chỉ dùng worktree nếu user explicit yêu cầu
- Top-level LP workers phải chạy **foreground**
- Không dùng `run_in_background=true` cho top-level workers
- Orchestrator phải sync contract/state trước khi qua step tiếp theo

### Split trách nhiệm đúng

| Thành phần | Làm gì |
|-----------|--------|
| Main chat | orchestrate, spawn, sync, decide next step |
| Worker | làm đúng 1 step, xuất output + contract |
| Runtime helper | apply transition / gate / status logic |
| State manager | persist state + events + artifacts |

---

## 11. Rules quan trọng

### Core rules

| Rule file | Vai trò |
|----------|---------|
| `.claude/rules/identity.md` | process discipline, verify-first, anti-hallucination |
| `.claude/rules/doc-rule.md` | placement rules cho docs/plans |
| `.claude/rules/response-format.md` | format final answer gửi user |

### Tinh thần chung

- đọc file thật trước khi sửa
- dùng tool/script thật để verify
- không bịa kết quả
- worker không được tự orchestration
- không bypass human gates

---

## 12. File nên đọc tiếp

Nếu muốn hiểu sâu, đọc theo thứ tự này:

1. `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
2. `.claude/skills/lp-pipeline-orchestrator/references/commands.md`
3. `.claude/skills/lp-state-manager/SKILL.md`
4. `.claude/skills/lp-state-manager/references/schema.md`
5. `.claude/commands/lp:index.md`
6. `.claude/commands/lp:pipeline.md`
7. `.claude/ARCHITECTURE.md`

---

## 13. Final mental model

```text
/lp:* command
→ main chat orchestrates
→ Claude Code agents execute workers
→ reports + machine contracts published
→ LP runtime syncs state / gates / artifacts
→ orchestrator chooses next step or waits for user
```

> ✅ Nếu hiểu đúng câu trên, cậu đã hiểu đúng pipeline LittlePea ở mức hệ thống.
