---
description: Canonical LittlePea planning command. Thin wrapper for the LP orchestrator.
---

# /lp:plan <requirement>

## Purpose

Tạo reviewed plan canonical cho LittlePea rồi dừng ở human gate trước implement.

## Source of truth

- `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Guarantees

- Tạo workflow state
- Chạy `create-plan` -> `review-plan`
- Sync machine contracts vào state
- Dừng sau review để chờ `/lp:implement`

## Artifacts

- `.claude/plans/PLAN_<NAME>/plan.md`
- `.claude/plans/PLAN_<NAME>/phase-XX-*.md`
- `.claude/plans/PLAN_<NAME>/manifests/ownership.json`
- `.claude/plans/PLAN_<NAME>/manifests/dependency-graph.json`
- `.claude/pipeline/PLAN_<NAME>/01-create-plan.output.*`
- `.claude/pipeline/PLAN_<NAME>/02-review-plan.output.*`

## Notes

- Đây là command canonical, không dùng `/lp-plan`
- Không mô tả full orchestration ở file này
- LP repo này dùng direct edit làm mode canonical; không auto chạy agent trong worktree nếu user chưa yêu cầu explicit
