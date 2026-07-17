# Các bên liên quan — Silent Shield

## 1. Cách đọc bản đồ stakeholder

Silent Shield phân biệt ba khái niệm không thể gộp chung:

- **Mức độ chịu ảnh hưởng:** hậu quả tích cực hoặc tiêu cực mà stakeholder có thể nhận từ hệ thống.
- **Quyền quyết định vận hành:** quyền phê duyệt, cấu hình hoặc thực hiện một bước trong quy trình.
- **Quyền liên quan đến dữ liệu:** mức độ stakeholder cần được thông báo, bảo vệ, giải thích, sửa sai hoặc tham gia quản trị dữ liệu.

Ban Lãnh đạo/Khoa/Viện là **primary system user** vì trực tiếp dùng dashboard và agent để rà soát. Họ không phải người dùng hay stakeholder duy nhất. GVCN, đơn vị hỗ trợ và sinh viên đều tham gia hoặc chịu tác động trực tiếp từ đầu ra.

## 2. Bản đồ tổng quan

| Stakeholder | Vai trò chính | Tương tác với hệ thống/quy trình | Mức độ chịu ảnh hưởng | Quyền quyết định vận hành | Quyền liên quan đến dữ liệu |
|:------------|:--------------|:--------------------------------|:-------------------------|:---------------------------|:----------------------------|
| Ban Lãnh đạo/Khoa/Viện | Primary system user; người phê duyệt chuyển tiếp | Xem báo cáo, rà bằng chứng, dùng agent, phê duyệt/loại/hoãn, điều phối | Rất cao | Cao | Cao trong phạm vi quản lý được cấp |
| Phòng Đào tạo | Data owner hoặc business process owner | Cấp và xác nhận dữ liệu học vụ; quản lý quy tắc học vụ, bảo lưu, nghỉ phép | Cao | Cao đối với dữ liệu và quy trình học vụ | Cao |
| Bộ phận CNTT | System owner và integration owner | Vận hành, phân quyền, giám sát đồng bộ, bảo mật và audit log | Cao | Cao đối với kỹ thuật | Cao đối với quản trị, không mặc nhiên có quyền xem nội dung case |
| GVCN/Cố vấn học tập | Người nhận handoff và thực hiện hỗ trợ | Nhận case đã duyệt theo lớp, liên hệ, xác nhận và phản hồi tối thiểu | Cao | Trung bình trong hoạt động hỗ trợ | Trung bình, giới hạn theo lớp/case được giao |
| Phòng CTSV/Tư vấn tâm lý | Đơn vị hỗ trợ hoặc chuyển tuyến | Nhận case khi phù hợp chuyên môn và ghi nhận hành động cần thiết | Cao | Trung bình trong phạm vi hỗ trợ | Trung bình, theo nguyên tắc cần biết |
| Sinh viên | Data subject và đối tượng thụ hưởng | Chịu tác động trực tiếp từ tín hiệu và hoạt động liên hệ | **Rất cao** | Thấp đối với vận hành hệ thống | **Cao** |
| Pháp chế/Bảo vệ dữ liệu/Hội đồng đạo đức | Privacy và fairness reviewer | Rà mục đích, dữ liệu, thời hạn lưu, thông báo, khiếu nại và chênh lệch nhóm | Cao | Cao đối với yêu cầu tuân thủ | Cao ở mức giám sát và kiểm tra |

## 3. Nhu cầu và trách nhiệm chi tiết

### Ban Lãnh đạo/Khoa/Viện

**Nhu cầu**

- Báo cáo tuần cho biết số tín hiệu mới, case đang theo dõi và tình trạng đồng bộ.
- Danh sách tín hiệu cần rà soát, không phải danh sách “sinh viên nguy cơ”.
- Bằng chứng giải thích: thay đổi nào, từ khi nào, dữ liệu có mới không và có ngoại lệ nào không.
- Agent để phân tích thêm từ dữ liệu được phép, không tự suy đoán hoặc tạo điểm.
- Chức năng phê duyệt, loại bỏ hoặc hoãn từng case và lưu lý do quyết định.

**Trách nhiệm và giới hạn**

- Phê duyệt việc chuyển tín hiệu tới đúng người hỗ trợ.
- Không dùng đầu ra để kỷ luật tự động hoặc coi tín hiệu là kết luận về sinh viên.
- Không chuyển tiếp dữ liệu vượt quá phạm vi người nhận cần biết.
- Không yêu cầu hoặc sử dụng raw risk score, trọng số model hay thuộc tính fairness của cá nhân để ra quyết định.
- Theo dõi khối lượng case, báo động giả và chênh lệch FPR giữa các nhóm.

### Phòng Đào tạo

**Nhu cầu**

- Kết nối nguồn SIS/điểm/chuyên cần ổn định, có kiểm tra chất lượng và độ mới.
- Phạm vi dữ liệu, chu kỳ đồng bộ và mục đích sử dụng được định nghĩa rõ.
- Quy tắc xử lý nghỉ có phép, bảo lưu và thay đổi lớp được phản ánh đúng.

**Trách nhiệm**

- Xác nhận tính đúng, đủ và định nghĩa nghiệp vụ của dữ liệu nguồn.
- Phối hợp sửa lỗi mapping và routing.
- Không cung cấp dữ liệu ngoài phạm vi cần thiết cho mục đích chăm sóc đã thống nhất.

### Bộ phận CNTT

**Nhu cầu**

- Kiến trúc tích hợp không ảnh hưởng hệ thống lõi.
- Cơ chế phân quyền, audit log, cảnh báo lỗi và quy trình xử lý sự cố rõ ràng.

**Trách nhiệm**

- Vận hành đồng bộ, bảo mật, sao lưu và kiểm soát truy cập.
- Hiển thị trạng thái lỗi/độ trễ thay vì để hệ thống âm thầm dùng dữ liệu cũ.
- Bảo đảm tài khoản kỹ thuật không được sử dụng để đọc case ngoài nhiệm vụ.
- Tách thuộc tính nhóm phục vụ fairness audit khỏi feature scoring và màn hình case cá nhân.

### GVCN/Cố vấn học tập

GVCN không nhất thiết phải thường xuyên đăng nhập dashboard. Điểm chạm tối thiểu gồm:

- nhận danh sách case **đã được Ban Lãnh đạo phê duyệt** theo lớp mình phụ trách;
- nhận tóm tắt trung lập về thay đổi cần quan tâm và độ mới dữ liệu;
- nhận email nháp do hệ thống hỗ trợ soạn, nhưng tự rà soát trước khi gửi;
- xác nhận đã tiếp nhận;
- liên hệ sinh viên với mục đích hỗ trợ, không đề cập nhãn hay kết luận;
- phản hồi kết quả ở mức tối thiểu để cập nhật trạng thái và tránh tín hiệu lặp.

GVCN cần có cách báo sai người, sai lớp, nghỉ có phép hoặc case không còn phù hợp mà không phải nhập liệu dài.

### Phòng CTSV/Tư vấn tâm lý

- Chỉ nhận case khi có phê duyệt và việc chuyển tuyến phù hợp với chức năng.
- Chỉ nhận thông tin tối thiểu cần thiết cho hoạt động hỗ trợ.
- Tự đánh giá chuyên môn; không dùng tín hiệu của Silent Shield như một chẩn đoán.
- Phản hồi trạng thái đủ để phối hợp, không đưa ghi chép tư vấn nhạy cảm vào dashboard chung.

### Sinh viên

Sinh viên có quyền quyết định vận hành thấp nhưng mức độ chịu ảnh hưởng và quyền liên quan đến dữ liệu rất cao. Thiết kế và quản trị cần bảo đảm:

- thông tin về mục đích và phạm vi sử dụng dữ liệu dễ hiểu;
- không hiển thị công khai nhãn “nguy cơ cao” hoặc suy đoán về hoàn cảnh;
- có kênh phản hồi hoặc sửa thông tin học vụ sai;
- hoạt động liên hệ mang tính hỗ trợ, không đe dọa hay trừng phạt;
- hạn chế người có thể truy cập và lưu dấu các lần xem/chuyển tiếp;
- có quy trình tiếp nhận khiếu nại hoặc phản ánh tác động không mong muốn.

### Pháp chế/Bảo vệ dữ liệu/Hội đồng đạo đức

- Rà soát mục đích, tính cần thiết, thời hạn lưu giữ và quyền truy cập.
- Kiểm tra cách truyền thông với sinh viên và quy trình phản hồi/sửa sai.
- Rà metric fairness, đặc biệt chênh lệch FPR, trước khi thay đổi ngưỡng hoặc mở rộng phạm vi.
- Có quyền yêu cầu tạm dừng một luồng xử lý nếu rủi ro dữ liệu hoặc tác động chưa được kiểm soát.

## 4. Quyền quyết định theo bước

| Quyết định | Người chịu trách nhiệm chính | Bên cần tham vấn | Giới hạn bắt buộc |
|:-----------|:----------------------------|:-----------------|:------------------|
| Phạm vi và tần suất đồng bộ dữ liệu | Phòng Đào tạo + CNTT | Bảo vệ dữ liệu, Ban Lãnh đạo | Tối thiểu hóa dữ liệu; hiển thị độ mới |
| Ngưỡng tạo tín hiệu/ưu tiên rà soát | Chủ sản phẩm/Ban Lãnh đạo | Data/ML, GVCN, fairness reviewer | Dựa trên baseline; theo dõi FPR và tải công việc |
| Phê duyệt chuyển một case | Ban Lãnh đạo/người được ủy quyền | Agent chỉ hỗ trợ giải thích | Con người quyết định; lưu lý do |
| Phân công case | Ban Lãnh đạo hoặc quy tắc routing đã duyệt | Phòng Đào tạo, GVCN | Chỉ chuyển đúng lớp và đúng phạm vi cần biết |
| Nội dung liên hệ sinh viên | GVCN/đơn vị hỗ trợ | Hệ thống chỉ soạn nháp | Trung lập, chăm sóc, không gắn nhãn |
| Kết thúc hoặc tiếp tục theo dõi case | GVCN + người quản lý quy trình | Đơn vị hỗ trợ khi cần | Cập nhật trạng thái case, không tạo thuộc tính cố định cho sinh viên |
| Kỷ luật/quyết định học vụ bất lợi | Quy trình học vụ độc lập | Các bên có thẩm quyền theo quy định | Silent Shield không tự động đề xuất hoặc quyết định |

## 5. Stakeholder cần xác nhận trước pilot

1. Ban Lãnh đạo: tiêu chí phê duyệt/loại/hoãn và tải review tối đa mỗi tuần.
2. GVCN: nội dung bàn giao tối thiểu, kênh nhận và thao tác phản hồi khả thi.
3. Phòng Đào tạo/CNTT: trường nguồn, độ mới, ngoại lệ nghiệp vụ và mapping lớp–GVCN.
4. Sinh viên hoặc đại diện sinh viên: mức độ dễ hiểu, cảm nhận về ngôn ngữ liên hệ và cơ chế sửa sai.
5. CTSV/Tư vấn: điều kiện chuyển tuyến và ranh giới dữ liệu nhạy cảm.
6. Bảo vệ dữ liệu/fairness reviewer: phân quyền, lưu giữ, metric nhóm và ngưỡng dừng.
