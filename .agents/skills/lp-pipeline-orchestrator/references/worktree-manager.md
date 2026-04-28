# Worktree Manager Notes (Epic Mode)

## Scope

Tài liệu này mô tả lifecycle worktree/branch cho Epic mode và hành vi recovery.

## Lifecycle

1. Pre-flight `.worktrees/` guard trong `.gitignore`
2. Tạo branch/worktree cho phase
3. Chạy baseline verify command trước delivery loop
4. Chạy `implement-plan -> review-implement -> qa-automation`
5. Merge về main
6. Cleanup worktree + branch

## Recovery rules

- Worktree setup fail: output `waiting_user` phải có hướng dẫn `git worktree prune` hoặc manual cleanup git/worktree state.
- Merge conflict: output `waiting_user` bắt buộc có `Conflict files: <list>`.
- Existing stale worktree: ưu tiên `waiting_user` để user chọn resume hoặc cleanup.

## cancel_requested safe boundary

`cancel_requested` không phải kill signal tức thời.

Chỉ được finalize `cancelled` tại một trong các boundary:
- command-exit boundary
- step-transition boundary
- worker-handoff boundary

Không được kill giữa command đang chạy.
