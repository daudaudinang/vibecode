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
- Khi chạy Epic mode, phase runtime enum dùng dạng lowercase: `pending | in_progress | waiting_user | completed | failed | cancelled`
- Context propagation mặc định chỉ đọc artifacts của direct dependency phases; không đọc raw notes ngoài direct dependency
- Nếu plan bật `broad_context_reports = true` và tổng phase `<= 5`, cho phép đọc thêm report của completed phases theo thứ tự phase index tăng dần
- Nếu phase có `dependency_critical = true` nhưng dependencies thiếu/không rõ, phải chuyển `waiting_user`; không fallback tuyến tính
