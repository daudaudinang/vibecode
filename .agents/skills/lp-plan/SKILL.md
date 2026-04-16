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
Nếu có `spec.md` thì plan phải bám vào spec này như source of truth nghiệp vụ/UX.

## Source of truth

- Orchestrator: skill `lp-pipeline-orchestrator` (`SKILL.md`)

## Guarantees

- Nếu requirement chưa rõ theo spec checklist, orchestrator có thể auto chạy `create-spec` -> `review-spec` trước khi vào `create-plan`
- Nếu đã có workflow `spec` pass cho cùng `plan_name`, orchestrator resume/promote cùng workflow sang lane `plan`
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
