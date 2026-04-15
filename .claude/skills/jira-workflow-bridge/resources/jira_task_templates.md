# Jira Task Templates for LP Intake

Các template này giúp Jira issue chứa đủ context để LP canonical workflows đọc và handoff chính xác.

---

## 1. Feature / Story / Task Template

```markdown
## Context
[Mô tả nhu cầu hoặc vấn đề đang giải quyết]

## Scope
### ✅ In Scope
- [Item 1]
- [Item 2]

### ❌ Out of Scope
- [Item 1]

## Business Rules
- [Rule 1]
- [Rule 2]

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Technical Context
- [File paths / API / module liên quan nếu biết]

## Notes for Agent
- [Convention, constraint, stakeholder note]

## Manual Test — Expected Results
- [Scenario 1 → expected]
- [Scenario 2 → expected]
```

---

## 2. Bug Template

```markdown
## Context
[Mô tả lỗi ngắn gọn]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected vs Actual
- **Expected:** [Kết quả mong đợi]
- **Actual:** [Kết quả thực tế]

## Bug Details
- **Environment:** [Browser / OS / Device]
- **Frequency:** [Always / Sometimes / Rare]
- **Impact:** [Low / Medium / High]

## Error Context
- [Log / stack trace / screenshot link]

## Technical Scope
- [File path / module nghi ngờ nếu biết]

## Acceptance Criteria
- [ ] Lỗi không còn tái hiện với luồng trên
- [ ] Không tạo regression ở flow liên quan

## Notes for Agent
- [Giả định, observations, workaround tạm thời nếu có]
```

---

## 3. Epic Template

```markdown
## Epic Goal
[Mục tiêu tổng thể]

## Context
[Vì sao cần epic này]

## Scope
### ✅ In Scope
- [Workstream 1]
- [Workstream 2]

### ❌ Out of Scope
- [Không làm ở epic này]

## Child Tasks (Breakdown)
| Key | Type | Summary | Priority | Status |
|-----|------|---------|----------|--------|
| PROJ-101 | Story | [Feature A] | High | To Do |
| PROJ-102 | Task | [Infra B] | Medium | To Do |

## Technical Architecture Notes
- [Module/service liên quan]
- [API or DB impact nếu có]

## References
- [Design doc / Figma / related links]
```

---

## Nguyên tắc viết task tốt cho LP

| Nguyên tắc | Vì sao quan trọng |
|---|---|
| File paths cụ thể | Giúp agent bắt đầu đọc code đúng chỗ |
| Acceptance Criteria dạng checklist | Dễ verify |
| Scope In/Out rõ | Giảm scope creep |
| Error logs/screenshots đầy đủ | Tăng tốc debug |
| Notes for Agent | Giữ context mềm nhưng hữu ích |
| Manual test expected results | Giúp QA và implement cùng hiểu mục tiêu |

## Keywords hữu ích

- `## Acceptance Criteria`
- `## Steps to Reproduce`
- `## Expected vs Actual`
- `## Scope`
- `## Business Rules`
- `## Technical Context`
- `## Notes for Agent`
- `## Manual Test — Expected Results`

## Ghi chú

- Template này phục vụ Jira intake cho LP canonical `/lp:*` flows
- Sau khi issue đủ rõ, Jira bridge sẽ route sang `/lp:plan`, `/lp:debug-investigator`, hoặc `/lp:implement`
- Không dùng template này để mô tả `.agent/*` hoặc `.agents/*` như source-of-truth runtime
