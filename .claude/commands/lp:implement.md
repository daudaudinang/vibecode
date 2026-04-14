---
description: Canonical LittlePea delivery-loop command. Thin wrapper for the LP orchestrator.
---

# /lp:implement <plan_file | plan_name | workflow_id>

## Purpose

Thực thi delivery loop canonical của LittlePea trên plan đã approved.

## Source of truth

- `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Preconditions

- `plan_approved = true`

## Guarantees

- Áp dụng runtime transition guards trước implement
- Chạy `implement-plan` -> `review-implement` -> `qa-automation`
- Sync contracts và gates vào workflow state
- Nếu review/QA trả blocker hoặc workflow cần user input thì dừng đúng gate

## Artifacts

- `.claude/pipeline/PLAN_<NAME>/03-implement-plan.output.*`
- `.claude/pipeline/PLAN_<NAME>/04-review-implement.output.*`
- `.claude/pipeline/PLAN_<NAME>/05-qa-automation.output.*`
- `.claude/plans/PLAN_<NAME>/manifests/benchmark.json`

## Notes

- Đây là command canonical, không dùng `/lp-implement`
- Worker `implement-plan` không phải source of truth cho full delivery loop
- Direct edit là mode canonical; không auto spawn agent trong worktree nếu user chưa yêu cầu explicit
- Top-level LP agents trong flow này phải chạy foreground; không dùng `run_in_background`
