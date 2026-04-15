---
name: init-project
description: Compatibility helper cho `/lp:init-project`. Dùng khi cần bootstrap hoặc cập nhật project agent context; không thuộc LP canonical orchestrator flow.
---

# Init Project

## Vai trò

Skill này là **compatibility helper**, không phải LP canonical runtime workflow.

Dùng khi user cần:
- bootstrap context cho project
- rà nhanh command/rules/skills hiện có
- tạo hoặc cập nhật tài liệu kiểu `AGENTS.md` **nếu repo đang dùng file đó** hoặc user yêu cầu rõ

## Không phải source of truth

- LP canonical orchestration: `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
- LP runtime/state: `.claude/skills/lp-state-manager/SKILL.md`
- Canonical command catalog: `.claude/commands/lp:index.md`
- Repo-local guidance: `README.md`, `.claude/CLAUDE.md`, `.claude/rules/*`

Skill này **không** được mô tả như bootstrap flow canonical của LP.

---

## Khi nào áp dụng

- User chạy `/lp:init-project`
- User yêu cầu kiểu: "init project", "bootstrap context", "tạo/cập nhật AGENTS.md", "tóm tắt rules/skills hiện có"

## Mục tiêu

Tạo một bản tóm tắt context bám repo thực tế bằng cách đọc:
- cấu trúc repo
- command catalog
- skills/rules trong `.claude/`
- config files thực tế (`package.json`, `pyproject.toml`, `tsconfig.json`, v.v.) nếu có

### Output ưu tiên

1. **Nếu repo đã dùng `AGENTS.md` hoặc user yêu cầu rõ**
   - tạo/cập nhật `AGENTS.md` như tài liệu compatibility cho agent bootstrap
2. **Nếu repo không dùng `AGENTS.md` và user không yêu cầu tạo file**
   - chỉ trả summary hoặc đề xuất source-of-truth hiện có dưới `.claude/`

> `AGENTS.md` là output compatibility tùy chọn. Không phải runtime/source-of-truth mặc định của LP.

---

## Quy trình

### Phase 1 — Thu thập context thật

Bắt buộc dùng tool thật trước khi kết luận.

Ưu tiên đọc:
- `README.md`
- `.claude/CLAUDE.md`
- `.claude/commands/lp:index.md`
- `.claude/commands/lp:pipeline.md`
- `.claude/skills/**/SKILL.md` (chỉ các skill liên quan)
- `.claude/rules/*.md`

Nếu có, đọc thêm:
- `package.json`
- `pyproject.toml`
- `tsconfig.json`
- eslint/prettier/tailwind config

### Phase 2 — Xác định mode hoạt động

#### Mode A: Summary-only

Dùng khi user chỉ muốn hiểu project context.

Output nên gồm:
- repo structure mức cao
- command surface chính
- source-of-truth hierarchy
- rules/skills nổi bật
- tech stack / commands thực tế nếu có

#### Mode B: Generate/update `AGENTS.md`

Chỉ dùng khi:
- user yêu cầu rõ, hoặc
- repo đã có `AGENTS.md` sẵn

Quy tắc:
- nội dung phải bám repo thực tế
- không được hardcode stack/commands khi chưa đọc file cấu hình
- nếu `AGENTS.md` cũ có phần lessons/gotchas hữu ích thì giữ lại
- không ghi đè source-of-truth của `.claude/*`

### Phase 3 — Verify

- đọc lại artifact vừa tạo/cập nhật
- kiểm tra không còn placeholder mơ hồ
- xác nhận wording không mô tả skill này như canonical LP orchestrator

---

## Nội dung khuyến nghị cho `AGENTS.md` (nếu cần)

- Project structure
- Commands thực tế
- Tech stack thực tế
- Source-of-truth hierarchy
- Skills overview từ `.claude/skills/*/SKILL.md`
- Rules overview từ `.claude/rules/*.md`
- Response language / collaboration notes
- Optional lessons / gotchas

---

## Constraints

- Không tái du nhập `.agents/*` làm runtime/source-of-truth mặc định
- Không mô tả `/init` như canonical public entrypoint; ưu tiên `/lp:init-project`
- Nếu nhắc `/init`, chỉ ghi là legacy alias / compatibility wording
- Không dùng tên tool cũ như `view_file`, `list_dir`, `grep_search` như thể đó là source-of-truth
- Không bịa commands, stack, rules, hay folder structure
- Không tự tạo `AGENTS.md` nếu user không muốn và repo cũng không dùng file đó

---

## Kết quả mong đợi

Sau khi chạy skill này, user biết:
- project đang dùng source-of-truth nào
- command nào là canonical `/lp:*`
- có cần thêm tài liệu compatibility như `AGENTS.md` hay không
- bước tiếp theo phù hợp là gì (`/lp:plan`, `/lp:implement`, hay chỉ review docs)
