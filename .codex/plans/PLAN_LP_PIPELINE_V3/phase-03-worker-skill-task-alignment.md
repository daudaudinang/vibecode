# Phase 03 - Worker Skill Task Alignment

## Scope
- Đồng bộ worker SKILL/TASK với orchestration contracts đã chốt ở P01/P02.
- Chuẩn hóa wording và enums across workers: chỉ dùng `pending | in_progress | waiting_user | completed | failed | cancelled`.
- Bổ sung hướng dẫn rõ cho phase notes/report update, context propagation, dependency-aware behavior.
- Làm rõ context-budget branch `broad_context_reports = true`: chỉ mở rộng đọc report completed phases khi phase-count `<= 5`, vẫn cấm đọc raw notes ngoài direct dependencies.
- Operationalize dependency gate cho worker: nếu `dependency_critical = true` nhưng dependencies thiếu/không rõ thì buộc `waiting_user`, không fallback tuyến tính.
- Chốt ownership cho các task files trước đây đang xuất hiện trong boundary nhưng chưa có owner (`create-spec`, `review-spec`, `persona-review`).

## Owned Files
- `.agents/skills/lp-implement/SKILL.md`
- `.agents/skills/lp-cook/SKILL.md`
- `.agents/skills/review-plan/SKILL.md`
- `.agents/skills/implement-plan/SKILL.md`
- `.agents/skills/review-implement/SKILL.md`
- `.agents/skills/qa-automation/SKILL.md`
- `.agents/skills/tasks/create-plan/TASK.md`
- `.agents/skills/tasks/review-plan/TASK.md`
- `.agents/skills/tasks/implement-plan/TASK.md`
- `.agents/skills/tasks/review-implement/TASK.md`
- `.agents/skills/tasks/qa-automation/TASK.md`
- `.agents/skills/tasks/review-spec/TASK.md`
- `.agents/skills/tasks/create-spec/TASK.md`
- `.agents/skills/tasks/persona-review/TASK.md`

## AC Mapping
- Primary: AC5, AC6, AC7
- Secondary support: AC9, AC12

## Verify Commands (Actionable + Evidence)
1. Enum normalization check
   - `python -c "from pathlib import Path; files=list(Path('.agents/skills').rglob('*.md')); bad=[];\nfor f in files:\n t=f.read_text(errors='ignore');\n if 'COMPLETED' in t or 'Done' in t:\n  bad.append(str(f));\nassert not bad, bad; print('enum-wording-ok')"`
   - Expected evidence: exit `0`, không còn drift wording trái enum canonical.
2. Phase artifact guidance coverage
   - `rg -n "phase notes|phase report|Notes for Later Phases|direct dependency|waiting_user|broad_context_reports|dependency_critical|fallback tuyến tính" .agents/skills/lp-implement/SKILL.md .agents/skills/implement-plan/SKILL.md .agents/skills/review-implement/SKILL.md .agents/skills/qa-automation/SKILL.md .agents/skills/lp-cook/SKILL.md`
   - Expected evidence: các worker liên quan đều có guidance thống nhất cho direct dependency path và broad-context branch.
3. Task boundary ownership closure
   - `python -c "from pathlib import Path; req=['create-spec','review-spec','persona-review'];\nfor r in req:\n p=Path(f'.agents/skills/tasks/{r}/TASK.md'); assert p.exists(), p;\nprint('task-ownership-covered')"`
   - Expected evidence: 3 task files bắt buộc tồn tại và nằm trong phạm vi phase này.
4. Broad-context ordering and notes boundary check
   - `rg -ni "phase <= 5|phase ≤ 5|tổng số phase|phase index tăng dần|broad_context_reports = true|không đọc raw notes|không đọc raw notes ngoài direct dependency" .codex/plans/PLAN_LP_PIPELINE_V3/spec.md .agents/skills/implement-plan/SKILL.md .agents/skills/review-implement/SKILL.md .agents/skills/qa-automation/SKILL.md`
   - Expected evidence: branch `broad_context_reports` được mô tả kèm thứ tự đọc report rõ ràng và vẫn giữ notes boundary.

## Exit Criteria
- Worker/task docs không còn mơ hồ về status wording và runtime source-of-truth.
- Context propagation rule cho phase N+1 được nêu rõ theo direct dependencies.
- Branch `broad_context_reports = true` và `dependency_critical = true` có hành vi explicit, không để fallback ngầm.
- Boundary items thuộc nhóm task files đều đã có owner rõ.

## Downstream Agent Notes
- Phase này không thay đổi state transaction logic; mọi state authority chi tiết để P04 xử lý.
- Nếu phải thay đổi contract field names, cập nhật đồng bộ cả SKILL và TASK tương ứng trong cùng commit.
