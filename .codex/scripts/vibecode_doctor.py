#!/usr/bin/env python3
"""Vibecode Doctor — Health check script for Codex + LP pipeline setup.

Deploy to: ~/.codex/scripts/vibecode_doctor.py
Checks: config, agents, skills, GitNexus, state DB.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


# ── Resolve project root ────────────────────────────────────────────────────
def _find_project_root() -> Path | None:
    """Try git root, then fall back to cwd."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return Path.cwd()


PROJECT_ROOT = _find_project_root()
CODEX_HOME = Path.home() / '.codex'
AGENTS_HOME = Path.home() / '.agents'


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, capture_output=True, text=True, timeout=30)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def status_line(state: str, message: str) -> str:
    return f'{state} {message}'


def main() -> int:
    lines: list[str] = []
    lines.append('─── Codex Vibecode Doctor ───')

    # ── 1. Global config ────────────────────────────────────────────────────
    global_config = CODEX_HOME / 'config.toml'
    if global_config.exists():
        lines.append(status_line('✅', f'global config: {global_config}'))
        if tomllib:
            try:
                data = tomllib.loads(global_config.read_text(encoding='utf-8'))
                model = data.get('model', '<not set>')
                lines.append(status_line('  ', f'  model: {model}'))
            except Exception as e:
                lines.append(status_line('⚠️', f'  config parse error: {e}'))
        else:
            lines.append(status_line('⚠️', '  tomllib unavailable, cannot parse config'))
    else:
        lines.append(status_line('❌', f'global config missing: {global_config}'))

    # ── 2. Global AGENTS.md ─────────────────────────────────────────────────
    global_agents_md = CODEX_HOME / 'AGENTS.md'
    if global_agents_md.exists():
        size = global_agents_md.stat().st_size
        lines.append(status_line('✅', f'global AGENTS.md: {global_agents_md} ({size} bytes)'))
    else:
        lines.append(status_line('❌', f'global AGENTS.md missing: {global_agents_md}'))

    # ── 3. Global agents ────────────────────────────────────────────────────
    global_agents_dir = CODEX_HOME / 'agents'
    if global_agents_dir.exists():
        agent_files = list(global_agents_dir.glob('*.toml'))
        lines.append(status_line('✅', f'global agents: {len(agent_files)} .toml files'))
        for af in sorted(agent_files):
            lines.append(status_line('  ', f'  {af.name}'))
    else:
        lines.append(status_line('⚠️', f'global agents dir missing: {global_agents_dir}'))

    # ── 4. Global user skills ───────────────────────────────────────────────
    global_skills_dir = AGENTS_HOME / 'skills'
    if global_skills_dir.exists():
        skill_dirs = [d for d in global_skills_dir.iterdir() if d.is_dir() and (d / 'SKILL.md').exists()]
        lines.append(status_line('✅', f'global user skills: {len(skill_dirs)} skills'))
    else:
        lines.append(status_line('⚠️', f'global skills dir missing: {global_skills_dir}'))

    # ── 5. Project-level .codex/ ────────────────────────────────────────────
    if PROJECT_ROOT:
        project_codex = PROJECT_ROOT / '.codex'
        project_agents_skills = PROJECT_ROOT / '.agents' / 'skills'

        if project_codex.exists():
            lines.append(status_line('✅', f'project .codex/ found: {project_codex}'))
        else:
            lines.append(status_line('  ', f'project .codex/ not found (optional)'))

        if project_agents_skills.exists():
            p_skills = [d for d in project_agents_skills.iterdir() if d.is_dir() and (d / 'SKILL.md').exists()]
            lines.append(status_line('✅', f'project skills: {len(p_skills)} skills'))
        else:
            lines.append(status_line('  ', f'project .agents/skills/ not found (optional)'))

        # State DB
        state_db = project_codex / 'state' / 'pipeline_state.db'
        if state_db.exists():
            lines.append(status_line('✅', f'pipeline state DB: {state_db}'))
        else:
            lines.append(status_line('  ', f'pipeline state DB not found (created on first use)'))

    # ── 6. GitNexus CLI availability ────────────────────────────────────────
    gitnexus_cli = shutil.which('gitnexus')
    npx = shutil.which('npx')
    if gitnexus_cli or npx:
        lines.append(status_line('✅', 'GitNexus CLI available via gitnexus or npx'))
    else:
        lines.append(status_line('❌', 'GitNexus CLI unavailable — install: npm install -g gitnexus'))

    # ── 7. GitNexus local index ─────────────────────────────────────────────
    if PROJECT_ROOT:
        gitnexus_index = PROJECT_ROOT / '.gitnexus'
        if gitnexus_index.exists():
            lines.append(status_line('✅', 'GitNexus local index found: .gitnexus/'))
        else:
            lines.append(status_line('⚠️', 'GitNexus local index missing — run: npx gitnexus analyze'))

    # ── 8. GitNexus runtime status ──────────────────────────────────────────
    if npx and PROJECT_ROOT:
        try:
            code, stdout, stderr = run(['npx', 'gitnexus', 'status'])
            merged = '\n'.join(part for part in [stdout, stderr] if part)
            if code == 0:
                if 'not indexed' in merged.lower():
                    lines.append(status_line('⚠️', 'GitNexus repo not indexed — run: npx gitnexus analyze'))
                else:
                    lines.append(status_line('✅', 'GitNexus repo appears indexed and queryable'))
            else:
                lines.append(status_line('❌', 'GitNexus status command failed'))
        except Exception:
            lines.append(status_line('⚠️', 'GitNexus status check timed out'))

    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
