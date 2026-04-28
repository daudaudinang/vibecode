---
name: qa-automation
description: |
  Đóng vai trò QA Automation Lead, thực hiện sinh kịch bản test Playwright (E2E),
  xác minh Acceptance Criteria (AC) bằng cách tương tác trình duyệt thực tế và thu thập Evidence.
  "chạy qa", "qa task", "test luồng", "manual test", "nghiệm thu".
---

# QA Automation

> **Full task guide**: `.agents/skills/tasks/qa-automation/TASK.md`

## Usage

```
/lp:qa-automation <AC_LIST_OR_TICKET>
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
/lp:qa-automation "Seller login redirects to dashboard"
/lp:qa-automation "B2B-157"  # reads AC from plan file
```

## Output

- QA Report with AC coverage
- Evidence from snapshots
- PASS/FAIL verdict per AC

---

## Orchestrator Reference

When Orchestrator receives `/lp:qa-automation`, invoke agent (via `@agent-name`) with:
- Task file: `.agents/skills/tasks/qa-automation/TASK.md`
- Inputs: ac_list, base_url (auto-detect), auth_credentials (auto-detect), test_mode

## Epic Context Rules

- Khi QA ở Epic mode, context baseline lấy từ plan/spec + direct dependency reports.
- Không đọc raw notes ngoài direct dependencies.
- Nếu plan bật `broad_context_reports = true` và tổng phase `<= 5`, có thể đọc thêm completed reports theo thứ tự phase index tăng dần.
- Nếu dependency critical chưa được khai báo rõ (`dependency_critical = true` + missing deps), dừng `waiting_user`, không fallback tuyến tính.
