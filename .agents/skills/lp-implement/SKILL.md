---
name: lp-implement
description: |
  Canonical LittlePea delivery-loop entrypoint. Chạy implement → review → QA.
  Trigger khi user nói: "lp:implement", "triển khai plan", "implement plan X",
  "thực thi kế hoạch", "bắt đầu implement", hoặc yêu cầu delivery sau plan approved.
---

# LP Implement — Canonical Delivery Entrypoint

## Purpose

Thực thi delivery loop canonical của LittlePea trên plan đã approved.

## Source of truth

- Orchestrator: skill `lp-pipeline-orchestrator` (`SKILL.md`)

## Preconditions

- `plan_approved = true`

## Guarantees

- Áp dụng runtime transition guards trước implement
- Chạy `implement-plan` → `review-implement` → `qa-automation`
- Sync contracts và gates vào workflow state
- Nếu review/QA trả blocker hoặc workflow cần user input thì dừng đúng gate

## Expected artifacts

- `.codex/pipeline/PLAN_<NAME>/03-implement-plan.output.*`
- `.codex/pipeline/PLAN_<NAME>/04-review-implement.output.*`
- `.codex/pipeline/PLAN_<NAME>/05-qa-automation.output.*`
- `.codex/plans/PLAN_<NAME>/manifests/benchmark.json`

## Rules

- Worker `implement-plan` không phải source of truth cho full delivery loop
- Direct edit là mode canonical; không auto spawn agent trong worktree
- Top-level LP agents phải chạy foreground; không dùng background