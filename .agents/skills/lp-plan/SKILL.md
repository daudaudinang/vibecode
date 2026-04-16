---
name: lp-plan
description: |
  Canonical LittlePea planning entrypoint. Tạo reviewed plan rồi dừng ở human gate.
  Trigger khi user nói: "lp:plan", "tạo plan", "lên kế hoạch", "plan cho feature X",
  "create plan", "planning", hoặc bất kỳ yêu cầu lập kế hoạch triển khai.
---

# LP Plan — Canonical Planning Entrypoint

## Purpose

Tạo reviewed plan canonical cho LittlePea rồi dừng ở human gate trước implement.

## Source of truth

- Orchestrator: skill `lp-pipeline-orchestrator` (`SKILL.md`)

## Guarantees

- Tạo workflow state
- Chạy `create-plan` → `review-plan`
- Sync machine contracts vào state
- Dừng sau review để chờ implement

## Expected artifacts

- `.codex/plans/PLAN_<NAME>/plan.md`
- `.codex/plans/PLAN_<NAME>/phase-XX-*.md`
- `.codex/plans/PLAN_<NAME>/manifests/ownership.json`
- `.codex/plans/PLAN_<NAME>/manifests/dependency-graph.json`
- `.codex/pipeline/PLAN_<NAME>/01-create-plan.output.*`
- `.codex/pipeline/PLAN_<NAME>/02-review-plan.output.*`

## Human gate

Canonical flow dừng sau `review-plan` và chờ user gate trước khi implement.

## Rules

- Khi skill này được gọi, phải follow orchestration policy trong `lp-pipeline-orchestrator`
- Không mô tả full orchestration logic ở file này
- Direct edit là mode canonical; không auto spawn agent trong worktree