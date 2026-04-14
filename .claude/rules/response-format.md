---
alwaysApply: true
---
# RESPONSE FORMATTING RULES - Quy tắc trình bày final answer

```markdown
<MEMORY[response-format]>

# Quy tắc Format Final Answer

Các quy tắc dưới đây áp dụng chủ yếu cho **phần trả lời cuối cùng gửi tới user**.
Không dùng rule này để làm nặng thinking/process nội bộ hoặc status update ngắn giữa chừng.

Mục tiêu là làm cho final answer cực dễ đọc, dễ hiểu, dễ review, phù hợp cả với người ít ngữ cảnh kỹ thuật.

## 1. Cấu trúc phản hồi chuẩn

Mỗi phản hồi nên có cấu trúc rõ ràng với headers phân cấp:

```
## 🎯 Tóm tắt / Mục tiêu
(1-2 câu tổng quan ngắn gọn)

## 📊 Phân tích / Chi tiết
(Nội dung chính với bảng, diagram, bullet points)

## ✅ Kết luận / Đề xuất / Action Items
(Tóm tắt và các bước tiếp theo)
```

## 2. Sử dụng Visual Markers

Có thể dùng emoji hoặc marker trực quan khi nó thực sự giúp final answer dễ quét hơn.
Không bắt buộc phải nhồi emoji nếu nội dung ngắn hoặc nếu marker đó không làm câu trả lời rõ hơn.

| Emoji | Sử dụng khi                             |
| ----- | --------------------------------------- |
| ✅     | Hoàn thành, đúng, passed, confirmed     |
| ❌     | Lỗi, sai, failed, rejected              |
| ⚠️     | Cảnh báo, cần lưu ý, warning            |
| 🔍     | Đang phân tích, điều tra, investigating |
| 🎯     | Mục tiêu chính, focus, objective        |
| 💡     | Gợi ý, tip, insight, idea               |
| 🚀     | Bắt đầu, triển khai, launch, action     |
| 📁     | File, folder, đường dẫn                 |
| 🔧     | Config, setting, cấu hình               |
| 📌     | Điểm quan trọng, pinned, highlight      |
| 🔗     | Liên kết, reference, connection         |
| 📝     | Ghi chú, note, documentation            |
| 🧪     | Testing, experiment, thử nghiệm         |
| 🛡️     | Security, bảo mật, protection           |
| ⚡     | Performance, tối ưu, fast               |
| 🔄     | Sync, update, refresh, loop             |

## 3. Sử dụng Bảng biểu (Tables)

Dùng bảng khi:
- So sánh nhiều items
- Liệt kê danh sách có nhiều thuộc tính
- Trình bày trạng thái của nhiều thành phần

Ví dụ:
| Thành phần | Vai trò | Trạng thái   |
| ---------- | ------- | ------------ |
| Module A   | Xử lý X | ✅ OK         |
| Module B   | Xử lý Y | ⚠️ Cần review |
| Module C   | Xử lý Z | ❌ Lỗi        |

## 4. Sử dụng Flow Diagrams (ASCII Art)

Dùng diagram khi mô tả:
- Luồng xử lý (data flow, process flow)
- Kiến trúc hệ thống
- Quan hệ giữa các thành phần

### Dạng ngang (Horizontal Flow):
```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Step 1  │ ──► │ Step 2  │ ──► │ Step 3  │
└─────────┘     └─────────┘     └─────────┘
```

### Dạng có branching:
```
┌─────────┐     ┌─────────┐
│ Input   │ ──► │ Process │
└─────────┘     └────┬────┘
                     │
            ┌────────┴────────┐
            ▼                 ▼
      ┌─────────┐       ┌─────────┐
      │ Success │       │  Error  │
      └─────────┘       └─────────┘
```

### Dạng đơn giản (cho flow ngắn):
```
Request → Validate → Process → Response
```

### Ký tự thường dùng:
- Mũi tên: `→`, `←`, `↑`, `↓`, `──►`, `◄──`, `▲`, `▼`
- Góc box: `┌`, `┐`, `└`, `┘`
- Đường kẻ: `─`, `│`, `├`, `┤`, `┬`, `┴`, `┼`

## 5. Bullet Points có phân cấp

Sử dụng bullet points với indent rõ ràng:

- **Cấp 1**: Ý chính, quan trọng nhất
  - Cấp 2: Chi tiết, giải thích
    - Cấp 3: Ví dụ cụ thể, edge cases

## 6. Code Blocks với Annotations

Khi hiển thị code, thêm comments giải thích:

```typescript
// ✅ Cách đúng
const data = await fetchData();

// ❌ Cách sai - không handle error
const data = fetchData(); // <- Thiếu await
```

## 7. Callout Boxes

Sử dụng blockquote với emoji để tạo callout:

> 💡 **Tip**: Gợi ý hữu ích cho người đọc

> ⚠️ **Lưu ý**: Điểm cần chú ý, có thể gây vấn đề

> ❌ **Lỗi**: Vấn đề nghiêm trọng cần sửa ngay

> ✅ **OK**: Xác nhận đã hoàn thành hoặc đúng

> 📌 **Quan trọng**: Thông tin critical không được bỏ qua

## 8. Nguyên tắc tổng quan

- Ưu tiên ngôn ngữ đơn giản, dễ hiểu, ít jargon
- Viết như đang giải thích cho người đọc có rất ít context kỹ thuật
- Mục tiêu là user đọc lướt vẫn nắm ý chính ngay
- Final answer nên dễ review hơn là trông cầu kỳ


| Nguyên tắc            | Mô tả                                                               |
| --------------------- | ------------------------------------------------------------------- |
| **Scannable**         | Người đọc có thể lướt nhanh và nắm ý chính qua headers, emoji, bảng |
| **Hierarchical**      | Thông tin quan trọng nhất lên đầu, chi tiết theo sau                |
| **Visual separation** | Dùng line breaks, horizontal rules (`---`) để tách các phần         |
| **Actionable**        | Kết thúc với đề xuất cụ thể, rõ ràng, có thể thực hiện được         |
| **Consistent**        | Sử dụng emoji và format nhất quán trong toàn bộ response            |

## 9. Anti-patterns (KHÔNG làm)

❌ **KHÔNG** viết wall of text không có cấu trúc
❌ **KHÔNG** sử dụng emoji random không có ý nghĩa
❌ **KHÔNG** tạo bảng cho chỉ 1-2 items (dùng bullet thay thế)
❌ **KHÔNG** vẽ diagram quá phức tạp, khó đọc
❌ **KHÔNG** bỏ qua tóm tắt/kết luận ở cuối
❌ **KHÔNG** viết quá dài dòng, giữ response concise

## 10. Ví dụ Response Mẫu

---

## 🎯 Tóm tắt

Phát hiện lỗi authentication ở module `auth-service`, nguyên nhân do token expired không được refresh đúng cách.

## 📊 Phân tích chi tiết

### Luồng hiện tại (có lỗi):
```
Login → Get Token → [Token Expired] → ❌ Request Failed
```

### Luồng đề xuất (đã fix):
```
Login → Get Token → [Token Expired] → Refresh Token → ✅ Retry Request
```

### So sánh:
| Aspect         | Hiện tại    | Đề xuất    |
| -------------- | ----------- | ---------- |
| Token refresh  | ❌ Không có  | ✅ Tự động  |
| Error handling | ⚠️ Thiếu     | ✅ Đầy đủ   |
| UX             | ❌ Bị logout | ✅ Seamless |

## ✅ Đề xuất Action Items

1. **Thêm interceptor** refresh token vào axios instance
2. **Implement** retry logic với exponential backoff
3. **Test** edge cases: token expired during request

> 💡 **Tip**: Có thể dùng thư viện `axios-auth-refresh` để đơn giản hóa implementation.

---

</MEMORY[response-format]>
```