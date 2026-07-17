# Nhật ký công việc

## 2026-07-18 (~04:15 H10 Done)

- `M04` artifact đã có ([handoff](10-m04-data-ml-handoff.md)); `H10` khóa contract: [EPU](../04-engineering/04-epu-data-integration-contract.md), [Data-ML](../04-engineering/08-data-ml-scoring-fairness-contract.md), decision #17.
- Taxonomy: `Rút học phí`/`Bảo lưu` → `unknown`; pseudonym ngoài repo; attendance default cửa sổ/mốc + `attendance_source_unapproved` tới H15; copy keys cho H12a.
- Supersede synthetic contract → `09-synthetic-…`; P0.5 **Done**; mở `H06a`/`H19`/`M05a`/`H12a`/`H13`/`H06c`. H10 Done ≠ nguồn đã duyệt (`M05b`).

## 2026-07-18 (~04:00 D3 Done)

- `D3` Done: repo đã `visibility=public` (`https://github.com/phanthutrang410/ABG_team`); anonymous API/HTML 200.
- Scan tracked tree (`scripts/d3_pii_secret_scan.py` + gitleaks): không secret trong tree; 24 SĐT trong `02-team.md` / `Khao_sat_ABG_tong_hop.md` → redact cột Liên hệ `—`.
- Evidence: [10-d3-github-pii-secret-scan.md](10-d3-github-pii-secret-scan.md); private JSON dưới `.ai-log-private/` (gitignored). `.gitleaks.toml` allowlist false positive + ignored paths.
- Residual: SĐT vẫn có trong git history cũ (không rewrite). `D4`/`V07` còn chờ `H02`/`G02`/`D4`.

## 2026-07-18 (scope: điểm danh theo thời gian = MVP)

- Sửa decision #9/#13, RULES, PRD, problem, signal catalog (`CORE-03`), traceability, sprint, stories, architecture, EPU contract/catalog/persistence: **điểm danh theo thời gian thuộc MVP**, không Post-MVP.
- `H15` chuyển về P1/MVP (source approval). Forecast/gated fusion (`M07`/`M08`/`H14`/`H17`/`T04`) vẫn research/Post-MVP ngoài CP2.
- Thiếu nguồn điểm danh → `insufficient_data`; cấm tạo chuỗi giả.

## 2026-07-18 (persistence DB readiness)

- Theo yêu cầu chuẩn bị database cho các task sau, thêm `H19` (schema/migration DB rỗng) và `H20` (import fixture approved) trước `H08`. DB cũ chỉ được inventory metadata/pattern; không copy schema/row/raw export.
- Chưa có M04, M05b hay artifact data-owner approval trong workspace: không nạp V59, `epu_data` hay synthetic. `H20` phải rollback nếu thiếu approval/hash/count/schema/PII gate.

## 2026-07-18 (~03:20 re-verify H06b / H07 / H05b)

- Re-audit DoD: transition API + templates + runbook đã đủ; chỉ sửa nit `.ai-log/README.md` example path `03-system-architecture` → `05-system-architecture`.
- Checks: `ruff check app tests` pass; `pytest -q tests/test_case_transitions.py` → 15 passed; `.\scripts\verify.ps1 -Quick` (xem kết quả cùng handoff).
- Verdict giữ Done cho cả ba; chưa commit (theo yêu cầu).

## 2026-07-18 (~02:40 board merge — H06b / H07 / H05b)

- `H06b` Done: Process §4 transitions + forbidden actions + `advisor_ref` gate dưới `/cases`; `backend/app/cases/*`, `main.py`, `tests/test_case_transitions.py` (15 xanh; Quick+full verify). Gap: in-memory store; chưa full public ReviewCase (`H06a`). `H03` còn `BLOCKED → H08`.
- `H07` Done: [deploy runbook](../04-engineering/06-deploy-runbook.md) draft từ arch, không secret; linked docs index + arch; finalize Live/smoke/rollback tại `D4`. `D4` còn `BLOCKED → H02, G02, D3`.
- `H05b` Done: `.ai-log/templates/*` + release-evidence template; pointer README/`07-release-evidence` only. Mở `V08`.

## 2026-07-18 (~H05a Done)

- `H05a` Done: [kiến trúc tối thiểu](../04-engineering/05-system-architecture.md); Process §4 khóa ma trận transition + mã API + `defer`/`advisor_ref` gate; PRD FR-06/07 + product statement; banner Target vs MVP trên BRD/scope; decision #15; index docs.
- Mở khóa `H06b`, `H07`, `H05b`. `H10`/`H13`/`H12a` vẫn chờ `M04` (và H10). P0.5 còn một chân `M04`.

## 2026-07-18 (~02:10 board recovery)

- P0.5 **chưa qua** (H05/M04 vẫn TODO lúc ~02:03): cập nhật [Sprint](03-sprint.md) recovery plan; tách choke-point docs `H05a/b`, `H11a/b`, `H12a/b`; thêm `D4r` (QA→fix→re-smoke); `H16` phụ thuộc thêm `V05`.
- Đồng bộ Process state machine cho `H06b`/`H03`; `H03` phụ thuộc `H08` + test thiếu `advisor_ref`; tách `M05a/b`; M06 = domain + manifests; reopen `M01` + `H18` + `G05` thay mock; `M07` sau `M02/H02/H13`; `M08`←`M02+H14+H15`, `T04`←`H17`.
- Cập nhật stories giang/Văn Hải, [release evidence](07-release-evidence.md), [EPU contract](../04-engineering/04-epu-data-integration-contract.md).

## 2026-07-18 (điều chỉnh ownership + hybrid research)

- Theo phân công mới, [Sprint](03-sprint.md) giao mọi tài liệu/contract/evidence Markdown cho **Hoàng**; code/build chỉ thuộc Hoàng, Khánh Duy, Giang và Thu Trang. **giang** và **Văn Hải** bắt đầu task từ P2: UAT/QA/review, slide–mô tả asset, rehearsal/video và submission.
- Thêm M07 để Duy nghiên cứu forecasting điểm danh + gated fusion. Research-only cho forecast/fusion: không tự tạo weekly attendance giả. **Sửa sau:** `H15` (source approval điểm danh) thuộc MVP; chỉ `M08`/`H17`/`T04` (và `H14` research contract) là Post-MVP/forecast ngoài CP2.
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
