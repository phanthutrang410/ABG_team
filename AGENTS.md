# Silent Shield — Agent / team entry

Đọc file này trước khi sửa code hoặc docs.

## Goal (48h)

**Silent Shield:** cảnh báo sớm thay đổi học tập cần được quan tâm từ xu hướng điểm + chuyên cần không xâm phạm; Ban Lãnh đạo rà soát trước khi bàn giao cho người hỗ trợ, có fairness đo được — demo live trước **11:00 19/7**.

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

Chi tiết board: [Sprint](docs/03-project/03-sprint.md) · PRD: [Product Requirements](docs/02-product/04-prd.md)

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
- Đưa PII sinh viên thật vào repo
- Commit `reference-Learning-Analytics-AI/` hoặc secrets  
- Xây adaptive tutor / OCR / career (ngoài đề)

## Verify

```powershell
.\scripts\verify.ps1
.\scripts\verify.ps1 -Quick
```

## Docs index

[docs/README.md](docs/README.md)
