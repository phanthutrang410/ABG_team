# Advisor-batch mail draft — nghiên cứu & contract mỏng

> **Status:** **H22 Build Done** · Research lock (decision #20) · Owner research: Hoàng (`H21`) · API: Hoàng (`H22`) · FE: Giang (`G06`)
> **HTTP:** `GET /advisor-handoff-drafts` → `AdvisorHandoffDraftListResponse` (draft-only; **no** send endpoint)
> **Nguồn:** [Process](../02-product/03-process.md) bước 9–11 · [PRD](../02-product/04-prd.md) FR-07 / FR-12 · [Ethics](../02-product/05-ethics.md) §4/§8 · [EPU fields](03-epu-reference-data-fields.md) §7 · H11a `neutral_draft`.
> **Global Agent target:** Agent chỉ cung cấp action điều hướng tới `/notify`; grouping/eligibility/draft preview vẫn do application service deterministic thực hiện, không có `send_mail` tool. Xem [doc 13 §§10,12](13-weekly-snapshot-global-agent-architecture.md).

## 1. Vấn đề

Ban Lãnh đạo (T1) sau khi duyệt nhiều case cần **giao theo từng giảng viên/cố vấn phụ trách**: lọc danh sách sinh viên cần theo dõi theo `advisor_ref`, rồi soạn **một bản nháp mail kèm danh sách** cho từng GV — không gửi đại trà, không tự SMTP.

## 2. Mục tiêu demo / sản phẩm

| Actor | Việc làm được | Việc **không** làm |
|:--|:--|:--|
| Ban Lãnh đạo | Xem nhóm case đã `approve` (hoặc đã `assign`) theo từng `advisor_ref`; copy/xuất bản nháp trung lập kèm danh sách `student_ref` (+ lớp nếu có) | Không thấy raw score; không nhận email SV/GV từ API public |
| Hệ thống/agent | Gom nhóm + soạn **draft only** (`requires_human_approval=true`) | Không `send`, không đổi state case, không bịa liên hệ |
| GV nhận mail | Nhận nội dung do **con người** gửi ngoài hệ thống (hoặc `mailto:` do lãnh đạo kích hoạt) | Không bắt buộc đăng nhập MVP |

## 3. Lựa chọn tool / cách tiếp cận (H21)

| Option | Mô tả | Ưu | Nhược | Khuyến nghị MVP 48h |
|:--|:--|:--|:--|:--|
| **A. In-app aggregate + copy** | API gom case theo `advisor_ref`; FE hiện panel + nút Copy / `mailto:` body | Không SMTP; khớp care boundary; demo nhanh | Contact thật vẫn ngoài hệ thống | **Chọn (core)** |
| **B. Agent `neutral_draft` theo lô** | Intent mở rộng: draft một mail / advisor từ list case đã duyệt | Tái dùng T01/T03 guardrail | Dễ over-claim nếu không khóa vocabulary | **Stretch** sau A |
| **C. Export CSV/JSON per advisor** | File tải về để mail-merge Outlook/Gmail | Ops quen | Dễ lộ PII nếu join map ngoài; khó kiểm soát claim | Chỉ ops vault, **không** commit |
| **D. SMTP / Graph / Gmail API send** | Hệ thống gửi hộ | “Đầy đủ” | Vi phạm Ethics draft-only; secret; ngoài scope 48h | **Loại** |

**Chốt:** Option **A** là DoD tối thiểu của `H22`+`G06`. Option **B** chỉ khi T02 ổn định và không tranh slot D4b. C/D không vào repo/Live MVP.

## 4. Contract dữ liệu (public / internal)

### 4.1 Input (sau human review)

- Chỉ case ở `approved_for_follow_up` hoặc `assigned` (không lấy `pending_review` / `dismissed`).
- Nhóm theo `advisor_ref` từ `advisor_assignment` / H08 mapping (server-side).
- Thiếu `advisor_ref` → bucket `mapping_repair` (không có draft mail; Process §4.4).

### 4.2 Public envelope (`H22` Done)

```text
GET /advisor-handoff-drafts
→ AdvisorHandoffDraftListResponse
  state: ok | empty | error
  bundles[]: AdvisorHandoffDraftBundle
  mapping_repair: { case_count, cases[], limitations[] }
  problem: null | IntegrationProblem

AdvisorHandoffDraftBundle
  advisor_ref: string          # pseudonym routing only (exception vs H11a ReviewCase)
  case_count: int
  cases[]:
    case_id, student_ref, review_priority_band,
    contributing_factor_codes[], coverage_status / coverage_reason_codes,
    case_state, class_code?
  draft:
    subject: string            # trung lập, không “nguy cơ bỏ học”
    body: string               # danh sách student_ref (+ lớp nếu có)
    requires_human_approval: true  # invariant
  limitations[]: string        # H12a keys / insufficient contact map
```

**Schema/code:** `backend/app/contracts/advisor_handoff_draft.py` · `backend/app/cases/advisor_draft.py` · `backend/app/cases/advisor_draft_router.py` · `tests/test_h22_advisor_handoff_draft_api.py`

**Cấm** trong envelope public / agent / FE fixture: email/SĐT/họ tên GV hoặc SV, MSSV, `model_score`, `is_dropout_outcome`, audit-group attrs, raw DWH. `advisor_ref` **được phép chỉ** trên envelope này.

Liên hệ thật (nếu có) chỉ resolve ở **ops vault ngoài repo** khi lãnh đạo dán vào client mail của họ — Silent Shield không lưu/trả contact.

### 4.3 Hành vi gửi

- `mailto:` / Copy clipboard = **UI helper**, không phải API send.
- Không endpoint `POST .../send-email`.
- Agent refusal giữ `auto_send_or_notify` (ADV-05).

## 5. Copy / vocabulary

- Tiêu đề/body: “danh sách sinh viên cần rà soát / theo dõi học vụ”, không “rủi ro bỏ học”, không chẩn đoán.
- Mỗi dòng: `student_ref` (+ mã lớp nếu có) + mức ưu tiên rà soát + 1–2 factor code trung lập.
- Footer: “Bản nháp — cần Ban Lãnh đạo duyệt trước khi gửi.”

## 6. Dependency & verify

| Task | Outcome | Depends | Verify |
|:--|:--|:--|:--|
| `H21` | Research + contract này khóa; không build | — | Doc khớp Ethics/Process; decision #20 — **Done** |
| `H22` | API bundle theo `advisor_ref` + fixture/test | H21, H03, H02 | **Done** — happy + mapping_repair + forbidden-field scan (`test_h22_*`) |
| `G06` | FE filter/group + Copy/`mailto:` draft | H22, G05 | **Unblocked**; lint/build; không PII; không auto-send |
| (optional) agent batch draft | Mở rộng `neutral_draft` lô | H21, T01, H22 | Adversarial + `requires_human_approval` |

Critical path CP2 (`G02`→`D4b`) **không** chờ `H22`/`G06`. Stretch demo value sau Live smoke hoặc song song nếu có slot.

## 7. Evidence khi Done

- Contract/tests: không có field liên hệ; mọi draft `requires_human_approval=true`.
- Demo script: lãnh đạo lọc theo GV → copy nháp → (tuỳ chọn) mở mail client — **không** claim hệ thống đã gửi mail.
