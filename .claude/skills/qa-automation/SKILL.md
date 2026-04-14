---
name: qa-automation
description: |
  Đóng vai trò QA Automation Lead, thực hiện sinh kịch bản test Playwright (E2E),
  xác minh Acceptance Criteria (AC) bằng cách tương tác trình duyệt thực tế và thu thập Evidence.
  "chạy qa", "qa task", "test luồng", "manual test", "nghiệm thu".
---

# QA Automation

> **Full task guide**: `.claude/skills/tasks/qa-automation/TASK.md`

## Usage

```
/qa-automation <AC_LIST_OR_TICKET>
```

## What It Does

1. **Pre-flight Check** — Verify playwright-cli, server health, auth credentials
2. **AC to Test Plan** — Convert acceptance criteria into executable test steps
3. **Interactive Testing** — Use `playwright-cli` to interact with browser directly
4. **Evidence Collection** — Capture snapshots, console logs, network responses
5. **Verdict Report** — Generate PASS/FAIL report with evidence

## Modes

| Mode | When | Tool |
|------|------|------|
| 🖱️ **Interactive** (default) | Most cases | `playwright-cli` |
| 🤖 **E2E Spec** | User says "run e2e test" | `npx playwright test` |

## Examples

```
/qa-automation "Seller login redirects to dashboard"
/qa-automation "B2B-157"  # reads AC from plan file
```

## Output

- QA Report with AC coverage
- Evidence from snapshots
- PASS/FAIL verdict per AC

---

## Main Chat Reference

When Main Chat receives `/qa-automation`, spawn subagent with:
- Task file: `.claude/skills/tasks/qa-automation/TASK.md`
- Inputs: ac_list, base_url (auto-detect), auth_credentials (auto-detect), test_mode
