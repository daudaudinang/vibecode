# Codex global config, subagents, skills, commands, và so sánh với Claude Code

> Mục tiêu: tổng hợp **chính xác từ tài liệu chính thức mới nhất** về Codex liên quan tới global config, project config, subagents, skills, slash commands, và đối chiếu với Claude Code.
>
> Phạm vi nguồn:
> - OpenAI Developers / repo `openai/codex`
> - Anthropic Claude Code docs
> - Không dùng blog bên thứ ba làm nguồn chính

---

## 1) Kết luận nhanh

### Codex dùng mấy lớp cấu hình?

Codex có kiến trúc cấu hình nhiều lớp, theo thứ tự ưu tiên cao → thấp:

1. CLI flags và `--config`
2. Profile (`--profile <name>`)
3. Project config `.codex/config.toml` từ root repo đến thư mục hiện tại, thư mục gần nhất thắng
4. User config `~/.codex/config.toml`
5. System config `/etc/codex/config.toml` (nếu có)
6. Built-in defaults

### Global config của Codex nằm ở đâu?

- **Home chính**: `CODEX_HOME` nếu set, mặc định là `~/.codex`
- **User config chính**: `~/.codex/config.toml`
- **System config**: `/etc/codex/config.toml`
- **Global instruction file**: `~/.codex/AGENTS.md` hoặc `~/.codex/AGENTS.override.md`
- **Global custom agents**: `~/.codex/agents/*.toml`
- **User skills**: `$HOME/.agents/skills`
- **System/admin skills**: `/etc/codex/skills`
- **Hooks**: thường đặt ở `~/.codex/hooks.json` hoặc `<repo>/.codex/hooks.json` khi bật feature `codex_hooks`

### Codex subagents có bản chất gì?

Codex subagents là **child agents được spawn khi user explicit yêu cầu**. Chúng:

- có thread riêng
- có thể chạy song song
- dùng sandbox policy kế thừa từ parent, nhưng custom agent có thể set override riêng
- vẫn bị runtime override của parent turn áp lại khi spawn
- có giới hạn toàn cục qua `[agents]`

### Codex skills khác gì Claude Code skills?

Khác rất mạnh ở tầng authoring:

- **Codex skills** là **thư mục skill chuẩn**, tâm điểm là `SKILL.md`, có thể kèm `scripts/`, `references/`, `assets/`, `agents/openai.yaml`.
- **Claude Code** tách khá rõ 3 lớp khác nhau trong docs chính thức: `CLAUDE.md` cho instructions/memory, `settings.json` cho cấu hình runtime, và `.claude/commands/*.md` cho custom slash commands. Subagents lại là file `.md` riêng trong `.claude/agents/` hoặc `~/.claude/agents/`.
- Vì vậy khi so sánh với Codex, không nên gộp toàn bộ Claude customization vào một khái niệm “skills” duy nhất; nó là hệ nhiều lớp khác Codex.

### Codex slash commands khác Claude Code slash commands thế nào?

- **Codex**: built-in command set thiên về runtime control của chính Codex như `/agent`, `/plugins`, `/apps`, `/experimental`, `/debug-config`, `/statusline`, `/title`.
- **Claude Code**: built-in command set khác, và custom slash command trong doc chính thức dùng `.claude/commands/*.md` với frontmatter như `allowed-tools`, `argument-hint`, `description`, `model`.

---

## 2) Cấu trúc global của Codex

## 2.1. `CODEX_HOME` và thư mục global

Theo tài liệu OpenAI, Codex lưu state cục bộ dưới `CODEX_HOME`, mặc định là `~/.codex`.

Các file/trạng thái thường gặp trong đó:

- `config.toml`
- `auth.json` hoặc OS keychain/keyring
- `history.jsonl` nếu bật persistence
- logs, cache, state khác

### Cây thư mục global quan trọng

```text
~/.codex/
├── config.toml                 # user-level config
├── hooks.json                  # lifecycle hooks nếu bật feature codex_hooks
├── AGENTS.md                   # global instructions
├── AGENTS.override.md          # global override instructions
├── agents/
│   └── *.toml                  # custom agent definitions
└── ...                         # auth, history, logs, cache, sqlite state...
```

## 2.2. Cấu hình project của Codex

Trong repo, Codex dùng:

```text
.codex/
├── config.toml
├── hooks.json
└── agents/
    └── *.toml
```

Điểm rất quan trọng:

- Codex chỉ load `.codex/config.toml` nếu **project được trust**.
- Codex đi từ project root tới current working directory và load mọi `.codex/config.toml` trên đường đi.
- File gần current working directory hơn sẽ override file ở trên.
- Relative path trong project config được resolve tương đối theo thư mục `.codex/` chứa file đó.
- Đây là layer **project config/runtime**. Nó khác với `.agents/skills`, vốn là layer **skill discovery/authoring**.
- Theo tài liệu Team Config của OpenAI, teams còn có thể chuẩn hóa defaults/rules/skills cho tổ chức; nhưng path/precedence cụ thể vẫn tham chiếu về hệ config cơ bản ở `config.toml` + tài liệu Config basics.

### Phân biệt nhanh 3 lớp trong Codex

```text
.codex/config.toml + hooks.json   → config/runtime behavior
.codex/agents/*.toml              → custom agents/subagents
.agents/skills/**                 → reusable skills
```

Điểm này rất dễ nhầm nếu chỉ nhìn lướt cấu trúc thư mục.

---

## 3) AGENTS.md trong Codex

## 3.1. Vai trò

`AGENTS.md` là cơ chế instruction chain của Codex. Codex đọc **trước khi làm việc**.

Codex build instruction chain theo thứ tự:

1. Global scope: `~/.codex/AGENTS.override.md` nếu có, nếu không thì `~/.codex/AGENTS.md`
2. Project scope: từ project root xuống current directory, mỗi cấp chọn tối đa 1 file theo thứ tự:
   - `AGENTS.override.md`
   - `AGENTS.md`
   - các tên fallback trong `project_doc_fallback_filenames`
3. Ghép nội dung từ root xuống dưới; file gần current dir hơn xuất hiện sau, nên override mạnh hơn

## 3.2. Các config liên quan AGENTS.md

Từ tài liệu Codex:

- `project_doc_max_bytes`: giới hạn tổng bytes của instruction docs được nạp
- `project_doc_fallback_filenames`: các tên fallback ngoài `AGENTS.md`

Ví dụ tài liệu OpenAI nêu rõ có thể thêm fallback như:

```toml
project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]
project_doc_max_bytes = 65536
```

## 3.3. File global chính xác

- `~/.codex/AGENTS.md`: global defaults
- `~/.codex/AGENTS.override.md`: global override tạm thời

Đây là khác biệt rất đáng chú ý với Claude Code, nơi memory/instructions xoay quanh `CLAUDE.md` và hệ thống memory riêng.

---

## 4) Subagents trong Codex

## 4.1. Hành vi runtime

Theo OpenAI Developers:

- Codex **chỉ spawn subagent khi user explicit yêu cầu**
- Codex orchestrate việc spawn, follow-up, wait result, close thread
- Có thể chạy song song nhiều subagent
- Khi nhiều agent cùng chạy, Codex đợi đủ kết quả rồi trả consolidated response

### Ý nghĩa kiến trúc

Subagent của Codex là **threaded child workflow** được runtime điều phối, không chỉ là prompt template.

Luồng khái niệm:

```text
Parent agent
→ explicit request to spawn subagents
→ Codex runtime creates child agent threads
→ each child runs model + tools separately
→ parent waits / routes follow-up / collects outputs
→ parent returns merged answer
```

## 4.2. Approval và sandbox khi spawn

Tài liệu OpenAI nêu rõ:

- Subagents **inherit sandbox policy** của parent
- Approval request có thể nổi lên từ thread không active trong CLI interactive mode
- Nếu non-interactive hoặc không thể xin approval mới, action cần approval mới sẽ fail và error trả về parent
- Codex reapply **live runtime overrides** của parent turn khi spawn child
  - gồm sandbox
  - approval choices set trong session
  - ví dụ `/approvals` thay đổi, hoặc `--yolo`
- Custom agent file có thể set sandbox config riêng cho từng custom agent

### Ý nghĩa thực tế

Custom agent file trong Codex **không hoàn toàn độc lập** với runtime parent. Runtime override của session cha vẫn có trọng lượng khi spawn.

## 4.3. Built-in agents của Codex

OpenAI docs liệt kê built-in agents:

- `default`: general-purpose fallback
- `worker`: execution-focused
- `explorer`: read-heavy codebase exploration

Nếu custom agent trùng tên built-in như `explorer`, custom agent sẽ **take precedence**.

## 4.4. Vị trí custom agents của Codex

- **Global/user**: `~/.codex/agents/*.toml`
- **Project**: `.codex/agents/*.toml`

Mỗi file `.toml` định nghĩa **một custom agent**.

## 4.5. Global `[agents]` config của Codex

Theo doc `Subagents`:

```toml
[agents]
max_threads = 6
max_depth = 1
job_max_runtime_seconds = 1800 # ví dụ logic default tool-level
```

### Các field global chính thức

| Field | Bắt buộc | Ý nghĩa |
|---|---:|---|
| `agents.max_threads` | Không | Giới hạn số agent thread mở đồng thời |
| `agents.max_depth` | Không | Độ sâu nesting của agent spawn |
| `agents.job_max_runtime_seconds` | Không | Timeout mặc định cho worker trong `spawn_agents_on_csv` |

### Default quan trọng

| Field | Default theo doc |
|---|---|
| `agents.max_threads` | `6` |
| `agents.max_depth` | `1` |
| `agents.job_max_runtime_seconds` | nếu unset thì `spawn_agents_on_csv` dùng default per-call `1800s` |

### Ý nghĩa của `max_depth`

OpenAI cảnh báo rõ:

- `max_depth = 1` cho phép direct child spawn
- ngăn nesting sâu hơn
- tăng depth có thể làm fan-out lặp lại
- kéo theo tăng token, latency, resource usage

## 4.6. Schema custom agent file của Codex

Mỗi file custom agent `.toml` bắt buộc có:

| Field | Required | Ý nghĩa |
|---|---:|---|
| `name` | Có | Tên agent, source of truth cho việc nhận diện/spawn |
| `description` | Có | Mô tả khi nào nên dùng agent |
| `developer_instructions` | Có | Prompt/instruction lõi của agent |
| `nickname_candidates` | Không | Danh sách nickname hiển thị |

Ngoài ra, docs nói có thể thêm các key config bình thường như:

- `model`
- `model_reasoning_effort`
- `sandbox_mode`
- `mcp_servers`
- `skills.config`

Nếu omit các field optional này thì chúng **inherit từ parent session**.

## 4.7. `nickname_candidates`

Field này là presentation-only:

- dùng để đặt tên hiển thị dễ đọc hơn cho nhiều instance cùng loại agent
- không đổi `name` thật của agent
- yêu cầu danh sách non-empty, unique
- ký tự cho phép: ASCII letters, digits, spaces, hyphens, underscores

Ví dụ doc:

```toml
name = "reviewer"
description = "PR reviewer focused on correctness, security, and missing tests."
developer_instructions = """
Review code like an owner.
Prioritize correctness, security, behavior regressions, and missing test coverage.
"""
nickname_candidates = ["Atlas", "Delta", "Echo"]
```

## 4.8. `spawn_agents_on_csv`

Đây là điểm Codex có tài liệu rõ hơn Claude Code ở mặt batch fan-out.

Tool/workflow này cho phép:

- đọc CSV
- spawn 1 worker subagent / 1 row
- chờ full batch xong
- export result ra CSV

Tham số OpenAI docs nêu:

- `csv_path`
- `instruction`
- `id_column`
- `output_schema`
- `output_csv_path`
- `max_concurrency`
- `max_runtime_seconds`

Mỗi worker phải gọi `report_agent_job_result` đúng 1 lần.

### Ý nghĩa kiến trúc

Codex có runtime pattern chính thức cho **batch subagent orchestration** qua CSV. Đây là pattern tài liệu public mô tả rõ.

---

## 5) Skills trong Codex

## 5.1. Authoring model

Theo OpenAI docs, skill là **directory-based reusable workflow unit**.

Cấu trúc chuẩn:

```text
my-skill/
├── SKILL.md           # bắt buộc
├── scripts/           # optional
├── references/        # optional
├── assets/            # optional
└── agents/
    └── openai.yaml    # optional
```

`SKILL.md` phải có frontmatter:

```md
---
name: skill-name
description: Explain exactly when this skill should and should not trigger.
---

Skill instructions for Codex to follow.
```

## 5.2. Progressive disclosure

Codex không nạp full nội dung mọi skill ngay từ đầu.

Theo docs:

- Ban đầu Codex chỉ giữ metadata skill:
  - `name`
  - `description`
  - file path
  - metadata optional từ `agents/openai.yaml`
- Chỉ khi Codex quyết định dùng skill thì mới load full `SKILL.md`

Đây là cơ chế rất quan trọng để giảm context load.

## 5.3. Cách activate skill

Codex có 2 kiểu:

1. **Explicit invocation**: dùng `/skills` hoặc gõ `$` để mention skill
2. **Implicit invocation**: Codex tự chọn khi task match `description`

Nếu muốn chặn implicit invocation, dùng `policy.allow_implicit_invocation: false` trong `agents/openai.yaml`.

## 5.4. Vị trí discovery của skills trong Codex

Theo docs, Codex scan skill ở nhiều scope:

| Scope | Vị trí | Ghi chú |
|---|---|---|
| REPO | `.agents/skills` từ current dir lên repo root | repo-scoped skill discovery |
| USER | `$HOME/.agents/skills` | user skill dùng cho mọi repo |
| ADMIN | `/etc/codex/skills` | skill toàn máy/container |
| SYSTEM | bundled by OpenAI | built-in skills |

### Điểm rất quan trọng

Codex dùng **`.agents/skills`**, không phải `.codex/skills`.

Tức là:

- `.codex/` thiên về config/runtime/agent file
- `.agents/skills/` là skill authoring/discovery path

Đây là chi tiết kiến trúc dễ nhầm.

## 5.5. Tắt skill bằng config

Codex hỗ trợ disable skill mà không xóa file:

```toml
[[skills.config]]
path = "/path/to/skill/SKILL.md"
enabled = false
```

## 5.6. `agents/openai.yaml` trong skill

OpenAI docs nêu file optional này dùng cho:

- UI metadata
- invocation policy
- tool dependencies

Ví dụ field:

### `interface`

| Field | Ý nghĩa |
|---|---|
| `display_name` | tên hiển thị |
| `short_description` | mô tả ngắn |
| `icon_small` | icon nhỏ |
| `icon_large` | icon lớn |
| `brand_color` | màu thương hiệu |
| `default_prompt` | prompt mặc định bao quanh skill |

### `policy`

| Field | Ý nghĩa |
|---|---|
| `allow_implicit_invocation` | nếu `false`, không auto invoke skill |
| `products[]` | giới hạn product surface nếu có |

### `dependencies.tools[]`

OpenAI docs minh họa tool dependency dạng:

```yaml
dependencies:
  tools:
    - type: "mcp"
      value: "openaiDeveloperDocs"
      description: "OpenAI Docs MCP server"
      transport: "streamable_http"
      url: "https://developers.openai.com/mcp"
```

### Ý nghĩa

Codex skill có metadata packaging/UI/dependency tốt hơn ở mặt public docs so với mô hình command markdown đơn giản.

---

## 6) Slash commands trong Codex

## 6.1. Built-in slash commands chính thức

Từ OpenAI docs hiện tại:

| Command | Vai trò ngắn |
|---|---|
| `/permissions` | đổi policy quyền/phê duyệt |
| `/sandbox-add-read-dir` | thêm read dir cho sandbox trên Windows |
| `/agent` | chuyển active agent thread |
| `/apps` | browse connector apps |
| `/plugins` | browse/manage plugins |
| `/clear` | clear terminal + fresh chat |
| `/compact` | summarize conversation để giải phóng context |
| `/copy` | copy output mới nhất |
| `/diff` | xem git diff, kể cả untracked |
| `/exit`, `/quit` | thoát CLI |
| `/experimental` | toggle experimental features |
| `/feedback` | gửi logs/feedback cho maintainer |
| `/init` | tạo `AGENTS.md` scaffold |
| `/logout` | sign out |
| `/mcp` | list MCP tools |
| `/mention` | attach file vào conversation |
| `/model` | đổi model |
| `/fast` | toggle Fast mode |
| `/plan` | vào plan mode |
| `/personality` | đổi style giao tiếp |
| `/ps` | xem background terminals |
| `/stop` | dừng background terminals |
| `/fork` | fork conversation thread |
| `/resume` | resume session cũ |
| `/new` | chat mới trong cùng CLI session |
| `/review` | review working tree |
| `/status` | xem session config + token usage |
| `/debug-config` | debug config layers và requirements |
| `/statusline` | cấu hình footer status line |
| `/title` | cấu hình terminal title |

Alias cũ:

- `/approvals` còn hoạt động nhưng không còn hiện trong popup list
- `/clean` là alias cho `/stop`

## 6.2. Bản chất command của Codex

Codex slash commands thiên về:

- session control
- config/debug runtime
- thread management
- plugin/app browsing
- review/plan/compact

OpenAI docs slash command **không mô tả custom slash command markdown authoring giống Claude Code** trong trang này. Trọng tâm docs public là built-in runtime commands.

---

## 7) So sánh kiến trúc Codex vs Claude Code

## 7.1. Tổng quan rất ngắn

| Chủ đề | Codex | Claude Code |
|---|---|---|
| Global home | `~/.codex` | `~/.claude` |
| Global instruction file | `AGENTS.md` | `CLAUDE.md` |
| Main runtime config file | `config.toml` | `settings.json` |
| Project config root | `.codex/` | `.claude/` |
| Custom agents/subagents | `.codex/agents/*.toml` | `.claude/agents/*.md` |
| Reusable skill/workflow path | `.agents/skills`, `~/.agents/skills` | custom slash commands ở `.claude/commands/`, `~/.claude/commands/`; subagents ở `.claude/agents/` |
| Skill/command format | directory + `SKILL.md` + optional `openai.yaml` | markdown commands + markdown subagents |
| Subagent spawn | explicit request only | có thể proactive delegate theo task match và policy/tooling hiện hành |
| Built-in thread/agent command | `/agent` | `/agents` để manage subagents |
| Hooks/config layering | `config.toml` + `hooks.json` | `settings.json` + hooks config trong settings |
| Enterprise managed settings | managed defaults / requirements / team config docs | `managed-settings.json` |

## 7.2. So sánh subagents/agents

### Codex

- custom agent là file `.toml`
- required fields: `name`, `description`, `developer_instructions`
- optional: `nickname_candidates`, và các config key khác như `model`, `sandbox_mode`, `mcp_servers`, `skills.config`
- global limits ở `[agents]`
- built-in agents rõ: `default`, `worker`, `explorer`
- spawn khi **explicit ask**
- runtime parent override được reapply lên child
- có tài liệu public về `spawn_agents_on_csv`

### Claude Code

Theo Anthropic docs:

- subagent là file markdown với YAML frontmatter
- location:
  - `.claude/agents/`
  - `~/.claude/agents/`
- fields chính:
  - `name`
  - `description`
  - `tools` (optional)
  - `model` (optional: `sonnet`, `opus`, `haiku`, hoặc `inherit`)
- phần body markdown là system prompt của subagent
- nếu omit `tools` thì inherit all tools từ main thread
- project-level subagent thắng user-level khi trùng tên
- Claude Code có built-in `/agents` command để manage subagents
- Claude Code docs nhấn mạnh **automatic delegation** dựa trên task description + agent description + context

### Điểm khác biệt lõi

| Khía cạnh | Codex | Claude Code |
|---|---|---|
| File format | TOML | Markdown + YAML frontmatter |
| Prompt field | `developer_instructions` | body của file `.md` |
| Tool restriction | gián tiếp qua config/tool deps/skill config | `tools:` trực tiếp trong frontmatter |
| Built-in auto delegation | docs nói explicit ask để spawn | docs nói có thể proactive delegate tự động |
| Runtime global caps | `[agents]` rõ ràng | docs public trang subagents không nêu bảng global caps tương tự |
| Batch orchestration | có `spawn_agents_on_csv` | không thấy public doc tương đương trong nguồn đã dùng |
| Nickname/display | có `nickname_candidates` | không thấy field public tương đương trên trang subagents |

## 7.3. So sánh skills

### Codex

- skills là đơn vị reusable workflow chính thức
- format mạnh, giàu cấu trúc
- discovery từ `.agents/skills`, `~/.agents/skills`, `/etc/codex/skills`, built-in system skills
- hỗ trợ `scripts/`, `references/`, `assets/`, `agents/openai.yaml`
- có progressive disclosure
- có implicit + explicit invoke
- có disable theo `[[skills.config]]`
- có plugin làm distribution unit cho reusable skills/apps

### Claude Code

Từ docs chính thức của Anthropic:

- runtime config của Claude Code nằm ở:
  - `~/.claude/settings.json`
  - `.claude/settings.json`
  - `.claude/settings.local.json`
  - enterprise managed settings file
- custom slash commands project/user lưu ở `.claude/commands/` và `~/.claude/commands/`
- command file là markdown có frontmatter như:
  - `allowed-tools`
  - `argument-hint`
  - `description`
  - `model`
- command body có thể dùng:
  - `$ARGUMENTS`, `$1`, `$2`
  - `!\`bash command\`` để pre-run bash context
  - `@file` để include file reference
- MCP prompts được expose thành slash commands theo pattern:
  - `/mcp__<server-name>__<prompt-name>`
- subagents của Claude Code lại nằm ở `.claude/agents/` hoặc `~/.claude/agents/`

Vì vậy, nếu so với Codex, Claude Code có kiến trúc customization public docs khá tách bạch:

```text
CLAUDE.md                   → instructions / memory-style guidance
settings.json               → runtime config / permissions / hooks / env
.claude/commands/*.md       → custom slash commands
.claude/agents/*.md         → custom subagents
```

Điểm này khác với Codex, nơi `config.toml` giữ vai trò trung tâm hơn và skill authoring lại tách sang `.agents/skills/`.

### Khác biệt lõi giữa Codex skills và Claude Code commands/skills

| Khía cạnh | Codex | Claude Code |
|---|---|---|
| Reusable workflow primary format | skill directory | markdown command / skill ecosystem riêng |
| Main manifest | `SKILL.md` | `.md` command file hoặc skill invoked qua Skill tool |
| Optional metadata | `agents/openai.yaml` | frontmatter command fields / agent frontmatter |
| Discovery path | `.agents/skills` | `.claude/commands` cho custom slash commands |
| Plugin packaging | có, rõ trong docs | không phải trọng tâm trong nguồn đang dùng |
| Progressive disclosure | có, official docs nêu rõ | không thấy public doc tương đương trong nguồn đã dùng |

## 7.4. So sánh slash commands

### Codex built-ins nổi bật hơn ở:

- `/agent`
- `/plugins`
- `/apps`
- `/experimental`
- `/debug-config`
- `/statusline`
- `/title`
- `/ps`, `/stop`
- `/fork`, `/resume`, `/new`

### Claude Code built-ins nổi bật hơn ở:

- `/agents`
- `/memory`
- `/doctor`
- `/pr_comments`
- `/terminal-setup`
- `/vim`
- `/config`
- `/cost`

### Khác biệt về custom slash commands

- Claude Code docs public mô tả rõ **custom slash command authoring** bằng markdown file trong `.claude/commands/`.
- Trong bộ nguồn Codex official được dùng ở đây, docs public tập trung mạnh hơn vào **skills** và built-in slash commands; workflow tùy biến được đẩy nhiều hơn sang skills / plugin / custom agent layer.
- Nói chặt hơn: trong bộ nguồn đã dùng cho tài liệu này, mình **không thấy** một trang public official của Codex mô tả custom slash commands theo kiểu markdown repo-local tương đương Claude Code. Vì vậy phần này cần đọc đúng là “không thấy trong nguồn đã dùng”, không phải “Codex hoàn toàn không có”.

> 📌 Đây là một trong các điểm mình đã siết lại để tránh kết luận quá đà.

---

## 7.5. So sánh lớp cấu hình runtime

### Codex

Codex dùng `config.toml` làm trung tâm cho:

- model / provider
- sandbox / approval
- MCP servers
- profiles
- features
- project doc discovery
- agents global settings
- skill disable config
- telemetry / history / notifications

### Claude Code

Claude Code dùng `settings.json` làm trung tâm cho:

- permissions
- hooks
- env
- model
- status line
- MCP approvals/settings liên quan `.mcp.json`
- project và user settings precedence
- enterprise managed policy settings

### Kết luận nhỏ

Cả hai đều có cấu hình phân lớp, nhưng:

- **Codex**: nghiêng về TOML config + agent/skill ecosystem riêng
- **Claude Code**: nghiêng về JSON settings + command files + agent markdown files

Điều này ảnh hưởng trực tiếp tới cách tổ chức global repo template và cách chuẩn hóa cho team.

---

## 7.6. Cẩn trọng khi so sánh “global” giữa hai hệ

Khi nói “global” cần tách 4 nghĩa khác nhau:

| Loại | Codex | Claude Code |
|---|---|---|
| Global home | `~/.codex` | `~/.claude` |
| Global runtime config | `~/.codex/config.toml` | `~/.claude/settings.json` |
| Global persistent instructions | `~/.codex/AGENTS.md` | global `CLAUDE.md` / memory files trong hệ Claude Code |
| Global custom agents | `~/.codex/agents/*.toml` | `~/.claude/agents/*.md` |
| Global reusable workflows | `~/.agents/skills` | `~/.claude/commands/*.md` + user subagents |

Nếu không tách 4 lớp này, rất dễ so sánh lệch.

---

## 7.7. Điểm cần đọc rất cẩn thận trong phần Codex Team Config

OpenAI có trang Team Config / Admin Setup nói về việc teams chia sẻ:

- defaults qua `config.toml`
- rules qua `rules/`
- skills qua `skills/`

Nhưng tài liệu đó nằm trong bối cảnh rollout/admin và tham chiếu ngược về Config basics để xác nhận precedence/location cụ thể.

Vì vậy trong tài liệu này, mình dùng Team Config như **bằng chứng về mô hình chuẩn hóa tổ chức**, còn các kết luận chi tiết về path/preference vẫn bám vào các trang cấu hình cơ bản và advanced config.

Điểm này cũng đã được siết lại để tránh dùng trang admin như nguồn duy nhất cho behavior kỹ thuật chi tiết.

---

## 8) Những thứ Codex có mà Claude Code public doc ở đây không thấy nhấn mạnh tương đương

| Năng lực / field | Codex | Ghi chú |
|---|---|---|
| `[agents].max_threads` | Có | giới hạn concurrency toàn cục |
| `[agents].max_depth` | Có | giới hạn nesting toàn cục |
| `[agents].job_max_runtime_seconds` | Có | timeout batch worker mặc định |
| `nickname_candidates` | Có | chỉ để hiển thị agent name đẹp hơn |
| `spawn_agents_on_csv` | Có | batch fan-out workflow public doc rõ |
| `report_agent_job_result` | Có | contract bắt buộc cho CSV worker |
| `agents/openai.yaml` trong skill | Có | UI + dependency + policy metadata |
| Plugin là distribution unit | Có | bundle skills/apps/integrations |
| `project_doc_fallback_filenames` | Có | mở rộng AGENTS discovery |
| `project_doc_max_bytes` | Có | limit instruction chain bytes |
| `/debug-config` | Có | debug config layering |
| `/statusline`, `/title` | Có | config UI runtime rõ |
| profiles trong config | Có | `--profile <name>` + `[profiles.<name>]` |
| `--config` override TOML keys | Có | override key bất kỳ cho 1 run |
| `hooks.json` cạnh config layer | Có | khi bật `codex_hooks` |

---

## 9) Những thứ Claude Code public doc ở đây có mà Codex khác cách thể hiện

| Năng lực / field | Claude Code | Ghi chú |
|---|---|---|
| Subagent file `.md` với YAML frontmatter | Có | khác hoàn toàn TOML agent của Codex |
| `tools:` trực tiếp trên subagent | Có | dễ author hơn cho tool allowlist |
| `model: inherit` | Có | public doc nêu rõ |
| `/agents` built-in manager | Có | tạo/sửa/xóa subagent trực tiếp |
| `.claude/commands/*.md` | Có | custom slash command repo-scoped |
| `allowed-tools` frontmatter trong command | Có | command-level permission shaping |
| `$ARGUMENTS`, `$1`, `$2` | Có | command templating |
| `!\`bash\`` pre-execution trong command | Có | inject command output vào context |
| `@file` references trong command | Có | include file vào command context |
| `/mcp__server__prompt` | Có | MCP prompts thành slash commands |

---

## 10) Ví dụ cấu hình chuẩn tối thiểu của Codex

## 10.1. User global config

```toml
# ~/.codex/config.toml
model = "gpt-5.4"
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[agents]
max_threads = 6
max_depth = 1

[features]
multi_agent = true
```

## 10.2. Global instructions

```md
# ~/.codex/AGENTS.md
## Working agreements
- Run tests after code changes.
- Prefer minimal changes.
- Ask before adding new dependencies.
```

## 10.3. Project custom agent

```toml
# .codex/agents/reviewer.toml
name = "reviewer"
description = "PR reviewer focused on correctness, security, and missing tests."
model = "gpt-5.4"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
Review code like an owner.
Prioritize correctness, security, regressions, and missing tests.
"""
```

## 10.4. User skill

```text
~/.agents/skills/my-skill/
├── SKILL.md
└── agents/openai.yaml
```

---

## 11) Kết luận kiến trúc

## 11.1. Cách nghĩ đúng về Codex

Codex tách khá rõ 4 lớp:

```text
~/.codex / .codex     → config + agents + hooks + AGENTS instructions
.agents/skills        → reusable workflow authoring
plugins               → distribution/package layer cho skills/apps
runtime subagents     → threaded delegated execution managed by Codex
```

## 11.2. Cách nghĩ đúng về khác biệt với Claude Code

Claude Code và Codex đều có agent/subagent, command, instruction docs.

Nhưng hướng thiết kế public docs hiện tại khác nhau:

- **Codex**: nghiêng về `config.toml` + `AGENTS.md` + `.codex/agents/*.toml` + `.agents/skills/` + plugins
- **Claude Code**: nghiêng về `CLAUDE.md` + `.claude/agents/*.md` + `.claude/commands/*.md` + built-in subagent manager

## 11.3. Khác biệt bản chất subagent

- **Codex subagents**: explicit, thread-based, có global caps, có batch CSV workflow, custom agent file là TOML config layer.
- **Claude Code subagents**: markdown-defined specialized assistants, dễ author thủ công hơn, public doc nhấn mạnh auto delegation và direct tool allowlisting.

---

## 12) Ghi chú về độ tin cậy nguồn

Tài liệu này chỉ dựa trên nguồn chính thức đã đọc:

### OpenAI / Codex

- OpenAI Developers Codex docs
- GitHub repo `openai/codex`

### Anthropic / Claude Code

- Claude Code official docs

Nếu cần đối chiếu sâu thêm ở mức code implementation của Codex runtime, nên đọc tiếp các phần sau trong repo `openai/codex`:

- `codex-rs/core/config.schema.json`
- `codex-rs/config/`
- `codex-rs/core-skills/`
- `codex-rs/skills/`
- `codex-rs/core/` và state-machine docs liên quan

---

## 13) Nguồn chính thức đã dùng

### Codex

- https://developers.openai.com/codex/config-basic
- https://developers.openai.com/codex/config-advanced
- https://developers.openai.com/codex/config-reference
- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/cli/slash-commands
- https://developers.openai.com/codex/subagents
- https://github.com/openai/codex/blob/master/README.md
- https://github.com/openai/codex/blob/master/docs/config.md
- https://github.com/openai/codex/blob/master/docs/agents_md.md
- https://github.com/openai/codex/blob/master/docs/skills.md
- https://github.com/openai/codex/blob/master/docs/slash_commands.md
- https://github.com/openai/codex/blob/master/codex-rs/core/config.schema.json
- https://github.com/openai/codex/blob/master/AGENTS.md

### Claude Code

- https://docs.anthropic.com/en/docs/claude-code
- https://docs.anthropic.com/en/docs/claude-code/sub-agents
- https://docs.anthropic.com/en/docs/claude-code/slash-commands
- https://docs.anthropic.com/en/docs/claude-code/settings

### Codex team/admin context

- https://developers.openai.com/codex/team-config
