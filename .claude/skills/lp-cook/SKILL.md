---
name: lp-cook
description: Thin wrapper for the canonical /lp:cook autopilot flow.
---

# LP Cook — Thin Wrapper

## Status

Wrapper mỏng cho autopilot canonical của LittlePea.

## Canonical entrypoint

- User-facing command: `/lp:cook <requirement>`
- Source of truth: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Purpose

- Giữ backward compatibility cho skill name `lp-cook`
- Không chứa orchestration logic đầy đủ
- Không phải source of truth

## Canonical guarantees

- Plan -> review -> implement -> review -> QA
- Human-in-the-loop tại blocker / waiting-user gates
- Auto-fix loops bị giới hạn retry và boundary
- Benchmark artifacts được ghi lại

## Expected artifacts from canonical flow

- `.claude/plans/PLAN_<NAME>/plan.md`
- `.claude/plans/PLAN_<NAME>/manifests/ownership.json`
- `.claude/plans/PLAN_<NAME>/manifests/dependency-graph.json`
- `.claude/plans/PLAN_<NAME>/manifests/benchmark.json`
- `.claude/pipeline/PLAN_<NAME>/NN-step.output.*`

## Notes

- Không dùng `/lp-cook` làm syntax canonical trong docs mới
- Generic `/cook` không phải canonical flow cho LittlePea.