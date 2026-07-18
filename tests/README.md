# Kiểm thử xuyên hệ thống

Thư mục này sở hữu các kịch bản đi qua nhiều runtime thật trong cùng một lần chạy.

- `frontend/tests` kiểm tra frontend độc lập và mock API tại biên mạng.
- `backend/tests` kiểm tra contract, API, dữ liệu và nghiệp vụ bằng pytest.
- `tests/system` bật PostgreSQL, backend và frontend thật rồi kiểm tra bằng Playwright.

System test không thay thế test của từng tầng. Chỉ đặt test tại đây khi hành vi cần chứng minh frontend và backend kết nối đúng qua HTTP hoặc cần dữ liệu được nạp vào database thật.

Xem [hướng dẫn system test](system/README.md) để cài đặt và chạy.
