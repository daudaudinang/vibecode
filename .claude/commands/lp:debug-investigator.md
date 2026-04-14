---
description: Canonical LittlePea debug entrypoint. Thin wrapper for the debug-investigator skill.
---

# /lp:debug-investigator <symptom>

## Purpose

Điều tra root cause theo mode read-only, có thể sync vào LP workflow khi dùng cùng orchestrator.

## Source of truth

- `.claude/skills/debug-investigator/SKILL.md`
- Nếu debug được chạy trong LP pipeline: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Guarantees

- Hypothesis-driven investigation
- Không tự ý sửa code trong debug step
- Output là root cause analysis + fix recommendations

## Notes

- Đây là LP-facing debug entrypoint
- Nếu scope fix đủ lớn, bước tiếp theo thường là `/lp:plan <fix-scope>`
