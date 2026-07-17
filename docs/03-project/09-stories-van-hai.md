# Story briefs — Văn Hải (Đậu Văn Hải)

> **Bắt đầu từ P2.** Bạn làm QA/release độc lập, rehearsal, video và submission. Hoàng hoàn thiện checklist/evidence Markdown; bạn chỉ bàn giao screenshot, gap và xác nhận nộp, không tự sửa docs/deploy/code.

Board tổng: [Sprint](03-sprint.md) · Evidence source: [Release evidence](07-release-evidence.md).

## V07 — QA release và smoke độc lập (lần 1)

| | |
|:--|:--|
| Outcome | Smoke độc lập Live URL/GitHub lần 1; defect/gap đủ để owner fix và Hoàng chạy `D4r`. |
| Gate / deadline | P2 · ~21:20 |
| Owner | Văn Hải |
| Depends | D3, D4 |

1. Mở Live URL ở tab ẩn danh/trình duyệt khác; kiểm tra health và luồng list → case.
2. Kiểm GitHub public, link không yêu cầu đăng nhập, không lộ secret/PII.
3. Rà nhanh claim trên bản deploy: không raw score, không kết luận dropout, rõ `insufficient_data` khi thiếu nguồn.
4. Gửi screenshot, thời điểm smoke và mọi gap cho Hoàng/**owner build**; **không** coi đây là tín hiệu nộp CP2 — còn vòng `D4r`.

## V05 — Nộp Checkpoint 2

| | |
|:--|:--|
| Outcome | BTC nhận Live URL và GitHub public trước 23:00. |
| Gate / deadline | P2 · ~22:45 |
| Owner | Văn Hải |
| Depends | D3, D4r, V07 |

Chỉ nộp sau **`D4r` xanh** (đã có cửa sổ fix/redeploy/re-smoke sau V07). Lưu screenshot/email/mã xác nhận và bàn giao cho Hoàng cập nhật evidence (`H16`).

## V02 — Script demo và rehearsal

| | |
|:--|:--|
| Outcome | Script 4 phút + Q&A 2 phút khớp live/copy đã khóa. |
| Gate / deadline | P3 · 08:00 |
| Owner | Văn Hải |
| Depends | D4r, G02, T02, G03, G04, H12a |

Script demo điểm theo kỳ + điểm danh theo thời gian (hoặc `insufficient_data` nếu `H15` chưa xong), priority review, human review (Process states), grounded agent, coverage/fairness gate. Forecast/fusion chỉ được nhắc là research/Post-MVP — không gọi chuyên cần theo thời gian là Post-MVP.

## D2 — Video

| | |
|:--|:--|
| Outcome | Video ≤5 phút dùng đúng Live URL và asset D1. |
| Gate / deadline | P3 · 09:30 |
| Owner | Văn Hải |
| Depends | D1, D4r |

Kiểm thời lượng, human review, fairness hoặc threshold, không PII/secret và không quay bản local khác bản deploy đã `D4r`.

## V08 — Audit AI log

| | |
|:--|:--|
| Outcome | Gap AI log được ghi để Hoàng hoàn thiện D5. |
| Gate / deadline | P3 · 09:45 |
| Owner | Văn Hải |
| Depends | H05b |

Rà manifest và online-chats theo template `H05b`: link ẩn danh, không secret/PII/raw session, không bịa log hộ thành viên. Bàn giao gap/đường dẫn cho Hoàng.

## V06 — Nộp cổng cuối

| | |
|:--|:--|
| Outcome | BTC nhận đủ slide, video, GitHub, Live URL, mô tả và AI log trước 11:00. |
| Gate / deadline | P3 · 10:30 |
| Owner | Văn Hải |
| Depends | D1, D2, D3, D4r, D5, H09, H16 |

Đối chiếu từng deliverable với evidence Hoàng đã hoàn thiện (gồm CP2 sau V05), submit form, lưu xác nhận và báo team. Không coi một mục “đã xong” khi chưa có link hoặc evidence.
