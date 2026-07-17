# Dữ liệu synthetic cho demo

Thư mục chỉ chứa dữ liệu giả lập, không có PII thật.

| Tệp | Nội dung | Dùng trong MVP |
|:----|:---------|:--------------|
| `students.csv` | Mã synthetic, lớp/cohort và hai thuộc tính nhóm synthetic | Mapping demo; thuộc tính nhóm chỉ dùng cho fairness audit, không dùng scoring |
| `grades_timeseries.csv` | Điểm theo tuần | Xu hướng và biến động điểm |
| `attendance_timeseries.csv` | Tỷ lệ chuyên cần theo tuần | Mức và xu hướng chuyên cần |

## Giới hạn đã biết

- Generator hiện dùng tên lớp K-12 như `10A1`, trong khi [Problems Brief](../../docs/01-requirements/02-problems-brief.md) mô tả bối cảnh sinh viên và Ban Lãnh đạo Khoa/Trường. Đây là artifact demo cần được đổi sang cohort đại học hoặc công bố rõ trước khi chốt video.
- Ba tệp hiện chưa có outcome/ground-truth label. Không được gọi selection rate là FPR hoặc tính precision/recall nếu chưa bổ sung nhãn synthetic có định nghĩa rõ.
- Nhóm kinh tế/dân tộc là synthetic và chỉ chứng minh pipeline có thể phân rã metric; không chứng minh hệ thống production công bằng.
- Dữ liệu không đại diện cho phân bố, hành vi hay kết quả của sinh viên thật.

Phạm vi và điều kiện sử dụng xem [PRD](../../docs/02-product/04-prd.md), [Danh mục tín hiệu](../../docs/02-product/06-signal-catalog.md) và [Ethics](../../docs/02-product/05-ethics.md).
