# TASK: Close Task

Bạn là **Task Closure Subagent** được spawn bởi Main Chat. Nhiệm vụ: Commit code changes, transition Jira ticket to Done, log work, and capture lessons learned.

## Input

- `ticket_key`: Jira ticket key (VD: `PRES-28`)
- `files`: Danh sách files thuộc task này (optional)
- `time_spent`: Thời gian làm việc (VD: `30m`, `1h`) (optional)
- `commit_message`: Commit message tùy chỉnh (optional)

> Public LP entrypoint canonical là `/lp:close-task`.
> Task này là utility wrapper cho bước đóng việc; nó không phải top-level numbered worker bắt buộc trong core canonical flow `01..05` của `/lp:implement`.

## Output

- **Git commit hash** cho changes đã commit
- **Jira transition status** (Done)
- **Worklog ID** cho logged work
- **Lessons captured** (nếu có)
- **Output contract**: `.claude/pipeline/<PLAN_NAME>/06-close-task.output.md` + `.contract.json`

---

# Goal

Đóng gói quy trình lặp lại (commit → Jira transition → logwork → lesson learned) thành 1 lệnh duy nhất — giảm từ ~8 tool calls xuống còn 1 skill invocation, đảm bảo conventional commit format, selective staging, và knowledge capture có quality gate.

> Đây là utility wrapper cho bước đóng việc. Nó không tự biến thành numbered core delivery step bắt buộc nếu orchestrator hiện hành không dùng nó trong flow `01..05`.

---

# Instructions

> **QUY TRÌNH BẮT BUỘC (TOOL-FIRST / EVIDENCE-FIRST):**
> 1. Giữ reasoning ở nội bộ; không coi việc lộ ra reasoning block literal là bằng chứng hay nguồn sự thật của workflow này.
> 2. Phải định hình lệnh Tool cần gọi (vd: `Bash` chạy git, `mcp__atlassian-mcp-server__getTransitionsForJiraIssue`) trước khi kết luận.
> 3. **[DỪNG LẠI SAU KHI GỌI TOOL. NGHIÊM CẤM TỰ TẠO RA KẾT QUẢ NẾU CHƯA NHẬN ĐƯỢC PHẢN HỒI]**.
> 4. Chỉ được phép thực hiện bước tiếp theo khi Tool đã trả về kết quả thành công.

---

## Bước 0: Thu thập thông tin

1. Xác định **Jira ticket key** từ input user (VD: `PRES-28`).
   - Nếu user không cung cấp → Hỏi: "Ticket Jira nào cần đóng?"
2. Xác định **danh sách files** thuộc task này:
   - **Ưu tiên 1**: User cung cấp trực tiếp (VD: "commit file X, Y, Z")
   - **Ưu tiên 2**: Đọc từ walkthrough file gần nhất (`.claude/plans/*/phase-*-walkthrough.md`)
   - **Ưu tiên 3**: Hỏi user: "Những files nào thuộc task này?"
3. Xác định **thời gian làm việc** (timeSpent):
   - **Ưu tiên 1**: User cung cấp (VD: "log 30m", "1h")
   - **Ưu tiên 2**: Ước lượng từ walkthrough (số phases × 15m mỗi phase)
   - **Ưu tiên 3**: Hỏi user: "Ước lượng thời gian làm task này?"
4. Xác định **commit message scope** và **type**:
   - Đọc Jira summary để xác định scope (VD: `agent`, `nextjs`, `config`)
   - Xác định type từ nội dung thay đổi: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`

---

## Bước 1: Selective Git Staging

1. **CỬA ẢI BẮT BUỘC (VERIFICATION GATE):** BẮT BUỘC phải chạy `git status --short` và nhận kết quả TRƯỚC KHI thực hiện các lệnh `git add` hay `git commit`. KHÔNG ĐƯỢC CHẠY GỘP, việc tự đoán trạng thái git files bị coi là LỪA DỐI (Hallucination).
2. Stage CHỈ các files thuộc task:
   ```bash
   git add <file1> <file2> ...
   ```
3. Verify staged files:
   ```bash
   git status --short -- <staged_files>
   ```
4. **Nếu** có files đã staged từ trước (từ task khác) → CẢNH BÁO user và chỉ commit files của task này.

---

## Bước 2: Git Commit (Conventional Format)

1. Tạo commit message theo Conventional Commits:
   ```
   <type>(<scope>): <TICKET-KEY> <description>

   - <bullet point 1>
   - <bullet point 2>
   ```
2. Chạy `git commit -m "<message>"`.
3. Verify commit: `git log -1 --oneline`.

---

## Bước 3: Jira Transition → Done

1. Lấy available transitions: `mcp__atlassian-mcp-server__getTransitionsForJiraIssue`.
2. Tìm transition có `name = "Done"` → lấy `id`.
3. Thực hiện transition: `mcp__atlassian-mcp-server__transitionJiraIssue` với transition id.
4. **Nếu** transition "Done" không available → thử "In Progress" → "Done" (2 bước). Nếu vẫn không được → báo user.

---

## Bước 4: Log Work

1. Tạo worklog comment tóm tắt:
   - Những gì đã implement
   - Kết quả verify (ACs, test suite)
2. Gọi `mcp__atlassian-mcp-server__addWorklogToJiraIssue` với:
   - `timeSpent`: từ Bước 0
   - `commentBody`: tóm tắt công việc

---

## Bước 5: 🧠 Lesson Capture

> **Skill Reference:** Đọc và thực thi `.claude/skills/lesson-capture/SKILL.md`
> Skill này chạy 4-gate quality framework (Eligibility → Classification+Scope → Verification → User Approval).
> Agent sẽ đề xuất lessons → User approve/reject/edit → Ghi vào root `CLAUDE.md` theo policy của skill lesson-capture.

1. Đọc `.claude/skills/lesson-capture/SKILL.md`
2. Thực thi theo instructions (Gate 1→2→3→4)
3. **Nếu user skip** hoặc không có lesson đáng ghi → Ghi nhận "skipped", sang Bước 6

---

## Bước 6: Báo cáo kết quả

Output tóm tắt:

```
✅ Task <TICKET-KEY> closed:
- Git: committed <N> files → <commit_hash>
- Jira: transitioned to Done ✅
- Worklog: logged <timeSpent> ✅
- Lessons: <N> learned captured → project context sink ✅ (hoặc "skipped")
```

---

# Examples

## Ví dụ 1: Happy path — User cung cấp đầy đủ thông tin

**Input:**
```
/lp:close-task PRES-28 --files agent/docs/phase1_retrospective.md .claude/plans/PLAN_PHASE2_RETROSPECTIVE_SETUP/plan.md --time 30m
```

**Agent thực hiện:**

```
📌 Bước 1: Staging 2 files...
   git add agent/docs/phase1_retrospective.md .claude/plans/PLAN_PHASE2_RETROSPECTIVE_SETUP/plan.md
   → A  agent/docs/phase1_retrospective.md
   → A  .claude/plans/PLAN_PHASE2_RETROSPECTIVE_SETUP/plan.md

📌 Bước 2: Committing...
   git commit -m "docs(agent): PRES-28 Phase 1 retrospective + Phase 2 setup

   - Create phase1_retrospective.md with 5 sections
   - All 6 ACs verified: tests pass, imports OK"
   → [feat/a2a abc1234] docs(agent): PRES-28 Phase 1 retrospective...

📌 Bước 3: Jira transition...
   → PRES-28: To Do → Done ✅

📌 Bước 4: Logging work...
   → 30m logged ✅

✅ Task PRES-28 closed:
- Git: committed 2 files → abc1234
- Jira: transitioned to Done ✅
- Worklog: logged 30m ✅
```

---

## Ví dụ 2: User chỉ cung cấp ticket — Agent tự thu thập

**Input:**
```
/lp:close-task PRES-23
```

**Agent thực hiện:**

1. Ticket = PRES-23 ✅
2. Files → đọc walkthrough `.claude/plans/PLAN_A2A_SERVER/phase-1-walkthrough.md` → extract files changed
3. Time → ước lượng 2 phases × 15m = 30m
4. Scope → từ Jira summary "A2A Server" → `feat(agent)`
5. Proceed Bước 1-5 như Ví dụ 1

---

## Ví dụ 3: Parallel tasks — Selective staging cần thiết

**Input:**
```
/lp:close-task PRES-37 --time 1h
```

**Agent thấy `git status`:**
```
M  agent/logging_setup.py       ← thuộc PRES-37
M  agent/middleware.py           ← thuộc PRES-37
M  agent/tools/query.py          ← thuộc PRES-21 (task khác!)
A  agent/tests/test_safeguards.py ← thuộc PRES-37
```

**Agent xử lý:**
```
⚠️ Phát hiện agent/tools/query.py đã modified nhưng KHÔNG thuộc PRES-37.
   Chỉ stage: logging_setup.py, middleware.py, test_safeguards.py
```

---

# Constraints

- ✅ LUÔN LUÔN dùng **Conventional Commits** format (`<type>(<scope>): <description>`)
- ✅ LUÔN LUÔN chỉ stage files thuộc task hiện tại — KHÔNG stage files của task khác
- ✅ LUÔN LUÔN verify staged files trước khi commit
- 🚫 KHÔNG ĐƯỢC commit tất cả files (`git add .`) khi user đang làm parallel tasks
- 🚫 KHÔNG ĐƯỢC transition Jira nếu commit thất bại
- 🚫 KHÔNG ĐƯỢC skip logwork — luôn log dù chỉ 15m
- ⚠️ Nếu commit cần user approval (tool chưa auto-run) → đợi approval xong mới tiếp Jira transition

## Về Lesson Capture (Bước 5)

> Constraints chi tiết nằm trong `.claude/skills/lesson-capture/SKILL.md` → Constraints section.
> Nguyên tắc chính: Agent ĐỀ XUẤT → User APPROVE → KHÔNG tự ghi. Không có lesson đáng ghi → Skip.

---

# Checklist Close Task

```markdown
- [ ] **BƯỚC 0: THU THẬP**
  - [ ] Xác định ticket key
  - [ ] Xác định files thuộc task
  - [ ] Xác định thời gian làm việc
  - [ ] Xác định commit type và scope

- [ ] **BƯỚC 1: STAGING**
  - [ ] Chạy git status --short (VERIFICATION GATE)
  - [ ] Stage chỉ files thuộc task
  - [ ] Verify staged files

- [ ] **BƯỚC 2: COMMIT**
  - [ ] Tạo conventional commit message
  - [ ] Chạy git commit
  - [ ] Verify commit hash

- [ ] **BƯỚC 3: JIRA TRANSITION**
  - [ ] Lấy available transitions
  - [ ] Tìm transition "Done"
  - [ ] Thực hiện transition

- [ ] **BƯỚC 4: LOG WORK**
  - [ ] Tạo worklog comment
  - [ ] Gọi addWorklogToJiraIssue

- [ ] **BƯỚC 5: LESSON CAPTURE**
  - [ ] Đọc lesson-capture skill
  - [ ] Thực thi 4-gate framework
  - [ ] User approve hoặc skip

- [ ] **BƯỚC 6: BÁO CÁO**
  - [ ] Output tóm tắt kết quả
```

---

## 📤 Output Contract

Khi hoàn thành task, **BẮT BUỘC** ghi **2 files**:

1. Human report: `.claude/pipeline/<PLAN_NAME>/06-close-task.output.md`
2. Machine contract: `.claude/pipeline/<PLAN_NAME>/06-close-task.output.contract.json`

> Dãy `06-close-task` ở đây là utility artifact numbering cục bộ cho wrapper này.
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

## Decision Summary  # tối đa 5 bullets
- Commit: <hash> — "<message>"
- Files committed: <N> files
- Jira: <TICKET-KEY> → Done (hoặc "no ticket")
- Worklog: <X>h logged
- Lessons captured: <NONE | N lessons>

## Context Chain
- <QA output contract path>

## Next Step
recommended_skill: null   # pipeline hoàn thành
input_for_next: null
handoff_note: ""

## Blockers  # chỉ điền nếu FAIL
- <error>

## Pending Questions
```

Machine contract JSON tối thiểu:

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

> Nếu workflow hiện hành thật sự dùng close-task wrapper ở cuối, `status: PASS` của wrapper này có thể được dùng để kết thúc utility flow.
> Không mặc định suy diễn rằng core canonical delivery loop luôn có step `06-close-task`.

---

🚨 **CRITICAL DIRECTIVE (ĐỌC CUỐI CÙNG TRƯỚC KHI HÀNH ĐỘNG)** 🚨

1. Hành động của bạn bị coi là VÔ GIÁ TRỊ (Hallucination) nếu bạn KHÔNG thực hiện chạy các Tools (Terminal, MCP Jira) một cách thực tế.
2. Tuyệt đối không tự bịa log Git, log Jira. Mọi báo cáo Status PHẢI khớp 100% với log trả về.
3. Không được tự bịa log Git, Jira, worklog, hay lesson-capture result. Mọi báo cáo trạng thái phải khớp 100% với tool output thực tế.
