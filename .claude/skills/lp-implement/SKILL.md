---
name: lp-implement
description: Thin wrapper for the canonical /lp:implement delivery loop.
---

# LP Implement — Thin Wrapper

## Status

Wrapper mỏng cho delivery loop canonical của LittlePea.

## Canonical entrypoint

- User-facing command: `/lp:implement <plan_file | plan_name | workflow_id>`
- Source of truth: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`

## Purpose

- Giữ backward compatibility cho skill name `lp-implement`
- Không chứa orchestration logic đầy đủ
- Không phải source of truth

## Rules

- `plan_approved = true` là precondition bắt buộc
- Delivery loop canonical dùng runtime transition guards và workflow state làm backbone
- Worker `implement-plan` không tự quyết định flow kế tiếp

## Expected artifacts from canonical flow

- `.claude/pipeline/PLAN_<NAME>/03-implement-plan.output.*`
- `.claude/pipeline/PLAN_<NAME>/04-review-implement.output.*`
- `.claude/pipeline/PLAN_<NAME>/05-qa-automation.output.*`
- `.claude/plans/PLAN_<NAME>/manifests/benchmark.json`

## Completion rule

Canonical `/lp:implement` chỉ hoàn tất khi review pass, QA pass, và không còn `scope_violation`.