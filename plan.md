# Plan — FE wiring: luồng GVCN "mở link → đã xem → xác nhận tiếp nhận" (data thật)

> Mục tiêu: nối trang GVCN (`/advisor`) với backend thật để luồng email → login → xem → tiếp nhận chạy end-to-end trên trình duyệt, thay cho client demo hiện tại.
> Backend đã sẵn sàng (H36a). Đây là phần **frontend consumer** còn thiếu.

## 0. Bối cảnh

- **Backend đã có (verified):**
  - `GET /review-cases` — list case (BLĐ thấy tất cả; **GVCN chỉ thấy case thuộc advisor_scope của mình**).
  - `GET /review-cases/{case_id}` — chi tiết `ReviewCase` (lý do trung lập, coverage, factors), RBAC theo scope.
  - `GET /cases/{case_id}` — `TransitionResponse` (`state`, **`viewed_at`**, `monitoring_until`, `updated_at`…), RBAC theo scope.
  - `POST /cases/{case_id}/viewed` — **GVCN-only, idempotent**, ghi `viewed_at` ("đã xem").
  - `POST /cases/{case_id}/transitions {accept|monitor|resolve}` — hành động GVCN; `accept`: `assigned → follow_up_in_progress`.
  - Auth: `POST /auth/login`, `GET /auth/me`, `POST /auth/active-role`, `POST /auth/logout` (cookie `ss_session`).
- **FE hiện tại:** `AdvisorWorkspace` = **client demo** (`generateAdvisorDemoCases` + localStorage), gate bởi `isAdvisorLocalDemoEnabled()`. Đã có sẵn UX: deep-link `?case=`, `openCase → markAdvisorDemoViewed`, nút "Xác nhận tiếp nhận", chip "Chưa xem"/"Quá hạn". **Nhưng chạy trên case_id demo, không gọi backend.**
- **Vấn đề khoá:** case_id thật (`rc-s-…`) ≠ case_id demo (`demo-assignment-…`) → link email không khớp; "đã xem"/"tiếp nhận" chỉ lưu localStorage, khoa không thấy.

## 1. Contract mới cần khai báo ở FE

- [ ] `frontend/src/lib/types.ts`: thêm `viewed_at?: string | null` vào type `TransitionResponse` (đã có `state`, `updated_at`, `monitoring_until`, `reason_code`, `review_at`, `mapping_repair_queued`).

## 2. api.ts — 2 hàm mới (đều `...CREDENTIALS`)

- [ ] `fetchCaseWorkflow(caseId): Promise<TransitionResponse | null>` → `GET /cases/{id}` (state + viewed_at). `null` = 404/lỗi (fail-closed).
- [ ] `postCaseViewed(caseId): Promise<TransitionResponse | null>` → `POST /cases/{id}/viewed`. `null` khi 403/404/lỗi.
- Lưu ý: `fetchReviewCase`, `postCaseTransition` **đã có** và đã gửi credentials — tái dùng.

## 3. Nguồn dữ liệu thật cho hàng đợi GVCN

- [ ] Tạo hook `useAdvisorCases()` (thay `generateAdvisorDemoCases` khi đăng nhập gvcn):
  - Gọi `GET /review-cases` → nhận các `ReviewCase` GVCN-scoped (backend đã lọc).
  - Với mỗi case, `case_state` lấy từ… **vấn đề:** `/review-cases` trả `ReviewCase` (không có `case_state` workflow đầy đủ? — kiểm tra: `ReviewCase.case_state` CÓ tồn tại). Dùng `case_state` để phân nhóm hàng đợi (assigned = cần tiếp nhận, follow_up_in_progress = đang hỗ trợ…).
  - `viewed_at` **không có** trên `ReviewCase` (allowlist đóng). Để hiện "Chưa xem" ở list: hoặc (a) chấp nhận chỉ hiện receipt ở panel chi tiết (gọi `GET /cases/{id}` khi mở), hoặc (b) thêm một endpoint list-workflow riêng sau (backend follow-up).
- [ ] `AdvisorWorkspace`: khi `activeRole === "gvcn"` và đăng nhập server → dùng data thật; giữ nhánh demo **chỉ khi** `isAdvisorLocalDemoEnabled()` (offline/UI work).

## 4. Luồng deep-link + panel chi tiết (phần cốt lõi)

- [ ] Khi mở `/advisor?case=<real_id>`:
  1. `fetchReviewCase(id)` → data hiển thị (lý do, coverage, factors).
  2. `fetchCaseWorkflow(id)` → `state` + `viewed_at` hiện tại.
  3. `postCaseViewed(id)` → ghi "đã xem" (chỉ khi `state === "assigned"` và chưa viewed) → cập nhật `viewed_at` trên UI.
  4. Render panel: badge "Đã xem lúc …" / "Chưa ghi nhận", nút hành động theo `state`.
- [ ] Nút **"Xác nhận tiếp nhận"** → `postCaseTransition(id, {action:"accept"})` → `follow_up_in_progress` → refresh workflow + list.
- [ ] Click 1 row trong hàng đợi cũng đi qua cùng luồng mở-case này (mark viewed).

## 5. Overdue / nhắc nhở (thật)

- [ ] Panel chi tiết: "quá hạn chưa tiếp nhận" tính từ `updated_at` của `GET /cases/{id}` (thời điểm bàn giao ≈ khi sang `assigned`) so với ngưỡng `HANDOFF_ACK_OVERDUE_DAYS`.
- [ ] **Follow-up backend (chưa làm):** metric "X case quá hạn chưa tiếp nhận" phía **khoa** cần thời điểm assign trên list → cần endpoint/field mới (không nhét vào `ReviewCase` đóng). Ghi nhận, làm sau.

## 6. Dọn dẹp demo

- [ ] Các helper demo (`markAdvisorDemoViewed`, `isHandoffOverdue`, `viewed_at` trên `AdvisorDemoCase`) → giữ cho nhánh demo, KHÔNG dùng ở nhánh thật.
- [ ] Bỏ ghi localStorage cho case thật (chỉ demo mới lưu local).

## 7. Verify

- [ ] Lint + build FE.
- [ ] Đăng nhập **gvcn/demo123** → `/advisor`: thấy 4 case thật; mở 1 case `assigned` → panel hiện "Đã xem lúc…"; bấm "Xác nhận tiếp nhận" → chuyển "Đang hỗ trợ".
- [ ] Đăng nhập **quanly** → `/overview`/`/notify`: case vừa tiếp nhận đổi trạng thái (khoa thấy được, đóng vòng).
- [ ] Mở link trong mail draft (`/advisor?case=<real_id>`) khi đã đăng nhập gvcn → tự chọn đúng SV + ghi "đã xem".

## 8. Rủi ro / flag

- **Gate demo vs thật:** quyết định `isAdvisorLocalDemoEnabled` — nên chuyển sang **data thật khi đăng nhập gvcn**, demo chỉ khi `NEXT_PUBLIC_ADVISOR_LOCAL_DEMO=1`. Cần thống nhất với owner advisor-routing (H36).
- **`viewed_at` không lên list** (do `ReviewCase` allowlist đóng H11a) → "Chưa xem" ở list là hạn chế; chỉ chắc chắn ở panel chi tiết. Nếu cần list-level, thêm endpoint workflow-list (backend follow-up, owner cases).
- **Overdue phía khoa** cần backend (mục 5) — chưa có.
- Các file backend cho H36a (cases/store/router/schema/migration + `dwh/migrate.HEAD_REVISION`) hiện **chưa commit**; cần owner cases/auth review trước khi FE dựa vào.

## 9. Ước lượng file đụng (FE)

- `frontend/src/lib/types.ts` — thêm `viewed_at` vào `TransitionResponse`.
- `frontend/src/lib/api.ts` — `fetchCaseWorkflow`, `postCaseViewed`.
- `frontend/src/components/AdvisorWorkspace.tsx` — nhánh data thật + luồng open/viewed/accept.
- (tuỳ chọn) hook mới `frontend/src/lib/use-advisor-cases.ts`.
- `frontend/src/lib/advisor-routing.ts` — điều chỉnh điều kiện bật data thật (nếu chốt).
