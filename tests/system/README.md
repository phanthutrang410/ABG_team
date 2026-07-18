# Playwright system test

Bộ test này chạy qua PostgreSQL, FastAPI và Next.js thật. Không dùng `page.route`, fixture response hoặc backend giả.

## Phạm vi

- `/health` xác nhận backend kết nối được database.
- `/review-cases` xác nhận dữ liệu đã import đi qua public API và không lộ trường bị cấm.
- Ngưỡng, tác động tổng hợp và fairness được đọc từ backend thật và đóng an toàn khi thiếu điều kiện công bố.
- Agent thật từ chối yêu cầu lộ điểm mà không phụ thuộc model bên ngoài.
- Đăng nhập được thực hiện trên trình duyệt thật.
- Trang Phân tích phải hiển thị response nhận trực tiếp từ backend.
- Workspace GVCN không tự sinh fixture khi API phân quyền phía server chưa sẵn sàng.

## Chuẩn bị

Yêu cầu Docker, Node.js và Python 3.12. Cài backend, package test và Chromium từ root repository:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -e "./backend[dev]"

npm ci --prefix frontend
npm ci --prefix tests/system
npx --prefix tests/system playwright install chromium
```

## Chạy

```powershell
.\tests\system\run.ps1
```

Hoặc chạy cùng toàn bộ cổng xác minh của repository:

```powershell
.\scripts\verify.ps1 -System
```

Script tạo một PostgreSQL container tạm ở cổng 55433, chạy migration, import hai nguồn dữ liệu đã duyệt, bật backend ở cổng 8100 và frontend ở cổng 3200. Script sở hữu và dừng chính xác các tiến trình đã tạo; container tạm luôn được xóa khi kết thúc, kể cả khi test lỗi.

Nếu cổng database mặc định đang được sử dụng:

```powershell
.\tests\system\run.ps1 -DatabasePort 55434 -BackendPort 8101 -FrontendPort 3201
```

Có thể đặt `SYSTEM_TEST_PYTHON` để chọn Python environment khác. Environment đó phải cài `backend[dev]` và tương thích với phiên bản trong `backend/pyproject.toml`.

## Nguyên tắc

1. Không mock API trong system test.
2. Không dùng database phát triển hoặc production.
3. Không đưa PII, secret hoặc raw score vào dữ liệu test và báo cáo.
4. Chỉ kiểm tra contract công khai và hành vi người dùng ổn định.
5. Lỗi ở một runtime phải làm toàn bộ system test thất bại; không fallback sang fixture.

## Kiểm tra bản online

System test ở trên chỉ chứng minh ba runtime local kết nối đúng. Trước checkpoint 48h, chạy thêm cổng online:

```powershell
.\tests\system\release\run.ps1 `
  -BaseUrl "https://<frontend>" `
  -ApiBaseUrl "https://<backend>" `
  -RepositoryUrl "https://github.com/<owner>/<repo>"
```

Xem [hướng dẫn release](release/README.md) và [checklist checkpoint 48h](release/CHECKLIST-48H.md). Cổng mặc định yêu cầu AI online trả `status=ok`; `-AllowUnavailableAi` chỉ dùng chẩn đoán contract và không đủ làm bằng chứng checkpoint.
