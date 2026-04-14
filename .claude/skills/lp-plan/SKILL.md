---
name: lp-plan
description: Thin wrapper for the canonical /lp:plan flow.
---

# LP Plan — Thin Wrapper

## Status

Wrapper mỏng cho planning flow canonical của LittlePea.

## Canonical entrypoint

- User-facing command: `/lp:plan <requirement>`
- Source of truth: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Purpose

- Giữ backward compatibility cho skill name `lp-plan`
- Không chứa orchestration logic đầy đủ
- Không phải source of truth

## Rules

- Không dùng `/lp-plan` làm syntax canonical trong docs mới
- Không mô tả full flow tại file này
- Khi skill này được gọi, phải follow orchestration policy trong `lp-pipeline-orchestrator`

## Expected artifacts from canonical flow

- `.claude/plans/PLAN_<NAME>/plan.md`
- `.claude/plans/PLAN_<NAME>/phase-XX-*.md`
- `.claude/plans/PLAN_<NAME>/manifests/ownership.json`
- `.claude/plans/PLAN_<NAME>/manifests/dependency-graph.json`
- `.claude/pipeline/PLAN_<NAME>/01-create-plan.output.*`
- `.claude/pipeline/PLAN_<NAME>/02-review-plan.output.*`

## Human gate

Canonical `/lp:plan` dừng sau `review-plan` và chờ user gate.