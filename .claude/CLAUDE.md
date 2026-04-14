# CLAUDE.md

Project-local guidance for Claude Code in this repository.

## Purpose

This file captures the small set of project-local rules worth keeping close to the codebase.

Use this file for repo-local execution guidance.
Also check the root `CLAUDE.md` file for project-scope instructions when it exists.
Use project-scope rules and skills under `./.claude/` as the local source of truth when they exist.

## Communication style

- Always respond in Vietnamese unless the user explicitly asks for another language.
- Use positive, simple, easy-to-follow wording.
- Prefer plain language over jargon; if a technical term is necessary, explain it in simple words.
- Write as if explaining to a beginner who needs clarity, not speed.
- Avoid stacking too many technical terms in one sentence.
- Keep reports concise, but never at the cost of clarity.
- Terse/caveman style có thể dùng cho status update ngắn hoặc phản hồi trung gian nếu user muốn.
- Final answer gửi user phải thoát terse/caveman style và quay về văn phong bình thường, rõ ràng, đầy đủ.
- Final answer phải follow `./.claude/rules/response-format.md`; nếu có xung đột với mode nén chữ thì `response-format.md` thắng.

## Core workflow

- Before planning or implementing, read `./README.md` first.
- Keep reports concise; clarity is more important than polished prose.
- List unresolved questions at the end of reports when there are any.
- For deterministic dates like `YYMMDD`, use shell commands instead of model memory.

## LittlePea pipeline

- Source of truth for `/lp:*` orchestration: `./.claude/skills/lp-pipeline-orchestrator/SKILL.md`
- Source of truth for LP state/runtime DB operations: `./.claude/skills/lp-state-manager/SKILL.md`
- Source of truth for LP behavior constraints: `./.claude/rules/identity.md`
- Canonical command catalog: `./.claude/commands/lp:index.md`
- Quick workflow catalog: `./.claude/commands/lp:pipeline.md`

### Canonical `/lp:*` commands

- Public orchestration commands: `/lp:plan`, `/lp:implement`, `/lp:cook`, `/lp:debug-investigator`
- Utility wrappers: `/lp:qa-automation`, `/lp:close-task`, `/lp:lesson-capture`, `/lp:pipeline`
- Deprecated worker aliases: `/lp:create-plan`, `/lp:review-plan`, `/lp:implement-plan`
- Namespace placeholders chưa có project-scope skill thật: `/lp:init-project`, `/lp:sync-agents-context`, `/lp:jira-workflow-bridge`
- QA trong LP delivery loop vẫn chủ yếu được điều phối nội bộ bằng worker skill `qa-automation`, thường đi qua `/lp:implement` hoặc `/lp:cook`.
- Khi cần chạy QA như LP namespace wrapper độc lập, dùng `/lp:qa-automation`.
- Command gốc của skill vẫn tồn tại là `/qa-automation`, nhưng trong LP docs nên ưu tiên `/lp:qa-automation` cho nhất quán namespace.
- Không dùng tên `/lp:qa-auto`.

### LP operating rules

- Treat LP runtime artifacts under `./.claude/` as canonical for this repo.
- Do not reintroduce `.agents`-based runtime layout for LP pipeline work.
- LP top-level worker steps phải dùng agents; main chat đóng vai trò orchestrator, không thay worker step khi flow canonical yêu cầu agent worker.
- Mặc định spawn LP agents ngay trong current workspace, không dùng worktree isolation.
- Chỉ dùng worktree isolation nếu user explicit yêu cầu.
- LP top-level worker steps phải chạy foreground; không dùng `run_in_background`.
- Prefer direct-edit mode in the current workspace cho LP trừ khi user explicit yêu cầu isolation khác.
- Nếu cần qua step tiếp theo, phải sync contract/state của step hiện tại trước.
- Với `review-plan` và `review-implement`, canonical model là 4 agents độc lập theo 4 persona bắt buộc, chạy song song rồi orchestrator tổng hợp; không dùng roster recommendation mềm cho 2 flow canonical này.
- Không dùng wording mơ hồ kiểu khiến IDE hiểu thành “đừng dùng agents”; intent đúng là “use agents, but no worktree by default”.

## Verification discipline

- After code edits, run a compile/syntax check when applicable.
- After logic changes, run the smallest relevant test command that gives real evidence.
- Do not use fake data, cheats, or temporary hacks just to pass tests/builds.
- If you update docs or pipeline/task artifacts, read them back to verify the written content matches intent.

## Orchestration discipline

- Use sequential execution when tasks depend on previous outputs.
- Use parallel execution only for isolated work with clear ownership boundaries.
- Before parallel work, identify shared resources and likely conflict points.
- For LP workflows, shared resources include `./.claude/state/` and `./.claude/pipeline/`.

## Scope control

- Prefer small, direct changes over framework-like abstractions.
- Do not import generic workflow conventions that conflict with LP canonical flow.
- Do not assume `./docs/`, `./plans/`, or other template directories exist unless verified in this repo.
- If a referenced file or convention does not exist in the repo, treat it as stale until verified.
