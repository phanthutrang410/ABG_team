# Kiểm thử backend

Backend dùng pytest cho API, contract, dữ liệu, scoring, fairness, workflow, agent và báo cáo tuần. Test nằm cạnh runtime Python để dùng chung fixture và cấu hình trong `backend/pyproject.toml`.

## Cài đặt

Từ root repository:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -e "./backend[dev]"
```

Python 3.12 là runtime kiểm thử đã được xác minh cho repository này.

Các test migration, import và workflow cần PostgreSQL. Bật database local trước khi chạy toàn bộ suite:

```powershell
docker compose up -d db
```

Nếu cần database test tách biệt, dùng một cổng riêng và truyền URL qua biến môi trường:

```powershell
docker run --rm -d --name silentshield-test-db `
  -e POSTGRES_USER=silentshield `
  -e POSTGRES_PASSWORD=silentshield `
  -e POSTGRES_DB=silentshield `
  -p 55432:5432 postgres:16

$env:TEST_DATABASE_URL="postgresql+psycopg://silentshield:silentshield@localhost:55432/silentshield"
```

## Chạy test

```powershell
# Toàn bộ test mặc định, loại slow và eval
backend/.venv/Scripts/python.exe -m pytest -q backend/tests -m "not slow and not eval"

# Một tệp
backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_h03_care_workflow.py

# Một test
backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_public_route_policy.py::test_critical_public_routes_keep_their_documented_methods

# Lint backend và test
backend/.venv/Scripts/ruff.exe check backend/app backend/tests
```

Test có marker `slow` hoặc `eval` không thuộc cổng xác minh mặc định. Khi chạy riêng, phải ghi rõ kết quả và chi phí hoặc dependency bên ngoài liên quan.

## Phạm vi và nguyên tắc

- Contract test khóa schema, trạng thái lỗi, trường bắt buộc và trường bị cấm.
- API test kiểm tra happy path, validation, quyền truy cập và lỗi dependency.
- Workflow test kiểm tra chuyển trạng thái hợp lệ, chuyển trạng thái bị cấm và audit cần thiết.
- Data, ML và fairness test kiểm tra tính xác định, dữ liệu thiếu, công thức, ground truth và tách nhóm kiểm toán khỏi scoring.
- Agent test dùng model giả lập cho grounding, refusal và yêu cầu đối kháng. Live eval chỉ chạy khi task cho phép.
- Bug fix phải có regression test thất bại trước khi sửa và pass sau khi sửa.

Không tạo fixture thay cho dependency chưa hoàn tất và không dùng broad exception, skip hoặc assertion yếu để che lỗi. Dữ liệu test chỉ dùng mã giả, không dùng PII hoặc secret.

## Vị trí test xuyên hệ thống

Bộ `tests/system` ở root chạy frontend, backend và PostgreSQL thật bằng Playwright. Pytest contract và nghiệp vụ vẫn nằm tại đây; system test không thay thế test backend.
