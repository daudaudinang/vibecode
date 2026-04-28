# Phase 01 - Assessment And Template Foundation

## Scope
- Chuẩn hóa `assess-complexity` output theo rubric 6 chiều (D1..D6), recommendation mapping và override rules.
- Chuẩn hóa Epic plan template để chứa rõ: invariants, phase list/dependencies, mode decision audit trail.
- Chốt contract `single source of truth`: runtime publish path phải ở `.codex/*`.

## Owned Files
- `.agents/skills/lp-pipeline-orchestrator/references/complexity-assessment.md` (new)
- `.agents/skills/create-plan/references/epic-plan-template.md` (new)
- `.agents/skills/create-plan/SKILL.md`
- `.agents/skills/lp-plan/SKILL.md`

## AC Mapping
- Primary: AC2, AC3, AC17
- Secondary support: AC1

Note: AC1 support ở phase này chỉ nằm ở template guard cho single/epic split.

## Verify Commands (Actionable + Evidence)
1. Rubric structure check
   - `rg -n "D1|D2|D3|D4|D5|D6|0-6|7-11|12-18|User decides|Epic override" .agents/skills/lp-pipeline-orchestrator/references/complexity-assessment.md`
   - Expected evidence: đủ dimension + recommendation mapping xuất hiện đầy đủ.
2. Epic template contract check
   - `rg -n "Invariants|Phase list|dependencies|mode_decision|override_reason|Final Integration Verify Commands" .agents/skills/create-plan/references/epic-plan-template.md`
   - Expected evidence: template có đầy đủ section bắt buộc và có mode decision audit fields.
3. Runtime root wording guard
   - `rg -n "\.codex/|\.agents/plans/" .agents/skills/create-plan/SKILL.md .agents/skills/lp-plan/SKILL.md`
   - Expected evidence: `.codex/*` được nêu là runtime canonical; `.agents/plans/*` chỉ design workspace reference.

## Exit Criteria
- `assess-complexity` có output contract rõ, deterministic mapping và user-confirm gate.
- Epic template đủ fields để downstream implement/review chạy không cần đoán.
- Mode decision audit trail có chỗ persist trong plan artifact.

## Downstream Agent Notes
- Không cài runtime behavior trong phase này; chỉ chuẩn hóa rubric/template + wording contracts.
- Nếu template chưa có `Final Integration Verify Commands` schema machine-readable thì chưa được mark done.
