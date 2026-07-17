# Silent Shield — Agent / team entry

Đọc file này trước khi sửa code hoặc docs.

## Goal (48h)

**Silent Shield:** cảnh báo sớm HS nguy cơ bỏ học/khủng hoảng từ điểm + điểm danh + xu hướng hành vi (không xâm phạm), chỉ hỗ trợ con người, có fairness đo được — demo live trước **11:00 19/7**.

### Nộp đủ 5 hạng mục

| # | Deliverable | Owner |
|:-:|:------------|:------|
| D1 | Slide | A* + V* |
| D2 | Video ≤5 phút | V* + A* |
| D3 | GitHub | H* |
| D4 | Live URL | H* |
| D5 | Nhật ký AI | V* (cả team) |

### Rubric bắt buộc làm thật

1. Riêng tư — không giám sát chat/camera/mic  
2. Care — không dán nhãn / kỷ luật tự động  
3. Fairness — metric nhóm trên synthetic, hiện trên UI  
4. Kiểm soát báo động giả + giải thích yếu tố đóng góp  

Chi tiết board: [docs/sprint.md](docs/sprint.md) · PRD: [docs/prd.md](docs/prd.md)

## Lanes

| Prefix | Owner |
|:------:|:------|
| H* | Hoàng |
| M* | Khánh Duy |
| G* | Trường Giang |
| T* | Thu Trang |
| A* | Hạ Giang |
| V* | Văn Hải |
| D* | Nộp bài BTC |

Branch: `feature/<id>-<short>` · Commit: `feat:` / `fix:` / `docs:` / `test:` / `chore:`

## Do not

- LLM bịa risk score — chỉ giải thích điểm từ model/API  
- Đưa PII học sinh thật vào repo  
- Commit `reference-Learning-Analytics-AI/` hoặc secrets  
- Xây adaptive tutor / OCR / career (ngoài đề)

## Verify

```powershell
.\scripts\verify.ps1
.\scripts\verify.ps1 -Quick
```

## Docs index

[docs/README.md](docs/README.md)
