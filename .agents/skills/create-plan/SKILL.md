---
name: create-plan
description: Worker-only skill that creates one canonical LP plan package and returns machine-readable planning artifacts.
---

# Create Plan — Worker Only

## Goal

Tạo 1 plan canonical cho LittlePea, đủ artifact để orchestrator review, gate, và resume.

## Worker-only responsibility

- Chỉ làm step `create-plan`
- Không tự orchestration sang `review-plan`
- Không tự approve plan
- Chỉ tạo plan artifacts + machine contract cho planning step hiện tại

## Canonical inputs

- Requirement từ user hoặc orchestrator
- `.codex/plans/PLAN_<NAME>/spec.md` nếu tồn tại (source of truth nghiệp vụ/UX)
- Context codebase liên quan
- Nếu có: ticket/workflow metadata từ orchestrator

## Planning model

Plan package phải phản ánh đúng runtime model mới:
- One plan = one primary controller
- Multiple conversations may review/coordinate
- Parallel execution only via child jobs/subagents under the primary run
- Top-level phases chỉ được đánh dấu parallel-ready khi ownership thực sự không overlap và orchestration có thể giao song song an toàn

## Plan profiles

### Standard plan

Dùng cho task thường. Tối thiểu phải có:
- Goal
- Acceptance Criteria
- Execution Boundary
- Implementation Order
- Risks
- Verify Commands

### Parallel-ready plan

Chỉ bật khi task đủ lớn hoặc user yêu cầu parallel **và** top-level phase ownership thực sự disjoint. Ngoài standard plan, phải có:
- phase files
- dependency graph
- parallel groups
- file ownership matrix
- conflict prevention notes
- phase prerequisites

Nếu top-level phases không disjoint nhưng vẫn cần làm song song, plan phải mô tả theo model **single-controller child-parallel** thay vì gắn nhãn `parallel-ready` cho top-level phases.

## Canonical artifacts

Plan output phải ghi dưới:

```text
.codex/plans/PLAN_<NAME>/
  plan.md
  phase-01-*.md
  phase-02-*.md
  manifests/
    ownership.json
    dependency-graph.json
    benchmark.json
```

Pipeline output:
- `.codex/pipeline/PLAN_<NAME>/01-create-plan.output.md`
- `.codex/pipeline/PLAN_<NAME>/01-create-plan.output.contract.json`

## Artifact rules

- `plan.md` là overview ngắn, không nhồi toàn bộ chi tiết
- Chi tiết phase nằm ở `phase-XX-*.md`
- `ownership.json` phải mô tả ownership/no-overlap khi plan parallel-ready
- `dependency-graph.json` phải mô tả phase dependencies nếu có parallelization
- `.codex/active-plan` được phép tồn tại như pointer, nhưng phải trỏ về `.codex/plans/PLAN_<NAME>/`

## Output contract expectations

Contract nên trả được các field sau khi applicable:
- `plan`
- `plan_path`
- `phase_files`
- `plan_profile = standard | parallel-ready`
- `owned_files`
- `dependencies`
- `duration_ms`
- `next.recommended_skill = review-plan | null`
- `plan_artifacts.final_plan_path`
- `plan_artifacts.plan_root_path`
- `plan_artifacts.ownership_manifest_path`
- `plan_artifacts.dependency_graph_path`
- `plan_artifacts.benchmark_manifest_path`

## Constraints

- Không dùng layout cũ `.codex/plans/PLAN_<NAME>.md`
- Luôn ghi pipeline output vào `.codex/pipeline/`
- Không tự đánh dấu `plan_approved = true`
- Không nhét orchestration policy đầy đủ vào worker skill này

## Handoff

Orchestrator sẽ đọc contract để sync artifacts, quyết định start `review-plan`, hoặc dừng ở human gate.
