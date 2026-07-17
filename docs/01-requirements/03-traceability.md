# Truy vết yêu cầu — Problems Brief → Silent Shield

## 1. Phạm vi đối chiếu

Tài liệu này ghi cách các yêu cầu trong `Problems_Brief` được chuyển thành tài liệu và phạm vi thực thi của Silent Shield. Tại thời điểm đối chiếu, file `Problems_Brief.docx` được nhắc tới trong IDE không có trên filesystem của workspace; nội dung được đọc từ [bản Markdown đã chuyển vào docs](02-problems-brief.md).

Bản Markdown được giữ làm nguồn tham chiếu, chỉ chuẩn hóa tiêu đề và vị trí file. PRD và các tài liệu product là bản vận hành đã được chuẩn hóa, không phải bản sao nguyên văn của brief.

## 2. Bản đồ yêu cầu

| Phần trong brief | Yêu cầu cốt lõi | Tài liệu vận hành | Trạng thái |
|:-----------------|:----------------|:------------------|:-----------|
| C.1–C.2 | Phát hiện quá muộn do dữ liệu phân tán và người phụ trách quá tải | [Bài toán](../02-product/01-problem.md), [Quy trình](../02-product/03-process.md) | Đã phản ánh |
| C.3 | Privacy, care, no labeling/no automatic discipline, fairness nhóm | [Ethics](../02-product/05-ethics.md), [PRD](../02-product/04-prd.md) | Bắt buộc trong MVP |
| C.4 | Kiểm soát false/missing alarm, fairness, handoff con người | [PRD](../02-product/04-prd.md), [Quy trình](../02-product/03-process.md) | Có acceptance cụ thể |
| D.1 | Agent là lớp triage; không chẩn đoán/kết luận/kỷ luật | [Bài toán](../02-product/01-problem.md), [Ethics](../02-product/05-ethics.md) | Đã phản ánh |
| D.2 | Ban Lãnh đạo là primary system user; GVCN thực thi case được giao | [Stakeholders](../02-product/02-stakeholders.md), [PRD](../02-product/04-prd.md) | Đã chuẩn hóa |
| D.3–D.3.1 | Metadata có sẵn, purpose limitation, minimization, phân tầng quyền | [Ethics](../02-product/05-ethics.md) | MVP synthetic; pilot thật cần phê duyệt |
| D.4 | Danh mục tín hiệu học vụ | [Danh mục tín hiệu](../02-product/06-signal-catalog.md) | Chỉ điểm + chuyên cần trong MVP |
| D.5.1 | D0–D3 và hành động gợi ý | [PRD](../02-product/04-prd.md), [Quy trình](../02-product/03-process.md) | Chuyển thành mức ưu tiên của **case**, không phải nhãn sinh viên |
| D.5.2 | Coverage/depth; ưu tiên within-student; im lặng khi thiếu dữ liệu | [Danh mục tín hiệu](../02-product/06-signal-catalog.md), [Ethics](../02-product/05-ethics.md) | Bắt buộc hiển thị/kiểm soát |
| E.1–E.2 | Mở rộng vùng chăm sóc; giảm bỏ học và tăng gắn bó | [Bài toán](../02-product/01-problem.md) | Outcome dài hạn, không tuyên bố đạt trong MVP |
| E.3 | KPI hiệu quả, false alarm, fairness, handoff, retention | [Bài toán](../02-product/01-problem.md), [PRD](../02-product/04-prd.md) | Metric MVP tách khỏi KPI dài hạn |
| Phụ lục 20–25 | Tín hiệu tích cực/buffer | [Danh mục tín hiệu](../02-product/06-signal-catalog.md), [Ethics](../02-product/05-ethics.md) | Không dùng trong MVP |

## 3. Các quyết định diễn giải

### 3.1 “Risk” là ưu tiên case, không phải thuộc tính sinh viên

Brief dùng `Dropout Risk`, `D0–D3`, “điểm rủi ro” và đồng thời yêu cầu no labeling. Để hai yêu cầu không xung đột:

- model có thể giữ score nội bộ để xếp thứ tự;
- UI nghiệp vụ chỉ hiển thị **mức độ ưu tiên rà soát** và bằng chứng thay đổi;
- D0–D3 không được lưu hoặc nói như trạng thái cố định của sinh viên;
- trạng thái vận hành là `New Signal`, `Pending Review`, `Approved for Follow-up`, `Assigned`, `Resolved`… theo [Quy trình](../02-product/03-process.md).

### 3.2 Giải thích không đồng nghĩa lộ raw score

Brief yêu cầu giải thích yếu tố đóng góp nhưng tầng Ban Lãnh đạo không được thấy raw score/breakdown chi tiết. Vì vậy UI hiển thị tóm tắt có thể kiểm chứng như “điểm giảm trong 4 tuần” và “chuyên cần giảm”, cùng coverage/freshness; không hiển thị trọng số model hay thuộc tính fairness của cá nhân.

### 3.3 Fairness attribute chỉ dùng cho audit

Nhóm kinh tế/dân tộc synthetic phục vụ tính metric nhóm, không phải feature scoring và không được dùng để giải thích nguyên nhân cho một case. Kết quả synthetic chỉ chứng minh pipeline đo được fairness, không chứng minh hệ thống production đã công bằng.

### 3.4 Buffer chỉ bất đối xứng và không thuộc MVP

Việc có tín hiệu tham gia tích cực có thể được nghiên cứu như buffer; việc không có log không được làm tăng mức ưu tiên. Wi-Fi/RFID, CLB, thư viện và log hỗ trợ có privacy/bias risk nên bị loại khỏi MVP dù xuất hiện trong phụ lục brief.

### 3.5 Không có wellbeing score trong MVP

Brief nhắc tới `Final_W` nhưng không định nghĩa đầy đủ nhãn, ground truth hay quy trình kiểm định cho wellbeing. MVP chỉ phát hiện thay đổi học tập cần rà soát, không tạo W-score, chẩn đoán khủng hoảng hoặc suy đoán sức khỏe tâm thần.

## 4. Độ lệch còn mở giữa brief và scaffold

| Độ lệch | Hiện trạng | Cách xử lý tài liệu | Việc kỹ thuật cần chốt |
|:--------|:-----------|:--------------------|:-----------------------|
| Bối cảnh đại học vs dữ liệu demo K-12 | Brief dùng sinh viên, GPA/tín chỉ và Ban Lãnh đạo Khoa/Trường; [generator](../../backend/app/ml/early_warning/synthetic.py) hiện dùng lớp `10A1`–`12C1` | Product docs theo bối cảnh brief; README dữ liệu ghi rõ artifact demo | Đổi dataset sang cohort đại học hoặc công bố rõ demo domain trước khi quay video |
| Primary user | Brief chọn Ban Lãnh đạo; PRD cũ đặt GVCN ở trung tâm dashboard | PRD/stakeholder/process đã lấy Ban Lãnh đạo làm primary user | UI/routing cần khớp luồng review trước handoff |
| Phạm vi tín hiệu | Brief liệt kê 13 dòng học vụ và 6 tín hiệu bổ sung; data hiện chỉ có điểm/chuyên cần | Tách catalog dài hạn khỏi MVP | Không tạo UI giả cho nguồn chưa có |
| Coverage/depth | Brief yêu cầu nhưng [feature contract](../../backend/app/ml/early_warning/types.py) hiện chưa thể hiện đầy đủ | Đưa vào PRD/ethics/catalog | Bổ sung contract/API/UI hoặc ghi rõ limitation trong demo |
| Output D0–D3 | [Dashboard mock](../../frontend/src/app/dashboard/page.tsx) còn hiển thị “Điểm rủi ro” và raw score | Chuyển thành ưu tiên của case và trạng thái workflow | Đổi copy/UI/API public, ẩn raw score và đổi tên `risk list` trước demo |
| Fairness ground truth | Dataset có group synthetic nhưng chưa thể hiện nhãn outcome trong ba CSV | PRD yêu cầu metric chỉ khi có ground truth và mẫu số rõ | Bổ sung synthetic outcome/label hoặc không gọi metric là FPR |

## 5. Trạng thái nguồn và bằng chứng

- Các ngưỡng, công thức và trích dẫn học thuật trong brief là đề xuất đầu vào, chưa mặc nhiên là yêu cầu đã kiểm định.
- Repo chưa có bibliography đầy đủ hoặc liên kết nguồn cho các nghiên cứu được nêu trong brief; không dùng các con số đó trong slide như fact đã xác minh nếu chưa kiểm tra nguồn.
- Phần thông tin đối tác trong brief còn để trống và phải được owner bài nộp xác nhận riêng.
- Nếu file DOCX sau này khác bản Markdown, cần đối chiếu lại và cập nhật bảng traceability này trước khi chốt slide/video.
