# vibecode

Canonical workspace for the LittlePea (`/lp:*`) workflow, with Codex-ready `.codex/` and `.agents/skills/` runtime layout.

## LittlePea in one screen

```text
Main chat orchestrator
→ spawn top-level worker agents
→ workers publish human report + machine contract
→ orchestrator syncs state/gates
→ orchestrator decides next step or stops at WAITING_USER
```

## What this repository contains

- `.codex/`: Codex config, AGENTS, custom agents, runtime artifacts
- `.agents/skills/`: orchestration + worker skills for Codex skill discovery
- `CODEX_GLOBAL_ARCHITECTURE.md`: Codex global structure and migration notes

## Canonical command surface

Use these commands as the public LP namespace:

- `/lp:spec <requirement>`
- `/lp:plan <requirement>`
- `/lp:implement <plan_file | plan_name | workflow_id>`
- `/lp:cook <requirement>`
- `/lp:debug-investigator <symptom>`

Utility wrappers:

- `/lp:review-implement <plan_file | plan_name | workflow_id>`
- `/lp:qa-automation <AC_LIST_OR_TICKET>`
- `/lp:close-task <ticket_key>`
- `/lp:lesson-capture`
- `/lp:pipeline`

## Runtime model

- Main chat = orchestrator
- Top-level LP workers = foreground agents trong current workspace
- Worker skills là worker-only; không tự orchestration sang step kế tiếp
- `review-plan` và `review-implement` dùng 4 persona bắt buộc
- Canonical top-level outputs publish vào `.codex/pipeline/PLAN_<NAME>/NN-step.output.*`
- `RUN_<WORKFLOW_ID>` vẫn tồn tại như runtime identity trong state/contracts, không phải canonical top-level output folder
- Spec-first flow khuyến nghị: `/lp:spec` -> `/lp:plan` -> `/lp:implement`

## Source of truth

- Global/runtime rules: `.codex/AGENTS.md`
- Orchestrator: `.agents/skills/lp-pipeline-orchestrator/SKILL.md`
- State backbone: `.agents/skills/lp-state-manager/SKILL.md`

## Global sync contract

Theo `CODEX_GLOBAL_ARCHITECTURE.md`, các file sau cần được sync từ project lên global user scope sau mỗi lần cập nhật:

| Source (project) | Destination (global) | Nội dung |
|---|---|---|
| `.codex/AGENTS.md` | `~/.codex/AGENTS.md` | Global instruction chain cho Codex |
| `.codex/agents/*.toml` | `~/.codex/agents/` | Custom agent definitions |
| `.codex/scripts/*` | `~/.codex/scripts/` | Helper scripts (kể cả sync-global.sh) |
| `.agents/skills/` | `~/.agents/skills/` | Reusable skills cho Codex discovery |

Runtime artifacts **KHÔNG** được sync lên global (giữ nguyên trong project scope):
- `.codex/plans/` — plan files
- `.codex/pipeline/` — pipeline output
- `.codex/state/` — SQLite state DB

### Sync script

Script tự động: `.codex/scripts/sync-global.sh`

```bash
# Sync tất cả (khuyến nghị)
bash .codex/scripts/sync-global.sh

# Preview trước khi sync (dry-run)
bash .codex/scripts/sync-global.sh --dry-run

# Sync từng phần
bash .codex/scripts/sync-global.sh agents-md   # chỉ AGENTS.md
bash .codex/scripts/sync-global.sh agents       # AGENTS.md + agent TOMLs
bash .codex/scripts/sync-global.sh skills       # chỉ skills
bash .codex/scripts/sync-global.sh scripts      # chỉ scripts
```

Script tự detect file nào đã up-to-date (md5 check) và chỉ copy file có thay đổi.

### Khi nào cần sync?

Chạy sync sau khi:
- Cập nhật `.codex/AGENTS.md` (thêm rule, sửa workflow)
- Thêm/sửa agent `.toml` trong `.codex/agents/`
- Thêm/sửa skill trong `.agents/skills/`
- Clone repo sang máy mới lần đầu

### Lưu ý

- Codex load `~/.agents/skills/` nếu không chạy trong context repo có `.agents/skills/`
- Global agents `~/.codex/agents/*.toml` available cho mọi repo, không chỉ vibecode-1
- Script có `timeout 5s` khi check accessibility của `~/.agents/skills/` để tránh hang nếu mount lỗi

## Documentation notes

- Prefer `/lp:*` notation in all new docs.
- Treat `/lp-plan`, `/lp-implement`, `/lp-cook` as compatibility wrappers only.
- `lp:index.md` is intentional; the `:` may look unusual, but it maps directly to the `/lp:*` command namespace.
- Artifact model canonical là: plan-scoped output paths + run-scoped identity trong state/contracts.
- `/lp:init-project` và `/lp:jira-workflow-bridge` là compatibility helpers có skill riêng, nhưng không phải source of truth cho orchestration.
- `/lp:sync-agents-context` hiện vẫn chỉ là namespace placeholder, không phải source of truth cho orchestration.
