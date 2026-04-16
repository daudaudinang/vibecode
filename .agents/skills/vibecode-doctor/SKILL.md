---
name: vibecode-doctor
description: Doctor command cho Vibecode. Kiểm tra canonical runtime root, legacy mirrors, active runtime DB, script availability, và GitNexus CLI/index readiness mức first-pass.
---

# Vibecode Doctor

## Mục tiêu

Cho user và assistant một điểm kiểm tra duy nhất để biết runtime conventions hiện tại có usable không.

## Khi nào dùng

- User hỏi vì sao tool calls fail nhiều
- User nghi canonical path / runtime root bị lệch
- User muốn biết GitNexus đã ready chưa
- Trước khi bắt đầu các flow lớn như plan / implement / debug-investigator

## Cách chạy

> **Scope note:** Lệnh dưới dùng `.codex/` là path tương đối với **project root** (cwd hiện tại).
> - Chạy từ trong project dir → kiểm tra **project state** (correct, intended behavior).
> - Muốn kiểm tra **global installation** (không có project context) → dùng absolute path:
>   `python ~/.codex/scripts/vibecode_doctor.py`
> - State DB, plans, pipeline luôn thuộc project scope — doctor không ghi bất cứ thứ gì.

```bash
# Trong project dir — check project health
python .codex/scripts/vibecode_doctor.py

# Ngoài project (global install check only)
python ~/.codex/scripts/vibecode_doctor.py
```

## Những gì phải kiểm tra

- canonical runtime root từ `.codex/config.toml`
- legacy mirrors có tồn tại không (`.agents`, `.cursor`, `.codex`)
- active state DB path canonical
- GitNexus CLI/index readiness mức first-pass
- LP script availability (`state_manager.py`, `lp_pipeline.py`, `validate_contract.py`)
- manifest/script surface có tồn tại để tiếp tục bootstrap/readiness flow hay không

## Output mong đợi

```text
✅ canonical runtime root: .codex
⚠️ legacy mirrors detected: .agents, .cursor
✅ active state db: .codex/state/pipeline_state.db
✅ GitNexus CLI available via gitnexus or npx
⚠️ GitNexus repo not indexed yet
```

## Rule vận hành

- Nếu doctor báo GitNexus chưa ready hoặc repo chưa indexed, ưu tiên bootstrap/analyze cho xong trước khi vào task lớn.
- Nếu doctor báo legacy mirrors cùng tồn tại, resolve canonical path manifest trước khi đọc/sửa skill.
- Doctor này là first-pass check; không coi nó là bằng chứng rằng MCP exposure hoặc doc/script semantic sync đã được verify đầy đủ.
