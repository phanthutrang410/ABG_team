# Story briefs — Văn Hải (Đậu Văn Hải)

> **Bắt đầu từ P2.** Bạn làm QA/release độc lập, rehearsal, video và nộp cổng cuối (`V06`). **Không** sở hữu nộp Checkpoint 2 (`V05` → Thu Trang). Hoàng hoàn thiện checklist/evidence Markdown; bạn chỉ bàn giao screenshot, gap và xác nhận — không tự sửa docs/deploy/code.

Board tổng: [Sprint](03-sprint.md) · Evidence source: [Release evidence](07-release-evidence.md).

## V07 — QA release và smoke độc lập (lần 1)

| | |
|:--|:--|
| Outcome | Báo cáo smoke độc lập (pass/fail + defect) đủ để Hoàng chạy `D4r`. **Không** phải tín hiệu nộp CP2. |
| Gate / deadline | P2 · ASAP sau D4b · trước cửa sổ fix/`D4r` (≥45–60 phút trước V05) |
| Owner | Văn Hải |
| Depends | D3, D4b — **Done**; unblocked |
| Gửi kết quả cho | Hoàng (owner `D4r`) · copy team |

### URL dùng để smoke (chốt với Hoàng nếu đổi)

| Mục | URL |
|:--|:--|
| FE Live (EC2) | `http://52.74.255.88:3000` |
| API health | `http://52.74.255.88:8000/health` |
| FE candidate (Vercel) — **smoke thêm**, chưa bắt buộc là URL nộp | `https://abg-team.vercel.app` |
| GitHub public | `https://github.com/phanthutrang410/ABG_team` |

Dùng **tab ẩn danh** hoặc trình duyệt/máy khác với máy Hoàng đã deploy. Không login GitHub khi kiểm public.

---

### Việc làm — từng bước

#### A. Chuẩn bị (2 phút)

1. Ghi giờ bắt đầu smoke (múi giờ +07).
2. Mở trình duyệt ẩn danh.
3. Không dùng `localhost` / bản local.

#### B. API health (3 phút)

4. Mở `http://52.74.255.88:8000/health`.
5. Pass khi JSON có `"status":"ok"` và `"database":true` (hoặc tương đương healthy).
6. Fail → chụp màn hình + ghi URL + giờ → dừng luồng FE nếu API chết (vẫn ghi defect).

#### C. FE Live — luồng list → case (10–15 phút)

7. Mở `http://52.74.255.88:3000` (login / chọn role nếu UI yêu cầu).
8. Vào dashboard / danh sách case.
9. Pass tối thiểu: danh sách hiện case (không trang trắng / lỗi cứng không recover).
10. Mở **một** case detail.
11. Pass tối thiểu: thấy mức ưu tiên rà soát / band (ví dụ `can_ra_soat`), **không** thấy raw score / “điểm rủi ro” / kết luận dropout.
12. (Nếu UI có) thử một care action nhìn thấy được (approve / dismiss / defer) — chỉ ghi pass/fail UI; **không** tự “sửa” nếu lỗi.

#### D. Claim / privacy nhanh trên UI (5 phút)

13. Quét copy trên list + detail: không kết luận “sẽ bỏ học”, không PII thật (họ tên/SĐT/email cá nhân).
14. Nếu thấy fairness/threshold panel: thiếu dữ liệu phải fail-closed / `insufficient_data` — không bịa metric nhóm.

#### E. GitHub public (5–10 phút)

15. Mở `https://github.com/phanthutrang410/ABG_team` **không** đăng nhập (hoặc cửa sổ ẩn danh).
16. Pass: repo `Public`; README/code xem được.
17. Fail nhanh nếu thấy: file `.env` có secret, token/API key trong README, PII thật trong screenshot/docs commit.
18. (Tuỳ chọn) Clone ẩn danh hoặc mở raw file — chỉ để xác nhận không bị private.

#### F. Vercel candidate — smoke phụ (5 phút, khuyến nghị)

19. Mở `https://abg-team.vercel.app` ẩn danh.
20. Pass: trang load; list/case hoặc health qua same-origin không lỗi cứng.
21. Ghi rõ: đây là **candidate** — Hoàng mới flip URL nộp sau `D4r` nếu team chốt HTTPS.

#### G. Kết thúc

22. Điền **Output bắt buộc** bên dưới.
23. Gửi Hoàng ngay (chat/email) — **không** tự nộp form BTC; **không** tự redeploy.
24. Nếu mọi bước pass và không defect blocker → ghi `V07 pass — sẵn sàng D4r` (vẫn chờ A05 của Hạ Giang).

---

### Không làm

- Không sửa code, docs canonical, deploy, env.
- Không nộp Checkpoint 2 (`V05` thuộc Thu Trang).
- Không coi smoke lần 1 = được nộp CP2 (còn `D4r` + A05).

---

### Output bắt buộc (copy gửi Hoàng)

Dán nguyên khối sau, điền đủ:

```text
## V07 smoke report — Văn Hải
Thời điểm: YYYY-MM-DD HH:MM +07
Trình duyệt / máy: …
Ẩn danh: có / không

### URL đã kiểm
- FE EC2: http://52.74.255.88:3000 → PASS / FAIL — ghi chú:
- API health: http://52.74.255.88:8000/health → PASS / FAIL — body tóm tắt:
- GitHub: https://github.com/phanthutrang410/ABG_team → PASS / FAIL — public?:
- Vercel candidate: https://abg-team.vercel.app → PASS / FAIL / SKIP — ghi chú:

### Luồng sản phẩm
- Login / role: PASS / FAIL / N/A
- List cases: PASS / FAIL
- Case detail (case_id nếu có): PASS / FAIL
- Không raw score / không dropout conclusion / không PII: PASS / FAIL
- Care action (nếu thử): PASS / FAIL / SKIP

### Defect list (mỗi dòng = 1 bug)
| # | Mức (blocker/major/minor) | Bước tái hiện | Kỳ vọng | Thực tế | Screenshot |
|:-:|:--|---|---|---|---|
| 1 |  |  |  |  | có/không (giữ ngoài repo) |

### Kết luận cho D4r
- [ ] Không blocker → Hoàng có thể vào D4r sau khi có A05
- [ ] Có blocker → liệt kê ID defect cần fix trước D4r
- V07 status: PASS / FAIL
```

**Done when:** Hoàng nhận được báo cáo trên (kể cả khi toàn PASS và defect list trống). Evidence screenshot giữ ngoài repo (không commit PII); Hoàng mới gắn vào [07-release-evidence](07-release-evidence.md) nếu cần.

---

## V02 — Script demo và rehearsal (self-owned)

| | |
|:--|:--|
| Outcome | Script 4 phút + Q&A 2 phút khớp Live; tự làm với Hạ Giang. |
| Gate / deadline | P3 |
| Owner | Văn Hải (+ Hạ Giang) |
| Depends | D4r (Live URL) |
| Status | Self-owned · decision #25 |

Tự soạn pitch/script với Hạ Giang. **Không** chờ Hoàng viết script hay claim-lock. Live = `https://abg-team.vercel.app`. Không overclaim Global Agent / hybrid / chuyên cần đủ nếu chưa có trên Live.

## D2 — Video

| | |
|:--|:--|
| Outcome | Video ≤5 phút dùng đúng Live URL và asset D1. |
| Gate / deadline | P3 · 09:30 |
| Owner | Văn Hải |
| Depends | D1, D4r |

Kiểm thời lượng, human review, fairness hoặc threshold, không PII/secret và không quay bản local khác bản deploy đã `D4r`.

## V08 — Audit AI log (defer — gần CP2 / trước D5)

| | |
|:--|:--|
| Outcome | Gap AI log được ghi **một thể** để Hoàng hoàn thiện D5. |
| Gate / deadline | **Defer** tới cửa sổ gần nộp CP2 → trước `D5` (decision #19). |
| Owner | Văn Hải |
| Depends | H05b |

Khi tới cửa sổ: yêu cầu từng thành viên backfill manifest + link online **một lần**; rà theo template `H05b`; không bịa log hộ. Bàn giao gap cho Hoàng/`D5`. CP2 **không** phụ thuộc V08.

## V06 — Nộp cổng cuối

| | |
|:--|:--|
| Outcome | BTC nhận đủ slide, video, GitHub, Live URL, mô tả và AI log trước 11:00. |
| Gate / deadline | P3 · 10:30 |
| Owner | Văn Hải |
| Depends | D1, D2, D3, D4r, D5, H09, H16 |

Đối chiếu từng deliverable với evidence Hoàng (gồm CP2 sau `V05` của Thu Trang), submit form cuối, lưu xác nhận và báo team.
