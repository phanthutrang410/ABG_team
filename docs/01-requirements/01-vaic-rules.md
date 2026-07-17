# Quy chế VAIC 2026 — checkpoint và cổng nộp bài

Tài liệu này chỉ giữ các yêu cầu ảnh hưởng trực tiếp tới việc build và nộp sản phẩm trong 48 giờ. Tất cả thời gian bên dưới là giờ Việt Nam (UTC+7), ngày **17–19/7/2026**.

## 1. Lịch đóng cổng

| Cổng | Deadline | Deliverable bắt buộc | Điều kiện qua cổng |
|:---|:---:|:---|:---|
| Bắt đầu sprint | **11:00 Thứ Sáu, 17/7** | Chọn đề sau khi BTC công bố 8 track; bắt đầu phát triển sản phẩm | Không dùng code/sản phẩm làm sẵn như phần bài thi; toàn bộ sản phẩm và code chính được phát triển trong 48 giờ thi |
| **Checkpoint 1 — Chốt hướng làm** | **11:00 Thứ Bảy, 18/7** | Tên dự án; track/vấn đề đã chọn; mô tả ngắn giải pháp; hướng tiếp cận dự kiến | Đã nộp đủ 4 nội dung cho BTC trước deadline |
| **Checkpoint 2 — Có bản chạy được** | **23:00 Thứ Bảy, 18/7** | URL sản phẩm đã deploy live; URL GitHub repository ở chế độ public | Cả hai URL đã nộp đúng hạn và mở được khi không đăng nhập |
| **Cổng nộp bài cuối — ĐÓNG CỔNG** | **11:00 Chủ Nhật, 19/7** | Bộ hồ sơ ở mục 2 | BTC xác nhận đã nhận đủ bài trước deadline; **không gia hạn** |
| Demo Day — Top 10 | **15:30 Chủ Nhật, 19/7** | Slide trình bày và sản phẩm live sẵn sàng demo trực tiếp | Đội được công bố vào Top 10; sẵn sàng pitch **4 phút** và Q&A **2 phút** |

> Deadline là thời điểm cổng đóng, không phải thời điểm bắt đầu upload. Nếu quá giờ, thiếu deliverable hoặc URL không truy cập được thì coi như chưa qua cổng.

## 2. Bộ hồ sơ tại cổng nộp bài cuối

- [ ] **Presentation slides**.
- [ ] **Demo video không quá 5 phút**.
- [ ] **GitHub repository public**.
- [ ] **Live deployed URL**.
- [ ] **Project description**.
- [ ] **AI collaboration log** đã loại bỏ secret, PII và nội dung không được phép công khai.

Hai trang quy chế nguồn cùng gọi đây là “05 tài liệu” nhưng không thống nhất mục thứ năm: mục 2.2 ghi **Project description**, còn mục 3.4 ghi **AI collaboration log**. Vì vậy đội phải chuẩn bị **cả hai**; khi form nộp chính thức mở, owner bài nộp đối chiếu trường bắt buộc của form và lưu bằng chứng BTC đã nhận bài.

## 3. Ràng buộc trực tiếp đối với quá trình build

- Sản phẩm phải có tinh thần **AI-native**: AI giữ vai trò rõ ràng trong giải pháp, không chỉ là tính năng phụ gắn thêm.
- Toàn bộ sản phẩm/code chính dùng để dự thi phải được phát triển trong 48 giờ của cuộc thi; được phép dùng thư viện có sẵn.
- Đội chịu trách nhiệm về nội dung, mã nguồn, dữ liệu và tài nguyên sử dụng; không đạo văn và phải tuân thủ yêu cầu kỹ thuật do BTC công bố.
- Mỗi đội có một đội trưởng làm đầu mối chính thức với BTC. Xác nhận/yêu cầu gửi qua đội trưởng có giá trị với toàn đội.
- Nhật ký cộng tác AI phải được ghi trong lúc build, gắn được với artifact/kết quả và không chứa secret, PII hoặc raw session không phù hợp để nộp.

## 4. Gate checklist vận hành

### Trước Checkpoint 1

- [ ] Tên dự án thống nhất trên repo, slide nháp và nội dung gửi BTC.
- [ ] Track/vấn đề đã chọn đúng tên BTC công bố.
- [ ] Mô tả ngắn nêu rõ người dùng, vấn đề, giải pháp và vai trò của AI.
- [ ] Hướng tiếp cận đủ cụ thể để khóa phạm vi build 24 giờ còn lại.

### Trước Checkpoint 2

- [ ] Live URL chạy được bằng cửa sổ ẩn danh, không phụ thuộc máy local.
- [ ] Public GitHub URL mở được khi đăng xuất và không chứa secret/PII.
- [ ] Luồng demo cốt lõi chạy được trên bản deploy.
- [ ] Có owner theo dõi deploy và phương án khôi phục nếu bản live lỗi.

### Trước cổng nộp bài cuối

- [ ] Upload sớm và kiểm tra lại từng trường trên form nộp.
- [ ] Video có thời lượng **≤ 5:00**, phát được và dùng đúng Live URL/version cuối.
- [ ] Slide, project description, README, video và AI log thống nhất tên dự án, phạm vi và tuyên bố.
- [ ] Repository public có hướng dẫn chạy; commit cuối cần nộp đã được push.
- [ ] Live URL được smoke test ẩn danh trên desktop và không lộ secret/PII.
- [ ] Lưu bằng chứng nộp thành công trước **11:00 19/7**.

### Trước Demo Day nếu vào Top 10

- [ ] Demo live đã được rehearsal theo đúng kịch bản.
- [ ] Pitch nằm trong 4 phút; Q&A chuẩn bị cho 2 phút.
- [ ] Có video/bản ghi dự phòng và người chịu trách nhiệm chuyển phương án khi live demo lỗi.

## 5. Tiêu chí chấm điểm để ưu tiên build

| Tiêu chí | Điểm |
|:---|:---:|
| Chất lượng triển khai kỹ thuật | 20 |
| Kiến trúc AI-native và đổi mới sáng tạo | 20 |
| Tính khả thi kinh doanh và lộ trình pilot | 20 |
| UX AI-native và tư duy thiết kế | 15 |
| An toàn AI, grounding và độ tin cậy | 15 |
| Trình bày và bảo vệ giải pháp | 10 |

Ba tiêu chí đầu chiếm **60/100 điểm**. Khi phải cắt scope, ưu tiên một luồng live ổn định, vai trò AI thuyết phục và câu chuyện pilot khả thi trước các tính năng phụ.

## 6. Nguồn vận hành liên quan

- Kế hoạch thực thi: [Sprint](../03-project/03-sprint.md).
- Phạm vi sản phẩm: [PRD MVP](../02-product/04-prd.md).
- Nhật ký AI: [`.ai-log/README.md`](../../.ai-log/README.md).
