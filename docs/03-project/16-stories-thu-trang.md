# Story briefs — Thu Trang (Phan Thu Trang)

> Lane chính: Agent (T01–T04). **Bổ sung 18/7:** owner nộp Checkpoint 2 (`V05`) — không sửa code/docs để “che” defect; chỉ nộp sau `D4r` xanh.

Board tổng: [Sprint](03-sprint.md) · Evidence: [Release evidence](07-release-evidence.md). Agent stories vẫn theo Sprint §7.

## V05 — Nộp Checkpoint 2

| | |
|:--|:--|
| Outcome | BTC nhận **Live URL** + **GitHub public** trước 23:00 T7 18/7; có xác nhận nộp. |
| Gate / deadline | P2 · ~22:45 (sau cửa sổ fix ≥45–60 phút từ V07+A05) |
| Owner | **Thu Trang** (chuyển từ Văn Hải · 18/7) |
| Depends | D3 ✓, V07, A05 → **D4r xanh**, rồi mới nộp |
| Status | **Done 18/7 tối** — Live `https://abg-team.vercel.app` · GitHub `https://github.com/phanthutrang410/ABG_team` · receipt ngoài repo → Hoàng/`H16` |
| Gửi sau nộp | Hoàng (`H16` evidence) · copy team |

### Việc làm — từng bước

1. **Chờ tín hiệu go từ Hoàng:** `D4r` Done (đã fix defect từ V07 + A05 → redeploy → re-smoke xanh).
2. Xác nhận 2 URL sẽ nộp (Hoàng chốt — thường GitHub + Live FE sau D4r; có thể là EC2 hoặc Vercel nếu đã flip):
   - GitHub: `https://github.com/phanthutrang410/ABG_team`
   - Live URL: theo Hoàng sau D4r (không tự đổi URL).
3. Mở form Checkpoint 2 của BTC.
4. Điền Live URL + GitHub public đúng bản đã re-smoke.
5. Submit trước **23:00 +07**.
6. Lưu bằng chứng nộp (screenshot form / email / mã xác nhận) — **ngoài repo**.
7. Báo Hoàng + team: giờ nộp, 2 URL đã gửi, link/ảnh xác nhận (private).

### Không làm

- Không nộp trước `D4r` xanh / trong ~10 phút sau smoke lần 1 của V07.
- Không tự redeploy hay sửa defect.
- Không commit receipt có PII vào git.

### Output bắt buộc

```text
## V05 CP2 submit — Thu Trang
Thời điểm nộp: YYYY-MM-DD HH:MM +07
Live URL đã nộp: …
GitHub đã nộp: https://github.com/phanthutrang410/ABG_team
D4r xác nhận xanh bởi: Hoàng — giờ:
Xác nhận BTC: có screenshot/email (ngoài repo) — mô tả ngắn:
V05 status: DONE / BLOCKED → …
```

**Done when:** BTC đã nhận 2 URL + Thu Trang bàn giao xác nhận cho Hoàng cập nhật [07-release-evidence §2](07-release-evidence.md) / `H16`.
