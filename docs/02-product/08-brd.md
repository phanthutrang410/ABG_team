# BRD — Silent Shield (Business Requirements)

## 1. Mục đích tài liệu

BRD mô tả yêu cầu ở **cấp nghiệp vụ** cho sản phẩm đích (bối cảnh đại học). [PRD](04-prd.md) là bản chuyển các yêu cầu này thành phạm vi demo được trong MVP 48 giờ — khi hai tài liệu khác nhau, áp dụng thứ tự ưu tiên trong [docs/README](../README.md).

Lưu ý thuật ngữ: tài liệu này dùng thang D0–D3/W0–W3 và từ "cảnh báo" ở cấp nghiệp vụ; mọi hiển thị trên giao diện phải tuân theo bảng thuật ngữ nhất quán trong [Bài toán](01-problem.md) ("tín hiệu cần rà soát", "mức độ ưu tiên rà soát").

## 2. Mục tiêu nghiệp vụ

* Giúp nhà trường chuyển từ mô hình can thiệp phản ứng sang mô hình can thiệp sớm dựa trên dữ liệu vận hành sẵn có.
* Mở rộng khả năng chăm sóc sinh viên mà không tăng thêm tải công việc giám sát cho giảng viên chủ nhiệm.
* Đảm bảo mọi cảnh báo đều dẫn tới hành động chăm sóc do con người quyết định.

## 3. Business Requirements

| Mã | Yêu cầu |
| :---- | :---- |
| BR-01 | Hệ thống phải tổng hợp tín hiệu học vụ và hành vi (metadata) để xác định danh sách sinh viên cần được chú ý, kèm mức độ ưu tiên. |
| BR-02 | Hệ thống phải trình bày báo cáo ưu tiên ở cấp Ban Lãnh đạo Khoa/Trường |
| BR-03 | Hệ thống phải gắn mỗi cảnh báo với một mức độ tin cậy (confidence/coverage score) dựa trên độ phủ dữ liệu. |
| BR-04 | Hệ thống phải tách riêng hai trục phân loại: Nguy cơ bỏ học (Dropout Risk) và Wellbeing, không được gộp chung. |
| BR-05 | Hệ thống phải cho phép Ban Lãnh đạo giao nhiệm vụ tiếp cận cụ thể cho đúng giảng viên/chuyên viên phụ trách |
| BR-06 | Hệ thống phải ghi nhận kết quả (không liên hệ được / hỏi thăm–ổn / hỗ trợ nhẹ / chuyển tuyến / cảnh báo sai rõ ràng) làm dữ liệu phản hồi để hiệu chỉnh ngưỡng cảnh báo theo thời gian. |
| BR-07 | Hệ thống phải theo dõi vòng đời mỗi ca theo SLA: ca ưu tiên cao (D3/W3) chưa được Ban Lãnh đạo duyệt sau 3 ngày làm việc → tự động nhắc lại; chưa được xử lý sau 5 ngày làm việc → escalate lên cấp phụ trách công tác sinh viên theo quy trình do trường định nghĩa. Ca đã phân công nhưng người phụ trách chưa ghi nhận kết quả sau 7 ngày → nhắc người phụ trách và hiển thị trạng thái "quá hạn" trong hàng đợi T1. |
| BR-08 | Mọi cảnh báo hiển thị hoặc giao việc đều phải kèm lý do tổng hợp có thể truy vết về tín hiệu gốc, diễn đạt bằng từ vựng kiểm soát; không hiển thị điểm số thô hay thuật ngữ lâm sàng cho bất kỳ vai trò nghiệp vụ nào (T1/T3). |

## 4. Business Rules

* Hệ thống cấm chẩn đoán, dán nhãn, kỷ luật, hành động tự động; cho phép gợi ý mức độ ưu tiên chăm sóc để con người quyết định.
* Khi độ phủ dữ liệu thấp, hệ thống phải im lặng hoặc cảnh báo rõ ràng thay vì đưa ra cảnh báo có độ tin cậy thấp.
* Chuẩn hóa tín hiệu phải ưu tiên so sánh within-student hơn so sánh chéo giữa các sinh viên.
* Cấm thu thập, lưu trữ, suy diễn biến kinh tế/dân tộc và proxy trực tiếp ở mọi tầng. Mọi feature mới phải qua bước proxy-check trước khi vào production.
* Dữ liệu wellbeing có độ nhạy cảm cao phải có retention policy riêng: xóa sau thời gian ngắn nếu không được escalate.
* Không ca cảnh báo nào được phép "nằm im vô thời hạn" trong hàng đợi: mọi ca đều có đồng hồ SLA; cơ chế nhắc/escalate chỉ thông báo cho con người ở cấp cao hơn, tuyệt đối không tự động thực hiện bất kỳ hành động nào đối với sinh viên (nhất quán nguyên tắc human-in-the-loop).

## 5. Đối tượng sử dụng

| Vai trò | Mô tả |
| :---- | :---- |
| Ban Lãnh đạo Khoa/Trường | Người dùng chính; đọc báo cáo tổng hợp, ra quyết định phân bổ nguồn lực, giao nhiệm vụ |
| Giảng viên chủ nhiệm / chuyên viên hỗ trợ (T3) | Thực thi theo chỉ đạo; chỉ tiếp cận sinh viên khi được chỉ định ca cụ thể; nhận việc qua email do agent soạn sẵn — không bắt buộc đăng nhập hệ thống |
| Quản trị hệ thống / nhóm phát triển mô hình (Admin) | Vận hành, huấn luyện và kiểm định fairness trên dữ liệu đã giả danh hóa (pseudonymization) |

Chi tiết vai trò và quyền dữ liệu xem [Các bên liên quan](02-stakeholders.md).

## 6. Dữ liệu cần thiết

Dữ liệu học vụ (SIS): GPA theo kỳ, tín chỉ tích lũy/đăng ký, môn rớt, trạng thái học vụ (cảnh báo/probation), lịch sử chuyển ngành. Dữ liệu vận hành khác: log LMS (tần suất/thời lượng, không nội dung), điểm danh, log nộp bài, log đăng ký học phần, log hẹn cố vấn học tập. Dữ liệu bổ sung tùy chọn: log check-in sự kiện CLB/hoạt động ngoại khóa, log mượn thư viện, log đặt lịch career center/tutoring. (Không dùng log WiFi/định vị hiện diện vật lý — theo dõi hiện diện là vùng rủi ro riêng tư không tương xứng với giá trị tín hiệu mang lại.)

## 7. Điều kiện và ràng buộc

Xem chi tiết ràng buộc bắt buộc tại [Problems Brief](../01-requirements/02-problems-brief.md) mục C.3 (quyền riêng tư & bảo vệ dữ liệu cá nhân; chỉ hỗ trợ qua con người; công bằng giữa các nhóm). Các ràng buộc này có trọng số cao nhất trong tiêu chí chấm điểm và không được đánh đổi lấy độ chính xác mô hình.

## 8. Yêu cầu phân quyền

Phân tầng truy cập theo vai trò (data access tiering): Tầng T1 (Ban Lãnh đạo) chỉ thấy báo cáo tổng hợp — danh sách ưu tiên, nhóm tín hiệu ở dạng tổng hợp — không thấy điểm rủi ro thô hay breakdown chi tiết từng tín hiệu cá nhân. Tầng T3 (GVCN/chuyên viên hỗ trợ) chỉ thấy **ca được phân công** (qua email giao việc + secure link, hoặc đăng nhập hệ thống), phạm vi trần là lớp mình phụ trách; không thấy bảng xếp hạng rủi ro cả lớp (kể cả lớp mình), ca không được giao, điểm số hay breakdown tín hiệu. Tầng T2 (Admin/nhóm phát triển) chỉ thấy dữ liệu đã giả danh hóa (pseudonymization) và nhật ký vận hành, không thấy danh tính thật của sinh viên. Nguyên tắc xuyên suốt: purpose limitation, data minimization, giả danh hóa khi huấn luyện; mọi lượt xem/lượt xuất hồ sơ ưu tiên đều được ghi vào access-audit log (ai-xem-gì-lúc-nào).

## 9. Yêu cầu báo cáo

Báo cáo ưu tiên cấp chương trình cho Ban Lãnh đạo: danh sách sinh viên cần chú ý, mức ưu tiên (D0–D3 và tương đương ở trục Wellbeing), lý do tổng hợp, mức độ tin cậy. **Xem trong hệ thống là mặc định.** Xuất báo cáo chỉ hỗ trợ hai dạng: (1) **thống kê tổng hợp không định danh** theo lớp/khóa/học kỳ — phục vụ ra quyết định phân bổ nguồn lực; (2) **báo cáo chi tiết từng sinh viên (per-student)** khi Ban Lãnh đạo cần làm việc trực tiếp một ca — bản xuất dùng từ vựng kiểm soát, gắn watermark (người xuất + thời điểm) và mỗi lần xuất được ghi vào access-audit log. Không tồn tại chức năng xuất danh sách định danh hàng loạt.

## 10. Tiêu chí thành công

Tăng tỷ lệ ca được tiếp cận ở giai đoạn sớm so với tổng ca; giảm false-alarm rate ở nhóm ưu tiên cao; không có chênh lệch tỷ lệ cảnh báo bất thường giữa các nhóm cohort/ngành/hệ; tỷ lệ ca escalate được con người tiếp nhận và phản hồi cao; miss-rate đo qua audit điểm mù cuối kỳ (đối chiếu nhóm không được cảnh báo với outcome thực tế).

## 11. Tiêu chí nghiệm thu cấp nghiệp vụ (triển khai thực tế)

Đây là các kịch bản hoặc yêu cầu đánh giá xem hệ thống có giải quyết đúng bài toán nghiệp vụ hay không. Các tiêu chí cụ thể bao gồm:

* Mọi cảnh báo hiển thị cho người dùng đều kèm mức độ tin cậy và nguồn tín hiệu tổng hợp.
* Không có trường hợp nào hệ thống tự động thực hiện hành động (thông báo kỷ luật, khóa tài khoản...).
* Kiểm tra fairness chạy được trên tập dữ liệu thử và phát hiện được chênh lệch giả lập giữa các nhóm.
* Phân quyền T1/T3/T2 hoạt động đúng như mô tả tại mục 8, xác nhận qua kiểm thử truy cập — bao gồm: T3 không xem được ca không được giao và không xem được xếp hạng rủi ro cả lớp; mọi lượt xuất per-student có watermark và được ghi vào access-audit log; không gọi được bất kỳ chức năng bulk-export định danh nào.
* Dữ liệu đầu vào và đầu ra phải nhất quán, bảo mật và tuân thủ các chính sách bảo mật thông tin.
* Kiểm thử grounding & từ vựng: với tập ca thử, 100% lý do hiển thị phải truy vết được về ít nhất một tín hiệu đầu vào có thật (không có câu nào agent tự suy diễn thêm); quét toàn bộ text hiển thị bằng danh sách từ cấm (trầm cảm, khủng hoảng, nguy cơ tâm lý...) — 0 kết quả.
* Kịch bản kiểm thử SLA: tạo ca D3 giả lập và không xử lý — hệ thống phải phát nhắc đúng mốc 3 ngày và escalate đúng mốc 5 ngày, có ghi log; xác nhận không có hành động nào hướng tới sinh viên được thực hiện tự động trong toàn bộ chuỗi.
