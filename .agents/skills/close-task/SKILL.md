---
name: close-task
description: |
  Commit code changes, transition Jira ticket to Done, log work, and capture lessons learned.
  "commit và chuyển trạng thái", "done task", "finalize task", "đóng task", "/close-task".
---

# Close Task

> **Full task guide**: `.agents/skills/tasks/close-task/TASK.md`

## Usage

```
/close-task <TICKET-KEY> [--files "file1,file2"] [--time "30m"] [--message "commit message"]
```

## What It Does

1. **Selective Git Staging** — Stage only task-related files (not all files)
2. **Conventional Commit** — Create properly formatted commit message
3. **Jira Transition** — Move ticket to Done status
4. **Log Work** — Log time spent with worklog comment
5. **Lesson Capture** — Run lesson-capture skill to document learnings

## Examples

```
/close-task PRES-28 --files "agent/docs/phase1_retrospective.md" --time "30m"
/close-task PRES-37 --time "1h"
```

## Output

- Git commit hash
- Jira transition status
- Worklog ID
- Lessons captured (optional)

---

## Orchestrator Reference

When Orchestrator receives `/close-task`, invoke agent (via `@agent-name`) with:
- Task file: `.agents/skills/tasks/close-task/TASK.md`
- Inputs: ticket_key, files (optional), time_spent (optional), commit_message (optional)
