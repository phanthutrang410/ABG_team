# PRD — Silent Shield (MVP 48 giờ)

## 1. Mục đích và nguồn yêu cầu

PRD này chuyển [Problems Brief](../01-requirements/02-problems-brief.md) thành phạm vi có thể demo trong 48 giờ. Brief mô tả sản phẩm đích ở bối cảnh đại học, với **Ban Lãnh đạo Khoa/Trường** là người dùng hệ thống chính; GVCN/cố vấn và đơn vị hỗ trợ nhận case sau khi con người phê duyệt.

Khi tài liệu có khác biệt, áp dụng thứ tự sau:

1. quy chế và ràng buộc chính thức của cuộc thi;
2. các ràng buộc privacy, care và fairness trong Problems Brief;
3. phạm vi MVP và acceptance trong PRD này;
4. danh mục mở rộng trong [Danh mục tín hiệu](06-signal-catalog.md).

Các điểm đã diễn giải hoặc chưa thống nhất với scaffold hiện tại được ghi tại [Truy vết yêu cầu](../01-requirements/03-traceability.md).

## 2. Product statement

> Silent Shield tổng hợp thay đổi trong điểm và chuyên cần theo thời gian để tạo **tín hiệu cần rà soát** cho Ban Lãnh đạo. Hệ thống giúp con người ưu tiên sự quan tâm và chuyển đúng trường hợp tới người hỗ trợ; không chẩn đoán, gắn nhãn hay tự động đưa ra quyết định bất lợi cho sinh viên.

### Mục tiêu MVP

- Chứng minh có thể phát hiện thay đổi theo thời gian từ dữ liệu synthetic, không cần nội dung riêng tư.
- Cho Ban Lãnh đạo xem danh sách tín hiệu cần rà soát, lý do, độ phủ và độ mới của dữ liệu.
- Cho phép con người phê duyệt, loại bỏ hoặc hoãn trước khi bàn giao.
- Hiển thị kiểm soát báo động giả và fairness bằng metric thật trên dữ liệu synthetic.
- Cho agent giải thích đầu ra có sẵn mà không tự tạo điểm hoặc suy đoán nguyên nhân.

### Không tuyên bố trong MVP

- Không tuyên bố phát hiện trầm cảm, bắt nạt, khủng hoảng tâm lý hay nguyên nhân bỏ học.
- Không tuyên bố hiệu quả trên sinh viên thật hoặc khả năng giảm tỷ lệ bỏ học thực tế.
- Không coi dữ liệu synthetic là bằng chứng hệ thống công bằng trong triển khai thật.

## 3. Người dùng và quyền hành động

| Vai trò | Nhu cầu trong MVP | Quyền/giới hạn |
|:--------|:------------------|:---------------|
| Ban Lãnh đạo Khoa/Trường | Xem toàn cảnh, rà tín hiệu, xem fairness và điều phối | Là primary system user; phê duyệt/loại/hoãn việc chuyển tiếp, không “phê duyệt sinh viên” |
| GVCN/Cố vấn học tập | Nhận case đúng phạm vi và lý do đủ để bắt đầu hỗ trợ | Chỉ nhận case đã duyệt; quyết định cách liên hệ; không thấy dữ liệu ngoài case/lớp được giao |
| Đơn vị hỗ trợ | Tiếp nhận case phù hợp chức năng | Chỉ nhận dữ liệu tối thiểu cần biết; tự đánh giá chuyên môn |
| Admin kỹ thuật/Data-ML | Nạp dữ liệu, vận hành model và kiểm tra fairness | Chỉ dùng dữ liệu synthetic/pseudonymized; không mặc nhiên có quyền xem danh tính và case |
| Sinh viên | Được hỗ trợ và được bảo vệ khỏi kết luận sai | Không phải người dùng dashboard trong MVP; không bị gắn nhãn hoặc nhận thông báo tự động |

Chi tiết trách nhiệm xem [Các bên liên quan](02-stakeholders.md), luồng xử lý xem [Quy trình](03-process.md).

## 4. Phạm vi dữ liệu MVP

### Dữ liệu được nạp

| Tệp synthetic | Trường phục vụ sản phẩm | Mục đích |
|:---------------|:------------------------|:---------|
| `students.csv` | mã synthetic, lớp/cohort, nhóm synthetic phục vụ audit | Mapping case và tính fairness; thuộc tính nhóm không đi vào điểm ưu tiên |
| `grades_timeseries.csv` | mã synthetic, tuần, điểm | Độ biến động và xu hướng điểm theo thời gian |
| `attendance_timeseries.csv` | mã synthetic, tuần, tỷ lệ chuyên cần | Mức chuyên cần và xu hướng thay đổi theo thời gian |

MVP không dùng GPA, tín chỉ, LMS, nộp bài, CLB, thư viện, Wi-Fi/campus hoặc log dịch vụ hỗ trợ. Đây chỉ là ứng viên hậu MVP và phải qua rà soát mục đích, độ cần thiết, bias và quyền truy cập trước khi dùng.

### Hợp đồng feature tối thiểu

- biến động điểm trong cửa sổ quan sát;
- độ dốc xu hướng điểm;
- tỷ lệ chuyên cần trong cửa sổ quan sát;
- độ dốc xu hướng chuyên cần;
- độ phủ dữ liệu và số kỳ quan sát hợp lệ;
- thuộc tính nhóm synthetic chỉ cho fairness audit, tách khỏi feature chấm điểm.

Mọi đầu ra phải mang `model_version`, thời điểm tính và các yếu tố đóng góp lấy từ model/API. LLM không được tính hoặc thay đổi mức độ ưu tiên.

## 5. Trải nghiệm sản phẩm trong MVP

### 5.1 Dashboard tổng quan

Ban Lãnh đạo xem được:

- số tín hiệu mới cần rà soát và số case theo trạng thái;
- danh sách được sắp theo **mức độ ưu tiên rà soát**, không phải “danh sách sinh viên nguy cơ”;
- trạng thái/độ mới nguồn dữ liệu;
- panel fairness ghi rõ dữ liệu synthetic và cỡ mẫu từng nhóm;
- ngưỡng đang dùng và tác động của ngưỡng tới báo động giả/khối lượng rà soát.

### 5.2 Chi tiết tín hiệu

Mỗi tín hiệu hiển thị:

- mã synthetic và phạm vi lớp/cohort;
- điều gì đã thay đổi và trong khoảng thời gian nào;
- nhóm yếu tố đóng góp có thể kiểm chứng bằng dữ liệu;
- độ phủ, độ mới và giới hạn dữ liệu;
- mức độ ưu tiên dạng dải/nhóm; không hiển thị raw risk score hoặc trọng số model cho người dùng nghiệp vụ;
- trạng thái case, lịch sử quyết định và lý do loại/hoãn nếu có.

### 5.3 Rà soát và bàn giao

Người có thẩm quyền có thể:

- phê duyệt chuyển tới người hỗ trợ;
- loại tín hiệu với lý do chuẩn hóa như dữ liệu sai, nghỉ có phép, đã được hỗ trợ hoặc không đủ căn cứ;
- hoãn và đặt thời điểm xem lại;
- bàn giao đúng GVCN/đơn vị hỗ trợ sau khi phê duyệt;
- lưu phản hồi tối thiểu để tránh cảnh báo lặp.

### 5.4 Agent giải thích có căn cứ

Agent có thể tóm tắt biến động, giải thích các yếu tố do model/API cung cấp và soạn bản nháp liên hệ trung lập. Agent phải từ chối hoặc nêu thiếu dữ liệu khi bị yêu cầu:

- tự tính, sửa hoặc đoán điểm;
- chẩn đoán sức khỏe tâm thần;
- suy đoán hoàn cảnh kinh tế, dân tộc, gia đình hoặc nguyên nhân cá nhân;
- quyết định liên hệ, kỷ luật hay thay đổi trạng thái học vụ;
- tự gửi email hoặc thông báo nhạy cảm.

## 6. Luồng demo chuẩn

1. Nạp ba tệp synthetic và hiển thị trạng thái dữ liệu.
2. Tính feature theo thời gian, độ phủ và đầu ra model/API.
3. Mở dashboard toàn đơn vị, xem danh sách tín hiệu và fairness.
4. Mở một case, kiểm tra thay đổi, yếu tố đóng góp và giới hạn dữ liệu.
5. Hỏi agent “Vì sao case này cần được rà soát?” và nhận câu trả lời bám dữ liệu.
6. Phê duyệt hoặc loại/hoãn case; nếu phê duyệt thì bàn giao cho người hỗ trợ.
7. Thay đổi ngưỡng để minh họa trade-off giữa bỏ sót, báo động giả và tải review.

## 7. Yêu cầu chức năng và acceptance

| ID | Yêu cầu | Acceptance của MVP |
|:---|:--------|:-------------------|
| FR-01 | Nạp dữ liệu synthetic | Ba tệp được đọc theo schema; lỗi thiếu trường hoặc dữ liệu không hợp lệ được báo rõ, không âm thầm bỏ qua |
| FR-02 | Tạo feature theo thời gian | Có ít nhất xu hướng/biến động điểm và xu hướng/tỷ lệ chuyên cần; kết quả tái lập được với cùng dữ liệu/model version |
| FR-03 | Kiểm tra coverage/freshness | Case hiển thị số kỳ hợp lệ, tình trạng thiếu/cũ; cấu hình có thể chặn tín hiệu khi không đủ căn cứ |
| FR-04 | Chấm mức ưu tiên | Model/API tạo mức ưu tiên và contributing factors; LLM không nằm trong đường tính điểm |
| FR-05 | Danh sách và chi tiết | Danh sách sắp theo ưu tiên; chi tiết giải thích thay đổi bằng ngôn ngữ trung lập; không dùng nhãn `High-risk student` |
| FR-06 | Human review | Có hành động phê duyệt, loại hoặc hoãn và lưu lý do; chưa duyệt thì không bàn giao |
| FR-07 | Care handoff | Case đã duyệt được gán đúng người/phạm vi và ghi nhận trạng thái tiếp nhận tối thiểu |
| FR-08 | Agent grounded | Câu trả lời dùng dữ liệu/model output có sẵn, nêu giới hạn và không bịa điểm/chẩn đoán |
| FR-09 | Fairness audit | Hiển thị ít nhất FPR theo nhóm synthetic, chênh lệch FPR, cỡ mẫu và nhãn “synthetic”; thuộc tính nhóm không tham gia scoring |
| FR-10 | False-alarm control | Demo được tác động của ngưỡng; có luồng loại false positive, ngoại lệ và chống lặp |
| FR-11 | Privacy/care copy | Dashboard nêu rõ mục đích hỗ trợ, dữ liệu được dùng, dữ liệu bị cấm và quyền quyết định của con người |

## 8. Non-functional requirements

- **Privacy:** chỉ dùng dữ liệu synthetic trong demo; không đưa PII thật hoặc secrets vào repo/log/video.
- **Explainability:** mọi case có yếu tố đóng góp, coverage và model version; không giải thích bằng suy đoán của LLM.
- **Fairness:** metric có mẫu số/cỡ mẫu; không kết luận khi nhóm quá nhỏ hoặc không có ground truth.
- **Reliability:** lỗi nguồn hoặc dữ liệu cũ phải hiện ra; fail closed khi thiếu dữ liệu bắt buộc.
- **Auditability:** quyết định của con người và chuyển trạng thái case có dấu vết tối thiểu.
- **Accessibility:** copy tiếng Việt dễ hiểu, không kỳ thị và không dùng màu sắc làm tín hiệu duy nhất.

## 9. Ngoài phạm vi 48 giờ

- Tích hợp SIS/LMS production và dữ liệu sinh viên thật.
- Xác thực/RBAC production đầy đủ, retention/deletion automation và quy trình khiếu nại hoàn chỉnh.
- Huấn luyện/kiểm định trên dữ liệu thật hoặc khẳng định hiệu quả lâm sàng/tâm lý.
- Dùng các tín hiệu mở rộng hay buffer trong [Danh mục tín hiệu](06-signal-catalog.md).
- Adaptive tutor, OCR/TTS, career matching, giám sát chat/camera/micro/mạng xã hội.

## 10. Definition of Done

MVP chỉ được coi là hoàn thành khi:

1. luồng demo ở mục 6 chạy end-to-end trên Live URL;
2. FR-01 đến FR-11 có bằng chứng trên UI/API hoặc test phù hợp;
3. bốn rubric privacy, care, fairness và false-alarm/explainability xuất hiện trong sản phẩm, không chỉ trong slide;
4. README, video, slide và AI log dùng cùng thuật ngữ và không tuyên bố vượt quá bằng chứng;
5. `scripts/verify.ps1` chạy đạt hoặc mọi bước bị skip/fail được ghi rõ trước khi nộp.
