# Phase 02 - Orchestrator Epic Mode Runtime

## Scope
- Refactor orchestrator để support mode split rõ ràng: Single vs Epic.
- Implement Epic phase lifecycle: branch/worktree setup, baseline gate, delivery loop entry, safe boundary handling.
- Chốt ownership cho AC11 ở layer orchestrator: partial cancel command boundary + downstream dependency re-evaluation.
- Chuẩn hóa operator `waiting_user` one-screen recovery output cho 4 blocker classes.
- Merge-conflict recovery prompt bắt buộc có `Conflict files: <list>` (AC10), không dùng wording generic thay thế.
- Worktree creation fail phải có guidance explicit: `git worktree prune` hoặc manual cleanup git/worktree state.
- Operationalize rõ nhánh `dependency_critical = true` thiếu dependency khai báo: `waiting_user` ngay, không fallback tuyến tính.
- Thiết lập accessor contract deterministic cho `single-regression-check.command` và `degraded-design-drift-check.command`.

## Owned Files
- `.agents/skills/lp-pipeline-orchestrator/SKILL.md`
- `.agents/skills/lp-pipeline-orchestrator/references/commands.md`
- `.agents/skills/lp-pipeline-orchestrator/references/worktree-manager.md` (new/update)
- `.agents/skills/lp-pipeline-orchestrator/references/operator-waiting-user-contract.md` (new)
- `.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py`

## AC Mapping
- Primary: AC1, AC4, AC11, AC14, AC15
- Secondary support: AC3, AC8, AC10, AC13, AC17

## Verify Commands (Actionable + Runtime Scenarios)
1. Accessor deterministic check
   - `python -c "import re; from pathlib import Path; text=Path('.agents/skills/lp-pipeline-orchestrator/references/commands.md').read_text(); keys=['single-regression-check.command','degraded-design-drift-check.command'];\nfor key in keys:\n lines=[ln for ln in text.splitlines() if key in ln];\n assert len(lines)==1, f'{key}: expected exactly 1 candidate line, got {len(lines)}';\n ln=lines[0].strip(); cmd=None;\n if '|' in ln:\n  parts=[p.strip() for p in ln.split('|') if p.strip()];\n  if parts and parts[0].strip('`')==key and len(parts)>=2:\n   cmd=parts[1];\n if cmd is None:\n  m=re.search(re.escape(key)+r'\\s*[:=]\\s*(.+)$', ln);\n  if m:\n   cmd=m.group(1).strip();\n assert cmd is not None, f'{key}: malformed accessor line: {ln}';\n cmd=cmd.strip('`').strip();\n assert cmd and cmd.lower() not in {'tbd','todo','<command>'}, f'{key}: empty/placeholder command';\nprint('accessors-deterministic-ok')\""`
   - Expected evidence: exit `0`; mỗi accessor resolve đúng 1 command deterministic. Missing / empty / malformed / multi-candidate => FAIL.
2. Baseline resolution priority check
   - `rg -n "baseline_verify_command|label normalize về lowercase = baseline|Không có fallback ngầm" .codex/plans/PLAN_LP_PIPELINE_V3/spec.md .agents/skills/lp-pipeline-orchestrator/SKILL.md .agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py`
   - Expected evidence: priority-1 (`baseline_verify_command`) và priority-2 (đúng 1 label `baseline` trong plan artifact) đều được mô tả/implement rõ; không có fallback ngầm ngoài plan artifact.
3. Single no-regression fixture execution
   - `python -c "from pathlib import Path; out=Path('.codex/tmp/single-worktrees-before.txt'); out.parent.mkdir(parents=True, exist_ok=True); root=Path('.worktrees'); paths=sorted(p.as_posix() for p in root.rglob('*')) if root.exists() else []; out.write_text('\\n'.join(paths) + ('\\n' if paths else '')); print('worktree-snapshot-before-ok', out, len(paths))"`
   - `python -c "import re,subprocess; from pathlib import Path; text=Path('.agents/skills/lp-pipeline-orchestrator/references/commands.md').read_text(); key='single-regression-check.command'; lines=[ln for ln in text.splitlines() if key in ln]; assert len(lines)==1, f'{key}: expected exactly 1 candidate line, got {len(lines)}'; ln=lines[0].strip(); cmd=None;\nif '|' in ln:\n parts=[p.strip() for p in ln.split('|') if p.strip()];\n if parts and parts[0].strip('`')==key and len(parts)>=2:\n  cmd=parts[1];\nif cmd is None:\n m=re.search(re.escape(key)+r'\\s*[:=]\\s*(.+)$', ln);\n if m:\n  cmd=m.group(1).strip();\nassert cmd is not None, f'{key}: malformed accessor line: {ln}'; cmd=cmd.strip('`').strip(); assert cmd and cmd.lower() not in {'tbd','todo','<command>'}, f'{key}: empty/placeholder command'; print('RUN', cmd); raise SystemExit(subprocess.call(cmd, shell=True))\""`
   - Expected evidence: exit `0`; snapshot `.worktrees` được tạo trong cùng verify bundle trước fixture, delta trước/sau rỗng, và không tạo `.codex/plans/PLAN_<NAME>/phases/`.
4. Single artifact shape invariant check
   - `python -c "import json,os; from pathlib import Path; marker=Path('.codex/tmp/final-integration-single-plan.txt'); plan=os.environ.get('LP_SINGLE_FIXTURE_PLAN') or (marker.read_text().strip() if marker.exists() else 'PLAN_V3_SINGLE_FIXTURE'); assert plan, 'single fixture plan id resolved empty';\nfor step in ['03-implement-plan','04-review-implement','05-qa-automation']:\n p=Path(f'.codex/pipeline/{plan}/{step}.output.contract.json'); assert p.exists(), f'missing contract: {p}'; d=json.loads(p.read_text());\n assert d.get('schema_version'); assert d.get('skill'); assert d.get('status'); assert d.get('artifacts',{}).get('primary');\nprint('single-artifact-shape-ok', plan)\""`
   - Expected evidence: exit `0`; resolve được plan id deterministic (optional `LP_SINGLE_FIXTURE_PLAN`, fallback marker/default) và mỗi contract `03/04/05` có đủ field bắt buộc (`schema_version`, `skill`, `status`, `artifacts.primary`).
   - Boundary note: check `no .worktrees refs` và `single flow không có phases dir` thuộc Final Integration bundle ở plan-level (`single-runtime-shape-check` + `no-worktree-artifact-check`), không claim ở bước này.
5. waiting_user operator contract check
   - `rg -n "Error:|Required action:|Context:|Next command:|Recovery evidence required:|Conflict files:" .agents/skills/lp-pipeline-orchestrator/references/operator-waiting-user-contract.md .agents/skills/lp-pipeline-orchestrator/SKILL.md`
   - Expected evidence: one-screen template đầy đủ field cho baseline/worktree/merge/dependency blockers; merge-conflict case có explicit `Conflict files: <list>`.
6. Edge-case operational branch check
   - `rg -ni "git worktree prune|manual cleanup|dependency_critical|fallback tuyến tính|broad_context_reports|safe boundary|cancel_requested" .codex/plans/PLAN_LP_PIPELINE_V3/spec.md .agents/skills/lp-pipeline-orchestrator/SKILL.md .agents/skills/lp-pipeline-orchestrator/references/worktree-manager.md .agents/skills/lp-pipeline-orchestrator/references/operator-waiting-user-contract.md .agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py`
   - Expected evidence: worktree fail recovery có prune/manual cleanup guidance; dependency-critical missing graph không fallback; cancel flow chỉ dừng ở safe boundary đã định nghĩa.

## Exit Criteria
- Single path giữ nguyên no-regression behavior theo AC1.
- Epic orchestration có baseline gate + cancel_requested safe-boundary behavior.
- `waiting_user` output format thống nhất và có thể parse/đối chiếu.
- Merge conflict/worktree failure prompts explicit đủ field bắt buộc để operator phục hồi không suy đoán.
- Accessor references deterministic để downstream phases không đoán command.

## Downstream Agent Notes
- Không chuyển state authority sang phase notes ở phase này; chỉ sync mirrors theo protocol.
- Không xử lý merge conflict bằng auto-resolve; bắt buộc dừng `waiting_user`.
- `cancel_requested` chỉ được commit thành `cancelled` tại safe boundary; không kill giữa command đang chạy.
