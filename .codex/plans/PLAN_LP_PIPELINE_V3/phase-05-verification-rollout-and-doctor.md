# Phase 05 - Verification Rollout And Doctor

## Scope
- Chốt verification bundle ở level plan/package để downstream review/implement có evidence path rõ.
- Định nghĩa section `Final Integration Verify Commands` parseable machine-readable cho AC12.
- Đồng bộ `.codex/AGENTS.md`, `vibecode-doctor`, `close-task`, `.gitignore` theo runtime invariants V3.
- Chuẩn hóa rollout benchmark labels theo ngôn ngữ operator-friendly.

## Owned Files
- `.codex/AGENTS.md`
- `.gitignore`
- `.agents/skills/vibecode-doctor/SKILL.md`
- `.agents/skills/close-task/SKILL.md`
- `.codex/plans/PLAN_LP_PIPELINE_V3/manifests/benchmark.json`

## AC Mapping
- Primary: AC9, AC12, AC16
- Secondary support: AC1, AC6, AC14

## Verify Commands (Actionable + Runtime Evidence)
1. Cross-reference coverage check (AC9 coverage layer)
   - `python -c "from pathlib import Path; files=[Path('.codex/AGENTS.md')] + sorted(Path('.agents/skills').rglob('*.md')); assert len(files) > 1, 'coverage-check: no skill markdown files found'; texts={str(f):f.read_text() for f in files}; required=['.codex/','state_manager.py','waiting_user','Final Integration Verify Commands','single-regression-check.command','degraded-design-drift-check.command']; missing=[k for k in required if not any(k in t for t in texts.values())]; assert not missing, f'coverage-check missing required references: {missing}'; runtime_markers=('runtime','canonical','publish','artifact root','runtime root','source of truth'); contextual_markers=('design workspace','reference only','reference-only','not runtime','legacy','contextual','example'); drift=[];\nfor p,t in texts.items():\n for i,ln in enumerate(t.splitlines(),1):\n  low=ln.lower();\n  if '.agents/plans/' not in low:\n   continue;\n  if not any(m in low for m in runtime_markers):\n   continue;\n  if any(m in low for m in contextual_markers):\n   continue;\n  drift.append(f'{p}:{i}:{ln.strip()}');\nassert not drift, f'active runtime drift to .agents/plans/* detected: {drift}'; print('cross-reference-coverage-ok', len(files), len(required))\""`
   - Expected evidence: verify bao phủ cả `.codex/AGENTS.md` và `.agents/skills/**/*.md`; stale-path guard chỉ fail khi có **active runtime claim** drift sang `.agents/plans/*`, không fail với contextual/reference-only mention.
2. Degraded drift semantics check (AC9 supplementary layer)
   - `python -c "import re; from pathlib import Path; text=Path('.agents/skills/lp-pipeline-orchestrator/references/commands.md').read_text(); key='degraded-design-drift-check.command'; lines=[ln for ln in text.splitlines() if key in ln]; assert len(lines)==1, f'{key}: expected exactly 1 candidate line, got {len(lines)}'; ln=lines[0].strip(); cmd=None;\nif '|' in ln:\n parts=[p.strip() for p in ln.split('|') if p.strip()];\n if parts and parts[0].strip('`')==key and len(parts)>=2:\n  cmd=parts[1];\nif cmd is None:\n m=re.search(re.escape(key)+r'\\s*[:=]\\s*(.+)$', ln);\n if m:\n  cmd=m.group(1).strip();\nassert cmd is not None, f'{key}: malformed accessor line: {ln}'; cmd=cmd.strip('`').strip(); assert cmd and cmd.lower() not in {'tbd','todo','<command>'}, f'{key}: empty/placeholder command'; low=cmd.lower(); assert ('rg ' in low or 'grep ' in low), f'degraded drift command must be grep/rg based: {cmd}'; forbidden_lines=[x.strip() for x in text.splitlines() if 'forbidden' in x.lower() and ('degraded-design-drift-check' in x or 'degraded design drift' in x.lower())]; assert forbidden_lines, 'missing forbidden-pattern declaration for degraded-design-drift-check in commands reference'; tokens=[];\nfor row in forbidden_lines:\n tokens.extend([m.group(1).strip() for m in re.finditer(r'`([^`]+)`', row) if m.group(1).strip() and 'degraded-design-drift-check' not in m.group(1) and m.group(1).strip().lower() not in {'forbidden','patterns','pattern'}]);\nassert tokens, 'forbidden-pattern declaration must include explicit backtick patterns'; missing=[tok for tok in sorted(set(tokens)) if tok not in cmd]; assert not missing, f'command does not cover declared forbidden patterns: {missing}'; assert not re.search(r'(^|\\s)-v(\\s|$)', low), f'degraded drift command must not invert grep semantics with -v: {cmd}'; banned=['|| true','|| exit 0','&& exit 1','! rg','!grep','! grep']; assert all(x not in low for x in banned), f'degraded drift command must preserve grep exit semantics (0=FAIL,1=PASS): {cmd}'; print('degraded-drift-semantics-ok', len(set(tokens)))\""`
   - Expected evidence: supplementary check chạy tại accessor duy nhất `degraded-design-drift-check.command`, command phủ đủ forbidden patterns trong cùng reference và semantics giữ nguyên `exit 0 = FAIL`, `exit 1 = PASS`.
3. Baseline resolution traceability check (AC14 secondary support)
   - `rg -n 'baseline_verify_command|label normalize về lowercase = `baseline`|không có fallback ngầm' .codex/plans/PLAN_LP_PIPELINE_V3/spec.md .codex/plans/PLAN_LP_PIPELINE_V3/plan.md .agents/skills/lp-pipeline-orchestrator/SKILL.md .agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py`
   - Expected evidence: phase-05 review bundle vẫn trace được đủ cả priority-1 (`baseline_verify_command`) và priority-2 (single `baseline` label trong plan artifact), không cần suy luận chéo phase.
4. Edge-case contract explicitness check (AC7/AC10/AC11 guard)
   - `rg -ni "Conflict files: <list>|git worktree prune|manual cleanup|dependency_critical = true|fallback tuyến tính|broad_context_reports = true|safe boundary|cancel_requested" .codex/plans/PLAN_LP_PIPELINE_V3/plan.md .codex/plans/PLAN_LP_PIPELINE_V3/phase-02-orchestrator-epic-mode-runtime.md .codex/plans/PLAN_LP_PIPELINE_V3/phase-03-worker-skill-task-alignment.md .codex/plans/PLAN_LP_PIPELINE_V3/phase-04-phase-state-resume-and-merge.md`
   - Expected evidence: cả 5 nhánh edge/recovery có wording explicit ở plan package, không còn phụ thuộc suy luận implicit.
5. `.worktrees/` guard check
   - `rg -n "^\.worktrees/$" .gitignore`
   - Expected evidence: `.worktrees/` được ignore rõ ràng.
6. Final Integration command schema parse check
   - `python -c "import json,re; from pathlib import Path; t=Path('.codex/plans/PLAN_LP_PIPELINE_V3/plan.md').read_text(); m=re.search(r'## Final Integration Verify Commands\n\n```json\n(.*?)\n```',t,re.S); assert m, 'missing section'; arr=json.loads(m.group(1)); assert isinstance(arr,list) and arr;\nfor i,x in enumerate(arr):\n assert isinstance(x.get('label'),str) and x['label'].strip();\n assert isinstance(x.get('command'),str) and x['command'].strip();\nprint('final-integration-schema-ok',len(arr))"`
   - Expected evidence: section tồn tại, parse được, mỗi entry có `label` + `command` non-empty.
7. Final Integration execution check (fail-fast)
   - `python -c "import json,re,subprocess,sys; from pathlib import Path; t=Path('.codex/plans/PLAN_LP_PIPELINE_V3/plan.md').read_text(); arr=json.loads(re.search(r'## Final Integration Verify Commands\n\n```json\n(.*?)\n```',t,re.S).group(1));\nfor item in arr:\n print('RUN',item['label']); rc=subprocess.call(item['command'],shell=True);\n if rc!=0: print('FAIL',item['label'],rc); sys.exit(rc);\nprint('final-integration-all-pass')"`
   - Expected evidence: command chạy đúng thứ tự, dừng ngay ở command fail đầu tiên.
   - AC1 self-contained evidence: snapshot `.worktrees` before + fixture run từ accessor `single-regression-check.command` đã nằm trong chính command list, không phụ thuộc pre-step ngoài danh sách.
   - AC9 self-contained evidence: `cross-reference-coverage-check` + `degraded-drift-semantics-check-from-accessor` đều nằm trong chính command list, không phụ thuộc pre-step ngoài danh sách.

## Exit Criteria
- Có command list parseable/schema machine-readable cho final integration QA.
- Verify flow có evidence runtime rõ, không còn kiểu check tĩnh-only.
- Benchmark labels dễ hiểu cho operator và có owner rõ.
- Phase này có thể validate wording/traceability cho các nhánh edge-case (AC7/AC10/AC11) như một cross-check, nhưng không giành ownership khỏi primary/secondary owners đã khai báo ở matrix/manifests.

## Downstream Agent Notes
- Nếu thêm command mới vào `Final Integration Verify Commands`, phải cập nhật AC-to-evidence mapping trong final QA report.
- Không mark done nếu mới pass schema check mà chưa chạy execution check fail-fast.
