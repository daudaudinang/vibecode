---
alwaysApply: true
---
# Quy tắc về vị trí đặt file tài liệu và plan

Rule này phải đi theo `identity.md`, không được ép mọi tài liệu vào `.claude/` nếu repo đang dùng nơi khác làm canonical.

## 1. Ưu tiên source of truth đã được repo dùng thật

- Tài liệu kỹ thuật đặt ở `docs/` hoặc thư mục project-scope đã được verify trong repo.
- Plan triển khai đặt ở `.claude/plans/PLAN_<TEN>/`.
- README và tài liệu tổng quan của dự án đặt ở root hoặc `docs/`.

## 2. Chỉ dùng `.claude/` khi đúng loại file

- `.claude/plans/` chỉ dành cho plan, phase breakdown, walkthrough implementation.
- `.claude/docs/` chỉ dùng khi repo này thực sự có và đang dùng nó như thư mục docs project-scope.
- Không tự tạo hoặc ép dùng `.claude/docs/` nếu chưa verify repo đang dùng convention đó.

## 3. Khi nào được lệch rule mặc định

- Nếu user chỉ định rõ vị trí file thì làm theo user.
- Nếu repo đã có convention cục bộ rõ ràng thì làm theo convention đã verify.
- Nếu file thuộc runtime/generated artifacts thì không coi là tài liệu; đặt theo thư mục runtime tương ứng thay vì docs/plans.

## 4. Mục tiêu áp dụng

- Tránh conflict giữa rule tổng quát và convention thực tế của repo.
- Giữ plan ở `.claude/plans/` theo LP flow hiện tại.
- Giữ tài liệu tổng quan/dự án ở nơi người trong repo kỳ vọng tìm thấy.