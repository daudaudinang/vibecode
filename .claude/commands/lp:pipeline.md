---
description: Catalog workflow cho bộ command LittlePea trong Claude Code.
---

# /lp:pipeline

## Purpose

Catalog nhanh để chọn đúng LP workflow thay vì nhớ flow bằng tay.

## Canonical feature flow

```text
/lp:plan <scope>
/lp:implement <plan_file | plan_name | workflow_id>
/lp:qa-automation <AC_LIST_OR_TICKET>   # optional standalone QA wrapper
/lp:close-task <ticket>
```

Trong flow chuẩn, QA thường đã chạy bên trong `/lp:implement`. `/lp:qa-automation` hữu ích khi cần rerun QA hoặc nghiệm thu riêng.

## Standalone QA flow

```text
/lp:qa-automation <AC_LIST_OR_TICKET>
```

## Canonical bug flow

```text
/lp:debug-investigator <symptom>
/lp:plan <fix-scope>
/lp:implement <plan_file | plan_name | workflow_id>
/lp:close-task <ticket>
```

## Autopilot flow

```text
/lp:cook <requirement>
```

## Notes

- Đây là catalog/doc command, không phải source of truth cho orchestration
- Canonical/public: `/lp:plan`, `/lp:implement`, `/lp:cook`, `/lp:debug-investigator`
- Utility wrappers: `/lp:qa-automation`, `/lp:close-task`, `/lp:lesson-capture`, `/lp:pipeline`
- Namespace placeholders chưa có project-scope skill thật: `/lp:init-project`, `/lp:sync-agents-context`, `/lp:jira-workflow-bridge`
- Orchestration thật nằm ở `.claude/skills/lp-pipeline-orchestrator/SKILL.md`
- Không dùng tên `/lp:qa-auto`; LP wrapper chuẩn là `/lp:qa-automation`.
