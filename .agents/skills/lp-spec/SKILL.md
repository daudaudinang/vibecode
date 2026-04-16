---
name: lp-spec
description: |
  Canonical LittlePea specification entrypoint. Chốt business requirements, UX flow,
  happy path, edge cases trước khi vào planning.
  Trigger khi user nói: "lp:spec", "làm spec", "chốt yêu cầu", "SRS", "URD", "spec flow".
---

# LP Spec — Canonical Specification Entrypoint

## Purpose

Chuẩn hoá yêu cầu nghiệp vụ + UX behavior để tạo một baseline không mơ hồ trước `/lp:plan`.

## Source of truth

- Orchestrator: skill `lp-pipeline-orchestrator` (`SKILL.md`)

## Guarantees

- Tạo workflow state cho step `create-spec`
- Chạy quality gate `review-spec` trước khi cho phép sang planning
- Xuất spec artifact có:
  - Business goals / scope
  - User flow (happy path + alternate path)
  - Edge/error cases và expected UI behavior
  - Acceptance criteria có thể test được
- Sync machine contract vào state
- Dừng ở human gate để user review/chốt trước planning

## Expected artifacts

- `.codex/plans/PLAN_<NAME>/spec.md`
- `.codex/pipeline/PLAN_<NAME>/00-create-spec.output.*`
- `.codex/pipeline/PLAN_<NAME>/00-review-spec.output.*`

## Rules

- Skill này chỉ làm rõ "build WHAT".
- Không thay thế implementation plan; không tự orchestration sang implementation.
- Direct edit là mode canonical; không auto spawn agent trong worktree.
