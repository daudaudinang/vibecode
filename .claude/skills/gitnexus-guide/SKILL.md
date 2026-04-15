---
name: gitnexus-guide
description: "Use when the user asks about GitNexus itself — available tools, how to query the knowledge graph, MCP resources, graph schema, or workflow reference. Examples: \"What GitNexus tools are available?\", \"How do I use GitNexus?\""
---

# GitNexus Guide

Quick reference for all GitNexus MCP tools, resources, and the knowledge graph schema.

## Always Start Here

For any task involving code understanding, debugging, impact analysis, or refactoring:

1. **Detect GitNexus config/capability** for current runtime/session
2. **Bootstrap GitNexus if needed** (CLI/package, MCP binding, verify command)
3. **Run analyze / prepare index** so repo becomes queryable
4. **Verify ready state** using context/status/list signal
5. **Only then** read `gitnexus://repo/{name}/context` and follow the relevant skill

> Fallback to `Grep`/`Read` only when bootstrap/verify fails or GitNexus is insufficient for the question. In that case, say clearly that degraded mode is active.

## Bootstrap Contract

```text
Detect GitNexus config
    ↓
Check MCP/tool availability
    ↓
If missing:
  - install package / CLI
  - setup MCP binding
  - verify command works
    ↓
Run analyze
    ↓
Mark status = ready
    ↓
Expose clear fallback only if bootstrap fail
```

## Ready vs degraded

- `READY`: GitNexus usable for current repo after detect/bootstrap/verify
- `DEGRADED`: bootstrap failed, capability unavailable, repo not queryable, or GitNexus insufficient
- Do not silently skip GitNexus when repo policy says GitNexus is core capability

## Doctor

Use Vibecode doctor to inspect canonical root, active DB path, GitNexus readiness, and fallback state:

```bash
python .claude/scripts/vibecode_doctor.py
```

Read `.claude/manifest.json` before resolving canonical roots or runtime paths.

## Skills

| Task                                         | Skill to read       |
| -------------------------------------------- | ------------------- |
| Understand architecture / "How does X work?" | `gitnexus-exploring`         |
| Blast radius / "What breaks if I change X?"  | `gitnexus-impact-analysis`   |
| Trace bugs / "Why is X failing?"             | `gitnexus-debugging`         |
| Rename / extract / split / refactor          | `gitnexus-refactoring`       |
| Tools, resources, schema reference           | `gitnexus-guide` (this file) |
| Index, status, clean, wiki CLI commands      | `gitnexus-cli`               |

## Tools Reference

| Tool             | What it gives you                                                        |
| ---------------- | ------------------------------------------------------------------------ |
| `query`          | Process-grouped code intelligence — execution flows related to a concept |
| `context`        | 360-degree symbol view — categorized refs, processes it participates in  |
| `impact`         | Symbol blast radius — what breaks at depth 1/2/3 with confidence         |
| `detect_changes` | Git-diff impact — what do your current changes affect                    |
| `rename`         | Multi-file coordinated rename with confidence-tagged edits               |
| `cypher`         | Raw graph queries (read `gitnexus://repo/{name}/schema` first)           |
| `list_repos`     | Discover indexed repos                                                   |

## Resources Reference

Lightweight reads (~100-500 tokens) for navigation:

| Resource                                       | Content                                   |
| ---------------------------------------------- | ----------------------------------------- |
| `gitnexus://repo/{name}/context`               | Stats, staleness check                    |
| `gitnexus://repo/{name}/clusters`              | All functional areas with cohesion scores |
| `gitnexus://repo/{name}/cluster/{clusterName}` | Area members                              |
| `gitnexus://repo/{name}/processes`             | All execution flows                       |
| `gitnexus://repo/{name}/process/{processName}` | Step-by-step trace                        |
| `gitnexus://repo/{name}/schema`                | Graph schema for Cypher                   |

## Graph Schema

**Nodes:** File, Function, Class, Interface, Method, Community, Process
**Edges (via CodeRelation.type):** CALLS, IMPORTS, EXTENDS, IMPLEMENTS, DEFINES, MEMBER_OF, STEP_IN_PROCESS

```cypher
MATCH (caller)-[:CodeRelation {type: 'CALLS'}]->(f:Function {name: "myFunc"})
RETURN caller.name, caller.filePath
```
