# H16 — CP2 acceptance matrix + locked limitations

> **Owner:** Hoàng · **Gate:** CP2 evidence lock · **Captured:** 2026-07-18 ~22:50 +07  
> **Depends (Done):** `A05`, `V07`, `D4r`, `V05`  
> **SoT checklist:** [07-release-evidence.md](07-release-evidence.md) §2  
> **Không** invent screenshot/Live URL; **không** overclaim feature chưa ship trên URL nộp.

## 0. Submission lock (CP2)

| Mục | Giá trị |
|:--|:--|
| Live URL nộp | `https://abg-team.vercel.app` |
| GitHub | `https://github.com/phanthutrang410/ABG_team` |
| API behind rewrite | EC2 `http://52.74.255.88:8000` · image `:d4r` · digest `sha256:2b01b24a233e374b655fab55bf8bf9be2ff886437c202a7a9b51e9d957f256a1` |
| Vercel dpl (D4r) | `dpl_7EFasiFPqP4HUCwoqKUSaBkoaRGi` |
| V05 | Done — Thu Trang nộp BTC; receipt ngoài repo |
| QA chain | V07 [18](18-v07-a05-smoke-uat-2026-07-18.md) → D4r [19](19-d4r-resmoke-2026-07-18.md) → V05 [16](16-stories-thu-trang.md) |

## 1. FR acceptance matrix (PRD §7 / DoD §10)

Mỗi FR: **Pass** = evidence UI/API/test; **Limit** = known-limit đã khóa (được phép nói trên slide/README); **N/A stretch** = không bắt buộc CP2.

| FR | Verdict | Evidence (repo / Live) | Limitation / claim rule |
|:--|:--|:--|:--|
| FR-01 Nạp EPU chuẩn hóa | **Pass** | `M05b`/`H15`/`H20` · [07 §5b](07-release-evidence.md) · Live import sem `73274079…` / att `78d7153f…` · `tests/test_h20_*` + `test_source_gate.py` | Raw semester ngoài git; chỉ path đã duyệt |
| FR-02 Feature điểm + chuyên cần | **Limit** | Điểm/học kỳ trên Live list/detail (band + `grade_*` factors) · D4b/D4r n=50 | Live mọi case `attendance_source_unapproved` / `data_state=partial` — **không** claim chuyên cần đủ trên Live; nhánh thiếu = fail-closed |
| FR-03 Coverage/freshness | **Pass** | Public `ReviewCase` coverage/limitations · `tests/test_h02_review_case_api.py` · A05 partial/`insufficient_data` | Partial attendance phản ánh limitation, không “ổn định” |
| FR-04 Mức ưu tiên + factors | **Pass** | Live bands `uu_tien_som`/`can_ra_soat` + factors; M02 `m02-baseline-0.1`; không LLM trên scoring path | Không lộ `model_score` |
| FR-05 List + detail | **Pass** | Live `GET /review-cases` state=ok n=50; detail `rc-s-00518c9485a9`; FE Vercel `/overview` 200 · V07+D4r | Không nhãn high-risk / raw score |
| FR-06 Human review | **Pass (API/UI code)** | `H03`/`G03` · `tests/test_h03_care_workflow.py` · `CareActions.tsx` Process §4 | Interactive care **SKIP** trên Live shared (V07/A05) — demo chỉ claim khi operator chạy trên môi trường được phép |
| FR-07 Care handoff | **Pass (API)** | Assign + `mapping_repair` · H03/H08 · `tests/test_h03_*` | Client không gửi `advisor_ref`; Live interactive SKIP |
| FR-08 Agent grounded | **Limit** | Backend mocked E2E H23–H26 · [07 §5c](07-release-evidence.md); Live POST explanation → `200 unavailable` fail-closed (no OpenAI key) · D4r | **Không** claim agent đã trả lời grounded trên Live; **không** claim Global Agent / weekly UI |
| FR-09 Fairness | **Pass (fail-closed)** | Live `/fairness/report` → `insufficient_data` + `no_approved_audit_attribute` · A05/D4r · `tests/test_h04_*` | Đúng PRD khi thiếu nhóm audit — không metric giả |
| FR-10 False-alarm / threshold | **Pass** | Live `/config/thresholds` + `/impact` aggregates · A05 · `tests/test_h04_*` · FE Threshold panel | Aggregates only; không PII |
| FR-11 Privacy/care copy | **Pass** | `copy.ts` H12a + banner H12b · A05 meta care copy · public API sạch | Không giám sát chat/camera; demo auth ≠ production RBAC |
| FR-12 Advisor draft (**stretch**) | **Limit** | API Live `GET /advisor-handoff-drafts` 200 `empty` (D4r); H22 tests; FE `/notify` 200 | **Không** SMTP; G06 Copy/`mailto:` **chưa** Done — không claim FE draft lô đã ship |

## 2. Rubric (VAIC / RULES §2) — xuất hiện trên sản phẩm

| Rubric | Evidence | Claim an toàn |
|:--|:--|:--|
| Privacy | Public envelopes không PII/`advisor_ref`/`model_score`; D3 scan; bulk export ẩn (D4r) | Pseudonym `student_ref` only |
| Care | Process §4 UI/API; copy “ưu tiên rà soát”; không kỷ luật tự động | Human-in-the-loop trước handoff |
| Fairness | Live `insufficient_data` khi thiếu audit attribute | Không công bố FPR giả |
| False-alarm / explainability | Threshold impact + factors trên case; agent fail-closed khi provider down | Factors từ model/API, không suy đoán LLM trên Live |

## 3. Known-limit cho README (`H09`) — không phải slide pack

> **Decision #25:** Hạ Giang + Văn Hải tự làm slide/pitch. Hoàng **không** duy trì claim-lock / skeleton slide / script pitch. Mục dưới chỉ phục vụ README + tránh overclaim nội bộ.

### An toàn khi mô tả sản phẩm (README / evidence)

1. Health + list→case ẩn danh (band, factors, limitations).
2. Fairness fail-closed (`insufficient_data`).
3. Threshold/impact aggregates.
4. Human-review có trong API/UI; mutate Live chỉ khi được phép.
5. Advisor draft API draft-only (có thể `empty`).
6. Agent endpoint fail-closed (`unavailable`) khi thiếu provider key.

### Cấm overclaim

1. Điểm danh/chuyên cần **đủ** trên Live (`attendance_source_unapproved`).
2. Agent grounded **đã trả lời** trên Live / live OpenAI.
3. Global Agent, weekly briefing UI, production RBAC.
4. Forecast / gated fusion / hybrid (FREEZE).
5. SMTP / auto-send; FE G06 Copy/`mailto:` Done.
6. EC2 FE `:3000` làm URL nộp.

`H12b` skeleton = **historical optional** — không bắt buộc cho D1.

## 4. CP2 checklist mapping → [07 §2](07-release-evidence.md)

| Checklist row | Status sau H16 |
|:--|:--|
| D4b smoke lần 1 | [x] |
| H27 Vercel candidate | [x] |
| V07 smoke độc lập | [x] |
| D4r fix→re-smoke | [x] |
| D3 GitHub scan | [x] |
| V05 BTC 2 URL | [x] |
| **H16 hoàn thiện evidence CP2** | **[x]** — doc này + pointer §2 |

Final-gate rows (§3: slide/video/README/AI log/V06) **không** tick trong H16.

## 5. Gaps còn mở (không block CP2 evidence)

| Gap | Owner tiếp | Note |
|:--|:--|:--|
| H09 README + known-limit | Hoàng | Unblocked bởi H16 |
| D1 / V02 / D2 slide-pitch-video | Hạ Giang + Văn Hải | **Self-owned** decision #25 — không chờ Hoàng doc |
| G06 FE mailto draft | Khánh Duy | Stretch FR-12 |
| Attendance Live partial | Duy/Giang/ops | Known-limit tới khi re-import/prove |
| D5 / V06 | Hoàng / Văn Hải | AI log + form cuối |
| FE scoping `cohort`/department | Hoàng chốt decision | Không tự thêm field |

## 6. Done when (H16)

- [x] FR-01…FR-11 có Pass hoặc Limit có path evidence.
- [x] FR-12 có Limit rõ (stretch).
- [x] CP2 §2 row H16 filled + tick.
- [x] Claim/limitation §3 sẵn cho **README H09** (không còn deliverable slide/pitch — decision #25).
- [x] Không tick final-gate giả.
