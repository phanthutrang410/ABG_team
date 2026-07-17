# H13 — Checkpoint 1: nội dung paste BTC

> **Owner nộp:** Hoàng · **Deadline:** 11:00 18/7/2026 · **Status nội dung:** sẵn sàng paste · **Status form/receipt:** BLOCKED → human BTC submit  
> Nguồn: [topic-selection](01-topic-selection.md), [PRD](../02-product/04-prd.md), [VAIC rules](../01-requirements/01-vaic-rules.md).  
> **Không claim:** hybrid/forecast đã ship; “Điểm rủi ro” / raw score; chuyên cần = Post-MVP; “xu hướng dài hạn”.

Copy từng khối bên dưới vào form BTC (4 trường). Không invent URL form trong repo.

---

## 1. Tên dự án

```
Silent Shield
```

## 2. Track / vấn đề đã chọn

```
The Silent Shield — cảnh báo sớm (early-warning) cho người học có thay đổi cần được quan tâm (Đơn vị đề: Duy Tân).
```

## 3. Mô tả ngắn giải pháp

```
Silent Shield hỗ trợ Ban Lãnh đạo Khoa/Trường ưu tiên quan tâm đúng lúc tới sinh viên có thay đổi học vụ cần rà soát, dựa trên tín hiệu không xâm phạm: điểm theo học kỳ và điểm danh theo thời gian (khi có nguồn đã duyệt/pseudonymize). Hệ thống tạo tín hiệu cần rà soát kèm yếu tố đóng góp, độ phủ và độ mới dữ liệu; con người phê duyệt, loại bỏ hoặc hoãn trước khi bàn giao cho GVCN/cố vấn hay đơn vị hỗ trợ. AI baseline chỉ sinh mức ưu tiên rà soát và yếu tố giải thích; agent LLM chỉ giải thích đầu ra đã có, không tự tính điểm hay suy đoán nguyên nhân. Không chẩn đoán, không dán nhãn, không quyết định bất lợi tự động. Khi thiếu chuỗi điểm danh đã duyệt, nhánh chuyên cần trả insufficient_data — điểm danh theo thời gian vẫn thuộc MVP, không đẩy ra ngoài phạm vi.
```

## 4. Hướng tiếp cận dự kiến

```
Khóa contract dữ liệu và scoring trước (tích hợp EPU + Data-ML), rồi envelope public an toàn → schema/persistence → baseline ML trên điểm theo kỳ và chuyên cần theo thời gian → API/UI quy trình care và agent giải thích grounded. Ưu tiên privacy-by-design, human-in-the-loop và fail-closed khi thiếu dữ liệu. Forecasting/fusion điểm danh (hướng hybrid) chỉ nghiên cứu sau baseline MVP; không nằm trong phạm vi tuyên bố tại Checkpoint 1/2.
```

---

## Việc còn lại (human)

1. Mở form Checkpoint 1 do BTC cung cấp (ngoài repo — không ghi URL giả).
2. Dán 4 khối trên; gửi trước **11:00**.
3. Lưu link/receipt xác nhận → điền cột Evidence và tick checklist tại [07-release-evidence.md](07-release-evidence.md) §1 (hàng form + xác nhận).
4. Chỉ khi có receipt mới tick `H13` Done trên Sprint.
