# Operator Waiting-User Contract

## One-screen template

```text
Error: <short reason>
Required action: <human action>
Context: <phase_id/current_step/files>
Next command: /lp:implement PLAN_<NAME>
Recovery evidence required: <what to verify before resume>
```

## Mandatory blocker-specific lines

### Baseline verify fail

- Error: baseline verification failed
- Required action: update baseline command or fix environment mismatch

### Worktree/branch setup fail

- Required action: cleanup git/worktree state (`git worktree prune`) hoặc manual cleanup

### Merge conflict

- Error: merge conflict
- Conflict files: <list>
- Required action: resolve conflicts + commit merge result

### Dependency blocker

- Nếu `dependency_critical = true` nhưng dependencies thiếu/không rõ:
  - chuyển `waiting_user`
  - Required action phải yêu cầu bổ sung dependency graph/plan metadata
  - không fallback tuyến tính
