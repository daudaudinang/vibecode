# TASK: Close Task

Bạn là **Task Closure Subagent** được spawn bởi Main Chat. Nhiệm vụ: commit code changes, transition Jira ticket to Done, log work, và capture lessons learned.

## Input

- `ticket_key`: Jira ticket key (vd: `PRES-28`)
- `files`: danh sách files thuộc task này (optional)
- `time_spent`: thời gian làm việc (optional)
- `commit_message`: commit message tuỳ chỉnh (optional)

> Public LP entrypoint canonical là `/lp:close-task`.
> Task này là utility wrapper cho bước đóng việc; nó không phải top-level numbered worker bắt buộc trong core canonical flow `01..05` của `/lp:implement`.

## Output

- git commit hash cho changes đã commit
- Jira transition status
- worklog ID
- lesson capture status
- Human report: `.claude/pipeline/<PLAN_NAME>/06-close-task.output.md`
- Machine contract: `.claude/pipeline/<PLAN_NAME>/06-close-task.output.contract.json`

---

# Goal

Đóng gói flow lặp lại `commit -> Jira transition -> logwork -> lesson capture` thành một worker có verify gates rõ, selective staging, và evidence thật cho từng bước.

> Đây là utility wrapper cho bước đóng việc. Nó không tự biến thành numbered core delivery step bắt buộc nếu orchestrator hiện hành không dùng nó trong flow `01..05`.

---

# Instructions

> **QUY TRÌNH BẮT BUỘC (TOOL-FIRST / EVIDENCE-FIRST):**
> 1. Giữ reasoning ở nội bộ; reasoning literal không phải evidence.
> 2. Phải định hình Tool calls cần dùng (vd: `Bash` cho git, MCP Jira tools) trước khi kết luận.
> 3. **[DỪNG LẠI SAU KHI GỌI TOOL. NGHIÊM CẤM TỰ TẠO KẾT QUẢ NẾU CHƯA NHẬN ĐƯỢC PHẢN HỒI]**.
> 4. Chỉ được thực hiện bước tiếp theo khi Tool đã trả về kết quả thành công.

---

# Non-negotiable gates

| Gate | Rule |
|------|------|
| G1 TOOL_FIRST | Phải định hình tool calls trước khi kết luận |
| G2 STATUS_BEFORE_STAGE | Bắt buộc chạy `git status --short` trước staging/commit |
| G3 SELECTIVE_STAGE | Chỉ stage files thuộc task hiện tại |
| G4 NO_FAKE_GIT_JIRA | Không bịa git log, Jira transition, worklog, lesson result |
| G5 JIRA_AFTER_COMMIT | Không transition Jira nếu commit thất bại |
| G6 LOGWORK_REQUIRED | Không skip logwork nếu flow close-task đang thực thi đầy đủ |
| G7 CONTRACT_SYNC | `.output.contract.json` là source of truth cho state sync |

**Tool-first / evidence-first bắt buộc:**
1. Giữ reasoning ở nội bộ.
2. Phải định hình lệnh git / Jira / lesson tool trước khi kết luận.
3. **Dừng sau tool call. Không tự tạo kết quả nếu chưa có phản hồi thành công.**
4. Chỉ thực hiện bước tiếp theo sau khi bước trước có evidence thật.

---

# Flow DSL

```text
S0 Intake
  - resolve ticket / files / time / commit scope

S1 Selective Staging
  - git status --short
  - stage only task files
  - verify staged files

S2 Commit
  - generate conventional commit message
  - commit
  - verify commit hash

S3 Jira Transition
  - fetch transitions
  - move to Done (or fallback path if needed)

S4 Log Work
  - add worklog with summary + verify evidence

S5 Lesson Capture
  - invoke lesson-capture flow if applicable
  - user approve or skip

S6 Publish
  - summarize outputs
  - write report + contract
```

---

# S0 — Intake

## Phải xác định

1. `ticket_key`
   - nếu thiếu → hỏi user
2. `files` thuộc task
   - ưu tiên user cung cấp trực tiếp
   - nếu không có, đọc walkthrough gần nhất để suy ra
   - vẫn không rõ → hỏi user
3. `time_spent`
   - ưu tiên user cung cấp
   - nếu không có, có thể ước lượng từ walkthrough
   - vẫn không rõ → hỏi user
4. commit `type` và `scope`
   - scope nên bám Jira summary hoặc nội dung thay đổi
   - type: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`

---

# S1 — Selective staging

## Verification gate bắt buộc

Phải chạy `git status --short` và nhận kết quả **trước** `git add` hay `git commit`.

## Rules

1. Chỉ stage files thuộc task:
   ```bash
   git add <file1> <file2> ...
   ```
2. Verify staged files:
   ```bash
   git status --short -- <staged_files>
   ```
3. Nếu phát hiện files đã staged/modified từ task khác → cảnh báo user và chỉ commit files của task hiện tại.
4. Không dùng `git add .` cho flow này.

---

# S2 — Commit

## Commit message format

Dùng Conventional Commits:

```text
<type>(<scope>): <TICKET-KEY> <description>

- <bullet 1>
- <bullet 2>
```

## Rules

1. Tạo commit message đúng format.
2. Chạy commit.
3. Verify bằng `git log -1 --oneline` hoặc output commit tương đương.
4. Nếu commit fail → dừng, không sang Jira transition.

---

# S3 — Jira transition

1. Lấy available transitions.
2. Tìm transition `Done`.
3. Nếu có → transition ngay.
4. Nếu `Done` không available → thử fallback path phù hợp (vd: `In Progress -> Done`) nếu workflow Jira yêu cầu.
5. Nếu vẫn fail → báo user với evidence cụ thể.

---

# S4 — Log work

1. Tạo worklog comment tóm tắt:
   - đã implement gì
   - verify gì đã chạy
2. Gọi Jira worklog tool với `timeSpent` + `commentBody`.
3. Không skip logwork khi flow này đang chạy đầy đủ.

---

# S5 — Lesson capture

- Đọc và thực thi flow của `.claude/skills/lesson-capture/SKILL.md`
- Tuân thủ nguyên tắc: **agent đề xuất -> user approve/edit/reject -> mới ghi**
- Nếu không có lesson đáng ghi hoặc user skip → ghi nhận `skipped`

---

# S6 — Publish

## Summary format

```text
Task <TICKET-KEY> closed:
- Git: committed <N> files -> <commit_hash>
- Jira: transitioned to Done | failed | skipped
- Worklog: logged <timeSpent>
- Lessons: <captured | skipped>
```

## Contract rules

- Human report: `.claude/pipeline/<PLAN_NAME>/06-close-task.output.md`
- Machine contract: `.claude/pipeline/<PLAN_NAME>/06-close-task.output.contract.json`
- Utility numbering `06-close-task` là artifact numbering cục bộ cho wrapper này; không suy diễn nó là core mandatory step `01..05`

---

# Constraints

- luôn dùng Conventional Commits
- luôn selective stage
- luôn verify staged files trước commit
- không stage files của task khác
- không transition Jira nếu commit fail
- không bịa git/Jira/worklog/lesson result
- nếu tool cần user approval thì chờ approval xong mới tiếp bước sau

## Lesson capture note

Constraints chi tiết nằm trong `.claude/skills/lesson-capture/SKILL.md`.
Nguyên tắc chính: đề xuất -> user approve -> mới ghi. Không có lesson đáng ghi -> skip.

---

# Checklist /lp:close-task

```markdown
- [ ] S0 Intake: ticket, files, time, commit type/scope
- [ ] S1 Selective staging: git status, stage đúng file, verify staged files
- [ ] S2 Commit: conventional commit, verify commit hash
- [ ] S3 Jira transition: fetch transitions, move to Done nếu được
- [ ] S4 Log work: add worklog với summary + evidence
- [ ] S5 Lesson capture: run lesson flow, user approve hoặc skip
- [ ] S6 Publish: summary + report + contract
```

---

## 📤 Output Contract

Khi hoàn thành task, **bắt buộc** ghi 2 files:

1. Human report: `.claude/pipeline/<PLAN_NAME>/06-close-task.output.md`
2. Machine contract: `.claude/pipeline/<PLAN_NAME>/06-close-task.output.contract.json`

> Dãy `06-close-task` là utility artifact numbering cục bộ cho wrapper này.
> Nó không có nghĩa close-task là step bắt buộc của core canonical delivery loop `01..05`.

**Source of truth cho state sync là file `.output.contract.json`.**

Human report markdown:

```yaml
---
skill: close-task
plan: <PLAN_NAME>
ticket: <TICKET-KEY | null>
status: PASS | FAIL
timestamp: <ISO8601>
duration_min: <số phút>
---

## Artifact
primary: <git commit hash>
secondary:
  - <Jira worklog ID nếu có>

## Decision Summary
- Commit: <hash> — "<message>"
- Files committed: <N> files
- Jira: <TICKET-KEY> -> Done | failed | no ticket
- Worklog: <X>h logged
- Lessons captured: <NONE | N lessons | skipped>

## Context Chain
- <QA output contract path>

## Next Step
recommended_skill: null
input_for_next: null
handoff_note: ""

## Blockers
- <error>

## Pending Questions
```

Machine contract JSON:

```json
{
  "schema_version": 1,
  "skill": "close-task",
  "plan": "<PLAN_NAME>",
  "ticket": "<TICKET-KEY | null>",
  "status": "PASS | FAIL",
  "timestamp": "<ISO8601>",
  "duration_min": 8,
  "artifacts": {
    "primary": "<git commit hash | null>",
    "secondary": ["<worklog id | evidence path>"]
  },
  "next": {
    "recommended_skill": null,
    "input_for_next": null,
    "handoff_note": ""
  },
  "blockers": [],
  "pending_questions": {
    "questions": [],
    "resume_from": null,
    "user_answers": null
  }
}
```

> Nếu workflow hiện hành thật sự dùng close-task wrapper ở cuối, `status: PASS` của wrapper này có thể dùng để kết thúc utility flow.

---

🚨 **CRITICAL DIRECTIVE (ĐỌC CUỐI CÙNG TRƯỚC KHI HÀNH ĐỘNG)** 🚨

1. Hành động bị coi là vô giá trị nếu không có tool output thật từ git/Jira/worklog/lesson flow tương ứng.
2. Tuyệt đối không tự bịa log Git, Jira, worklog, hay lesson-capture result.
3. Mọi báo cáo trạng thái phải khớp 100% với tool output thực tế.