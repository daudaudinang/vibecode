---
name: persona-reviewer
description: Multi-persona reviewer for plans and code. Read TASK.md for details.
---

# Persona Reviewer

> **Full task guide**: `.agents/skills/tasks/persona-review/TASK.md`

## Usage

```
/persona-reviewer {persona}: Review {artifact_path}
```

## Canonical personas available

| Persona | Persona ID | Focus |
|---------|------------|-------|
| **Senior PM** | `senior_pm` | Requirement fidelity, AC completeness, scope clarity, business-value delivery |
| **Senior UI/UX Designer** | `senior_uiux_designer` | UX flow clarity, wording, design consistency, regression/friction risk |
| **Senior Developer** | `senior_developer` | Logic correctness, tests/evidence, edge cases, boundary correctness |
| **System Architecture** | `system_architecture` | Coupling, decomposition, dependency logic, scalability/maintainability |

## How Orchestrator Should Invoke

Canonical model: spawn **4 agents độc lập chạy song song**, mỗi agent giữ đúng 1 persona, rồi orchestrator mới validate evidence, normalize conflicts, và merge findings.

```text
Agent 1 → senior_pm
Agent 2 → senior_uiux_designer
Agent 3 → senior_developer
Agent 4 → system_architecture
→ wait for all
→ orchestrator merge
```

Không dùng roster legacy `architect / security / senior-dev / ux-pm` cho canonical review-plan/review-implement flow.

Không dùng "depth level" để giả lập multi-review.

> Source of truth cho canonical review flow: `.agents/skills/review-plan/SKILL.md`, `.agents/skills/review-implement/SKILL.md`, `.agents/skills/lp-pipeline-orchestrator/SKILL.md`

> File này chỉ nên được dùng như helper/reference cho persona-style review, không được override canonical 4-agent review architecture.

