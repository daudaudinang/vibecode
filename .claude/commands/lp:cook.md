---
description: Canonical LittlePea autopilot command. Thin wrapper for the LP orchestrator.
---

# /lp:cook <requirement>

## Purpose

Chạy autopilot canonical của LittlePea: planning loop rồi delivery loop, với human gates khi cần.

## Source of truth

- `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Guarantees

- Plan -> review -> implement -> review -> QA
- Human-in-the-loop tại blocker hoặc waiting-user gates
- Retry loop bị giới hạn ở runtime/state layer
- Benchmark artifacts được ghi lại
- Runtime hiện hỗ trợ direct edit trong workspace hiện tại; worktree chỉ là isolation tùy chọn khi user explicit yêu cầu
- Không auto spawn LP agents trong worktree

## Artifacts

- `.claude/plans/PLAN_<NAME>/plan.md`
- `.claude/plans/PLAN_<NAME>/manifests/ownership.json`
- `.claude/plans/PLAN_<NAME>/manifests/dependency-graph.json`
- `.claude/plans/PLAN_<NAME>/manifests/benchmark.json`
- `.claude/pipeline/PLAN_<NAME>/NN-step.output.*`

## Notes

- Đây là command canonical, không dùng `/lp-cook`
- Generic `/cook` không phải canonical LittlePea flow
