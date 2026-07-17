# Đạo đức, quyền riêng tư và an toàn — Silent Shield

## 1. Vai trò của tài liệu

Các kiểm soát trong tài liệu này là **điều kiện nghiệm thu sản phẩm**, không phải phần tuyên bố bổ sung cho slide. Chúng cụ thể hóa bốn yêu cầu trọng số cao của brief: privacy, care, fairness và kiểm soát báo động giả có giải thích.

MVP chỉ chạy trên bản trích xuất EPU đã được data owner phê duyệt, pseudonymize và tối thiểu hóa theo [hợp đồng tích hợp](../04-engineering/04-epu-data-integration-contract.md). Việc chuyển sang feed SIS/pilot vận hành vẫn cần một vòng phê duyệt riêng về mục đích, căn cứ sử dụng, thông báo, phân quyền, lưu giữ, sửa sai và xử lý sự cố theo chính sách nhà trường và pháp luật áp dụng.

## 2. Privacy by design

### Được phép trong MVP

- Điểm theo học kỳ và feature xu hướng/biến động được suy ra từ điểm khi có ít nhất hai kỳ hợp lệ.
- `student_ref` pseudonymous cùng mapping lớp/cohort tối thiểu cần cho case.
- `advisor_ref` pseudonymous chỉ cho routing sau human approval.
- Thuộc tính nhóm chỉ để tính fairness khi được phê duyệt riêng; không đưa vào model scoring và không giải thích case cá nhân.

### Cấm thu thập, đọc hoặc suy luận

- Nội dung chat, email, cuộc gọi, bài đăng hoặc trao đổi riêng tư.
- Camera, micro, nhận diện khuôn mặt, mạng xã hội, spyware hoặc theo dõi thiết bị.
- Nội dung tư vấn tâm lý, hồ sơ sức khỏe hoặc ghi chép hỗ trợ nhạy cảm.
- Chẩn đoán hay nguyên nhân như trầm cảm, bắt nạt, khó khăn tài chính, hoàn cảnh gia đình hoặc đặc điểm dân tộc.
- Raw reference, MSSV, họ tên, ngày sinh, email, SĐT hoặc PII sinh viên trong repo, log, ảnh chụp màn hình, slide hoặc video demo.

Các nguồn như LMS metadata, CLB, thư viện, Wi-Fi/RFID và log dịch vụ hỗ trợ trong brief là **ứng viên chưa được duyệt**, không thuộc MVP. Xem [Danh mục tín hiệu](06-signal-catalog.md).

### Nguyên tắc dữ liệu

- **Purpose limitation:** chỉ dùng để ưu tiên rà soát và chăm sóc, không tái sử dụng cho kỷ luật, tuyển sinh, học bổng hoặc xếp hạng.
- **Data minimization:** chỉ lấy trường cần cho feature, routing và audit đã định nghĩa.
- **Separation:** thuộc tính nhóm dùng cho fairness audit được tách khỏi feature scoring và khỏi màn hình case cá nhân.
- **Freshness:** hiển thị thời điểm cập nhật; dữ liệu cũ/thiếu không được ngầm coi là hiện tại.
- **Retention:** Bản trích xuất MVP có thời hạn lưu, source manifest và chủ sở hữu rõ; feed/pilot thật phải có thời hạn theo từng loại dữ liệu và xóa tín hiệu/case khi hết mục đích.
- **Auditability:** lưu dấu truy cập và hành động bàn giao ở mức phù hợp; không ghi nội dung tư vấn nhạy cảm vào audit log chung.

## 3. Phân tầng quyền truy cập

| Vai trò/tầng | Được thấy | Không được thấy hoặc làm |
|:-------------|:----------|:-------------------------|
| Ban Lãnh đạo/người review | Danh sách tín hiệu, dải ưu tiên, tóm tắt thay đổi, coverage/freshness, trạng thái case và metric tổng hợp | Raw risk score, trọng số model chi tiết, thuộc tính nhóm nhạy cảm của cá nhân; không tự động kỷ luật |
| GVCN/đơn vị hỗ trợ | Case đã duyệt thuộc phạm vi được giao, lý do trung lập và dữ liệu tối thiểu cần liên hệ | Case chưa duyệt, dữ liệu ngoài lớp/phạm vi, thuộc tính fairness, ghi chép nhạy cảm của đơn vị khác |
| Admin kỹ thuật/Data-ML | Bản trích xuất pseudonymized cần cho vận hành/kiểm định, log kỹ thuật | Danh tính thật gắn với score; không dùng tài khoản kỹ thuật để duyệt hay hỗ trợ case |
| Agent/LLM | Context đã được RBAC lọc, feature và output model được phép giải thích | Không truy cập nguồn ngoài quyền, không tự tính/sửa score, không tự gửi hoặc thay đổi trạng thái |

Việc phê duyệt nghĩa là phê duyệt **chuyển một tín hiệu tới người hỗ trợ**, không phải xác nhận một kết luận về sinh viên.

## 4. Care, not punish

- Đầu ra là **tín hiệu cần rà soát** thuộc về một case, không phải nhãn thuộc về sinh viên.
- UI dùng “mức độ ưu tiên rà soát”, “cần xem xét sớm” và “yếu tố đóng góp”; không dùng `high-risk student`, “cảnh báo đỏ” hay “model kết luận bỏ học”.
- Con người rà soát trước mọi bàn giao; GVCN/đơn vị hỗ trợ quyết định cách tiếp cận dựa trên bối cảnh thực tế.
- Email/thông báo do agent soạn chỉ là bản nháp trung lập và phải được người có trách nhiệm duyệt trước khi gửi.
- Silent Shield không tự động kỷ luật, hạn chế quyền lợi, thay đổi điểm, trạng thái học vụ hoặc ưu tiên dịch vụ.
- Sinh viên phải có kênh phản hồi dữ liệu sai và không bị bất lợi chỉ vì một case bị tạo.

## 5. Kiểm soát báo động giả và thiếu căn cứ

| Kiểm soát | Cách áp dụng |
|:----------|:-------------|
| Trend trước threshold | Ưu tiên so sinh viên với lịch sử của chính họ; ngưỡng tuyệt đối không đứng một mình |
| Coverage/depth | Hiển thị số kỳ hợp lệ, tỷ lệ thiếu và phạm vi nguồn; chặn tín hiệu khi không đủ căn cứ theo cấu hình |
| Data quality/freshness | Gắn cờ nguồn lỗi hoặc quá cũ; fail closed thay vì tạo case từ dữ liệu đáng ngờ |
| Ngoại lệ nghiệp vụ | Xử lý nghỉ có phép, bảo lưu, thay đổi lớp/mapping và đặc thù môn học trước hoặc trong bước review |
| Human review | Cho phép phê duyệt, loại, hoãn và lưu lý do; không tự động chuyển tiếp |
| Chống lặp | Không tạo lại case đã resolved/monitoring nếu không có thay đổi mới đủ ý nghĩa |
| Threshold transparency | Hiển thị tác động của ngưỡng tới precision/recall, FPR và số case cần review chỉ khi snapshot có nhãn/cỡ mẫu phù hợp |
| Feedback loop | Tổng hợp lý do loại và case sai để điều chỉnh dữ liệu/ngưỡng; không dùng phản hồi để tự học production ngoài kiểm soát |

Khi coverage thấp, im lặng có giải thích (`insufficient_data`) an toàn hơn một cảnh báo thiếu căn cứ. “Im lặng” không được hiển thị thành “ổn định”.

## 6. Fairness có thể đo

### Phạm vi MVP

- Chỉ đo trên thuộc tính nhóm đã được phê duyệt và ghi rõ source, thời điểm, cỡ mẫu/mẫu số cạnh mọi metric.
- Thuộc tính nhóm không được đưa vào scoring hoặc lời giải thích cá nhân.
- Hiển thị cỡ mẫu/mẫu số từng nhóm; không kết luận khi nhóm quá nhỏ hoặc ground truth không đủ.
- Metric tối thiểu: FPR theo nhóm và chênh lệch FPR lớn nhất–nhỏ nhất.
- Khi dữ liệu cho phép, hiển thị thêm precision, recall/TPR và selection rate theo nhóm để tránh tối ưu một metric duy nhất.

Demographic parity không tự động đồng nghĩa với công bằng; precision cao cũng không loại trừ bỏ sót. Mọi thay đổi ngưỡng phải xem đồng thời tác hại do false positive, false negative và tải công việc hỗ trợ.

### Điều kiện dừng/rà soát

MVP phải gắn cờ thay vì tuyên bố “fair” khi:

- không có nhãn ground truth để tính FPR/TPR;
- nhóm có cỡ mẫu quá nhỏ;
- chênh lệch metric vượt ngưỡng nội bộ đã công bố;
- dữ liệu thiếu không phân bố đều giữa các nhóm;
- cải thiện metric tổng thể làm một nhóm chịu báo động giả hoặc bỏ sót nhiều hơn đáng kể.

Ngưỡng nội bộ dùng cho demo phải được ghi cùng snapshot/model version; không chuyển nguyên sang nguồn hay bối cảnh khác.

## 7. Buffer tích cực

Nếu hậu MVP dùng tín hiệu tham gia tích cực, chúng chỉ được **giảm nhẹ** mức ưu tiên theo công thức có trần. Việc không tham gia CLB, thư viện, campus hoặc dịch vụ hỗ trợ không được làm tăng score. Buffer không được che mất tín hiệu học vụ mạnh và phải qua privacy/fairness review trước khi bật.

MVP không triển khai buffer và không tạo wellbeing score.

## 8. Ranh giới của agent

Agent được phép:

- tóm tắt dữ liệu đã cấp quyền;
- giải thích contributing factors do model/API trả về;
- nêu coverage, freshness và giới hạn;
- soạn câu hỏi hoặc email hỗ trợ trung lập.

Agent phải từ chối hoặc trả lời “không đủ dữ liệu” nếu bị yêu cầu chẩn đoán, suy đoán nguyên nhân, tạo risk score, quyết định bàn giao/kỷ luật hoặc truy cập dữ liệu ngoài phạm vi. Câu trả lời phải phân biệt rõ **dữ kiện**, **output model** và **giới hạn**.

## 9. Checklist trước pilot dữ liệu thật

- [ ] Mục đích, data owner, trường dữ liệu và thời hạn lưu được phê duyệt.
- [ ] Thông báo cho sinh viên và kênh sửa sai/khiếu nại đã được thiết kế.
- [ ] RBAC, audit log, mã hóa, backup và quy trình sự cố đã được kiểm thử.
- [ ] Model được validate/calibrate trên bối cảnh trường mục tiêu; không dùng kết quả reference/demo để suy rộng.
- [ ] Metric tổng thể và theo nhóm có cỡ mẫu, khoảng bất định và ngưỡng dừng.
- [ ] GVCN/đơn vị hỗ trợ xác nhận tải case và nội dung handoff khả thi.
- [ ] Có cơ chế tạm dừng scoring/handoff và quy trình review định kỳ.
- [ ] Không có dữ liệu bị cấm hoặc nguồn ứng viên chưa qua phê duyệt trong pipeline.
