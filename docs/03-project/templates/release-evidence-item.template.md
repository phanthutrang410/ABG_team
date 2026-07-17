# Release evidence item — fill template (H05b)

> Use one block per checklist row in [07-release-evidence.md](../07-release-evidence.md).  
> Paste the filled **Evidence** cell (or attach privately) — do not invent screenshots or mock Live URLs.  
> Owner of the Markdown checklist remains Hoàng (`H16`); QA/submission owners hand off paths only.

```text
Item:           <tên mục trên checklist, VD: Live URL smoke lần 1>
Gate:           CP1 | CP2 | Final | Demo Day
Task nguồn:     <ID, VD: D4 / V07>
Owner evidence: <người tạo bằng chứng>
Captured at:    <YYYY-MM-DDTHH:MM +07>
Evidence type:  url | screenshot | email/confirm | scan-log | other
Evidence ref:   <URL công khai hoặc đường dẫn file trong repo>
Private ref:    <Drive private nếu có; không commit ảnh nhạy cảm>
What verified:  <1–2 câu hành vi đã kiểm, VD: /health 200; list→case ẩn danh>
Redactions:       <none | mô tả đã che>
BLOCKED →:      <task ID nếu chưa có evidence thật; để trống nếu có>
Status:         [ ] pending | [x] done
```

## Minimal example (fictional placeholders)

```text
Item:           GitHub public + PII/secret scan
Gate:           CP2
Task nguồn:     D3
Owner evidence: Hoàng
Captured at:    2026-07-18T21:05+07
Evidence type:  url + scan-log
Evidence ref:   https://github.com/<org>/<repo> ; docs/.../scan-notes.md
Private ref:    (none)
What verified:  Repo public; scan không thấy .env/key/PII trong tree nộp
Redactions:      none
BLOCKED →:
Status:         [x] done
```
