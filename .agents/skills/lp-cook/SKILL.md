---
name: lp-cook
description: |
  Canonical LittlePea autopilot. Chạy full pipeline: spec → plan → review → implement → review → QA.
  Trigger khi user nói: "lp:cook", "cook feature X", "autopilot", "chạy full pipeline",
  "nấu", "build end-to-end", hoặc yêu cầu chạy toàn bộ pipeline từ đầu đến cuối.
---

# LP Cook — Canonical Autopilot Entrypoint

## Purpose

Chạy autopilot canonical của LittlePea: spec loop -> planning loop -> delivery loop, với human gates khi cần.

## Source of truth

- Orchestrator: skill `lp-pipeline-orchestrator` (`SKILL.md`)

## Guarantees

- Spec → plan → review → implement → review → QA
- Human-in-the-loop tại blocker hoặc waiting-user gates
- Retry loop bị giới hạn ở runtime/state layer
- Benchmark artifacts được ghi lại
- Direct edit trong workspace hiện tại; worktree chỉ khi user explicit yêu cầu
- Epic mode giữ phase notes/report để handoff context giữa các phase
- Context read mặc định theo direct dependency; chỉ mở rộng theo `broad_context_reports = true` khi phase-count `<= 5`
- Nếu gặp phase `dependency_critical = true` thiếu dependencies explicit thì dừng `waiting_user`, không fallback tuyến tính

## Expected artifacts

- `.codex/plans/PLAN_<NAME>/plan.md`
- `.codex/plans/PLAN_<NAME>/manifests/ownership.json`
- `.codex/plans/PLAN_<NAME>/manifests/dependency-graph.json`
- `.codex/plans/PLAN_<NAME>/manifests/benchmark.json`
- `.codex/pipeline/PLAN_<NAME>/NN-step.output.*`
