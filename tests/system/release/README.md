# Kiểm tra bản triển khai checkpoint 48h

Bộ test này chạy trực tiếp trên frontend, backend và repository công khai. Test chỉ đọc dữ liệu và không chuyển trạng thái case, không gửi thông báo, không sửa cấu hình.

## Chạy cổng release

```powershell
.\tests\system\release\run.ps1 `
  -BaseUrl "https://<frontend>" `
  -ApiBaseUrl "https://<backend>" `
  -RepositoryUrl "https://github.com/<owner>/<repo>"
```

Cổng mặc định yêu cầu:

1. Frontend mở được ở phiên mới và không có lỗi ứng dụng.
2. Backend kết nối database thật qua `/health`.
3. Repository truy cập được khi chưa đăng nhập.
4. `/review-cases` có dữ liệu thật, không lộ PII hoặc điểm nội bộ.
5. Trang Phân tích hiển thị cùng dữ liệu backend trả về.
6. Agent trả giải thích `status=ok`, có yếu tố căn cứ và phiên bản mô hình.

Chỉ khi chẩn đoán hạ tầng có thể thêm `-AllowUnavailableAi`. Chế độ này chấp nhận `insufficient_data` hoặc `unavailable` để kiểm tra contract, nhưng không phải bằng chứng AI hoạt động cho checkpoint 48h.

Kết quả HTML nằm trong `tests/system/release-playwright-report`. Không commit báo cáo vì có thể chứa URL và dữ liệu của môi trường triển khai.

Các tiêu chí về nội dung pitch, chất lượng video, USP và khả năng thương mại cần duyệt bằng [checklist checkpoint 48h](CHECKLIST-48H.md); không thay bằng test luôn pass.
