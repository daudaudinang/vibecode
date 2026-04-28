# Complexity Assessment Rubric (LP Pipeline V3)

Mục tiêu của rubric này là tạo quyết định mode nhất quán cho `/lp:plan`: `single` hay `epic`.

## Dimensions (D1..D6)

Mỗi chiều chấm từ `0..3`.

| Dimension | Score 0 | Score 1 | Score 2 | Score 3 |
|---|---|---|---|---|
| D1 - Domain crossing | 1 module | 2 modules liên quan nhẹ | 2-3 modules core | >= 4 modules hoặc nhiều bounded contexts |
| D2 - Requirement ambiguity | rõ gần như đầy đủ | còn 1-2 điểm nhỏ | còn nhiều điểm cần xác nhận | mơ hồ lớn, chưa đủ để lập kế hoạch an toàn |
| D3 - Workflow depth | 1 flow chính | 1 flow + 1 edge | nhiều flow có ràng buộc | nhiều flow/phân nhánh phức tạp |
| D4 - Data/state coupling | local state đơn giản | có shared state nhỏ | nhiều state transitions | state machine/phụ thuộc chéo cao |
| D5 - Risk profile | low-risk | có regression nhỏ | risk trung bình cao | risk cao (public API, migration, auth/payment, dữ liệu quan trọng) |
| D6 - Context volume | <= 3 files | 4-10 files | 11-20 files | > 20 files hoặc context đọc > 2000 LOC |

## Total score và recommendation

- `0-6`: Recommend `single`
- `7-11`: `User decides` (agent đưa evidence + trade-off)
- `12-18`: Recommend `epic`

## Override rules

- `Epic override` luôn được bật khi bất kỳ điều kiện nào đúng:
  - `D5 = 3`
  - `D1 = 3` và `D4 >= 2`
  - User explicit yêu cầu epic/worktree isolation
- Nếu có override, contract phải ghi rõ `override_reason`.

## Output contract fields

Bắt buộc tối thiểu:

```json
{
  "mode_decision": "single | epic",
  "total_score": 0,
  "dimensions": {
    "D1": 0,
    "D2": 0,
    "D3": 0,
    "D4": 0,
    "D5": 0,
    "D6": 0
  },
  "recommendation": "single | user-decides | epic",
  "user_decision_required": false,
  "epic_override": false,
  "override_reason": null
}
```

## User-confirm gate

Agent chỉ recommend; user là người chốt mode cuối cùng trước khi đi tiếp.
