# Architecture v2 — Main Chat Orchestrator

> Updated: 2025-04-10  
> Key change: **Main chat là orchestrator**, subagents là workers.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER                                       │
│                   "/lp-plan feature X"                              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   MAIN CHAT (Orchestrator)                        │
│  - Đọc lp-plan/SKILL.md (orchestration guide)                    │
│  - QUYẾT ĐỊNG flow: spawn ai? khi nào sync?                            │
│  - Gom kết quả từ subagents                                        │
│  - Sync state vào SQLite                                           │
└─────────────────────────────────────────────────────────────────────┘
        │                                  │
        │ (spawn Agent tool)               │ (spawn Agent tool)
        ▼                                  ▼
┌───────────────────────┐     ┌───────────────────────┐
│   PLANNER SUBAGENT     │     │   REVIEW PERSONA AGENTS │
│   (planner)            │     │   (general-purpose)     │
│                        │     │                         │
│ - Đọc TASK.md          │     │ - senior_pm             │
│ - Tạo plan             │     │ - senior_uiux_designer  │
│ - Ghi output contract  │     │ - senior_developer      │
│                        │     │ - system_architecture   │
└────────────────────────┘     └────────────────────────┘
        │                                  │
        ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      OUTPUT CONTRACTS                              │
│  - .claude/pipeline/PLAN_X/01-create-plan.output.md              │
│  - .claude/pipeline/PLAN_X/01-create-plan.output.contract.json      │
│  - .claude/state/pipeline_state.db (workflow state)              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ (sync + resolve-next)
┌─────────────────────────────────────────────────────────────────────┐
│                   MAIN CHAT (tiếp tục)                           │
│  - Check resolve-next                                               │
│  - Nếu "review-plan" → spawn REVIEWER agent                         │
│  - Nếu "implement" → spawn FULLSTACK agent                          │
│  - Nếu "qa" → spawn TESTER agent                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
.claude/skills/
├── tasks/                           # TASK GUIDES cho SUBAGENTS
│   ├── create-plan/TASK.md          # ← Planner đọc này
│   ├── implement-plan/TASK.md       # ← Fullstack-developer đọc này
│   ├── review-plan/TASK.md          # ← Reviewer đọc này
│   ├── review-implement/TASK.md     # ← Reviewer đọc này
│   └── persona-review/TASK.md       # ← Persona reviewers đọc này
│
├── lp-plan/SKILL.md                 # ← Main chat đọc (orchestration)
├── lp-implement/SKILL.md            # ← Main chat đọc (orchestration)
├── lp-cook/SKILL.md                 # ← Main chat đọc (orchestration)
│
├── create-plan/SKILL.md             # ← Legacy, có thể xóa
├── implement-plan/SKILL.md          # ← Legacy, có thể xóa
├── review-plan/SKILL.md             # ← Legacy, có thể xóa
├── review-implement/SKILL.md        # ← Legacy, có thể xóa
│
├── persona-reviewer/SKILL.md       # ← Helper/reference cho single-persona review
│
├── lp-state-manager/               # Scripts
├── lp-pipeline-orchestrator/      # Scripts
│
└── persona-reviewer/personas/      # Legacy persona notes (không phải source of truth canonical)
```

## Key Differences from v1

| Aspect | v1 (Wrong) | v2 (Correct) |
|--------|------------|---------------|
| **Who orchestrates?** | Skills tự chạy | Main chat orchestrates |
| **SKILL.md reader** | AI (không rõ main/sub) | Main chat (orchestration guide) |
| **TASK.md reader** | N/A | Subagent (task guide) |
| **Agent tool caller** | Skill tự gọi | Main chat gọi |
| **State sync** | Skill tự sync | Main chat sync |

## Example Flow: /lp-plan

### What Main Chat Does:

1. **Đọc** `lp-plan/SKILL.md`
2. **Chạy** `lp_pipeline.py start-plan`
3. **Spawn** planner agent: `Agent(subagent_type="planner", prompt="TASK: Create plan...")`
4. **Chạy** `lp_pipeline.py sync-output`
5. **Chạy** `lp_pipeline.py next`
6. **Spawn** 4 reviewer agents song song: `senior_pm`, `senior_uiux_designer`, `senior_developer`, `system_architecture`
7. **Tổng hợp** findings + validate evidence/conflicts ở orchestrator
8. **Chạy** `lp_pipeline.py sync-output`
9. **Báo user** kết quả

### What Planner Subagent Does:

1. **Đọc** `tasks/create-plan/TASK.md`
2. **Thực thi** task → tạo plan
3. **Ghi** output contract

## Usage Examples

### 1. Simple plan

```
User: /lp-plan Tạo combobox font chọn

Main chat:
1. start-plan → workflow_id = WF_001
2. Agent(planner, "TASK: Create plan...")
3. sync-output → status = PASS
4. next → step = "review-plan"
5. Spawn 4 persona review agents song song
6. Orchestrator merge + validate findings
7. sync-output → status = PASS
8. "✅ Plan đã reviewed! Gợi ý: /lp-implement PLAN_FONT_COMBOBOX"
```

### 2. Parallel 4-agent review

```
Main chat:
1. Agent(general-purpose, "TASK: Review plan (senior_pm persona)...")
2. Agent(general-purpose, "TASK: Review plan (senior_uiux_designer persona)...")
3. Agent(general-purpose, "TASK: Review plan (senior_developer persona)...")
4. Agent(general-purpose, "TASK: Review plan (system_architecture persona)...")
5. Wait for ALL
6. Validate evidence + normalize conflicts
7. Merge findings
8. Report
```

## Migration Checklist

- [x] Tạo `tasks/` folder
- [x] Tạo TASK.md files cho subagents
- [x] Viết lại lp-plan/SKILL.md (orchestration guide)
- [x] Viết lại lp-implement/SKILL.md (orchestration guide)
- [x] Viết lại lp-cook/SKILL.md (orchestration guide)
- [x] Update persona-reviewer/SKILL.md
- [x] Update paths `.codex` → `.claude`
- [ ] Test end-to-end với user command
- [ ] Clean up legacy SKILL.md files (optional)
