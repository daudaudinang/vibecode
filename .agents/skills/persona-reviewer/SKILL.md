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

| Persona                   | Persona ID             | Focus                                                                         |
| ------------------------- | ---------------------- | ----------------------------------------------------------------------------- |
| **Senior PM**             | `senior_pm`            | Requirement fidelity, AC completeness, scope clarity, business-value delivery |
| **Senior UI/UX Designer** | `senior_uiux_designer` | UX flow clarity, wording, design consistency, regression/friction risk        |
| **Senior Developer**      | `senior_developer`     | Logic correctness, tests/evidence, edge cases, boundary correctness           |
| **System Architecture**   | `system_architecture`  | Coupling, decomposition, dependency logic, scalability/maintainability        |

## How Orchestrator Should Invoke

Canonical review model có **2 modes**:

### Standard mode (Review tiêu chuẩn - Sử dụng trong lần đầu tiên review hoặc khi được chỉ định review SÂU và KỸ)

Spawn **4 agents độc lập**, mỗi agent giữ đúng 1 persona, chạy song song:

```text
Agent 1 → senior_pm
Agent 2 → senior_uiux_designer
Agent 3 → senior_developer
Agent 4 → system_architecture
→ wait for all
→ orchestrator merge
```

Đảm bảo full independence, tránh anchoring/confirmation bias.

### Fast mode (Review nhanh - Sử dụng khi re-review trong loop)

**1 agent duy nhất chạy multi-persona** — đánh giá lần lượt từ 4 góc nhìn trong cùng 1 pass:

```text
1 Agent → senior_pm perspective
       → senior_uiux_designer perspective
       → senior_developer perspective
       → system_architecture perspective
       → tổng hợp verdict cuối
```

Tập trung vào delta changes so với review trước. Nhanh hơn ~75%.

### Khi nào dùng mode nào?

- Chưa có review trước đó → **standard mode**
- Đã có ít nhất 1 lần review trước → **fast mode**

Không dùng roster legacy `architect / security / senior-dev / ux-pm` cho canonical review-plan/review-implement flow.

> Source of truth cho canonical review flow: `.agents/skills/review-plan/SKILL.md`, `.agents/skills/review-implement/SKILL.md`, `.agents/skills/lp-pipeline-orchestrator/SKILL.md`

> File này chỉ nên được dùng như helper/reference cho persona-style review, không được override canonical review architecture.
