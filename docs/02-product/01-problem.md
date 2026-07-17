# Bài toán sản phẩm — Silent Shield

## 1. Mục đích tài liệu

Tài liệu xác định bài toán kinh doanh và giáo dục mà Silent Shield cần giải quyết. Nội dung được chuẩn hóa từ [Problems Brief](../01-requirements/02-problems-brief.md); cách ánh xạ sang các tài liệu vận hành xem tại [Truy vết yêu cầu](../01-requirements/03-traceability.md).

Phạm vi của sản phẩm là hỗ trợ nhà trường nhận ra sớm các thay đổi đáng chú ý trong dữ liệu học tập để con người cân nhắc hoạt động chăm sóc phù hợp. Ban Lãnh đạo Khoa/Trường là người dùng hệ thống chính; GVCN/cố vấn và đơn vị hỗ trợ tham gia sau bước rà soát, không phải gánh thêm một luồng giám sát liên tục.

Silent Shield không chẩn đoán sức khỏe tâm thần, không gắn nhãn sinh viên và không tự động đưa ra quyết định ảnh hưởng đến sinh viên.

## 2. Problem Statement

> Nhà trường gặp khó khăn trong việc nhận diện sớm những thay đổi đáng chú ý trong quá trình học tập của sinh viên do dữ liệu phân tán và giáo viên quá tải. Điều này khiến các trường hợp có nguy cơ bỏ học hoặc cần được hỗ trợ thường chỉ được chú ý khi vấn đề đã trở nên nghiêm trọng.

### Bối cảnh

Thông tin về điểm số, chuyên cần và mức độ tham gia học tập thường nằm ở nhiều hệ thống hoặc tệp theo dõi khác nhau. GVCN/cố vấn học tập phải dựa chủ yếu vào quan sát và kinh nghiệm trong khi vẫn đảm nhiệm giảng dạy và công việc hành chính. Vì vậy, những thay đổi diễn ra từ từ hoặc không biểu hiện rõ có thể bị bỏ sót cho đến cuối kỳ.

### Đối tượng chịu ảnh hưởng

- Sinh viên chịu tác động trực tiếp nếu nhu cầu hỗ trợ không được nhận ra kịp thời hoặc nếu một tín hiệu sai bị sử dụng không đúng mục đích.
- GVCN/cố vấn học tập thiếu một bức tranh tổng hợp để ưu tiên hoạt động quan tâm và hỗ trợ.
- Ban Lãnh đạo/Khoa/Viện thiếu báo cáo nhất quán để rà soát, điều phối và đánh giá hiệu quả quy trình chăm sóc.
- Các đơn vị dữ liệu và hỗ trợ phải phối hợp thủ công, khiến việc bàn giao chậm hoặc không rõ trách nhiệm.

## 3. Định nghĩa đầu ra sản phẩm

> Tín hiệu cần rà soát là đầu ra được tạo từ sự thay đổi bất thường trong dữ liệu học tập theo thời gian, nhằm hỗ trợ người có trách nhiệm quyết định liệu sinh viên có cần được quan tâm hoặc liên hệ hay không.

Tín hiệu thuộc về một **case trong quy trình rà soát**, không phải trạng thái, đặc điểm hay kết luận về sinh viên. Hệ thống có thể tính một giá trị nội bộ để xếp thứ tự, nhưng trên giao diện giá trị này phải được gọi là **mức độ ưu tiên rà soát** và luôn đi kèm:

- điều gì đã thay đổi và thay đổi từ khi nào;
- nguồn dữ liệu, độ mới và tình trạng chất lượng dữ liệu;
- các yếu tố đóng góp có thể kiểm chứng;
- mức độ tin cậy hoặc giới hạn của tín hiệu;
- ngoại lệ nghiệp vụ đã biết, nếu có.

### Thuật ngữ sử dụng nhất quán

| Không dùng | Dùng trong tài liệu và giao diện |
|:-----------|:--------------------------------|
| Danh sách sinh viên có nguy cơ | Danh sách tín hiệu cần rà soát |
| Risk score | Mức độ ưu tiên rà soát |
| Cảnh báo đỏ | Tín hiệu ưu tiên |
| Sinh viên nguy cơ cao | Trường hợp cần được xem xét sớm |
| Model predicts dropout | Hệ thống phát hiện thay đổi tương đồng với các mẫu cần quan tâm |
| Approve student | Phê duyệt việc chuyển tín hiệu tới người hỗ trợ |

## 4. Mục tiêu và kết quả kỳ vọng

1. **Nhận biết sớm hơn:** tổng hợp biến động điểm số và chuyên cần/hành vi học tập theo thời gian để đưa các trường hợp cần chú ý vào quy trình rà soát trước khi vấn đề trở nên nghiêm trọng. **MVP** dùng điểm theo học kỳ + điểm danh theo thời gian — xem [PRD §4](04-prd.md).
2. **Mở rộng vùng phủ chăm sóc:** giúp GVCN/cố vấn học tập tiếp cận cả những sinh viên ít biểu hiện ra bên ngoài nhưng có thay đổi đáng chú ý trong quá trình học.
3. **Giảm tải có kiểm soát:** chỉ đưa ra tín hiệu mới hoặc có thay đổi, hạn chế lặp lại case đã xử lý và đo khối lượng công việc phát sinh.
4. **Hỗ trợ quyết định có giải thích:** cung cấp bằng chứng để Ban Lãnh đạo phê duyệt, loại bỏ hoặc hoãn việc chuyển tiếp; không thay thế nhận định của con người.
5. **Bảo vệ quyền và lợi ích của sinh viên:** giảm báo động giả, kiểm tra chênh lệch hiệu năng giữa các nhóm và chỉ sử dụng đầu ra cho mục đích chăm sóc.

## 5. Phạm vi dữ liệu

### Được phép sử dụng

- Điểm theo học kỳ và xu hướng điểm khi một hồ sơ có ít nhất hai học kỳ hợp lệ.
- Điểm danh / chuyên cần theo thời gian từ nguồn được phê duyệt (`H15`); thiếu nguồn → `insufficient_data`, không bịa chuỗi.
- Trạng thái học vụ và mapping cố vấn học tập trong bản trích xuất EPU đã được phê duyệt, chỉ ở mức tối thiểu cho evaluation/routing.
- Dữ liệu hành vi học tập tổng hợp như tần suất đăng nhập LMS, mức độ hoàn thành hoặc nộp bài trễ **chỉ khi đã được phê duyệt cho giai đoạn sau MVP**.
- Các trường dữ liệu đã pseudonymize cần thiết để phân lớp, xác định người nhận case và chuyển đúng đơn vị hỗ trợ.
- Thuộc tính nhóm phục vụ fairness chỉ khi có nguồn được phê duyệt; không dùng làm nguyên nhân suy đoán cho một cá nhân.

MVP dùng bản trích xuất đã qua data gate, pseudonymize và chỉ có các trường trong [hợp đồng tích hợp](../04-engineering/04-epu-data-integration-contract.md). Điểm danh theo thời gian thuộc MVP; nếu catalog hiện chưa có chuỗi đã duyệt thì phải lấy nguồn qua `H15`, không đẩy ra Post-MVP và không tạo feature giả. Danh mục mở rộng không phải cam kết triển khai; xem [Danh mục tín hiệu](06-signal-catalog.md).

### Không thu thập hoặc suy luận

- Nội dung tin nhắn, email, cuộc gọi hoặc trao đổi riêng tư.
- Camera, micro, mạng xã hội hoặc công cụ theo dõi thiết bị.
- Chẩn đoán hay nguyên nhân như trầm cảm, bắt nạt, khó khăn tài chính, hoàn cảnh gia đình hoặc đặc điểm dân tộc.

## 6. Nguyên tắc sử dụng đầu ra

- Tín hiệu không phải kết luận về tình trạng của sinh viên.
- Hệ thống không chẩn đoán sức khỏe tâm thần và không xác định nguyên nhân của thay đổi.
- Sinh viên không bị hiển thị công khai là “nguy cơ cao”.
- Mọi tín hiệu phải được người có trách nhiệm rà soát trước khi chuyển tiếp.
- Việc phê duyệt chỉ có nghĩa là phê duyệt **chuyển tín hiệu tới người hỗ trợ**, không phải phê duyệt hay đánh giá sinh viên.
- Không tự động áp dụng kỷ luật, hạn chế quyền lợi hoặc ra quyết định học vụ bất lợi.
- Không tự động gửi nội dung nhạy cảm cho GVCN hoặc sinh viên khi chưa được người có thẩm quyền duyệt.
- Mọi liên hệ với sinh viên phải dùng ngôn ngữ trung lập, hỗ trợ và không nêu rằng sinh viên “có nguy cơ bỏ học”.

## 7. Giới hạn của agent

Agent chỉ được hoạt động trên dữ liệu mà người dùng có quyền truy cập và có thể:

- tóm tắt biến động dữ liệu;
- so sánh với lịch sử của chính sinh viên;
- giải thích các yếu tố đã đóng góp vào tín hiệu do model/API cung cấp;
- trả lời câu hỏi có căn cứ từ dữ liệu được phép;
- soạn email hỗ trợ bằng ngôn ngữ trung lập;
- gợi ý câu hỏi để GVCN trao đổi với sinh viên.

Agent không được tự tạo hoặc thay đổi điểm của model, chẩn đoán, suy đoán hoàn cảnh, quyết định kỷ luật, tự kết luận tín hiệu là đúng hoặc tự gửi email nhạy cảm. Chi tiết nguyên tắc sản phẩm xem tại [Ethics](05-ethics.md).

## 8. Giả định và ràng buộc

- Dữ liệu nguồn có mã sinh viên và thông tin lớp đủ nhất quán để ghép nối và bàn giao đúng người.
- Chu kỳ đồng bộ theo snapshot/kỳ học mà source đã phê duyệt cấp; độ mới phải được hiển thị trên báo cáo.
- Dữ liệu thiếu, lỗi hoặc quá cũ phải làm giảm độ tin cậy và có thể chặn tạo tín hiệu mới.
- Nghỉ có phép, bảo lưu và case đang được xử lý cần được dùng để giảm báo động giả và cảnh báo lặp.
- Ngưỡng và chỉ số fairness chỉ được đánh giá khi data gate có nhãn, nhóm audit được phê duyệt và cỡ mẫu đủ; không tuyên bố hiệu quả ngoài phạm vi snapshot đã kiểm chứng.
- Ban Lãnh đạo là người dùng hệ thống chính nhưng không phải stakeholder hay người tham gia quy trình duy nhất.

## 9. Success metrics

Các ngưỡng chấp nhận cần được chốt sau khi có baseline trên snapshot EPU đã được duyệt và xác nhận của stakeholder; không chọn mục tiêu chỉ để làm đẹp số liệu.

| Nhóm | Chỉ số | Cách sử dụng |
|:-----|:-------|:-------------|
| Chất lượng | Precision/recall trên snapshot có nhãn đã được duyệt | Đánh giá khả năng tìm đúng mẫu cần quan tâm và mức bỏ sót ở ngưỡng đang dùng; không tính khi nhãn/cỡ mẫu thiếu |
| Báo động giả | False-positive rate (FPR) | Kiểm soát tỷ lệ trường hợp bị đưa ra rà soát nhưng bị xác nhận không cần chuyển tiếp |
| Khối lượng | Số tín hiệu mới mỗi kỳ đồng bộ | Theo dõi tải đầu vào của Ban Lãnh đạo và phát hiện tăng bất thường |
| Rà soát | Tỷ lệ được phê duyệt chuyển tiếp | Kiểm tra mức hữu ích của tín hiệu đối với quy trình chăm sóc |
| Rà soát | Tỷ lệ bị loại sau rà soát | Phân tích nguyên nhân để điều chỉnh ngưỡng, dữ liệu hoặc ngoại lệ nghiệp vụ |
| Tốc độ | Thời gian từ khi phát sinh tín hiệu đến khi con người xem xét | Đo khả năng nhận biết và phản hồi sớm |
| Bàn giao | Tỷ lệ chuyển đúng GVCN/đơn vị phụ trách | Kiểm tra chất lượng phân lớp và routing |
| Fairness | Chênh lệch FPR giữa các nhóm audit được phê duyệt | Chỉ hiển thị khi có nhóm, nhãn và cỡ mẫu đủ; nếu không trả `insufficient_data` |
| Tải công việc | Số case mới và case đang xử lý trên mỗi GVCN/kỳ đồng bộ | Ngăn hệ thống tạo khối lượng hỗ trợ không khả thi |
| Dữ liệu | Tỷ lệ nguồn đồng bộ đúng hạn và độ trễ dữ liệu | Tránh đưa tín hiệu từ dữ liệu lỗi hoặc quá cũ |

Retention rate và mức hài lòng với dịch vụ hỗ trợ là outcome dài hạn được đề xuất trong brief, không phải acceptance của MVP. Chỉ được dùng để đánh giá tác động sau khi có pilot, baseline, thời gian theo dõi và thiết kế đo lường phù hợp; không được trình bày như kết quả đã đạt.
