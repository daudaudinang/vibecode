---
description: Compatibility wrapper for project bootstrap/context initialization.
---

# /lp:init-project

## Status

Compatibility wrapper. Project đã có skill `init-project`, nhưng flow này không thuộc LP canonical orchestrator.

## Purpose

Giữ entrypoint namespace cho nhu cầu bootstrap hoặc cập nhật project agent context theo hướng helper/compatibility.

## Notes

- Source of truth cho hành vi wrapper này nằm ở `.claude/skills/init-project/SKILL.md`
- Flow này không phải canonical runtime workflow và không phải source of truth cho orchestration/state của LP
- Dùng khi cần bootstrap context hoặc hỗ trợ migration từ flow cũ; không cạnh tranh với `lp-pipeline-orchestrator`
- Sau khi init xong, nếu cần sync thêm context legacy thì mới cân nhắc `/lp:sync-agents-context`
