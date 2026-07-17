# Story briefs — giang (Trần Hạ Giang)

> **Bắt đầu từ P2.** Bạn không sở hữu build hoặc tài liệu nguồn chuẩn. Hoàng là owner của PRD, copy, acceptance matrix, release evidence và mọi contract Markdown. Bạn chạy review độc lập và chuẩn bị asset trình bày dựa trên bản đã khóa.

Board tổng: [Sprint](03-sprint.md).

## A05 — UAT, review claim/copy và acceptance

| | |
|:--|:--|
| Outcome | Có checklist pass/fail/gap cho luồng live và claim sản phẩm để Hoàng cập nhật acceptance/evidence và feed vòng `D4r`. |
| Gate / deadline | P2 · ~21:30 (song song V07; trước cửa sổ fix/`D4r`) |
| Owner | giang |
| Depends | H02, G02, H03, G03, M03, H04, G04, T02, D4, H12a |

### Cách làm

1. Chạy list → case → review/handoff trên Live URL; kiểm tra loading, error và `insufficient_data`.
2. Rà UI/agent/demo copy: chỉ dùng “tín hiệu cần rà soát” và “mức độ ưu tiên rà soát”; không có kết luận dropout, raw score, claim fairness thiếu dữ liệu hay hành động tự động.
3. Đối chiếu privacy, care, fairness, false-alarm với giao diện/test thật. Case state theo Process (không nhãn risk); “hoãn” = giữ Pending Review.
4. Gửi cho Hoàng bảng pass/fail, screenshot, đường dẫn test và defect có thể tái lập — **defect phải vào vòng owner fix → `D4r` trước khi Văn Hải nộp V05**.

### Không làm

- Không sửa PRD, acceptance matrix, release evidence hay copy canonical.
- Không tự sửa code để che lỗi.
- Không thay giới hạn dữ liệu bằng giả định.

### Done when

Hoàng nhận được evidence/gap có thể hành động cho `D4r` và `H16`. Nếu dependency chưa Done, ghi đúng blocker thay vì tự tạo mock.

## D1 — Asset slide và mô tả dự án

| | |
|:--|:--|
| Outcome | Slide final và asset mô tả để nộp, nhất quán với bản live/evidence. |
| Gate / deadline | P3 · 09:00 |
| Owner | giang |
| Depends | V02, H12b, H16, D4r |

### Cách làm

1. Chỉ lấy thông điệp, giới hạn và screenshot từ `H12b`/`H16` và Live URL đã qua `D4r`.
2. Trình bày MVP gồm điểm theo kỳ + điểm danh theo thời gian, human review, privacy/care, fairness fail-closed và agent grounded.
3. Nếu `H15` chưa Done, ghi giới hạn dữ liệu (`insufficient_data`) trên nhánh chuyên cần — **không** gọi đó là Post-MVP. Forecast/fusion (nếu nhắc) mới là research bị chặn.
4. Bàn giao asset cho Văn Hải quay D2 và nộp V06.

### Không làm

- Không chỉnh tài liệu nguồn chuẩn hay phát biểu mới ngoài `H12a`/`H12b`.
- Không dùng PII, raw score, raw attendance hoặc screenshot local chưa smoke.

### Done when

Slide/mô tả dùng URL thật (sau `D4r`), không claim vượt evidence và có thể dùng trực tiếp cho video/form nộp.

## Khi bị block

| Tình huống | Làm gì |
|:--|:--|
| Runtime copy chưa khóa | BLOCKED → H12a |
| Banner/asset copy chưa khóa | BLOCKED → H12b |
| Evidence/FR chưa đủ | BLOCKED → H16; gửi gap từ A05 |
| Live URL chưa re-smoke | BLOCKED → D4r; không dùng ảnh/mock thay thế |
