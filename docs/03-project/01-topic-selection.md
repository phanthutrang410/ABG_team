# Phân tích và quyết định chọn đề — VAIC 2026

> Mục tiêu: xét **6 đề mới** của BTC, chấm mức độ *transfer* được từ repo **EduInsight** (Learning Analytics đã build), và đề xuất chọn đề nào + việc cần làm.

> **Trạng thái:** tài liệu quyết định lịch sử tại đầu sprint. Sau khi chọn Silent Shield, yêu cầu nguồn nằm trong [Problems Brief](../01-requirements/02-problems-brief.md), phạm vi thực thi nằm trong [PRD](../02-product/04-prd.md), và khác biệt được ghi tại [Truy vết yêu cầu](../01-requirements/03-traceability.md).

---

## 0. Tài sản hiện có của EduInsight (căn cứ để chấm transfer)

Đây là "vốn" đang có, quyết định đề nào tái sử dụng được nhiều:

| Khối tài sản | Vị trí | Nội dung |
|:--|:--|:--|
| **ML cảnh báo sớm dropout** | `backend/app/ml/dropout/` (dataset, train, evaluate, score, types) | Pipeline hoàn chỉnh: huấn luyện, đánh giá, chấm điểm rủi ro từ feature học vụ; prediction có version, thời điểm, **yếu tố đóng góp (explainable)** |
| **ML rủi ro môn học** | `app/ml/course_risk.py`, `aggregation.py`, `scoring.py` | Chấm rủi ro cấp môn, tổng hợp theo SV–học kỳ |
| **Model can thiệp** | `app/models/intervention.py` | ĐÃ có sẵn khái niệm *intervention / handoff cho con người* |
| **AI Agent (LangGraph ReAct)** | `app/agent/` (graph, tools, guardrails, prompts, RBAC context, report tools) | Agent read-only, giải thích số liệu, không bịa xác suất; có guardrails |
| **DWH + ETL + Data Quality** | `app/analytics/etl.py`, star schema, schema `dwh` | Kho phân tích lịch sử, ETL idempotent, nhật ký chất lượng dữ liệu |
| **CLO/PLO (chuẩn đầu ra)** | `app/analytics/clo.py`, `health_score.py` | Mapping điểm thành phần → mức đạt chuẩn; health score |
| **RAG chương trình đào tạo** | `app/rag/ctdt_corpus.py`, `ctdt_retrieval.py` | Retrieval trên corpus CTDT (pgvector) |
| **Dashboard đa cấp** | frontend Next.js 16 | Trường→Khoa→Ngành→Chuyên ngành→Môn→Lớp→SV, drill-down, filter, deep link |
| **RBAC + Observability** | `app/agent/context_rbac.py`, auth | 5 role, phạm vi theo khoa/lớp/SV; trace, event log, dashboard giám sát |
| **Hạ tầng deploy** | Docker, Vercel + AWS EC2, Caddy TLS | Đã live, có backup, uptime monitor |

**Điểm mạnh cốt lõi để tái dùng:** *ML cảnh báo sớm có giải thích + Agent giải thích số liệu + Dashboard đa cấp + DWH + RBAC + đã deploy live.*

**Điểm yếu cần lưu ý:** EduInsight hướng **đại học/khoa**, sinh viên là *đối tượng được phân tích* (không phải người dùng đăng nhập). Không có: nội dung học K-12, sinh trắc/knowledge-graph tiên quyết, OCR/TTS, dữ liệu thị trường lao động.

---

## 1. Bảng chấm nhanh 6 đề

| # | Đề | Đơn vị | Domain | % Transfer | Chất lượng cơ hội | Kết luận |
|:-:|:--|:--|:--|:-:|:--|:--|
| 1 | **The Silent Shield** (cảnh báo sớm bỏ học/khủng hoảng) | Duy Tân | Early-warning giáo dục | **~75%** | Cao | ✅ **Chọn #1** |
| 2 | **AI Personalization & Content** (EduOne) | STEAM for Vietnam | Adaptive learning + gen content | **~45%** | Cao (đối tác uy tín, deliverable rõ) | ✅ Ứng viên #2 |
| 3 | **Adaptive tutor** (lớp học đa trình độ) | Duy Tân | Chẩn đoán lỗ hổng kiến thức | ~40% | Trung bình-cao | ⚠️ Cân nhắc |
| 4 | **Career Compass** (định hướng nghề) | Duy Tân | Thị trường lao động + hồ sơ SV | ~30% | Trung bình | ⚠️ Yếu transfer |
| 5 | **Adaptive tutor – nhánh du lịch bản địa** (đoạn dán lỗi trong đề 1) | Duy Tân | Matching du lịch cộng đồng | ~10% | — | ❌ Khác hẳn domain |
| 6 | **Audiobook từ sách scan** | Vbee AITalk | OCR + TTS pipeline | **~10%** | Cao nhưng lệch năng lực | ❌ Gần như build lại |

> Lưu ý: đề "Adaptive tutor" bị **dán lẫn** một đoạn brief khác (du lịch bản địa: matching cung–cầu, định giá, phân phối lợi ích cộng đồng). Đó là 2 đề khác nhau ghép nhầm — phần du lịch (#5) không liên quan repo.

---

## 2. Phân tích từng đề

### ✅ Đề 1 — The Silent Shield (KHUYẾN NGHỊ CHỌN)

**Yêu cầu:** Hệ thống **cảnh báo sớm** cho người học có thay đổi cần được quan tâm, dựa trên **tín hiệu không xâm phạm**: dao động điểm, chuyên cần và thay đổi hành vi học theo thời gian. Bản solution brief sau khi chọn đề sử dụng bối cảnh sinh viên và Ban Lãnh đạo Khoa/Trường.
**3 ràng buộc bắt buộc (trọng số cao):** (1) bảo vệ quyền riêng tư tối đa — *không* giám sát nội dung/tin nhắn riêng; (2) chỉ **hỗ trợ con người** can thiệp qua chăm sóc — không dán nhãn, không kỷ luật tự động, không thiên vị nhóm yếu thế; (3) **công bằng** — cảnh báo không lệch theo kinh tế/dân tộc.
**Chấm điểm:** đạo đức & riêng tư (cao nhất), độ chính xác + **kiểm soát báo động giả**, công bằng nhóm, chất lượng bàn giao cho con người.

**Vì sao transfer tốt nhất (~75%):**
- `ml/dropout/` **chính là** engine cảnh báo sớm cần có — cần thu hẹp feature cho MVP thành điểm và chuyên cần theo thời gian, đồng thời giữ output có giải thích.
- Prediction đã **có yếu tố đóng góp** → phục vụ giải thích + kiểm soát báo động giả.
- `models/intervention.py` đã có → khớp "bàn giao cho con người".
- Dashboard đa cấp + RBAC theo phạm vi → giáo viên/tư vấn xem đúng phạm vi.
- Agent giải thích số liệu, **không bịa** → đúng tinh thần "hỗ trợ, không dán nhãn".

**Việc cần làm (delta):**
1. **Chốt domain và actor:** solution brief đặt Ban Lãnh đạo Khoa/Trường là primary system user; GVCN/cố vấn và đơn vị hỗ trợ nhận handoff đã duyệt.
2. **Feature engineering theo thời gian:** thêm chuỗi thời gian điểm danh, dao động điểm (không chỉ snapshot GPA); phát hiện *thay đổi xu hướng*.
3. **Lớp Fairness (mới, trọng số cao):** đo & báo cáo chênh lệch cảnh báo theo nhóm (kinh tế/dân tộc); có metric fairness (equalized odds / demographic parity), có báo cáo bias trong UI.
4. **Lớp Privacy-by-design:** khẳng định pipeline chỉ dùng tín hiệu meta (điểm/điểm danh/hành vi tổng hợp), *không* nội dung riêng tư; tài liệu DPIA ngắn.
5. **Kiểm soát báo động giả:** tối ưu ngưỡng theo *precision*/chi phí sai (false positive gây hại); calibration; cho phép giáo viên phản hồi để hiệu chỉnh.
6. **Luồng handoff:** mở rộng `intervention` thành quy trình care (gợi ý ai cần hỗ trợ trước, ghi nhận hành động, không kỷ luật).
7. **Dữ liệu:** tạo synthetic dataset đúng domain đã chốt, có chuỗi thời gian, outcome synthetic rõ để đo FPR và thuộc tính nhóm chỉ cho fairness audit.

**Rủi ro:** đề nhấn *đạo đức/công bằng* trọng số cao — phải làm thật (metric + tài liệu), không chỉ nói. Dataset và persona demo phải thống nhất với solution brief.

---

### ✅ Đề 2 — AI Personalization & Content Creation (EduOne / STEAM for Vietnam)

**Yêu cầu:** (1) gợi ý **lộ trình/bài tập theo trình độ real-time** cho từng học sinh (thay vì 1 path chung, dropout >50%); (2) **tăng tốc tạo bài học** bằng AI draft + **có bước con người duyệt** trước khi publish.
**Deliverable:** prototype demo (URL/video), **GitHub công khai**, kiến trúc AI **giải thích được** (vì sao gợi ý path/content này), roadmap pilot 1–2 trang. Tiếng Việt bắt buộc. Pilot: 1 khóa/1 lớp/20 HS.
**Anti-pattern:** chỉ chạy trên data sạch, content tới HS mà không review, demo mockup không có AI thật, phụ thuộc hoàn toàn API trả phí đắt.

**Transfer (~45%):** hạ tầng dùng lại tốt — auth/RBAC, Agent + explainability, dashboard, RAG (`ctdt_corpus`), deploy live, đã có "explainable AI architecture" (điểm cộng deliverable). **Core mới:** engine gợi ý lộ trình adaptive + công cụ sinh nội dung có human-review.

**Việc cần làm:**
1. Recommendation engine theo trình độ (item difficulty, mastery/knowledge tracing đơn giản) — real-time, có **log gợi ý per-student** (demo yêu cầu).
2. Content authoring: LLM draft bài học + màn hình **human review** trước publish (bắt buộc).
3. Reuse Agent để làm phần "explainable" (vì sao path này) — repo đã có sẵn methodology đánh giá agent.
4. Roadmap pilot với EduOne (1–2 trang).
5. Chú ý anti-pattern: tránh phụ thuộc API đắt (hợp với model tiering đã có).

**Điểm cộng:** đối tác uy tín (STEAM), rubric rõ, đúng "chất" learning-analytics của repo. **Điểm trừ:** phải build tính năng adaptive path + gen content gần như mới.

---

### ⚠️ Đề 3 — Adaptive Tutor cho lớp học đa trình độ (Duy Tân)

**Yêu cầu:** Chẩn đoán **lỗ hổng kiến thức gốc rễ** (VD sai Toán lớp 7 vì hổng phân số lớp 5), sinh **lộ trình luyện tập cá nhân** đúng chỗ hổng; **dashboard giáo viên bắt buộc**: gom nhóm HS theo nhu cầu, gợi ý giúp ai trước, phát hiện lỗ hổng toàn lớp. Ràng buộc: **offline/low-bandwidth**, bám Chương trình GDPT 2018.
**Chấm:** chính xác chẩn đoán *gốc rễ*, cải thiện học tập, giá trị thực cho GV, chạy trên thiết bị yếu.

**Transfer (~40%):** dashboard đa cấp + gom nhóm + Agent giải thích + CLO (`analytics/clo.py`) tái dùng tốt cho phần "lỗ hổng theo chuẩn". **Core mới & khó:** knowledge graph tiên quyết (prerequisite mapping) để truy *gốc rễ*, nội dung K-12 theo GDPT 2018, ràng buộc **offline** (nghịch với kiến trúc cloud hiện tại).

**Việc cần làm:** xây knowledge graph môn/lớp; engine truy nguyên gốc rễ; ngân hàng bài tập GDPT 2018; kiến trúc chạy offline/edge (mâu thuẫn stack cloud → tốn công). **Rủi ro cao ở ràng buộc offline.**

---

### ⚠️ Đề 4 — Career Compass (Duy Tân)

**Yêu cầu:** Phân tích **cầu kỹ năng từ dữ liệu tuyển dụng** (job posting, kỹ năng, lương, xu hướng theo vùng/thời gian); xây hồ sơ năng lực–sở thích HS qua tương tác; gợi ý lộ trình học/nghề **giải thích được** (gồm hướng nghề, không chỉ ĐH). Ràng buộc đạo đức: mở rộng lựa chọn, chống thiên kiến giới/vùng.
**Chấm:** chất lượng trích tín hiệu kỹ năng, cá nhân hóa + explainability, chống thiên kiến (trọng số cao), hữu ích thực tế.

**Transfer (~30%):** dùng lại được Agent + explainability + `crawl/` infra + anti-bias mindset. Nhưng **domain lệch hẳn**: dữ liệu thị trường lao động (không phải hồ sơ học vụ), phải crawl + NLP trích kỹ năng từ job posting — gần như dự án dữ liệu mới.

---

### ❌ Đề 5 — Nhánh "du lịch bản địa" (đoạn dán nhầm trong đề 1)

Matching cung–cầu du khách ↔ hộ dân/bản làng, tạo hồ sơ bán tự động từ mô tả giọng nói tiếng địa phương + ảnh, gợi ý giá & quản lý sức chứa, tối ưu phân phối lợi ích cộng đồng. **Không liên quan repo** (~10%). Bỏ qua trừ khi BTC xác nhận đây là đề riêng muốn làm.

---

### ❌ Đề 6 — Audiobook từ sách scan (Vbee AITalk)

Pipeline: ảnh scan → tiền xử lý ảnh (deskew, khử bóng gáy) → **OCR tiếng Việt** → ghép văn bản qua trang → trích cấu trúc chương/mục → đọc bảng/ảnh tự nhiên → trang soát lỗi → **TTS batch (Vbee API) + SSML** → xuất m4b/MP3 + web player đồng bộ text-audio. NFR: sách 200 trang < 30 phút, pipeline resume được.

**Transfer (~10%):** chỉ dùng lại scaffolding deploy/pipeline chung. Toàn bộ năng lực cốt lõi (OCR, xử lý ảnh, TTS, player đồng bộ) là **mới hoàn toàn** — lệch hẳn khỏi thế mạnh learning-analytics. **Không khuyến nghị** nếu muốn tái dùng repo.

---

## 3. Khuyến nghị

**Chọn "The Silent Shield" (Đề 1).** Lý do:
- **Transfer cao nhất (~75%)**: `ml/dropout/` + `intervention` + explainable prediction + dashboard + RBAC gần như đúng bài.
- Đúng thế mạnh đã chứng minh (đã có hệ cảnh báo sớm live).
- Delta rõ ràng, làm được: feature theo thời gian + lớp Fairness + Privacy + kiểm soát báo động giả + luồng handoff.

**Phương án dự phòng: EduOne (Đề 2)** nếu muốn đối tác uy tín + rubric rõ + deliverable thân thiện (GitHub công khai, explainable — repo đã sẵn). Đổi lại phải build adaptive path + gen content.

**Đề nghị bước tiếp theo (khi bạn chốt):**
- Nếu chọn Đề 1: chốt **kế hoạch chi tiết** — feature theo thời gian, thiết kế Fairness/Privacy, synthetic dataset đúng domain và checklist bám 4 tiêu chí chấm.
- Nếu chọn Đề 2: tôi phác kiến trúc recommendation + luồng human-review + roadmap pilot EduOne.

---

### Phụ lục — Mức tái dùng theo khối tài sản

| Khối tài sản | Đề 1 Silent Shield | Đề 2 EduOne | Đề 3 Tutor | Đề 4 Career | Đề 6 Audiobook |
|:--|:-:|:-:|:-:|:-:|:-:|
| ML cảnh báo sớm (dropout) | ★★★ | ★ | ★ | – | – |
| Intervention/handoff | ★★★ | ★ | ★★ | ★ | – |
| Agent + explainability | ★★ | ★★★ | ★★ | ★★ | ★ |
| Dashboard đa cấp | ★★★ | ★★ | ★★★ | ★ | – |
| DWH/ETL | ★★ | ★★ | ★ | ★ | – |
| CLO/RAG chương trình | ★ | ★★ | ★★★ | ★ | – |
| RBAC + Observability | ★★★ | ★★ | ★★ | ★ | ★ |
| Hạ tầng deploy | ★★★ | ★★★ | ★★ | ★★ | ★★ |

★★★ dùng gần nguyên · ★★ dùng lại có sửa · ★ chạm nhẹ · – không dùng
