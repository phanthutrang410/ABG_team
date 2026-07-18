# H12b — Asset / claim-copy skeleton (Hạ Giang D1)

> **Owner khóa copy:** Hoàng · **Consumer slide/mô tả:** Hạ Giang (`giang`) task `D1` · **Status:** skeleton sẵn dùng  
> Nguồn: [PRD](../02-product/04-prd.md) §§2,4,9 · [Ethics](../02-product/05-ethics.md) §4 · [Signal catalog](../02-product/06-signal-catalog.md) CORE-03 · runtime `frontend/src/lib/copy.ts`  
> **Không** thay PRD/Ethics. **Không** dùng screenshot Live cho đến `D4r`. Sprint status do owner board cập nhật riêng.

## 1. Một dòng phạm vi (dùng trên slide mở / mô tả ngắn)

```
Silent Shield hỗ trợ Ban Lãnh đạo ưu tiên tín hiệu cần rà soát từ điểm theo học kỳ và điểm danh theo thời gian (khi có nguồn đã duyệt); con người duyệt trước bàn giao. Forecasting/fusion (hybrid) chưa ship.
```

## 2. Claim matrix (copy vào slide / checklist A05–D1)

| ID | Được phép? | Claim (VI trung lập) |
|:--|:--|:--|
| mvp-signals | Có | MVP: tín hiệu từ điểm theo học kỳ + điểm danh theo thời gian (nguồn đã duyệt/pseudonymize). |
| human-review | Có | Con người phê duyệt / loại / hoãn trước khi bàn giao; không kỷ luật tự động. |
| attendance-mvp-insufficient | Có | Điểm danh theo thời gian = **MVP**; thiếu nguồn `H15` → `insufficient_data` trên nhánh chuyên cần — **không** gọi là Post-MVP. |
| fairness-fail-closed | Có | Fairness chỉ công bố metric khi có thuộc tính audit đã duyệt + cỡ mẫu đủ; nếu không → `insufficient_data`. |
| agent-grounded | Có | Agent chỉ giải thích đầu ra model/API đã có (backend HTTP / Swagger); không tự tính điểm hay suy đoán nguyên nhân. **Không** claim FE Agent chat UI. |
| forecast-hybrid-shipped | **Không** | Cấm claim forecasting / gated fusion / hybrid đã ship hoặc nằm trong demo MVP. |
| attendance-post-mvp | **Không** | Cấm gọi điểm danh theo thời gian là Post-MVP / ngoài phạm vi khi thiếu nguồn. |
| raw-risk-label | **Không** | Cấm “Điểm rủi ro”, *high-risk student*, chẩn đoán bỏ học / sức khỏe tâm thần. |

Canonical strings cũng export trong FE: `ASSET_CLAIMS` / `BANNER_COPY` tại [`frontend/src/lib/copy.ts`](../../frontend/src/lib/copy.ts). Banner UI: dashboard `ScopeBanner`.

## 3. Outline slide skeleton (chưa cần screenshot)

| # | Slide | Nội dung khóa từ bảng trên | Chưa làm tới khi |
|:-:|:--|:--|:--|
| 1 | Vấn đề + product statement | §1 + mvp-signals | — |
| 2 | Phạm vi dữ liệu MVP | attendance-mvp-insufficient; nêu `H15` nếu nhánh chuyên cần fail-closed | Live evidence |
| 3 | Care / human review | human-review; thuật ngữ “tín hiệu cần rà soát” / “mức độ ưu tiên rà soát” | — |
| 4 | Fairness + privacy | fairness-fail-closed; không PII / không giám sát chat-camera | — |
| 5 | Agent grounded | agent-grounded | H26 + API/Swagger (không cần FE Agent UI) |
| 6 | Demo path + giới hạn | List→case→review; **ghi rõ** forecast/hybrid = research/blocked | `D4r` URL + `H16` |
| 7 | Không claim | Ba hàng **Không** ở §2 | Luôn |

## 4. Runtime vs asset

| Loại | Khóa ở đâu | Dùng khi |
|:--|:--|:--|
| H12a reason-code copy | `COPY` / Data-ML §6 | UI/agent khi API trả `reason_codes` |
| H12b banner + claim | `BANNER_COPY` / `ASSET_CLAIMS` + doc này | Banner dashboard + slide/mô tả nộp |

## 5. Hạ Giang — cách dùng ngay

1. Copy bảng §2 vào checklist claim-copy (`A05` / `D1`); đánh dấu pass/fail theo sản phẩm thật khi có Live.
2. Dựng outline §3 làm khung slide; để trống chỗ screenshot tới `D4r`.
3. Chỉ lấy thêm message/limitation từ `H16` + Live đã re-smoke — không invent claim mới.
4. Nếu lệch copy: gửi gap cho Hoàng; **không** sửa PRD/Ethics/contract.

Story: [08-stories-giang.md](08-stories-giang.md) · Board: [03-sprint.md](03-sprint.md) (`H12b`, `D1`).
