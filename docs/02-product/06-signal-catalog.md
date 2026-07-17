# Danh mục tín hiệu và phạm vi dữ liệu — Silent Shield

## 1. Mục đích

Tài liệu này tách danh mục tín hiệu dài hạn trong [Problems Brief](../01-requirements/02-problems-brief.md) khỏi phạm vi 48 giờ của [PRD](04-prd.md). Một tín hiệu xuất hiện trong brief **không đồng nghĩa** với việc đã được phê duyệt để thu thập, đưa vào model hoặc hiển thị trên UI.

Mỗi tín hiệu phải đi qua bốn cổng trước khi sử dụng: có mục đích chăm sóc rõ ràng, nguồn dữ liệu hợp lệ, bằng chứng đủ phù hợp với bối cảnh triển khai và kiểm soát privacy/fairness khả thi.

## 2. Phạm vi MVP đã chốt

| ID | Tín hiệu | Biểu diễn trong MVP | Nguồn synthetic | Trạng thái |
|:---|:---------|:--------------------|:-----------------|:-----------|
| CORE-01 | Xu hướng điểm | Độ dốc điểm theo tuần | `grades_timeseries.csv` | MVP |
| CORE-02 | Biến động điểm | Mức dao động trong cửa sổ quan sát | `grades_timeseries.csv` | MVP |
| CORE-03 | Mức chuyên cần | Tỷ lệ chuyên cần trong cửa sổ quan sát | `attendance_timeseries.csv` | MVP |
| CORE-04 | Xu hướng chuyên cần | Độ dốc tỷ lệ chuyên cần theo tuần | `attendance_timeseries.csv` | MVP |
| META-01 | Độ phủ dữ liệu | Số kỳ hợp lệ, tỷ lệ thiếu và phạm vi thời gian | Cả hai chuỗi thời gian | MVP, không dùng như tín hiệu rủi ro độc lập |
| AUDIT-01 | Nhóm kinh tế synthetic | Chỉ phân nhóm metric fairness | `students.csv` | Audit only, cấm dùng để scoring |
| AUDIT-02 | Nhóm dân tộc synthetic | Chỉ phân nhóm metric fairness | `students.csv` | Audit only, cấm dùng để scoring |

MVP ưu tiên thay đổi so với lịch sử của chính sinh viên. Ngưỡng tuyệt đối, nếu có, chỉ là điều kiện hỗ trợ và phải được demo cùng tác động tới false positive/false negative.

## 3. Ứng viên tín hiệu học vụ hậu MVP

Brief gọi đây là “12 tiêu chí” nhưng bảng nguồn có thêm một dòng “thời gian vào lớp” không đánh số. Danh mục dưới đây gán ID ổn định để tránh phụ thuộc vào số thứ tự bị lệch trong bản nguồn.

| ID | Tín hiệu trong brief | Nguồn dự kiến | Cách dùng an toàn nếu được duyệt | Trạng thái |
|:---|:---------------------|:---------------|:-------------------------------|:-----------|
| CAND-01 | GPA và xu hướng GPA | SIS | Ưu tiên delta theo kỳ; ngưỡng tuyệt đối không đứng một mình | Hậu MVP |
| CAND-02 | Tín chỉ tích lũy và môn không đạt | SIS | So với kế hoạch học tập và ngoại lệ học vụ đã xác nhận | Hậu MVP |
| CAND-03 | Credit momentum | SIS | So với tiến độ chương trình/cohort ẩn danh; rà bias theo ngành/hệ | Hậu MVP |
| CAND-04 | Hoạt động LMS | Metadata LMS | Chỉ tần suất/khoảng hoạt động; không đọc nội dung; ưu tiên within-student | Hậu MVP, cần privacy review |
| CAND-05 | Nộp bài và thời điểm nộp | LMS gradebook | Chỉ trạng thái/timing, không đánh giá nội dung bài | Hậu MVP |
| CAND-06 | Chuyên cần và vắng thi | Điểm danh/khảo thí | Xử lý nghỉ có phép, lỗi điểm danh và đặc thù môn trước khi tạo case | Một phần đã có trong MVP |
| CAND-07 | Thời gian vào lớp | Điểm danh theo giờ | Chỉ xu hướng đi muộn; cần xác minh chất lượng bằng chứng và ngoại lệ | Chưa duyệt |
| CAND-08 | Tiến độ so với cohort | SIS | Dùng thống kê cohort đủ lớn; hiển thị giới hạn khi chương trình khác nhau | Hậu MVP |
| CAND-09 | Hành vi đăng ký học phần | Log đăng ký | Không diễn giải việc giảm tải là disengagement nếu chưa rà bối cảnh | Hậu MVP |
| CAND-10 | Trạng thái cảnh báo/bảo lưu | Hồ sơ học vụ | Dùng như ngoại lệ/quy tắc nghiệp vụ có thời hạn, không thành nhãn cố định | Hậu MVP |
| CAND-11 | Chuyển ngành/chuyển hệ | Hồ sơ học vụ | Không mặc định là tín hiệu xấu; cần đánh giá mục đích và disparate impact | Chưa duyệt |
| CAND-12 | Tương tác với hệ thống hỗ trợ | Metadata lịch hẹn/thông báo | Không đọc nội dung; tuyệt đối tách dữ liệu tư vấn nhạy cảm | Chưa duyệt |
| CAND-13 | Điểm giữa kỳ/quiz | Gradebook | Dùng để nhận biết sớm trong kỳ; phải chuẩn hóa khác biệt môn học | Hậu MVP |

“Hậu MVP” chỉ có nghĩa là ứng viên phát triển tiếp, không phải cam kết triển khai. Các trích dẫn học thuật trong brief chưa được kiểm chứng độc lập trong repo và không thay thế bước validation trên bối cảnh trường cụ thể.

## 4. Tín hiệu tích cực và buffer

Phụ lục brief đề xuất dùng tham gia CLB, thư viện, hiện diện campus, workshop và dịch vụ hỗ trợ như **buffer**. Silent Shield áp dụng nguyên tắc bất đối xứng:

- có bằng chứng tham gia có thể giảm nhẹ mức ưu tiên sau khi được kiểm định;
- không có bằng chứng tham gia **không bao giờ** làm tăng mức ưu tiên;
- buffer không được xóa hoặc thay thế các tín hiệu học vụ chính;
- tổng tác động phải có trần và phải được fairness review;
- không suy ra sự cô lập, sức khỏe tinh thần hoặc hoàn cảnh từ việc không xuất hiện trong log.

| ID | Buffer/tín hiệu bổ sung | Rủi ro chính | Quyết định hiện tại |
|:---|:------------------------|:-------------|:--------------------|
| BUF-01 | Tham gia CLB/sự kiện | Bất lợi cho sinh viên đi làm, học từ xa hoặc không tham gia hoạt động chính thức | Không dùng trong MVP |
| BUF-02 | Dừng đột ngột hoạt động ngoại khóa | Dễ bị diễn giải thành tín hiệu wellbeing không có căn cứ | Không dùng; cần ethics review riêng |
| BUF-03 | Sử dụng thư viện | Không dùng thư viện không đồng nghĩa thiếu gắn kết | Không dùng trong MVP |
| BUF-04 | Hiện diện campus qua Wi-Fi/RFID | Có tính theo dõi vị trí và rủi ro xâm phạm cao | Không thu thập trong MVP |
| BUF-05 | Workshop/seminar học thuật | Log không đầy đủ và khác biệt cơ hội tiếp cận | Không dùng trong MVP |
| BUF-06 | Dịch vụ tutoring/mentoring/career | Nguy cơ trộn với dữ liệu tư vấn nhạy cảm | Không dùng; cấm dữ liệu tư vấn tâm lý |

Không triển khai công thức `Final_W` trong brief: MVP không tạo wellbeing score và không chẩn đoán khủng hoảng.

## 5. Coverage, depth và điều kiện im lặng

Mỗi feature phải đi kèm:

- cửa sổ thời gian và số quan sát hợp lệ;
- tỷ lệ thiếu, bản ghi lỗi và thời điểm dữ liệu mới nhất;
- phạm vi nguồn: một môn, một lớp hay toàn chương trình;
- giới hạn so sánh do khác biệt môn học/cohort;
- ngoại lệ đã biết như nghỉ có phép, bảo lưu hoặc mapping sai.

Khi dữ liệu không đủ, hệ thống phải trả về `insufficient_data` hoặc hạ độ tin cậy và chặn tạo tín hiệu theo cấu hình. Không được biến “không có dữ liệu” thành “ổn định”, cũng không được dùng một nguồn cục bộ để kết luận toàn cục.

## 6. Quy trình đưa tín hiệu mới vào hệ thống

1. Ghi rõ mục đích chăm sóc và quyết định mà tín hiệu sẽ hỗ trợ.
2. Xác nhận data owner, quyền sử dụng, độ mới, retention và cơ chế sửa sai.
3. Kiểm tra chất lượng bằng chứng; ghi rõ quần thể và bối cảnh nghiên cứu.
4. Thiết kế feature ưu tiên trend/within-student và các ngoại lệ nghiệp vụ.
5. Đánh giá precision, recall, FPR, coverage và chênh lệch nhóm trên dữ liệu phù hợp.
6. Review với Ban Lãnh đạo, GVCN, đại diện sinh viên và privacy/fairness reviewer.
7. Chạy thử có giám sát; có kill switch và tiêu chí rút tín hiệu nếu gây hại hoặc không hữu ích.

Mọi thay đổi danh mục phải cập nhật đồng thời PRD, model contract, data dictionary, UI copy và tài liệu demo.
