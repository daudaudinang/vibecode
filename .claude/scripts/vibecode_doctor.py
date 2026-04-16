#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / '.claude' / 'manifest.json'
LEGACY_ROOTS = ['.agents', '.cursor', '.codex']


def run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def status_line(state: str, message: str) -> str:
    return f'{state} {message}'


def main() -> int:
    lines: list[str] = []

    if not MANIFEST_PATH.exists():
        lines.append(status_line('❌', 'manifest missing: .claude/manifest.json'))
        print('\n'.join(lines))
        return 2

    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))

    canonical_root = manifest.get('canonical_runtime_root', '.claude')
    lines.append(status_line('✅', f'canonical runtime root: {canonical_root}'))

    detected_legacy = [root for root in LEGACY_ROOTS if (ROOT / root).exists()]
    if detected_legacy:
        lines.append(status_line('⚠️', f'legacy mirrors detected: {", ".join(detected_legacy)}'))
    else:
        lines.append(status_line('✅', 'legacy mirrors detected: none'))

    state_db = manifest.get('active_runtime', {}).get('state_db')
    if state_db:
        lines.append(status_line('✅', f'active state db: {state_db}'))
    else:
        lines.append(status_line('❌', 'active state db missing in manifest'))

    scripts = manifest.get('active_scripts', {})
    for key, rel_path in scripts.items():
        exists = (ROOT / rel_path).exists()
        icon = '✅' if exists else '❌'
        lines.append(status_line(icon, f'{key} script: {rel_path}'))

    # ── GitNexus: Layer 1 — CLI availability ────────────────────────────────
    gitnexus_cli = shutil.which('gitnexus')
    npx = shutil.which('npx')
    if gitnexus_cli or npx:
        lines.append(status_line('✅', 'GitNexus CLI available via gitnexus or npx'))
    else:
        lines.append(status_line('❌', 'GitNexus CLI unavailable — install: npm install -g gitnexus'))

    # ── GitNexus: Layer 2 — local index directory ────────────────────────────
    gitnexus_index_dir = ROOT / '.gitnexus'
    if gitnexus_index_dir.exists():
        lines.append(status_line('✅', f'GitNexus local index found: .gitnexus/'))
    else:
        lines.append(status_line('⚠️', 'GitNexus local index missing — run: npx gitnexus analyze'))

    # ── GitNexus: Layer 3 — MCP server binding ──────────────────────────────
    mcp_bound = False
    mcp_config_candidates = [
        Path.home() / '.claude.json',
        Path.home() / '.claude' / 'settings.json',
    ]
    for cfg_path in mcp_config_candidates:
        if cfg_path.exists():
            try:
                cfg_data = cfg_path.read_text(encoding='utf-8')
                if 'gitnexus' in cfg_data.lower():
                    mcp_bound = True
                    break
            except OSError:
                pass
    if mcp_bound:
        lines.append(status_line('✅', 'GitNexus MCP server entry found in Claude config'))
    else:
        lines.append(status_line('⚠️', 'GitNexus MCP server binding not detected in ~/.claude.json or ~/.claude/settings.json'))
        lines.append(status_line('   ', '→ Run: npx gitnexus setup   (then restart Claude Code)'))

    # ── GitNexus: Layer 4 — runtime status check ────────────────────────────
    if npx:
        code, stdout, stderr = run(['npx', 'gitnexus', 'status'])
        merged = '\n'.join(part for part in [stdout, stderr] if part)
        if code == 0:
            if 'Repository not indexed' in merged or 'not indexed' in merged.lower():
                lines.append(status_line('⚠️', 'GitNexus repo not indexed yet — run: npx gitnexus analyze'))
            else:
                lines.append(status_line('✅', 'GitNexus repo appears indexed and queryable'))
        else:
            lines.append(status_line('❌', 'GitNexus status command failed'))
            if merged:
                lines.append(status_line('   ', f'→ Detail: {merged.splitlines()[0]}'))
    elif gitnexus_cli:
        code, stdout, stderr = run(['gitnexus', 'status'])
        merged = '\n'.join(part for part in [stdout, stderr] if part)
        icon = '✅' if code == 0 else '❌'
        lines.append(status_line(icon, f'GitNexus CLI status: {merged.splitlines()[0] if merged else "no output"}'))
    else:
        lines.append(status_line('❌', 'Cannot verify GitNexus runtime status (npx/gitnexus unavailable)'))

    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

