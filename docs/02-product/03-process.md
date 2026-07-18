# Quy trình As-is / To-be — Silent Shield

## 1. Mục đích và nguyên tắc

Tài liệu mô tả quy trình nhận biết, rà soát và bàn giao **tín hiệu cần rà soát**. Trạng thái trong quy trình thuộc về tín hiệu/case, không phải nhãn hoặc thuộc tính của sinh viên.

Ba nguyên tắc xuyên suốt:

1. Hệ thống không chẩn đoán hoặc suy đoán nguyên nhân.
2. Hệ thống không gắn nhãn sinh viên.
3. Con người phê duyệt trước khi chuyển tiếp và giữ quyền quyết định cuối cùng.

## 2. Quy trình hiện tại (As-is)

### Phạm vi

- **Bắt đầu:** dữ liệu điểm, chuyên cần hoặc mức độ tham gia học tập bắt đầu có thay đổi đáng chú ý.
- **Kết thúc:** GVCN/Ban Đào tạo nhận ra vấn đề và thực hiện liên hệ, hoặc trường hợp chỉ được chú ý khi đã đến kỳ xét học vụ/vấn đề trở nên nghiêm trọng.
- **Người tham gia:** GVCN/cố vấn học tập, Phòng Đào tạo, Ban Lãnh đạo và đơn vị hỗ trợ khi được chuyển tuyến.
- **Công cụ:** sổ/file chuyên cần, bảng tính riêng, SIS/LMS và trao đổi thủ công.

### Luồng hiện tại

| Bước | Hoạt động | Điểm nghẽn |
|:----:|:----------|:-----------|
| 1 | GVCN ghi nhận chuyên cần và theo dõi lớp | Lớp đông, dữ liệu nằm ở nhiều nơi, khó xem biến động theo thời gian |
| 2 | GVCN tự đối chiếu điểm, chuyên cần và tương tác khi có thời gian hoặc khi thấy biểu hiện rõ | Phụ thuộc chủ yếu vào quan sát và kinh nghiệm của GVCN, trong khi thông tin liên quan nằm phân tán ở nhiều hệ thống |
| 3 | GVCN trao đổi với Phòng Đào tạo/Ban Lãnh đạo khi nghi ngờ có vấn đề | Không có tiêu chí, bằng chứng và trạng thái bàn giao thống nhất |
| 4 | Đơn vị phụ trách tra cứu thêm và quyết định có liên hệ hay không | Chậm, dễ trùng lặp hoặc bỏ sót những thay đổi diễn ra âm thầm |
| 5 | Cuối kỳ, Phòng Đào tạo thực hiện xét học vụ theo quy trình hiện hành | Dữ liệu được tổng hợp muộn; cơ hội hỗ trợ sớm bị thu hẹp |

### Hệ quả

- Người phụ trách mất thời gian tổng hợp thủ công nhưng vẫn khó thấy xu hướng.
- Những sinh viên ít biểu hiện ra ngoài có thể bị bỏ sót.
- Thiếu dấu vết cho biết ai đã xem, đã chuyển cho ai và kết quả ra sao.
- Không đo được báo động giả, tải công việc hoặc chênh lệch hiệu năng giữa các nhóm.

## 3. Quy trình tương lai (To-be)

### Phạm vi

- **Bắt đầu:** khi snapshot/kỳ dữ liệu đã được phê duyệt sẵn sàng.
- **Kết thúc một vòng:** case được giải quyết hoặc chuyển sang theo dõi; trạng thái và phản hồi tối thiểu được lưu để tránh tín hiệu lặp không cần thiết.
- **Dữ liệu đầu vào:** điểm theo học kỳ và mapping lớp–cố vấn từ bản trích xuất EPU đã được duyệt. Chuyên cần/nghỉ có phép hoặc hành vi học tập chỉ được thêm khi có nguồn riêng được phê duyệt.
- **Đầu ra:** báo cáo theo kỳ đồng bộ, tín hiệu cần rà soát kèm yếu tố đóng góp, case đã được phê duyệt để bàn giao và số liệu vận hành/fairness.

### Luồng chuẩn

| Bước | Hoạt động | Chủ thể chính | Đầu ra/kiểm soát |
|:----:|:----------|:--------------|:-----------------|
| 1 | Nạp snapshot/kỳ dữ liệu đã được phê duyệt | Hệ thống + CNTT/Phòng Đào tạo | Ghi thời điểm, nguồn, provenance và trạng thái nạp |
| 2 | Kiểm tra chất lượng và độ mới của dữ liệu | Hệ thống | Gắn cờ thiếu/lỗi/quá cũ; có thể chặn tạo tín hiệu mới |
| 3 | Tính coverage và phân tích thay đổi của từng sinh viên theo thời gian | Model/API | So sánh chủ yếu với lịch sử của chính sinh viên; thiếu dữ liệu thì trả `insufficient_data` hoặc hạ tin cậy, không suy đoán nguyên nhân |
| 4 | Phát hiện tín hiệu mới cần rà soát | Model/API | Tạo mức độ ưu tiên nội bộ và yếu tố đóng góp có thể kiểm chứng; UI nghiệp vụ không lộ raw score/trọng số |
| 5 | Lọc case đã xử lý hoặc không có thay đổi | Hệ thống | Giảm trùng lặp; tôn trọng trạng thái resolved/monitoring và ngoại lệ nghiệp vụ |
| 6 | Tạo báo cáo định kỳ cho Ban Lãnh đạo | Hệ thống | Tổng hợp tín hiệu mới, case đang theo dõi, freshness và trạng thái fairness (`insufficient_data` nếu chưa đủ nhóm/nhãn) |
| 7 | Rà soát và sử dụng agent khi cần | Ban Lãnh đạo | Agent chỉ tóm tắt/giải thích từ dữ liệu được phép, không tạo điểm hoặc kết luận |
| 8 | Phê duyệt, loại bỏ hoặc hoãn từng case | Ban Lãnh đạo/người được ủy quyền | Lưu quyết định và lý do; chưa phê duyệt thì không chuyển cho GVCN |
| 9 | Phân nhóm case đã duyệt theo lớp và GVCN (`advisor_ref`) | Hệ thống | Kiểm tra mapping; thiếu → mapping-repair; không gán người nhận giả |
| 10 | Hỗ trợ soạn email hoặc thông báo **theo từng GV** (danh sách SV kèm theo) | Hệ thống/agent | Chỉ tạo bản nháp trung lập (`requires_human_approval`); Copy/`mailto:`; không nói sinh viên “có nguy cơ bỏ học”; **không** SMTP/auto-send (FR-12 / [11-advisor…](../04-engineering/11-advisor-batch-mail-draft.md)) |
| 11 | Gửi thông tin tới GVCN | Ban Lãnh đạo (người) | Chỉ gửi dữ liệu tối thiểu cần thiết sau khi duyệt nháp; lưu dấu bàn giao khi `assign` |
| 12 | Liên hệ và hỗ trợ sinh viên | GVCN/đơn vị hỗ trợ | Con người lựa chọn cách liên hệ; không dùng cho kỷ luật tự động |
| 13 | Phản hồi kết quả ở mức tối thiểu | GVCN/đơn vị hỗ trợ | Xác nhận tiếp nhận, trạng thái và bước tiếp theo; không đưa ghi chép nhạy cảm vào dashboard chung |
| 14 | Cập nhật trạng thái và tránh tín hiệu lặp | Hệ thống | Đóng case hoặc chuyển monitoring; chỉ tạo lại khi có thay đổi mới đủ ý nghĩa |

### Điểm kiểm soát quyết định

- Model/API chỉ tạo và giải thích tín hiệu; không phê duyệt việc liên hệ.
- Agent không được thay đổi điểm, tự kết luận tín hiệu đúng/sai hoặc tự gửi nội dung nhạy cảm.
- Ban Lãnh đạo phê duyệt **việc chuyển tín hiệu**, không “phê duyệt sinh viên”.
- GVCN/đơn vị hỗ trợ quyết định cách tiếp cận sau khi xem bối cảnh thực tế.
- Mọi quyết định học vụ hoặc kỷ luật phải nằm ngoài luồng tự động của Silent Shield.

## 4. Trạng thái case

Không sử dụng `Low Risk`, `Medium Risk` hoặc `High Risk` làm trạng thái của sinh viên. Case sử dụng **đúng** các trạng thái quy trình dưới đây. Đây là contract cho transition API (`H06b`/`H03`): mọi schema/code phải khớp tên hiển thị và mã API trong bảng này.

### 4.1 Danh mục trạng thái và mã API

| Trạng thái (hiển thị) | Mã API bắt buộc | Ý nghĩa |
|:----------------------|:----------------|:--------|
| `New Signal` | `new_signal` | Tín hiệu mới sau kiểm tra dữ liệu và lọc lặp |
| `Pending Review` | `pending_review` | Đang chờ người có thẩm quyền xem bằng chứng |
| `Approved for Follow-up` | `approved_for_follow_up` | Đã duyệt việc chuyển tín hiệu cho người hỗ trợ |
| `Dismissed` | `dismissed` | Không chuyển tiếp sau rà soát; phải lưu lý do |
| `Assigned` | `assigned` | Đã bàn giao đúng GVCN/đơn vị hỗ trợ (`advisor_ref`) |
| `Follow-up in Progress` | `follow_up_in_progress` | Người phụ trách đã tiếp nhận và đang hỗ trợ |
| `Resolved` | `resolved` | Vòng hỗ trợ hiện tại đã hoàn tất |
| `Monitoring` | `monitoring` | Chưa cần hành động thêm; theo dõi có thời hạn |

**Cấm** dùng alias cũ làm state hoặc field API: `new`, `in_review`, `deferred`, `handed_off`, `Low Risk`, `Medium Risk`, `High Risk`.

### 4.2 Ma trận chuyển tiếp được phép

| Từ | Được tới | Ai / điều kiện |
|:---|:---------|:---------------|
| `New Signal` | `Pending Review` | Hệ thống sau tạo tín hiệu hợp lệ |
| `Pending Review` | `Approved for Follow-up` | Ban Lãnh đạo / người được ủy quyền · hành động `approve` |
| `Pending Review` | `Dismissed` | Cùng role · `dismiss` + lý do chuẩn hóa bắt buộc |
| `Pending Review` | `Pending Review` | Cùng role · `defer` + bắt buộc `review_at` (giữ state, không tạo state mới) |
| `Approved for Follow-up` | `Assigned` | Hệ thống/người điều phối · `assign` **chỉ khi** có `advisor_ref` hợp lệ |
| `Assigned` | `Follow-up in Progress` | Người nhận · `accept` |
| `Follow-up in Progress` | `Resolved` | Người nhận / điều phối · `resolve` |
| `Follow-up in Progress` | `Monitoring` | Người nhận / điều phối · `monitor` + thời hạn theo dõi |
| `Monitoring` | `Resolved` | Điều phối · kết thúc theo dõi |

`Dismissed` và `Resolved` là terminal của vòng hiện tại. Chỉ mở **case mới** khi có thay đổi dữ liệu đáng kể; không “reopen” bằng alias state cũ.

### 4.3 Hành động và trường phụ

| Hành động | State sau | Trường bắt buộc | Ghi chú |
|:----------|:----------|:----------------|:--------|
| `approve` | `Approved for Follow-up` | actor, timestamp | Không đồng nghĩa đã handoff |
| `dismiss` | `Dismissed` | reason code | |
| `defer` | vẫn `Pending Review` | `review_at` | **Không** phải state `Deferred` |
| `assign` | `Assigned` | `advisor_ref` | Thiếu → xem §4.4 |
| `accept` | `Follow-up in Progress` | actor | |
| `resolve` / `monitor` | `Resolved` / `Monitoring` | timestamp (+ hạn nếu monitor) | |

Agent/LLM không được gọi bất kỳ hành động chuyển trạng thái nào.

### 4.4 Gate `advisor_ref` và mapping-repair

- Phê duyệt (`approve`) chỉ duyệt **chuyển tín hiệu**, không tự bàn giao.
- `assign` / handoff **bắt buộc** có `advisor_ref` (và scope mapping hợp lệ) từ `advisor_assignment`.
- Thiếu `advisor_ref`: **dừng handoff**, đưa case vào hàng chờ **mapping-repair**; giữ `Approved for Follow-up` (hoặc trạng thái chờ sửa mapping tương đương trong API nội bộ) — **không** chuyển `Assigned` chỉ vì đã approve.
- Không gửi đại trà, không gán người nhận giả.

### 4.5 Chuyển tiếp / hành động bị cấm (reject)

| Cấm | Lý do |
|:----|:------|
| `New Signal` → `Assigned` / `Approved for Follow-up` bỏ qua review | Thiếu human review |
| `Pending Review` → `Assigned` | Phải `approve` trước |
| `assign` khi thiếu `advisor_ref` | Care boundary; đưa mapping-repair |
| Tạo state `Deferred` / `Handed Off` | Defer là action; handoff = `Assigned` |
| Dùng mã `new` / `in_review` / `deferred` / `handed_off` | Alias bị loại khỏi contract |
| Agent/LLM đổi state hoặc tự gửi thông báo | Ethics §8 / PRD FR-08 |
| Gắn `Low/Medium/High Risk` làm state sinh viên | Thuật ngữ sản phẩm: mức ưu tiên thuộc case |

## 5. Thông báo theo kỳ đồng bộ

### Có tín hiệu mới

Thông báo cho Ban Lãnh đạo gồm:

- số tín hiệu mới cần review;
- số case đang theo dõi và quá hạn review;
- tình trạng/độ mới của các nguồn dữ liệu;
- tóm tắt fairness kèm source/cỡ mẫu hoặc trạng thái `insufficient_data`, và cảnh báo nếu chênh lệch trên dữ liệu đủ điều kiện vượt ngưỡng nội bộ;
- liên kết vào danh sách chờ phê duyệt.

Không tự động gửi case mới cho GVCN trước bước phê duyệt.

### Không có tín hiệu mới

Chỉ gửi thông báo ngắn:

- dữ liệu đã cập nhật vào thời điểm nào;
- không phát sinh tín hiệu mới;
- số case đang được theo dõi hoặc quá hạn, nếu có;
- tình trạng đồng bộ và nguồn nào bị lỗi/quá cũ.

## 6. Ngoại lệ và cách xử lý

| Ngoại lệ | Xử lý bắt buộc |
|:---------|:---------------|
| Nguồn dữ liệu lỗi hoặc quá cũ | Hiển thị rõ freshness; không âm thầm coi dữ liệu cũ là hiện tại; chặn tín hiệu mới nếu không đủ tin cậy |
| Nghỉ có phép, bảo lưu hoặc thay đổi lớp chưa đồng bộ | Hiển thị ngoại lệ nếu biết; cho phép người review loại case với lý do chuẩn hóa; phản hồi lỗi về nguồn dữ liệu |
| Case vừa được xử lý xuất hiện lại | Không tạo lại nếu không có thay đổi đáng kể; hiển thị lịch sử trạng thái và thời hạn monitoring |
| Không xác định được GVCN/người nhận (`advisor_ref` thiếu hoặc mapping lỗi) | Dừng bàn giao (`assign` bị reject); đưa vào hàng chờ **mapping-repair**; không gửi đại trà; không coi `approve` là đã handoff — xem §4.4 |
| Agent thiếu dữ liệu căn cứ | Trả lời rằng chưa đủ dữ liệu và chỉ ra trường còn thiếu; không suy đoán |
| Chênh lệch FPR giữa các nhóm tăng | Gắn cờ fairness, rà ngưỡng/dữ liệu trước khi mở rộng; không dùng thuộc tính nhóm để suy đoán nguyên nhân cá nhân |
| Tải case vượt khả năng GVCN | Điều chỉnh ngưỡng hoặc lịch review có giám sát; không tự hạ ưu tiên của một cá nhân dựa trên thuộc tính nhạy cảm |

## 7. Chỉ số vận hành quy trình

- Số tín hiệu mới mỗi kỳ đồng bộ và số case tồn theo trạng thái.
- Tỷ lệ phê duyệt, loại bỏ và hoãn sau review.
- Thời gian từ `New Signal` đến lần review đầu tiên.
- Tỷ lệ bàn giao đúng GVCN/đơn vị hỗ trợ.
- Thời gian từ `Assigned` đến xác nhận tiếp nhận.
- Số case mới/đang xử lý trên mỗi GVCN.
- Tỷ lệ case lặp không có thay đổi đáng kể.
- FPR tổng thể và chênh lệch FPR giữa các nhóm audit được phê duyệt, khi có ground truth và cỡ mẫu đủ.
- Tỷ lệ nguồn dữ liệu đồng bộ đúng hạn.
