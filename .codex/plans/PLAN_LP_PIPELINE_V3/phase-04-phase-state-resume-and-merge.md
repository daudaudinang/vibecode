# Phase 04 - Phase State Resume And Merge

## Scope
- Enforce state authority matrix giữa SQLite và phase notes mirrors.
- Implement deterministic resume selector theo thứ tự `waiting_user -> in_progress -> pending` + dependency satisfaction.
- Implement merge-conflict + partial-cancel state transitions với sync order an toàn.
- Merge-conflict recovery path phải giữ explicit field `Conflict files: <list>` để operator resume không mơ hồ (AC10).
- Với phase có `dependency_critical = true` mà dependency chưa khai báo đủ: block bằng `waiting_user`, không fallback tuyến tính.
- Định nghĩa và enforce `cancel_requested` safe-boundary semantics ở mức runtime step boundaries (không kill giữa command đang chạy).
- Chốt runtime transitions cho AC11/AC13 để không drift khỏi orchestrator behavior.

## Owned Files
- `.agents/skills/lp-state-manager/SKILL.md`
- `.agents/skills/lp-state-manager/scripts/state_manager.py`
- `.agents/skills/lp-pipeline-orchestrator/SKILL.md`
- `.agents/skills/lp-pipeline-orchestrator/scripts/lp_pipeline.py`
- `.agents/skills/lp-pipeline-orchestrator/references/phase-notes-template.md`
- `.agents/skills/lp-pipeline-orchestrator/references/phase-report-template.md`

## AC Mapping
- Primary: AC8, AC10, AC13
- Secondary support: AC4, AC5, AC7, AC11, AC15

## Verify Commands (Actionable + Runtime Scenarios)
1. Resume ordering check
   - `python -c "import os,subprocess; cmd=os.environ['LP_EPIC_RESUME_SCENARIO_CMD']; print(cmd); raise SystemExit(subprocess.call(cmd, shell=True))"`
   - Expected evidence: scenario log chứng minh thứ tự chọn phase deterministic (`waiting_user` trước, sau đó `in_progress`, sau cùng `pending` satisfied deps) và không fallback tuyến tính khi phase `dependency_critical` thiếu dependency graph.
2. Merge-conflict state sync check
   - `python -c "import sqlite3,os; db=os.environ.get('LP_STATE_DB','.codex/state/pipeline_state.db'); wf=os.environ['LP_WORKFLOW_ID']; conn=sqlite3.connect(db); c=conn.cursor(); row=c.execute('select status,current_step,state_version from phase_runtime_state where workflow_id=? order by updated_at desc limit 1',(wf,)).fetchone(); assert row and row[0]=='waiting_user' and row[1]=='merge-phase'; print('merge-waiting_user-sync-ok',row)"`
   - `python -c "import os; from pathlib import Path; log=Path(os.environ['LP_MERGE_RECOVERY_LOG']); t=log.read_text(); assert 'Error: merge conflict' in t; assert 'Conflict files:' in t; assert 'Next command: /lp:implement PLAN_' in t; print('merge-recovery-contract-ok', log)"`
   - Expected evidence: SQLite authoritative row đã sync đúng trước khi resume và recovery output chứa explicit `Conflict files: <list>`.
3. Partial-cancel dependency blocker check
   - `python -c "import os,subprocess; cmd=os.environ['LP_PARTIAL_CANCEL_SCENARIO_CMD']; print(cmd); raise SystemExit(subprocess.call(cmd, shell=True))"`
   - Expected evidence: phase bị cancel -> downstream dependency bắt buộc chuyển `waiting_user`; không auto-start; nếu phase đang chạy thì chỉ cancel tại safe boundary gần nhất.
4. Safe-boundary cancel semantics check
   - `python -c "import os,subprocess; cmd=os.environ['LP_CANCEL_BOUNDARY_SCENARIO_CMD']; print(cmd); raise SystemExit(subprocess.call(cmd, shell=True))"`
   - Expected evidence: command đang chạy không bị kill giữa chừng; `cancel_requested` chỉ flip phase sang `cancelled` sau command-exit/step-transition/worker-handoff boundary.
5. State-version reconciliation check
   - `rg -n "state_version|soft mismatch|hard mismatch|reconciliation" .agents/skills/lp-state-manager/SKILL.md .agents/skills/lp-pipeline-orchestrator/SKILL.md`
   - Expected evidence: protocol reconcile được mô tả rõ và thống nhất ở cả state-manager/orchestrator.

## Exit Criteria
- Resume không chạy lại từ đầu khi đã có `current_step` authoritative.
- Merge conflict và partial cancel đều có state transition rõ + recovery path rõ.
- Safe-boundary semantics được mô tả rõ theo step boundary, không ambiguous cho implement/review agents.
- Không có silent override khi state mismatch hard.

## Downstream Agent Notes
- Nếu schema DB cần thay đổi, bắt buộc đi kèm migration và backward-compat check.
- Bất kỳ command nào chạm `waiting_user` phải ghi đủ one-screen operator contract đã chốt ở P02.
