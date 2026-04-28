# PLAN: PLAN_LP_PIPELINE_V3

- Plan profile: standard (phased, sequential)
- Tier: L
- Revision: v2 (revise loop)
- Sources: `README.md`, `spec.md`, `architecture-reference.md`, `.agents/skills/create-plan/SKILL.md`

## Goal
Triển khai LP Pipeline V3 theo spec PASS, với trọng tâm: `assess-complexity`, mode Single/Epic, Epic phase lifecycle (worktree + branch + phase notes/report), partial-cancel/runtime resume rõ ràng, và giữ backward compatibility trên runtime canonical `.codex/*` + SQLite backbone.

## Runtime Invariants And Source Of Truth (Single Contract Page)
1. Runtime artifacts canonical chỉ publish dưới `.codex/*`.
2. `.agents/plans/*` (nếu có) chỉ là design workspace reference, không phải runtime publish path.
3. SQLite (`state_manager.py`) là authority cho: `workflow state`, `phase status`, `current_step`, `state_version`, `resume metadata`.
4. Phase notes là authority cho: decisions/debt/notes. Các trường `status`, `current_step`, `retry_count`, `state_version` trong phase notes chỉ là mirror từ SQLite.
5. Canonical status enum bắt buộc dùng thống nhất: `pending | in_progress | waiting_user | completed | failed | cancelled`.
6. V3 vẫn chạy top-level phases theo thứ tự tuần tự; chưa bật top-level parallel execution.
7. Khi SQLite và phase-notes mirror conflict:
   - soft mismatch (stale mirror): auto-heal từ SQLite + publish reconciliation note.
   - hard mismatch: chuyển `waiting_user`, không auto-override.

## Operator Contract: `waiting_user` (One-screen Output)
Mọi blocker runtime trong Epic mode phải dùng cùng output shape để operator xử lý nhanh:

```text
Error: <short reason>
Required action: <human action>
Context: <phase_id/current_step/files if any>
Next command: /lp:implement PLAN_<NAME>
Recovery evidence required: <what to verify before resume>
```

Blocker-specific required lines (không được thay bằng wording generic):
- Worktree/branch setup fail: `Required action` phải nêu rõ hướng `git worktree prune` **hoặc** manual cleanup git/worktree state.
- Merge conflict: prompt bắt buộc có dòng `Conflict files: <list>` (list file conflict tương đối repo, không để trống).
- Dependency blocker với `dependency_critical = true` và thiếu dependencies khai báo: bắt buộc `waiting_user`, `Required action` phải yêu cầu bổ sung dependency graph/plan metadata; KHÔNG fallback tuyến tính về phase `N-1`.

Bắt buộc áp dụng cho 4 tình huống:
- Baseline verification fail
- Worktree/branch setup fail
- Merge conflict
- Dependency blocker (bao gồm downstream block sau partial cancel)

## Safe Boundary Definition For `cancel_requested`
`cancel_requested` chỉ là ý định dừng, không phải kill signal tức thời. Boundary an toàn cho Epic mode:
1. Command-exit boundary: command đang chạy đã trả exit code.
2. Step-transition boundary: state SQLite + mirror sync của step hiện tại đã persist xong, chưa bắt đầu command kế tiếp.
3. Worker-handoff boundary: contract artifact của worker hiện tại đã ghi xong vào `.codex/pipeline/`.

Enforcement:
- Nếu phase đang `in_progress`, orchestrator chỉ được mark `cancel_requested`; tuyệt đối không kill giữa command đang chạy.
- Khi chạm boundary an toàn gần nhất, phase mới được chuyển `cancelled`.
- Nếu phase bị cancel là dependency bắt buộc, downstream phase phải chuyển `waiting_user` cho tới khi user re-plan hoặc cancel downstream.

## Acceptance Criteria Ownership Matrix

| AC | Primary owner phase | Secondary owner phase | Notes |
|---|---|---|---|
| AC1 | P02 | P05 | Single no-regression fixture + artifact shape invariant |
| AC2 | P01 | - | Complexity assessment visible |
| AC3 | P01 | P02 | Epic template + phase references |
| AC4 | P02 | P04 | Worktree lifecycle + baseline gate |
| AC5 | P03 | P04 | Phase notes update contract |
| AC6 | P03 | P05 | Merge/cleanup report behavior |
| AC7 | P03 | P04 | Context propagation rules |
| AC8 | P04 | P02 | Runtime authority compatibility |
| AC9 | P05 | P03 | Cross-reference consistency |
| AC10 | P04 | P02 | Merge conflict + resume hook |
| AC11 | P02 | P04 | Partial cancel orchestration + state transition |
| AC12 | P05 | P03 | Final integration QA command contract |
| AC13 | P04 | P02 | Deterministic resume after waiting_user |
| AC14 | P02 | P05 | Baseline command resolution contract |
| AC15 | P02 | P04 | Baseline failure handling |
| AC16 | P05 | - | Rollout metrics |
| AC17 | P01 | P02 | Mode decision audit trail |

## Execution Boundary (Must Match `manifests/ownership.json`)
Allowed:
- `.codex/AGENTS.md`
- `.gitignore`
- `.agents/skills/lp-pipeline-orchestrator/**`
- `.agents/skills/lp-plan/SKILL.md`
- `.agents/skills/lp-implement/SKILL.md`
- `.agents/skills/lp-cook/SKILL.md`
- `.agents/skills/create-plan/SKILL.md`
- `.agents/skills/review-plan/SKILL.md`
- `.agents/skills/implement-plan/SKILL.md`
- `.agents/skills/review-implement/SKILL.md`
- `.agents/skills/qa-automation/SKILL.md`
- `.agents/skills/vibecode-doctor/SKILL.md`
- `.agents/skills/close-task/SKILL.md`
- `.agents/skills/lp-state-manager/SKILL.md`
- `.agents/skills/lp-state-manager/scripts/state_manager.py`
- `.agents/skills/tasks/create-plan/TASK.md`
- `.agents/skills/tasks/review-plan/TASK.md`
- `.agents/skills/tasks/implement-plan/TASK.md`
- `.agents/skills/tasks/review-implement/TASK.md`
- `.agents/skills/tasks/qa-automation/TASK.md`
- `.agents/skills/tasks/review-spec/TASK.md`
- `.agents/skills/tasks/create-spec/TASK.md`
- `.agents/skills/tasks/persona-review/TASK.md`

Do Not Modify:
- Business code ngoài LP skill/runtime scope
- Runtime root migration sang `.agents/plans/*`
- Xóa SQLite/state_manager runtime backbone trong V3

## Implementation Order
1. [phase-01-assessment-and-template-foundation.md](./phase-01-assessment-and-template-foundation.md)
2. [phase-02-orchestrator-epic-mode-runtime.md](./phase-02-orchestrator-epic-mode-runtime.md)
3. [phase-03-worker-skill-task-alignment.md](./phase-03-worker-skill-task-alignment.md)
4. [phase-04-phase-state-resume-and-merge.md](./phase-04-phase-state-resume-and-merge.md)
5. [phase-05-verification-rollout-and-doctor.md](./phase-05-verification-rollout-and-doctor.md)

## Plan-level Verify Scenarios (Runtime Evidence)
1. Accessor integrity + degraded drift semantics
   - Resolve accessor từ `.agents/skills/lp-pipeline-orchestrator/references/commands.md` cho `single-regression-check.command` và `degraded-design-drift-check.command`.
   - PASS chỉ khi mỗi accessor resolve thành đúng 1 command deterministic, non-empty, parseable theo accessor line format.
   - AC9 supplementary check bắt buộc chạy qua accessor duy nhất `degraded-design-drift-check.command`; command phải là grep/rg detector trên forbidden patterns khai báo trong cùng reference, và phải giữ semantics exit code: `0 = FAIL` (phát hiện drift), `1 = PASS` (không phát hiện drift).
   - Missing / empty / malformed / multi-candidate / semantics mismatch => FAIL.
2. Baseline resolution contract
   - Verify rõ cả 2 nhánh AC14:
     - Priority 1: `baseline_verify_command` trong phase frontmatter
     - Priority 2: đúng 1 entry label normalize về lowercase = `baseline` trong section `Verify Commands` của plan artifact
   - Nếu nhiều candidate / malformed / thiếu command / fallback ngầm ngoài plan artifact => FAIL.
3. Single no-regression scenario
   - Resolve deterministic `single-regression-check.command`, snapshot `.worktrees` before, rồi chạy fixture command từ accessor vừa resolve.
   - Evidence bắt buộc: exit code `0`; snapshot delta `.worktrees` trước/sau fixture bằng rỗng (không tạo artifact mới); không tạo `.codex/plans/PLAN_<NAME>/phases/`; output contracts `03/04/05` có `schema_version`, `skill`, `status`, `artifacts.primary`.
4. Epic blocker contracts + dependency-critical branch scenario
   - Simulate từng blocker (`baseline-fail`, `worktree-fail`, `merge-conflict`, `dependency-blocker`).
   - Evidence bắt buộc:
     - Merge-conflict prompt chứa `Conflict files: <list>`.
     - Worktree-fail prompt chứa guidance `git worktree prune` hoặc manual cleanup.
     - Nhánh `dependency_critical = true` nhưng thiếu dependencies khai báo phải chuyển `waiting_user`, không fallback tuyến tính.
     - SQLite authoritative status sync đúng theo blocker context.
5. Context-budget branch scenario (`broad_context_reports = true`)
   - Với epic plan bật explicit `broad_context_reports = true` và tổng phase `<= 5`: cho phép đọc thêm report của completed phases theo thứ tự phase index tăng dần.
   - Dù bật branch này, agent vẫn không đọc raw notes ngoài direct dependency phases.
6. `cancel_requested` safe-boundary scenario
   - Chứng minh orchestrator không kill giữa command đang chạy; chỉ chuyển `cancelled` sau command-exit/step-transition/worker-handoff boundary gần nhất.
   - Nếu phase cancel là dependency bắt buộc: downstream phase phải về `waiting_user`.
7. Final integration QA scenario
   - Parse section `Final Integration Verify Commands` theo schema.
   - Command list bắt buộc có cả `cross-reference-coverage-check` và `degraded-drift-semantics-check-from-accessor` trước khi chạy execution checks còn lại.
   - Chạy full command list theo thứ tự, fail-fast tại lệnh đầu tiên exit != 0.

## Final Integration Verify Commands

```json
[
  {
    "label": "accessor-contract-check-and-export",
    "command": "python -c \"import json,re; from pathlib import Path; out=Path('.codex/tmp/final-integration-accessors.json'); out.parent.mkdir(parents=True, exist_ok=True); text=Path('.agents/skills/lp-pipeline-orchestrator/references/commands.md').read_text(); keys=['single-regression-check.command','degraded-design-drift-check.command']; resolved={};\nfor key in keys:\n lines=[ln for ln in text.splitlines() if key in ln];\n assert len(lines)==1, f'{key}: expected exactly 1 candidate line, got {len(lines)}';\n ln=lines[0].strip(); cmd=None;\n if '|' in ln:\n  parts=[p.strip() for p in ln.split('|') if p.strip()];\n  if parts and parts[0].strip(chr(96))==key and len(parts)>=2:\n   cmd=parts[1];\n if cmd is None:\n  m=re.search(re.escape(key)+r'\\s*[:=]\\s*(.+)$', ln);\n  if m:\n   cmd=m.group(1).strip();\n assert cmd is not None, f'{key}: malformed accessor line: {ln}';\n cmd=cmd.strip(chr(96)).strip();\n assert cmd and cmd.lower() not in {'tbd','todo','<command>'}, f'{key}: empty/placeholder command';\n resolved[key]=cmd;\nassert len(set(resolved.values()))==2, f'accessors must resolve to two deterministic commands: {resolved}';\nout.write_text(json.dumps(resolved, indent=2, sort_keys=True) + '\\n');\nprint('accessors-deterministic-ok', out)\""
  },
  {
    "label": "cross-reference-coverage-check",
    "command": "python -c \"from pathlib import Path; files=[Path('.codex/AGENTS.md')] + sorted(Path('.agents/skills').rglob('*.md')); assert len(files) > 1, 'coverage-check: no skill markdown files found'; texts={str(f):f.read_text() for f in files}; required=['.codex/','state_manager.py','waiting_user','Final Integration Verify Commands','single-regression-check.command','degraded-design-drift-check.command']; missing=[k for k in required if not any(k in t for t in texts.values())]; assert not missing, f'coverage-check missing required references: {missing}'; runtime_markers=('runtime','canonical','publish','artifact root','runtime root','source of truth'); contextual_markers=('design workspace','reference only','reference-only','not runtime','legacy','contextual','example'); drift=[];\nfor p,t in texts.items():\n for i,ln in enumerate(t.splitlines(),1):\n  low=ln.lower();\n  if '.agents/plans/' not in low:\n   continue;\n  if not any(m in low for m in runtime_markers):\n   continue;\n  if any(m in low for m in contextual_markers):\n   continue;\n  drift.append(f'{p}:{i}:{ln.strip()}');\nassert not drift, f'active runtime drift to .agents/plans/* detected: {drift}'; print('cross-reference-coverage-ok', len(files), len(required))\""
  },
  {
    "label": "degraded-drift-semantics-check-from-accessor",
    "command": "python -c \"import json,re; from pathlib import Path; ref=Path('.agents/skills/lp-pipeline-orchestrator/references/commands.md'); text=ref.read_text(); accessor_map=Path('.codex/tmp/final-integration-accessors.json'); assert accessor_map.exists(), f'missing accessor map: {accessor_map}'; resolved=json.loads(accessor_map.read_text()); cmd=str(resolved.get('degraded-design-drift-check.command','')).strip(); assert cmd, 'degraded-design-drift-check.command missing/empty'; low=cmd.lower(); assert ('rg ' in low or 'grep ' in low), f'degraded drift command must be grep/rg based: {cmd}'; forbidden_lines=[ln.strip() for ln in text.splitlines() if 'forbidden' in ln.lower() and ('degraded-design-drift-check' in ln or 'degraded design drift' in ln.lower())]; assert forbidden_lines, 'missing forbidden-pattern declaration for degraded-design-drift-check in commands reference'; tokens=[];\nfor ln in forbidden_lines:\n tokens.extend([m.group(1).strip() for m in re.finditer(re.escape(chr(96))+r'([^'+re.escape(chr(96))+r']+)'+re.escape(chr(96)), ln) if m.group(1).strip() and 'degraded-design-drift-check' not in m.group(1) and m.group(1).strip().lower() not in {'forbidden','patterns','pattern'}]);\nassert tokens, 'forbidden-pattern declaration must include explicit backtick patterns'; missing=[tok for tok in sorted(set(tokens)) if tok not in cmd]; assert not missing, f'command does not cover declared forbidden patterns: {missing}'; assert not re.search(r'(^|\\s)-v(\\s|$)', low), f'degraded drift command must not invert grep semantics with -v: {cmd}'; banned=['|| true','|| exit 0','&& exit 1','! rg','!grep','! grep']; assert all(x not in low for x in banned), f'degraded drift command must preserve grep exit semantics (0=FAIL,1=PASS): {cmd}'; print('degraded-drift-semantics-ok', len(set(tokens)))\""
  },
  {
    "label": "snapshot-worktrees-before-single-fixture",
    "command": "python -c \"from pathlib import Path; out=Path('.codex/tmp/single-worktrees-before.txt'); out.parent.mkdir(parents=True, exist_ok=True); root=Path('.worktrees'); paths=sorted(p.as_posix() for p in root.rglob('*')) if root.exists() else []; out.write_text('\\n'.join(paths) + ('\\n' if paths else '')); print('worktree-snapshot-before-ok', out, len(paths))\""
  },
  {
    "label": "run-single-regression-fixture-from-accessor",
    "command": "python -c \"import json,subprocess; from pathlib import Path; accessor_map=Path('.codex/tmp/final-integration-accessors.json'); assert accessor_map.exists(), f'missing accessor map: {accessor_map}'; resolved=json.loads(accessor_map.read_text()); cmd=resolved.get('single-regression-check.command'); assert isinstance(cmd, str) and cmd.strip(), 'single-regression-check.command missing/empty'; print('RUN', cmd); raise SystemExit(subprocess.call(cmd, shell=True))\""
  },
  {
    "label": "single-runtime-shape-check",
    "command": "python -c \"import json,os; from pathlib import Path; plan=os.environ.get('LP_SINGLE_FIXTURE_PLAN','PLAN_V3_SINGLE_FIXTURE'); req=['03-implement-plan','04-review-implement','05-qa-automation'];\nfor s in req:\n p=Path(f'.codex/pipeline/{plan}/{s}.output.contract.json');\n assert p.exists(), f'missing contract: {p}';\n d=json.loads(p.read_text());\n assert all(k in d for k in ['schema_version','skill','status']), f'{p}: missing required fields';\n assert d.get('artifacts',{}).get('primary'), f'{p}: missing artifacts.primary';\nassert not Path(f'.codex/plans/{plan}/phases').is_dir(), f'unexpected phases dir for single flow: {plan}';\nprint('single-runtime-shape-ok')\""
  },
  {
    "label": "no-worktree-artifact-check",
    "command": "python -c \"import json,os; from pathlib import Path; plan=os.environ.get('LP_SINGLE_FIXTURE_PLAN','PLAN_V3_SINGLE_FIXTURE'); before_path=Path(os.environ.get('LP_SINGLE_WORKTREE_SNAPSHOT_BEFORE','.codex/tmp/single-worktrees-before.txt')); assert before_path.exists(), f'missing worktree-before snapshot: {before_path}'; before={ln.strip() for ln in before_path.read_text().splitlines() if ln.strip()}; root=Path('.worktrees'); after={p.as_posix() for p in root.rglob('*')} if root.exists() else set(); new=sorted(after-before); assert not new, f'new worktree artifacts detected: {new}';\ndef walk(v):\n if isinstance(v,dict):\n  for x in v.values():\n   yield from walk(x)\n elif isinstance(v,list):\n  for x in v:\n   yield from walk(x)\n elif isinstance(v,str):\n  yield v\nfor step in ['03-implement-plan','04-review-implement','05-qa-automation']:\n p=Path(f'.codex/pipeline/{plan}/{step}.output.contract.json');\n d=json.loads(p.read_text());\n bad=[s for s in walk(d) if '.worktrees/' in s or s.startswith('.worktrees')];\n assert not bad, f'{p}: unexpected worktree refs: {bad}';\nprint('single-no-worktree-delta-ok')\""
  },
  {
    "label": "edge-case-recovery-contract-check",
    "command": "python -c \"from pathlib import Path; files={'plan':Path('.codex/plans/PLAN_LP_PIPELINE_V3/plan.md'),'p02':Path('.codex/plans/PLAN_LP_PIPELINE_V3/phase-02-orchestrator-epic-mode-runtime.md'),'p03':Path('.codex/plans/PLAN_LP_PIPELINE_V3/phase-03-worker-skill-task-alignment.md'),'p04':Path('.codex/plans/PLAN_LP_PIPELINE_V3/phase-04-phase-state-resume-and-merge.md'),'p05':Path('.codex/plans/PLAN_LP_PIPELINE_V3/phase-05-verification-rollout-and-doctor.md')}; texts={k:v.read_text() for k,v in files.items()}; checks=[('merge-conflict-files-line','Conflict files: <list>',('plan','p02','p04')),('worktree-prune-guidance','git worktree prune',('plan','p02','p05')),('worktree-manual-cleanup-guidance','manual cleanup',('plan','p02','p05')),('dependency-critical-gate','dependency_critical = true',('plan','p03','p04')),('dependency-no-linear-fallback','fallback tuyến tính',('plan','p03','p04')),('broad-context-branch','broad_context_reports = true',('plan','p03','p05')),('safe-boundary-definition','safe boundary',('plan','p02','p04')),('cancel-requested-enforcement','cancel_requested',('plan','p02','p04'))]; missing=[];\nfor name,token,targets in checks:\n if not any(token.lower() in texts[t].lower() for t in targets):\n  missing.append(f'{name}:{token}:{targets}');\nassert not missing, f'edge-case contract missing coverage: {missing}'; print('edge-case-contract-explicit-ok', len(checks))\""
  },
  {
    "label": "status-enum-normalization-check",
    "command": "python -c \"from pathlib import Path; files=[Path('.codex/AGENTS.md'),Path('.agents/skills/lp-pipeline-orchestrator/SKILL.md')]; bad=[];\nfor f in files:\n t=f.read_text();\n if 'Done' in t or 'COMPLETED' in t:\n  bad.append(str(f));\nassert not bad, bad; print('status-wording-ok')\""
  }
]
```

## Risks
- High: Single flow regression khi thêm Epic runtime path.
- High: AC11 partial cancel drift giữa orchestrator behavior và state authority.
- Medium: waiting_user prompt không đồng nhất làm operator xử lý sai.
- Medium: Cross-reference drift giữa SKILL/TASK/AGENTS/commands.

## Deliverables
- `plan.md`
- `phase-01..05` files
- `manifests/ownership.json`
- `manifests/dependency-graph.json`
- `manifests/benchmark.json`
- `.codex/pipeline/PLAN_LP_PIPELINE_V3/01-create-plan.output.*`
