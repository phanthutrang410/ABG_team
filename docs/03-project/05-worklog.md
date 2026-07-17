# Nhật ký công việc

## 2026-07-18 (~02:10 board recovery)

- P0.5 **chưa qua** (H05/M04 vẫn TODO lúc ~02:03): cập nhật [Sprint](03-sprint.md) recovery plan; tách choke-point docs `H05a/b`, `H11a/b`, `H12a/b`; thêm `D4r` (QA→fix→re-smoke); `H16` phụ thuộc thêm `V05`.
- Đồng bộ Process state machine cho `H06b`/`H03`; `H03` phụ thuộc `H08` + test thiếu `advisor_ref`; tách `M05a/b`; M06 = 4 domain + manifests; reopen `M01` + `H18` + `G05` thay mock; `M07` sau `M02/H02/H13`; `M08`←`M02+H14+H15`, `T04`←`H17`.
- Cập nhật stories giang/Văn Hải, [release evidence](07-release-evidence.md), [EPU contract](../04-engineering/04-epu-data-integration-contract.md).

## 2026-07-18 (điều chỉnh ownership + hybrid research)

- Theo phân công mới, [Sprint](03-sprint.md) giao mọi tài liệu/contract/evidence Markdown cho **Hoàng**; code/build chỉ thuộc Hoàng, Khánh Duy, Giang và Thu Trang. **giang** và **Văn Hải** bắt đầu task từ P2: UAT/QA/review, slide–mô tả asset, rehearsal/video và submission.
- Thêm M07 để Duy nghiên cứu hybrid feature theo học kỳ + attendance forecasting. Đây là research-only: không tự tạo weekly attendance, fixture hay endpoint. H15/M08/T04 là Post-MVP và bị block đến khi data owner phê duyệt export pseudonymized, provenance và contract.
- Agent chỉ giải thích priority/evidence/limits do model/API trả về; không tạo hoặc khẳng định dropout risk cho sinh viên.

## 2026-07-18 (tái cấu trúc task)

- Chuẩn hóa [Sprint](03-sprint.md) thành một board định nghĩa task duy nhất: mỗi ID có **một owner**, outcome/artifact, DoD, verify/evidence và `Depends (phải Done)`.
- Bỏ vai trò nghiệm thu riêng khỏi task/story/release checklist. Task bị thiếu đầu vào phải ghi `BLOCKED → <task ID>`; không còn slot chưa đặc tả hoặc polish ad-hoc không ID.
- Đồng bộ [RULES.md](../../RULES.md), [AGENTS.md](../../AGENTS.md), stories giang/Văn Hải và [release evidence](07-release-evidence.md) theo quy ước này.

## 2026-07-18 (data reset EPU)

- Theo catalog EPU, loại pipeline synthetic cũ: không tạo chuỗi tuần/chuyên cần, nhãn outcome, thuộc tính fairness hoặc mapping GVCN giả để lấp field thiếu.
- Thêm [hợp đồng tích hợp EPU](../04-engineering/04-epu-data-integration-contract.md) và task M05 (source gate), M06 (extract/pseudonymize/normalize), H08 (DTO/fixture cho Hoàng). V59 và `epu_data` vẫn là candidate đến khi data owner xác nhận provenance/quyền sử dụng.
- Snapshot đã kiểm tra: V59 và `epu_data` không có `MSSV` giao nhau; M06 không được cross-join hai nguồn. Fairness thiếu nhóm audit hợp lệ phải trả `insufficient_data`.

## 2026-07-18 (đêm ~00:30)

- Bổ sung story non-tech cho **giang** và **Văn Hải**: [08-stories-giang.md](08-stories-giang.md), [09-stories-van-hai.md](09-stories-van-hai.md); mở rộng mô tả lane A/V trong [03-sprint.md](03-sprint.md) (P0.5→P3) bằng ngôn ngữ nghiệp vụ + link checklist

## 2026-07-17 (tối ~22:30)

- Nâng [03-sprint.md](03-sprint.md) theo format SprintPlanning tham khảo: 4 gate + **P0.5 Architecture Lock**; task docs/thiết kế đầy đủ cho 6 người. Cơ chế phân công và các slot chưa đặc tả của bản ghi này đã được thay bằng board one-owner có dependency/evidence ở mục 2026-07-18 bên trên.
- Lane 48h: Giang = FE, Thu Trang = agent; threshold/FP thuộc Khánh Duy
- Đồng hồ gắn Checkpoint 1 (11:00 18/7), Checkpoint 2 (23:00 18/7), đóng cổng (11:00 19/7)

## 2026-07-17 (chiều)

- P0 done: H01 backend `/health` + schemas `dwh`/`ml`, M01 synthetic CSV (40 hồ sơ), G01 Next.js dashboard mock
- Đối chiếu [Problems Brief](../01-requirements/02-problems-brief.md): chốt Ban Lãnh đạo là primary user, viết lại PRD/ethics, tách danh mục tín hiệu và ghi [các độ lệch còn mở](../01-requirements/03-traceability.md)
- Docker Postgres `vaic2026-db-1` up; `.env` created (cần điền `FPT_API_KEY`)
- Chưa xong: AWS creds invalid, `GITHUB_TOKEN` user env, LangSmith khi T02

## 2026-07-17

- Chọn đề Silent Shield (~75% transfer từ EduInsight) — [Quyết định chọn đề](01-topic-selection.md)
- Bootstrap skeleton tối giản + chuyển MD gốc vào `docs/`
- Phân lane H/M/G/T/A/V/D — [Đội ngũ và phân vai](02-team.md)
