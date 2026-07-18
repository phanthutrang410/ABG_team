# Silent Shield — Thiết kế Web UI/UX (bản đề xuất của Giang, lane FE)

> **Trạng thái:** tài liệu thiết kế làm việc — luồng màn hình theo tầm nhìn của Giang, đã đối chiếu
> PRD §5 · Ethics §3–4 · Process §4 · contract H11a/H06a. Phần nào cần backend bổ sung API đã đánh
> dấu `[cần API]` để Hoàng chốt. Không phải docs canonical.

---

## 1. Triết lý thiết kế

**Nhân văn trước, số liệu sau.** Người dùng là nhà giáo dục đang tìm sinh viên cần giúp đỡ —
không phải nhân viên an ninh soi camera. Mọi quyết định thiết kế đi theo 4 nguyên tắc:

| # | Nguyên tắc | Thể hiện trên UI |
|---|---|---|
| 1 | **Care, không phán xét** | Từ ngữ "cần rà soát/quan tâm sớm"; không "nguy cơ", không đỏ chói báo động; band luôn kèm chữ |
| 2 | **Trung thực về dữ liệu** | Coverage/freshness hiện rõ; thiếu dữ liệu = nói thiếu (`insufficient_data`), không im lặng thành "ổn" |
| 3 | **Con người quyết định** | Máy chỉ gợi ý ưu tiên; nút Duyệt/Loại/Hoãn/Bàn giao luôn do người bấm |
| 4 | **Đúng người đúng phạm vi** | Thấy gì phụ thuộc vai (mục 2); không phát tán danh sách theo dõi |

**Tông thị giác:** sạch, điềm tĩnh, hành chính hiện đại. Nền `#f6f7f9`, thẻ trắng bo 8px, chữ
`system-ui`; màu band pastel (đỏ nhạt/hổ phách) + chữ; xanh dương `#2a78d6` cho dữ liệu trung tính
(biểu đồ); khoảng trắng rộng, mỗi màn hình một nhiệm vụ chính.

---

## 2. Vai trò & phạm vi nhìn

| Vai | Phạm vi dashboard | Được thấy | KHÔNG được thấy |
|---|---|---|---|
| **Ban quản lý / Giám sát học tập** (T1) | Toàn khoa / trường / viện | Toàn bộ tín hiệu + case mọi trạng thái, fairness, ngưỡng, drill-down mọi cấp | Raw score, thuộc tính nhóm của cá nhân |
| **Giảng viên chủ nhiệm / CVHT** (T3) | Lớp mình phụ trách | Dữ liệu học vụ lớp mình (điểm, chuyên cần — dữ liệu họ vốn có quyền theo vai trò SIS); **case đã duyệt & bàn giao cho mình** kèm băng ưu tiên + lý do | Băng ưu tiên của case **chưa duyệt** (kể cả SV lớp mình); tín hiệu toàn đơn vị; fairness/ngưỡng |

> ⚠ **Điểm tinh tế quan trọng (Ethics §3):** GVCN xem được *dữ liệu học vụ* lớp mình (điều họ vốn
> làm hằng ngày), nhưng **mức ưu tiên rà soát của case chưa duyệt không hiển thị cho GVCN** — nếu
> không, hệ thống thành máy phát tán watchlist chưa kiểm chứng. Trên màn lớp của GVCN, cột
> "trạng thái quan tâm" chỉ có 2 giá trị: *"—"* hoặc *"Được bàn giao"* (kèm lý do).

**Đăng nhập:** tài khoản + mật khẩu (production: SSO trường; demo: form + captcha đơn giản chống
bot). Sau đăng nhập, hệ tra vai → điều hướng thẳng vào dashboard đúng phạm vi. Một người nhiều vai
→ màn chọn vai.

```
Login ──► tra vai ──┬─► BLĐ:  /dashboard        (toàn đơn vị)
                    └─► GVCN: /my-class          (lớp phụ trách)
```

---

## 3. Màn hình 1 — Đăng nhập

```
┌──────────────────────────────────────┐
│        Silent Shield                  │
│  Hệ thống hỗ trợ quan tâm sinh viên   │
│                                       │
│  Tài khoản   [________________]       │
│  Mật khẩu    [________________]       │
│  Mã xác nhận  4 + 7 = [____]  ↻      │
│                                       │
│  [        Đăng nhập        ]          │
│  Quên mật khẩu?                       │
│                                       │
│  ⓘ Dữ liệu pseudonymized · con người  │
│    duyệt trước mọi bàn giao           │
└──────────────────────────────────────┘
```

- Lỗi sai tài khoản/mật khẩu: thông báo trung lập, không tiết lộ "sai trường nào".
- "Quên mật khẩu": hướng dẫn liên hệ quản trị (demo không gửi email).
- Footer đăng nhập có ngay 1 dòng cam kết privacy — ấn tượng đầu tiên là sự tử tế.

---

## 4. Màn hình 2 — Dashboard tổng quan (theo vai)

### 4.1 Ban quản lý — toàn khoa/trường/viện

```
┌──────────────────────────────────────────────────────────────────────┐
│ Silent Shield        Khoa CNTT ▾   HK2 2024-2025 ▾        TS.Nam ▾  │ ← slice
├──────────────────────────────────────────────────────────────────────┤
│ Nguồn: Điểm ✓ HK2 · Điểm danh ⏳ chờ duyệt nguồn (insufficient)      │
├──────────────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                      │
│ │Tín hiệu │ │Chờ duyệt│ │Đã bàn   │ │Chưa đủ  │   ← thẻ đếm, click  │
│ │mới    8 │ │       5 │ │giao   3 │ │dữ liệu 4│     = drill xuống   │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘                      │
│ ┌───────────────────────────┐ ┌───────────────────────────────────┐  │
│ │ Phân bố mức ưu tiên       │ │ Tín hiệu mới theo kỳ (4 kỳ)       │  │
│ │ ▓▓▓▓▓▓ Cần rà soát   6    │ │      ▂  ▄  ▃  ▆                   │  │
│ │ ▓▓▓ Ưu tiên sớm      3    │ │     HK1 HK2 HK1 HK2               │  │
│ └───────────────────────────┘ └───────────────────────────────────┘  │
│ ┌───────────────────────────┐ ┌───────────────────────────────────┐  │
│ │ Case theo ngành (bar)     │ │ Case theo trạng thái (bar)        │  │
│ │ CNTT ▓▓▓▓▓ 5  click=drill │ │ Chờ duyệt ▓▓▓▓ …                 │  │
│ └───────────────────────────┘ └───────────────────────────────────┘  │
│                    [→ Mở danh sách theo dõi sinh viên]               │
└──────────────────────────────────────────────────────────────────────┘
```

**Slice / Filter / Drill-down:**
- **Slice** (thanh trên cùng): đơn vị (trường→viện→khoa→ngành) + học kỳ. Đổi slice → mọi thẻ/biểu đồ tính lại.
- **Filter** (trong màn danh sách): trạng thái case, band, lớp, coverage.
- **Drill-down:** click thẻ đếm → danh sách đã lọc theo thẻ; click cột "ngành" trong bar chart →
  slice xuống ngành đó; click 1 SV → dashboard SV (màn 4). Breadcrumb: `Trường / Khoa CNTT / KTPM / K66-A / SV`.

**Quy tắc biểu đồ** (theo chuẩn dataviz đã dùng): 1 series = 1 hue xanh, nhãn giá trị trực tiếp,
không legend thừa, không màu-làm-tín-hiệu-duy-nhất, hover có tooltip; nhánh thiếu dữ liệu vẽ
**khối trạng thái "chưa đủ dữ liệu + lý do"**, không vẽ chart trống hay số 0 gây hiểu nhầm.

### 4.2 GVCN — lớp phụ trách

Cùng khung nhưng phạm vi = lớp: thẻ đếm (sĩ số, SV có case được bàn giao, việc chờ xác nhận),
biểu đồ GPA trung bình lớp theo kỳ, chuyên cần lớp theo tuần `[cần API + nguồn duyệt]`. Không có
tab Fairness/Ngưỡng, không thấy case chưa duyệt.

---

## 5. Màn hình 3 — Theo dõi sinh viên (danh sách)

```
┌──────────────────────────────────────────────────────────────────────┐
│ ← Dashboard      Theo dõi sinh viên          🔍 [mã SV / tên / lớp ] │
│ Lọc: [Lớp ▾] [Trạng thái quan tâm ▾] [Coverage ▾]   Sắp: [Ưu tiên ▾]│
├──────────────────────────────────────────────────────────────────────┤
│ Mã SV    │ Tên*     │ Lớp        │ Trạng thái quan tâm │ GPA kỳ này │
│ 2201234  │ Nguyễn A │ K66-CNTT-A │ ● Cần rà soát       │ 2.4 ↓      │
│ 2201260  │ Trần B   │ K66-CNTT-A │ ● Ưu tiên sớm       │ 2.1 ↓      │
│ 2201301  │ Lê C     │ K66-CNTT-B │ ◌ Chưa đủ dữ liệu   │ —          │
│ 2201188  │ Phạm D   │ K66-CNTT-A │ —                   │ 3.2        │
└──────────────────────────────────────────────────────────────────────┘
  * MVP demo dùng mã pseudonym thay tên thật; bản production trong trường
    (đúng quyền) mới hiển thị tên. Tìm kiếm hoạt động trên cả hai chế độ.
```

- **Sắp xếp:** mức ưu tiên (mặc định) · mã SV · tên (A→Z) · lớp · GPA · coverage.
- **Tìm kiếm:** gõ tự do — khớp mã SV / tên / lớp, debounce 300ms, highlight kết quả.
- **Trạng thái quan tâm** dùng đúng band public (`Cần rà soát` / `Ưu tiên sớm`) + `Chưa đủ dữ liệu`
  + `—` (không có tín hiệu). Với GVCN: cột này chỉ hiện khi case **đã bàn giao**.
- Hàng có case → click mở dashboard SV; phần "hành động" (duyệt/loại/hoãn) đi theo quyền BLĐ.
- Empty/search-không-thấy: câu trung lập + gợi ý xóa bộ lọc.

`[cần API]` — endpoint list hiện (`GET /review-cases`) chỉ trả **case có band**, không trả toàn bộ
SV + GPA + tên/lớp. Màn này cần thêm: danh sách SV theo scope + GPA kỳ + lớp/cohort (đề xuất
`GET /students?scope=...` trả projection an toàn — Hoàng chốt schema).

---

## 6. Màn hình 4 — Dashboard một sinh viên

```
┌──────────────────────────────────────────────────────────────────────┐
│ ← Danh sách   SV 2201234 · Nguyễn A* · K66-CNTT-A   ● Cần rà soát   │
│ Case: Chờ duyệt · model ew-term-0.1 · snapshot 18/07                 │
├──────────────────────────────────────────────────────────────────────┤
│ ┌── Xu hướng GPA theo kỳ (line) ──────────────┐ ┌── Hành động ─────┐ │
│ │ 4.0┤                                        │ │ (theo quyền BLĐ) │ │
│ │    │   ●───●                                │ │ ✓ Duyệt bàn giao │ │
│ │ 3.0┤        ╲                               │ │ ✕ Loại (lý do ▾) │ │
│ │    │         ●───●                          │ │ ⏸ Hoãn           │ │
│ │ 2.0┤              ╲.                        │ │ ───────────────  │ │
│ │    └┬────┬────┬────┬─                       │ │ Lịch sử quyết    │ │
│ │    HK1  HK2  HK1  HK2                       │ │ định + lý do     │ │
│ │    23   23   24   24                        │ └──────────────────┘ │
│ └─────────────────────────────────────────────┘                      │
│ ┌── Môn học tham gia ───────────── Kỳ: [HK2 2024-25 ▾] ───────────┐  │
│ │ Môn            │ TC │ Điểm │ Trạng thái                          │  │
│ │ CTDL & GT      │ 3  │ 4.2  │ Không đạt                           │  │
│ │ CSDL           │ 3  │ 6.5  │ Đạt                                 │  │
│ └──────────────────────────────────────────────────────────────────┘  │
│ ┌── Chuyên cần ────────────────────────────────────────────────────┐  │
│ │ NẾU nguồn điểm danh đã duyệt (H15):                              │  │
│ │  • Donut/thanh: có mặt · vắng CÓ phép · vắng KHÔNG phép          │  │
│ │  • Line: tỷ lệ đi học theo tuần trong kỳ (so với chính SV)       │  │
│ │ NẾU chưa: khối "Chưa có nguồn điểm danh được phê duyệt — hệ      │  │
│ │ thống không kết luận về chuyên cần" (copy H12a, không vẽ giả)    │  │
│ └──────────────────────────────────────────────────────────────────┘  │
│ ┌── Vì sao cần rà soát? (agent) ──────────────── [Hỏi agent] ─────┐  │
│ │ Trả lời bám band/factors/coverage có sẵn; nêu giới hạn;          │  │
│ │ không đoán nguyên nhân cá nhân                                   │  │
│ └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

Chi tiết đúng thiết kế của bạn:
- **Line GPA qua các kỳ** — trục y 0–4 (hoặc 0–10 theo thang trường), điểm đánh dấu ≥8px, tooltip
  từng kỳ, vùng kỳ thiếu dữ liệu để trống + chú thích (không nội suy).
- **Danh sách môn có lọc theo kỳ** — dropdown kỳ; cột trạng thái Đạt/Không đạt bằng chữ.
- **Đi học phép / không phép** — phân rã 3 nhóm (có mặt · vắng CP · vắng KP) vì hai loại vắng có ý
  nghĩa rất khác nhau; vắng có phép nhiều không đẩy ưu tiên (ngoại lệ nghiệp vụ).
- **Xu hướng đi học theo tuần** — line theo tuần trong kỳ, so với baseline của **chính SV**.
- Mọi widget chuyên cần bọc trong điều kiện nguồn đã duyệt — fail-closed đúng decision #13.

`[cần API]` — GPA theo kỳ, bảng môn theo kỳ, chuyên cần theo tuần: đều chưa có trong `ReviewCase`
public. Cần endpoint chi tiết học vụ theo scope/quyền (đề xuất `GET /students/{ref}/academics`).

---

## 7. Phần tôi đề xuất phát triển thêm (trả lời câu hỏi của bạn)

1. **Hành động review ngay trong dashboard SV** (cột phải màn 4) — thiết kế của bạn mới "xem";
   thêm Duyệt/Loại/Hoãn/Bàn giao tại chỗ (API H03 đã có) thì BLĐ không phải nhảy màn — một luồng
   "thấy bằng chứng → quyết định" khép kín. Hoãn = giữ Chờ duyệt + ngày xem lại; bàn giao chặn khi
   thiếu mapping cố vấn.
2. **Panel agent "Vì sao cần rà soát?"** — backend đã có stub T01 với guardrails; đây là điểm demo
   FR-08 ăn điểm, nên có mặt ngay trong dashboard SV.
3. **Tab Ngưỡng + Fairness cho BLĐ** (API H04 đã có) — kéo ngưỡng xem số case đổi (FR-10);
   fairness hiển thị trạng thái `insufficient_data` có giải thích — đúng rubric fail-closed.
4. **Coverage ribbon trên mọi màn** — dải mỏng "Điểm ✓ HK2 · Điểm danh ⏳ chờ duyệt nguồn" để
   người dùng luôn biết đang nhìn dữ liệu đến đâu. Trung thực = đáng tin.
5. **Nhật ký quyết định (audit)** trong dashboard SV — ai duyệt/loại/hoãn, khi nào, lý do; và màn
   hàng-chờ-sửa-mapping khi thiếu cố vấn.
6. **Báo cáo định kỳ** — khối "tuần này: X tín hiệu mới, Y case quá hạn review" trên dashboard
   BLĐ (Process §5) — nhịp làm việc thật thay vì mở dashboard vu vơ.
7. **Trải nghiệm GVCN tối giản kiểu "hộp công việc"** — GVCN vào thấy ngay "2 case được bàn giao
   cho bạn, 1 chờ xác nhận tiếp nhận" thay vì dashboard nặng — họ là người bận nhất.
8. **Accessibility & humanity:** focus ring rõ; bảng đọc được bằng screen-reader; mọi trạng thái
   có chữ+icon (không màu trần); microcopy giọng đồng hành ("Hãy xem cùng nhau vì sao em ấy cần
   được quan tâm sớm").
9. **Chưa nên làm trong MVP** (ghi để khỏi sa đà): export danh sách (rủi ro phát tán), notification
   đẩy tự động tới GVCN (phải qua duyệt), so sánh SV với SV khác trên UI (bias — chỉ so với chính em ấy).

---

## 8. Ràng buộc bất biến khi implement (đối chiếu ma trận cũ)

- Không hiển thị `model_score`/xác suất/trọng số — chỉ band + chữ.
- Không nhãn "high-risk/nguy cơ bỏ học"; tín hiệu thuộc **case**, không phải thuộc tính SV.
- GVCN không thấy band của case chưa duyệt (mục 2).
- Thiếu dữ liệu → nói thiếu; không vẽ chart giả, không nội suy tuần/kỳ.
- Thuộc tính nhóm audit không bao giờ xuất hiện ở màn cá nhân.
- MVP demo: mã pseudonym thay tên; không PII thật trong repo/screenshot/video.

## 9. Khoảng trống API cần Hoàng chốt (tổng hợp)

| Cần cho | Đề xuất endpoint | Hiện trạng |
|---|---|---|
| Slice/drill + cột lớp trong list | `ReviewCase` public thêm `cohort/department/class_code` hoặc filter server-side | **Gap đã báo ở G02** |
| Màn theo dõi SV (mục 5) | `GET /students?scope=` — toàn bộ SV + GPA kỳ + lớp | Chưa có |
| Dashboard SV (mục 6) | `GET /students/{ref}/academics` — GPA theo kỳ, môn theo kỳ, chuyên cần tuần (sau H15) | Chưa có |
| Hành động review | `POST /cases/{id}/transitions` | ✅ H03 Done |
| Ngưỡng/fairness | `GET /config/thresholds(+impact)`, `GET /fairness/report` | ✅ H04 Done |
| Agent | endpoint explain (T02) | Stub sẵn, chờ T02 |

## 10. Lộ trình gợi ý

| Bước | Phạm vi | Điều kiện |
|---|---|---|
| 1 (nay) | Danh sách case + chi tiết case (G02 ✅) + hành động review (G03) + agent panel | H03/T02 sẵn |
| 2 | Ngưỡng + fairness tab BLĐ (G04) | H04 ✅ |
| 3 | Login + phân vai + màn GVCN "hộp công việc" | Team chốt scope auth demo |
| 4 | Dashboard tổng quan + biểu đồ + drill-down; màn theo dõi SV đầy đủ | API mục 9 |
| 5 | Dashboard SV đầy đủ (GPA line, môn, chuyên cần) | API + nguồn điểm danh H15 |
