# Scope & To-be Process — Silent Shield

> **Phạm vi tài liệu:** Mô tả **sản phẩm đích (Target / Post-MVP)**. **MVP 48 giờ** theo [PRD](04-prd.md): điểm theo học kỳ + điểm danh theo thời gian + coverage/freshness; trạng thái case = [Process §4](03-process.md) (`New Signal` … `Resolved`/`Monitoring`). Các mục dưới đây về SIS/LMS đầy đủ, Wellbeing, D0–D3, SLA BR-07 là Target — **không** phải acceptance MVP và **không** thay Process làm SoT state machine.

## 1. Mục đích tài liệu

Tài liệu chốt **phạm vi nghiệp vụ của sản phẩm đích** (in/out-of-scope) và quy trình to-be ở cấp nghiệp vụ, làm nguồn cho [BRD](08-brd.md). Quy trình vận hành chi tiết (as-is/to-be theo bước, chủ thể, đầu ra) và **state machine MVP** xem [Quy trình](03-process.md); phạm vi demo 48 giờ xem [PRD](04-prd.md).

## 2. Những vấn đề sản phẩm sẽ giải quyết

Giảm tải cho giảng viên chủ nhiệm không thể theo sát toàn bộ sinh viên phụ trách và thiếu công cụ tổng hợp tín hiệu học vụ và hành vi để hỗ trợ ra quyết định phân bổ nguồn lực chăm sóc → lấp đầy khoảng trống chăm sóc đối với nhóm sinh viên có dấu hiệu sớm nhưng chưa bùng phát khủng hoảng ('quiet middle').

## 3. Phạm vi (In-scope)

* Thu thập và xử lý metadata từ SIS, LMS, điểm danh, điểm quá trình, log đăng ký học phần, log hẹn cố vấn học tập.
* Tính toán đặc trưng within-student và so sánh cohort ẩn danh, kèm coverage/confidence score.
* Chấm điểm và phân loại theo hai trục: Dropout Risk (D0–D3) và Wellbeing.
* Kiểm định công bằng (fairness gate) trước khi hiển thị kết quả.
* Báo cáo ưu tiên theo phân tầng quyền truy cập (T1: Ban Lãnh đạo; T3: GVCN/chuyên viên — chỉ ca được phân công; T2: Admin).
* Quy trình chuyển giao (handoff) sang con người: giao nhiệm vụ, ghi nhận phản hồi, xác định cách phản ứng escalation đối với các ca vượt ngưỡng crisis.
* Cơ chế buffer từ tín hiệu tham gia hoạt động ngoài lớp (nếu triển khai mở rộng), dùng để giảm mức độ nghiêm trọng của cảnh báo, không dùng để tăng.
* Tầng sinh lý do & tường thuật (Explanation & Narrative) bằng AI-Agent: lý do tổng hợp theo từng ca, tóm tắt cấp chương trình, soạn thảo email giao việc — toàn bộ ở chế độ read-only và qua bộ lọc từ vựng kiểm soát.

## 4. Ngoài phạm vi — không có trong hệ thống (Out-of-scope)

* Chẩn đoán tâm lý, kết luận y khoa hoặc bất kỳ hình thức dán nhãn chính thức nào đối với sinh viên.
* Hành động kỷ luật tự động hoặc bán tự động dựa trên điểm rủi ro.
* Giám sát nội dung tin nhắn, email hoặc bất kỳ dữ liệu riêng tư nào của sinh viên.
* Thay thế vai trò quyết định và chăm sóc trực tiếp của con người.
* Thu thập dữ liệu tham vấn tâm lý hoặc dữ liệu sức khỏe nhạy cảm khác.
* Quản lý học phí, tuyển sinh, thi trực tuyến, hoặc thay thế toàn bộ LMS hiện tại.

## 5. Quy trình To-be

* Ingestion: thu thập metadata định kỳ từ SIS, LMS, điểm danh...; giả danh hóa (pseudonymization) và gắn nguồn/timestamp.
* Feature & Scoring: tính đặc trưng within-student, gắn coverage score, hợp nhất thành hai điểm (Dropout Risk, Wellbeing) kèm độ tin cậy.
* Fairness gate: kiểm định disparate impact theo nhóm; chặn + cảnh báo vận hành cho T2 + xử lý trong 48h nếu lệch bất thường; không cảnh báo khi coverage thấp.
* Explanation & Narrative (AI-Agent): nhận đóng góp của từng tín hiệu (feature contributions) từ bước Scoring, sinh lý do tổng hợp cho từng ca bằng từ vựng kiểm soát (controlled vocabulary — ngôn ngữ hành vi trung tính, không từ ngữ lâm sàng); soạn tóm tắt tình hình cấp chương trình cho báo cáo Ban Lãnh đạo; và soạn sẵn nội dung email giao việc để Ban Lãnh đạo duyệt. Agent hoạt động read-only: không sửa điểm, không suy diễn nguyên nhân đời tư, mọi câu chữ phải truy vết được về tín hiệu gốc (grounding).
* Presentation: hiển thị báo cáo ưu tiên cho Ban Lãnh đạo theo đúng tầng quyền (T1).
* Ra quyết định & giao nhiệm vụ: Ban Lãnh đạo xem báo cáo → giao nhiệm vụ cụ thể cho đúng người phụ trách, kèm lý do do tầng Explanation sinh ra (không phải lý do tự viết tay mỗi lần).
* Theo dõi SLA: hệ thống theo dõi trạng thái từng ca theo [Process §4](03-process.md) (`Pending Review` → `Approved for Follow-up` → `Assigned` → …); ca quá hạn được nhắc và escalate theo BR-07 (**Target**; MVP chỉ cần dấu vết quyết định tối thiểu). Không dùng chuỗi informal “chờ duyệt → đã phân công” làm mã API.
* Tiếp cận: warm check-in (D1/D2) hoặc chuyển tuyến chuyên trách công tác sinh viên (D3/crisis).
* Feedback: kết quả tiếp cận được ghi nhận, đưa trở lại hệ thống để hiệu chỉnh ngưỡng cảnh báo.

## 6. Vai trò stakeholder trong quy trình mới

Ban Lãnh đạo Khoa/Trường chuyển từ vai trò bị động sang vai trò chủ động ra quyết định phân bổ dựa trên dữ liệu. Giảng viên chủ nhiệm/chuyên viên hỗ trợ chuyển từ 'tự giám sát liên tục toàn bộ sinh viên' sang **tiếp cận chăm sóc theo phân công** — chỉ hành động với ca cụ thể được giao, kèm lý do đủ để hành động; không phải theo dõi liên tục bất kỳ ai.

## 7. Hệ thống/dữ liệu cần tích hợp

SIS cho dữ liệu học vụ; LMS cho log hoạt động và gradebook; hệ thống điểm danh; hệ thống đăng ký học phần; hệ thống quản lý hẹn cố vấn học tập được cập nhật định kỳ. Tùy chọn mở rộng: hệ thống check-in sự kiện CLB (QR), hệ thống thư viện, hệ thống đặt lịch career center/tutoring.

## 8. Dependency

Chất lượng và độ đầy đủ của dữ liệu từ các hệ thống nguồn quyết định độ phủ và độ tin cậy của tín hiệu; sự sẵn sàng của quy trình hành chính hiện có để cung cấp input; sự cam kết của Ban Lãnh đạo trong việc thực sự sử dụng báo cáo để giao nhiệm vụ.

## 9. Rủi ro

Độ phủ dữ liệu không đồng đều giữa các môn/khoa làm giảm độ tin cậy tín hiệu. Nguy cơ cảnh báo sai gây tổn hại tâm lý nếu ngưỡng chưa tốt trong giai đoạn đầu. Rủi ro bias nếu dữ liệu lịch sử vốn đã phản ánh bất bình đẳng hiện có. Rủi ro vận hành nếu Ban Lãnh đạo không đủ thời gian xử lý báo cáo — được giảm thiểu bằng cơ chế SLA/escalation (BR-07): ca khẩn không phụ thuộc vào lịch của một cá nhân mà có đường thoát lên cấp phụ trách CTSV. Lãnh đạo lạm dụng danh sách cho mục đích sàng lọc/kỷ luật. Cold-start SV năm nhất — within-student cần lịch sử, nhóm rủi ro cao nhất lại là nhóm chưa có baseline.

## 10. Điều kiện để bắt đầu triển khai

* Xác nhận nguồn dữ liệu SIS/LMS/điểm danh có thể truy xuất ở dạng metadata.
* Có cam kết từ Ban Lãnh đạo về việc tiếp nhận và sử dụng báo cáo.
* Xây dựng xong cơ chế pseudonymization, phân quyền T1/T3/T2 và access-audit log trước khi đưa dữ liệu thật vào hệ thống.
* Thống nhất ngưỡng ban đầu cho các mức D0–D3 dựa trên dữ liệu lịch sử hoặc nghiên cứu tham chiếu.
