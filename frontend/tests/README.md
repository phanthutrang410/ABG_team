# Kiểm thử frontend

Frontend có hai lớp kiểm thử:

- Node test kiểm tra các hàm thuần, dữ liệu demo và quy tắc điều hướng.
- Playwright kiểm tra hành vi thực tế trên Chromium, gồm đăng nhập, phân quyền giao diện, trạng thái dữ liệu, quy trình xử lý case, agent và bản nháp bàn giao.

## Cài đặt

Từ thư mục `frontend`:

```powershell
npm ci
npx playwright install chromium
```

Trên Linux CI, cài trình duyệt và thư viện hệ thống bằng:

```bash
npx playwright install --with-deps chromium
```

Không commit nội dung trong `test-results`, `playwright-report` hoặc tệp phiên đăng nhập. Cấu hình hiện dùng phiên demo được tạo riêng trong từng test, không lưu thông tin xác thực dùng chung.

## Chạy test

```powershell
# Toàn bộ frontend test
npm test

# Chỉ Node test
npm run test:unit

# Chỉ Playwright
npm run test:e2e

# Theo dõi trình duyệt khi kiểm tra lỗi
npm run test:e2e:headed

# Giao diện Playwright
npm run test:e2e:ui

# Mở báo cáo HTML của lần chạy gần nhất
npm run test:e2e:report
```

Playwright tự bật Next.js tại `http://127.0.0.1:3100`. Cổng riêng tránh xung đột với phiên phát triển thường dùng cổng 3000. Có thể kiểm tra một frontend đang chạy sẵn:

```powershell
$env:PLAYWRIGHT_BASE_URL="http://127.0.0.1:3000"
npm run test:e2e
```

Khi đặt `PLAYWRIGHT_BASE_URL`, Playwright không tự bật frontend. Người chạy test chịu trách nhiệm cấu hình `NEXT_PUBLIC_API_BASE` và `NEXT_PUBLIC_ADVISOR_LOCAL_DEMO` phù hợp.

## Phạm vi hiện có

| Tệp | Phạm vi |
|:---|:---|
| `advisor-demo.test.mts` | Dữ liệu demo GVCN, chuyển trạng thái và điều kiện đóng an toàn |
| `advisor-routing.test.mts` | Quy tắc điều hướng và cờ local demo |
| `e2e/auth-routing.spec.ts` | Đăng nhập, chọn vai, route guard và tài khoản trên layout |
| `e2e/management-states.spec.ts` | Danh sách, stale, error/retry, fairness và tìm kiếm |
| `e2e/case-workflow.spec.ts` | Hành động hợp lệ, mapping repair và giới hạn payload agent |
| `e2e/notify-drafts.spec.ts` | Bản nháp cần duyệt, không gửi tự động và trạng thái lỗi |

## Quy tắc viết test

1. Kiểm tra hành vi người dùng và kết quả nghiệp vụ, không kiểm tra chi tiết CSS.
2. Ưu tiên locator theo role, label, placeholder hoặc nội dung ổn định. Không dùng XPath và hạn chế selector phụ thuộc cấu trúc DOM.
3. Mock API tại biên mạng bằng `page.route`. Fixture phải đúng schema đã duyệt và không chứa PII, raw score, xác suất hoặc trọng số.
4. Mỗi test tự tạo session và dữ liệu cần dùng. Không phụ thuộc thứ tự chạy hoặc trạng thái của test trước.
5. Luôn kiểm tra các nhánh `empty`, `stale`, `error` hoặc `insufficient_data` khi thêm một consumer API mới.
6. Với thao tác thay đổi trạng thái, kiểm tra cả nút được phép, nút bị cấm và payload gửi lên server.
7. Không dùng `test.skip`, giảm assertion hoặc thêm timeout tùy ý để che lỗi không ổn định.

Tài liệu tham chiếu chính thức: [Playwright Test](https://playwright.dev/docs/intro), [locators](https://playwright.dev/docs/locators), [mock API](https://playwright.dev/docs/mock), [cấu hình](https://playwright.dev/docs/test-configuration) và [CI](https://playwright.dev/docs/ci).

## Cấu trúc test

Test frontend độc lập nằm trong `frontend/tests`; pytest nằm trong `backend/tests`. Bộ `tests/system` ở root kiểm tra frontend, backend và PostgreSQL thật, không mock API. Không chuyển unit test hoặc contract test của từng tầng lên root.
