# Field Mapping: Jira → LP Workflow Inputs

Bảng ánh xạ giữa Jira fields và input cần thiết cho LP canonical workflows.

---

## MCP Tool Reference (atlassian-mcp-server)

| Tool Name | Mục đích | Khi nào dùng |
|---|---|---|
| `getJiraIssue` | Lấy chi tiết issue | Đọc task từ Jira |
| `searchJiraIssuesUsingJql` | Tìm kiếm bằng JQL | Tìm tasks liên quan |
| `createJiraIssue` | Tạo issue mới | Tạo task/bug/story mới |
| `editJiraIssue` | Chỉnh sửa issue | Cập nhật fields |
| `transitionJiraIssue` | Chuyển trạng thái | Chỉ khi user yêu cầu |
| `getTransitionsForJiraIssue` | Lấy transitions có sẵn | Trước khi transition |
| `addCommentToJiraIssue` | Thêm comment | Ghi kết quả workflow |
| `addWorklogToJiraIssue` | Ghi worklog | Log thời gian làm việc |
| `getVisibleJiraProjects` | Danh sách projects | Khi tạo issue mới |
| `getJiraProjectIssueTypesMetadata` | Issue types của project | Biết types có sẵn |
| `getJiraIssueTypeMetaWithFields` | Fields theo issue type | Biết required fields |
| `lookupJiraAccountId` | Tìm account ID | Resolve assignee |

⚠️ Tool names là camelCase.

---

## Mapping cho `/lp:plan`

| Jira Field | LP Input | Ghi chú |
|---|---|---|
| `summary` | plan/feature name | Chuẩn hóa thành `PLAN_<NAME>` |
| `description` | requirement chính | Giữ nguyên ý nghĩa nghiệp vụ |
| AC trong description/custom field | acceptance criteria | Dùng cho planning/review |
| scope/business rules | planning context | In scope / out of scope |
| `priority.name` | priority context | Ảnh hưởng scope/urgency |
| `labels`, `components` | module hints | Gợi ý area cần khám phá |
| `parent` / epic | higher-level context | Goal tổng thể |
| linked issues | dependencies | blocker/related work |
| comments | quyết định đã chốt | Hints cho planner |
| attachments | design/reference | mockup, screenshot |

Canonical output path sau handoff:
- `.codex/plans/PLAN_<NAME>/plan.md`
- `.codex/pipeline/PLAN_<NAME>/01-create-plan.output.*`

---

## Mapping cho `/lp:debug-investigator`

| Jira Field | LP Input | Ghi chú |
|---|---|---|
| `summary` | symptom | Triệu chứng chính |
| `description` | error context | Mô tả lỗi đầy đủ |
| Steps to Reproduce | reproduce steps | Nếu có |
| Expected vs Actual | expected/actual | Nếu có |
| Environment/Frequency | env context | Browser, OS, mức độ lặp lại |
| logs/screenshots | evidence | Hỗ trợ điều tra |
| `labels`, `components` | module hints | Gợi ý phạm vi |
| comments | QA/dev observations | Context thêm |

Debug artifacts nếu được publish phải bám `.codex/` runtime layout hiện tại.

---

## Mapping cho `/lp:implement`

| Jira Field | LP Input | Ghi chú |
|---|---|---|
| `summary` | plan lookup hint | Resolve `PLAN_<NAME>` |
| `status.name` | readiness context | Kiểm tra có hợp để implement không |
| `fixVersions` | release context | Nếu có |
| subtasks | optional tracking | Không thay thế plan phases |

Lookup canonical plan file:
- `.codex/plans/PLAN_<NAME>/plan.md`

Nếu chưa resolve được plan file canonical, route lại `/lp:plan` thay vì cố implement thẳng.

---

## Mapping cho tạo Jira task mới

| Issue Type | Nội dung tối thiểu |
|---|---|
| Story / Task | context, scope, acceptance criteria |
| Bug | steps to reproduce, expected vs actual, impact |
| Epic | goal, scope, child work overview |
| Sub-task | summary ngắn + parent + scope cụ thể |

---

## Quy tắc chung

- Ưu tiên `/lp:*` trong docs và write-back notes
- Không dùng `.agent/*` hoặc `.agents/*` làm canonical lookup path
- Không public hóa worker-only flow như `/review-plan` hay `/review-implement` như next step mặc định
- Jira bridge chỉ map context rồi handoff sang LP canonical flow
