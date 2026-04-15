---
name: jira-workflow-bridge
description: |
  Compatibility helper cho context bắt đầu từ Jira. Đọc Jira issue qua MCP Atlassian,
  chuẩn hóa context, rồi handoff sang LP canonical `/lp:*` workflows hoặc tạo Jira issue mới khi user yêu cầu.
---

# Jira Workflow Bridge

## Vai trò

Skill này là **Jira intake/router helper**, không phải LP canonical orchestrator.

Nó dùng để:
- đọc Jira issue
- gom context nghiệp vụ/kỹ thuật
- route sang workflow LP phù hợp
- ghi comment/worklog ngược về Jira khi cần
- tạo issue Jira mới theo template nếu user yêu cầu

## Không phải source of truth

- LP canonical orchestration: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
- LP command catalog: `.claude/commands/lp:index.md`
- LP runtime/state: `.claude/skills/lp-state-manager/SKILL.md`

Skill này **không** được tự trở thành alternative orchestrator.

---

## Canonical command mapping

Khi context bắt đầu từ Jira, wrapper này phải handoff sang các command LP sau:

| Jira-driven intent | Canonical LP target |
|---|---|
| Plan feature/fix từ Jira | `/lp:plan` |
| Điều tra bug từ Jira | `/lp:debug-investigator` |
| Thực thi plan đã có | `/lp:implement` |

Legacy wording như `/create-plan`, `/debug`, `/implement-plan` chỉ được nhắc như compatibility mapping nếu thực sự cần giải thích migration.

---

## Artifact/path model phải dùng

- Plan package: `.claude/plans/PLAN_<NAME>/plan.md`
- Published pipeline artifacts: `.claude/pipeline/PLAN_<NAME>/NN-step.output.*`
- Runtime identity vẫn có thể dùng `RUN_<WORKFLOW_ID>` trong state/contracts

Không dùng `.agent/*` hoặc `.agents/*` như canonical artifact/runtime layout.

---

## Phần A — Đọc Jira issue rồi route sang LP workflow

### Bước 0: Nhận diện input

Kích hoạt khi user:
- đưa issue key như `PROJ-123`
- đưa Jira URL chứa issue key
- yêu cầu đọc/sync một Jira task để làm tiếp trong LP flow

Nếu input không phải Jira issue key/URL hợp lệ, thoát khỏi helper này và để command/workflow gốc xử lý.

### Bước 1: Fetch Jira context

Dùng các tool MCP Atlassian phù hợp, ưu tiên:
- `getJiraIssue`
- `searchJiraIssuesUsingJql`
- `getJiraIssueRemoteIssueLinks`
- `getVisibleJiraProjects`
- `getJiraProjectIssueTypesMetadata`
- `getJiraIssueTypeMetaWithFields`
- `lookupJiraAccountId`
- `addCommentToJiraIssue`
- `addWorklogToJiraIssue`

Trích xuất tối thiểu:
- `summary`
- `description`
- `issuetype.name`
- `status.name`
- `priority.name`
- `labels`
- `components`
- `parent` / epic context
- linked issues quan trọng
- comments có quyết định kỹ thuật/nghiệp vụ
- attachments nếu hữu ích

### Bước 2: Chuẩn hóa context

Tạo block context ngắn, rõ, bám Jira thật:
- Issue info
- Description nguyên văn hoặc tóm lược có kiểm soát
- Acceptance Criteria
- Scope / business rules nếu có
- Steps to Reproduce / Expected vs Actual nếu là bug
- Dependencies / linked issues quan trọng
- Comments/attachments có giá trị

### Bước 3: Chọn workflow đích

#### Route mặc định

| Issue type / intent | Handoff |
|---|---|
| `Bug` hoặc user muốn điều tra lỗi | `/lp:debug-investigator` |
| `Story` / `Task` / `Improvement` / `Epic` | `/lp:plan` |
| user yêu cầu implement từ plan đã có | `/lp:implement` |

Nếu user đã nói rõ intent thì ưu tiên intent của user.

### Bước 4: Handoff sang LP canonical flow

- Với planning: truyền Jira context làm requirement/context cho `/lp:plan`
- Với debugging: truyền symptom + reproduce/context cho `/lp:debug-investigator`
- Với implementation: resolve plan file canonical tại `.claude/plans/PLAN_<NAME>/plan.md` trước khi handoff sang `/lp:implement`

Nếu chưa có plan mà user muốn implement từ Jira issue:
- báo rõ cần chạy `/lp:plan` trước

### Bước 5: Ghi kết quả ngược về Jira

Chỉ ghi comment/worklog khi:
- user yêu cầu, hoặc
- workflow wrapper này được dùng như Jira-connected helper có write-back rõ ràng

Comment cần tham chiếu canonical LP artifacts, ví dụ:
- `.claude/plans/PLAN_<NAME>/plan.md`
- `.claude/pipeline/PLAN_<NAME>/01-create-plan.output.md`
- `.claude/pipeline/PLAN_<NAME>/04-review-implement.output.md`

Không gợi ý public flow cũ kiểu `/review-plan` hoặc `.agent/plans/...` như next step mặc định.

---

## Phần B — Tạo Jira issue mới

Kích hoạt khi user yêu cầu tạo story/task/bug/epic trên Jira.

### Quy trình ngắn

1. Xác định project bằng `getVisibleJiraProjects`
2. Xác định issue type bằng `getJiraProjectIssueTypesMetadata`
3. Lấy required fields bằng `getJiraIssueTypeMetaWithFields`
4. Resolve assignee bằng `lookupJiraAccountId` nếu cần
5. Tạo issue bằng `createJiraIssue`
6. Trả lại issue key/link cho user

### Chất lượng description

Description tạo mới phải đủ:
- context
- scope in/out nếu là feature/task
- acceptance criteria
- bug details / steps to reproduce nếu là bug
- notes hữu ích cho agent nếu user cung cấp

---

## Constraints

- Không bypass `lp-pipeline-orchestrator`
- Không public hóa legacy commands như flow chuẩn
- Không dùng `.agent/*` hoặc `.agents/*` làm artifact/runtime layout mặc định
- Không tự transition Jira issue nếu user chưa yêu cầu
- Không giả định thiếu context; thiếu thì hỏi user hoặc dừng
- Không log secrets/tokens/PII vào artifacts hay Jira comments
- Không sửa logic của worker LP; helper này chỉ lo intake, mapping, handoff, và write-back

---

## Resource files

- `resources/field_mapping.md`
- `resources/jira_comment_templates.md`
- `resources/jira_task_templates.md`

Các resource này phải bám canonical `/lp:*` commands và `.claude/*` artifact layout.
