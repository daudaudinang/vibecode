---
name: implement-plan
description: Worker-only skill that implements one canonical LP plan or phase within owned-file boundaries and returns machine-readable execution results.
---

# Implement Plan — Worker Only

## Goal

Triển khai 1 plan hoặc 1 phase thành code đúng boundary, đúng ownership, và có verification evidence.

## Worker-only responsibility

- Chỉ làm step `implement-plan`
- Không tự orchestration review / QA loop
- Không tự quyết định flow kế tiếp
- Chỉ implement trong boundary được giao

## Canonical inputs

- `.codex/plans/PLAN_<NAME>/plan.md` hoặc `phase-XX-*.md`
- `.codex/plans/PLAN_<NAME>/spec.md` nếu tồn tại
- `.codex/plans/PLAN_<NAME>/manifests/ownership.json`
- `.codex/plans/PLAN_<NAME>/manifests/dependency-graph.json` nếu plan parallel-ready

## Execution model assumptions

- Một plan chỉ có một primary writer/controller tại một thời điểm
- Nếu phase này được thực thi bởi worker, worker đang làm việc dưới primary run chứ không tự trở thành orchestrator mới
- Parallel work chỉ hợp lệ khi plan/package đã mô tả child-job ownership rõ ràng

## Scope rules

- Chỉ sửa owned files / allowed files của phase hiện tại
- Nếu touched files vượt boundary, phải report `scope_violation`
- Không claim completion nếu dependency phase chưa pass mà phase hiện tại phụ thuộc vào nó

## Verification rules

- Chạy verify commands hoặc test/lint liên quan thật sự
- Chỉ report `PASS` khi có evidence
- Nếu bị block bởi missing decision hoặc external dependency, trả `WAITING_USER` hoặc `FAIL` với blocker rõ ràng

## Output contract expectations

Contract nên trả được các field sau khi applicable:
- `phase_id`
- `parallel_group`
- `owned_files`
- `touched_files`
- `scope_violations`
- `retry_count`
- `duration_ms`
- `next.recommended_skill = review-implement | null`

Pipeline output:
- `.codex/pipeline/PLAN_<NAME>/03-implement-plan.output.md`
- `.codex/pipeline/PLAN_<NAME>/03-implement-plan.output.contract.json`

## Constraints

- Không tự spawn `review-implement`
- Không tự spawn `qa-automation`
- Không sửa ngoài boundary để “tiện tay”
- Không tự bypass scope violation

## Handoff

Orchestrator sẽ đọc contract để quyết định start `review-implement`, block workflow, hoặc quay lại user gate.
