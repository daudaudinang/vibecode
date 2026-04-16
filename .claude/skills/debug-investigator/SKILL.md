---
name: debug-investigator
description: |
  Điều tra lỗi hệ thống, tìm nguyên nhân gốc rễ (Root Cause Analysis). KHÔNG sửa code.
  "debug lỗi", "tìm nguyên nhân", "investigate bug", "tại sao lỗi X".
---

# Debug Investigator

> **Full task guide**: `.claude/skills/tasks/debug-investigator/TASK.md`

## Usage

```
/debug <error_description>
```

## What It Does

1. **Information Gathering** — Collect error details, context, reproduce steps
2. **Reproduce Plan** — Create safe reproduction plan (read-only commands)
3. **System Understanding** — Map out related execution flows
4. **Hypothesis-Driven Investigation** — Place hypotheses, test with code analysis
5. **Risk Ranking** — Rank findings by likelihood with confidence scores
6. **Verification** — Self-falsification protocol to avoid confirmation bias
7. **Report** — Root cause analysis with fix recommendations

## Key Features

- **Read-Only Investigation** — Agent never runs write commands without approval
- **Hypothesis-Driven** — Each code read serves to confirm/deny a hypothesis
- **Investigation Log** — Full audit trail including negative findings
- **Confidence Scores** — Each finding gets likelihood percentage

## Examples

```
/debug Login page shows "Loading..." forever
/debug Cart occasionally shows wrong quantity after adding items
/debug API /users returns 500 when user has no posts
```

## Output

- Debug Report with root cause
- Confidence score for each finding
- Fix recommendations with code changes
- Regression scope (affected files, tests to run)

---

## Main Chat Reference

When Main Chat receives `/lp:debug-investigator` (canonical) or `/debug` (legacy alias), spawn subagent with:
- Task file: `.claude/skills/tasks/debug-investigator/TASK.md`
- Inputs: error_description, context (optional), reproduce_steps (optional)
