# Nhật ký AI (D5)

**Owner:** Văn Hải - V· **Mọi thành viên** tự ghi lại việc dùng AI của mình vào đây trước khi nộp.

**Cấm:** commit session thô, API key, `.env`, PII (dữ liệu cá nhân thật). Git log ≠ nhật ký AI mà phải ghi thủ công.

---

## 1. Vì sao phải làm việc này

BTC (VAIC) yêu cầu chứng minh sản phẩm không làm hoàn toàn bằng AI mà không kiểm soát. Thiếu nhật ký AI = có thể bị loại ở vòng chấm, dù sản phẩm tốt.

## 2. Làm gì:

### Bước 1 — Ghi 1 dòng vào `manifest.csv` sau mỗi phiên làm việc quan trọng
Mỗi khi bạn dùng AI để hoàn thành một task có ý nghĩa (viết doc, sinh code, debug...), thêm 1 dòng:

```csv
session_id,member,tool,started_at,ended_at,task_id,purpose,result,artifacts,commit_sha,evidence_type,evidence_ref,screenshot,redactions,review_status
20260717-H01-hoang-codex-01,Hoàng,Claude Code,2026-07-17T22:30,2026-07-17T23:10,H05,Viết architecture doc + mermaid diagram,done,docs/04-engineering/03-system-architecture.md,a1b2c3d,file,,,,pending
```

**Giải thích cột:**
| Cột | Ý nghĩa |
|---|---|
| `session_id` | Định dạng gợi ý: `YYYYMMDD-<TaskID>-<tên>-<tool>-<số thứ tự>` |
| `member` | Tên trên board (Hoàng, Khánh Duy, Giang, Thu Trang, giang, Văn Hải) |
| `tool` | Claude Code / Claude.ai / ChatGPT / Cursor / Codex... |
| `started_at` / `ended_at` | Giờ bắt đầu/kết thúc (ISO, UTC+7) |
| `task_id` | ID task trên board sprint (VD: H05, M02, V03) |
| `purpose` | Mô tả ngắn mục đích để làm gì |
| `result` | done / partial / abandoned |
| `artifacts` | Đường dẫn file/output tạo ra |
| `commit_sha` | SHA commit liên quan (nếu có) |
| `evidence_type` | file / link / screenshot |
| `evidence_ref` | Link tới bằng chứng (nếu là link) |
| `screenshot` | Đường dẫn ảnh chụp (nếu có, để trong Drive private — xem bước 3) |
| `redactions` | Ghi chú nếu đã che/xoá thông tin nhạy cảm |
| `review_status` | pending / reviewed |

### Bước 2 — Nếu chat trên web (Claude.ai, ChatGPT web...) → ghi vào `online-chats.md`
Thêm 1 dòng vào bảng:

| session_id | member | tool | share_url | verified_incognito | notes |
|------------|--------|------|-----------|:------------------:|-------|
| 20260717-A01-giang-claude-01 | giang | Claude.ai | https://claude.ai/share/xxx | ✅ | Review PRD |

- **share_url**: dùng link share/export công khai của chat (không phải dán toàn bộ nội dung).
- **verified_incognito**: bạn đã tự mở link ở tab ẩn danh để xác nhận người khác xem được, không lỗi 403.

### Bước 3 — Nếu có ảnh chụp màn hình / export cần lưu
- **Không** commit ảnh/screenshot chứa thông tin nhạy cảm vào Git.
- Upload lên Drive **private**, rồi điền link vào dòng tương ứng trong `manifest.csv` (cột `screenshot`) hoặc note riêng theo format:

```
SUBMIT_PRIVATE_URL=<link_drive_private>
```

---

## 3. Trước khi nộp (checklist)

- [ ] `manifest.csv` có đủ dòng cho các phiên gắn với task đã nộp (đặc biệt các task demo/rubric)
- [ ] Mọi link trong `online-chats.md` mở được ở chế độ ẩn danh, không lộ secret
- [ ] Không có `.env`, API key, hoặc PII trong bất kỳ file nào ở `.ai-log/`
- [ ] `SUBMIT_PRIVATE_URL` (nếu có ảnh/export riêng) đã điền đủ
- [ ] Văn Hải đã rà lại tổng hợp trước khi đóng cổng nộp (D5)

**session_id gợi ý:** `20260717-H01-hoang-codex-01`
