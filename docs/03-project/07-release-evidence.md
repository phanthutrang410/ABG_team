# Release Evidence Checklist

> **Owner tài liệu/evidence:** Hoàng. **Owner QA/submission từ P2:** Văn Hải. giang chuẩn bị asset slide/mô tả sau khi copy/evidence đã khóa.
>
> Chỉ tick khi có evidence thật. Nếu dependency chưa Done, ghi BLOCKED → ID trong cột Evidence.

## 1. Checkpoint 1: 18/7 11:00

| Mục | Owner | Task nguồn | Evidence | Status |
|:--|:--|:--|:--|:--|
| Tên dự án, track, mô tả, hướng tiếp cận | Hoàng | H13 |  | [ ] |
| Đã nộp form/link BTC | Hoàng | H13 |  | [ ] |
| Xác nhận BTC đã nhận | Hoàng | H13 |  | [ ] |

## 2. Checkpoint 2: 18/7 23:00

| Mục | Owner | Task nguồn | Evidence | Status |
|:--|:--|:--|:--|:--|
| Live URL hoạt động (smoke lần 1) | Hoàng | D4 |  | [ ] |
| Smoke test ẩn danh độc lập lần 1 | Văn Hải | V07 |  | [ ] |
| Fix → redeploy → re-smoke | Hoàng | D4r |  | [ ] |
| GitHub public, PII/secret scan | Hoàng | D3 |  | [ ] |
| BTC nhận 2 URL | Văn Hải | V05 |  | [ ] |
| Hoàng hoàn thiện evidence CP2 | Hoàng | H16 (sau V07, V05) |  | [ ] |

## 3. Đóng cổng nộp cuối: 19/7 11:00

| Mục | Owner | Task nguồn | Evidence | Status |
|:--|:--|:--|:--|:--|
| Slide + asset mô tả | giang | D1 |  | [ ] |
| Video ≤5 phút, đúng URL | Văn Hải | D2 |  | [ ] |
| GitHub public + README | Hoàng | D3, H09 |  | [ ] |
| Live URL smoke cuối | Hoàng | D4r, H16 |  | [ ] |
| AI collaboration log hoàn thiện | Hoàng | D5 |  | [ ] |
| Form cuối đã gửi | Văn Hải | V06 |  | [ ] |
| Xác nhận BTC đã nhận | Văn Hải | V06 |  | [ ] |

## 4. Demo Day: 19/7 15:30 (nếu vào Top 10)

| Mục | Owner | Task nguồn | Evidence | Status |
|:--|:--|:--|:--|:--|
| Script pitch 4 phút + Q&A 2 phút | Văn Hải | V02 |  | [ ] |
| Rehearsal live | Văn Hải | V02, D4r |  | [ ] |
| Live URL sẵn sàng | Hoàng | D4r |  | [ ] |

## 5. Quy ước

- Hoàng cập nhật Markdown/evidence chuẩn sau handoff QA; Văn Hải không tự sửa checklist.
- CP2: không nộp `V05` trước `D4r` xanh. `H16` phải khóa evidence CP2 sau `V07` + `V05` (và gap `A05` nếu có).
- Asset slide/mô tả không được thay đổi scope/copy canonical do Hoàng khóa (`H12a` runtime; `H12b` banner/asset).
- Nếu một mục bị block, ghi dependency cụ thể và báo owner, không dùng screenshot/mock thay thế.
