# Silent Shield — Agent Execution Guide

> **Bắt buộc trước mọi task:** đọc toàn bộ file này và [RULES.md](RULES.md). Nếu không đọc được một trong hai, dừng và báo blocker.

`RULES.md` định nghĩa ranh giới team/sản phẩm; file này định nghĩa cách agent thực hiện task.

## 1. Task loop bắt buộc

### A. Preflight

1. Xác định task ID, phase, owner chịu trách nhiệm, outcome và FR/rubric liên quan.
2. Đọc row/story trong [Sprint](docs/03-project/03-sprint.md) và tài liệu theo router ở mục 2.
3. Chạy `git status --short`; đọc diff hiện có, không ghi đè thay đổi ngoài task.
4. Đọc code, contract/fixture và test gần nhất trước khi sửa.
5. Xác nhận dependency/input contract và điều kiện bắt đầu. Nếu task tiền đề chưa Done, ghi `BLOCKED → <task ID>`; không bắt đầu bằng heuristic hoặc tự tạo fixture thay thế.
6. Chọn targeted test, verify và evidence path trước khi implementation.

Task review/diagnose/report là read-only nếu người dùng không yêu cầu sửa. Assumption làm thay đổi scope/contract phải được nêu rõ và xin owner chốt.

### B. Task Brief

Task chưa có brief thì agent tự điền trước khi sửa; micro-task không cần tạo file riêng.

```text
ID — Outcome:
Phase / Priority / Timebox:
Owner:
Depends on (task ID phải Done) + readiness:
Read first:
Input contract / fixture:
Scope / Do not touch:
Verify:
Evidence / Done when:
```

### C. Build

1. Thực hiện thay đổi nhỏ nhất tạo được outcome/vertical slice.
2. Viết hoặc cập nhật test cùng thay đổi; bug fix cần regression test phù hợp.
3. Chỉ sửa trong scope; muốn sửa artifact lane khác phải báo owner của artifact đó và cập nhật dependency nếu cần.
4. Không che lỗi bằng broad exception, bỏ assertion, skip test hoặc placeholder luôn pass.
5. Không tự fallback scoring/priority ở frontend khi API thiếu.
6. Contract breaking change phải cập nhật trong cùng handoff: schema → fixture → provider → consumer → test → docs.

### D. Verify

1. Chạy targeted checks sớm trong vòng lặp.
2. Chạy Quick verify trước khi review diff.
3. Chạy full/appropriate verify theo matrix ở mục 4.
4. Chạy `git diff --check`, xem lại toàn bộ diff và `git status --short`.
5. Không báo “pass” nếu có bước skip mà không ghi rõ.

### E. Handoff

Chỉ tick Done khi đáp ứng [Definition of Done](RULES.md#5-khi-nào-được-coi-là-done) và gửi:

```text
Task / outcome:
Files changed:
Contract/API changes:
Checks run + exact result/skips:
Acceptance/evidence paths:
Known gaps/risks:
Next consumer / task được mở khóa:
```

## 2. Read-first router

Mọi task: `RULES.md`, Sprint/task brief, file sẽ sửa và test gần nhất.

| Task | Đọc thêm |
|:---|:---|
| Product/copy/UX | [PRD](docs/02-product/04-prd.md), [Ethics](docs/02-product/05-ethics.md), [Process](docs/02-product/03-process.md), [Traceability](docs/01-requirements/03-traceability.md) |
| Data/ML/fairness | PRD §§4,7–8; [Signal catalog](docs/02-product/06-signal-catalog.md); Ethics §§5–6; data README; ML types/generator/tests |
| Backend/API/case | PRD §§5–8; Process §§3–6; decisions; API/data contract và test liên quan |
| Frontend | PRD §§5–8; Process state machine; Ethics access/copy; public API schema/validated fixture |
| Agent/LLM | PRD §5.4 + FR-08; Ethics §8; model/API/agent contract; [FPT API](docs/04-engineering/01-fpt-ai-api.md) |
| Docs/release/deploy | [Docs index](docs/README.md), VAIC rules, Sprint, `.env.example`, `.ai-log/README.md`, release/deploy checklist |

Nếu prose, fixture và code lệch nhau, không âm thầm chọn một bản: theo thứ tự nguồn trong `RULES.md` và ghi decision cần chốt.

## 3. Contract-first

Interface provider → consumer phải khóa:

- schema; required/optional/null semantics;
- error, empty, stale và `insufficient_data` states;
- case transition và hành động bị cấm;
- coverage, freshness, `model_version`, thời điểm tính và contributing factors;
- ground truth, threshold, denominator, sample size, provenance và quyền dùng nguồn/nhóm audit cho fairness.

Product meaning theo PRD/Ethics/Process. Interface theo Pydantic/OpenAPI hoặc schema code đã duyệt. JSON chỉ là fixture được contract test validate; frontend mock không phải source of truth.

## 4. Test và verify

| Thay đổi | Tối thiểu trước handoff |
|:---|:---|
| Docs/copy/board | Link local bị ảnh hưởng, traceability, `git diff --check`, Quick verify |
| Backend/API/DB | Targeted pytest happy + failure/edge, Ruff, full verify |
| Schema/data/ML/fairness | Determinism, invalid/missing input, công thức/ground truth/group separation, full verify |
| Frontend | Lint, production build, test/smoke hành vi và copy, full verify |
| Agent | Mocked grounding/refusal/adversarial tests; live eval chỉ khi task cho phép |
| Cross-layer/release | Full verify, API/UI smoke, `/health`, Live URL incognito, rollback/fallback |

```powershell
# Fast loop
.\scripts\verify.ps1 -Quick

# Targeted backend example
Push-Location backend
ruff check app tests
python -m pytest -q tests/test_health.py
Pop-Location

# Frontend
npm run lint --prefix frontend
npm run build --prefix frontend

# Full handoff/gate
.\scripts\verify.ps1
git diff --check
git status --short
```

Full verify mặc định loại `slow` và `eval`; không chứng minh live-agent evaluation. `npm test --prefix frontend` hiện là placeholder, chưa phải behavioral evidence. Chưa có automated docs-link/index checker, API E2E, contract/fairness/agent suite đầy đủ; phải ghi các gap này trong handoff.
