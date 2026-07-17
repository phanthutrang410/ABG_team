# PRD — Silent Shield (MVP 48h)

## Problem

Phát hiện muộn HS nguy cơ bỏ học / khủng hoảng. Cần tín hiệu sớm từ dữ liệu học vụ, không giám sát đời tư, bàn giao cho người chăm sóc.

## Users

| Role | Việc cần làm |
|:-----|:-------------|
| GV chủ nhiệm | Xem HS lớp cần quan tâm + lý do |
| Tư vấn | Nhận handoff, ghi hành động |
| Admin (demo) | Tổng quan + fairness |

## Flows

1. Nạp synthetic điểm/điểm danh → features  
2. Score early-warning + contributing factors  
3. Dashboard list → chi tiết  
4. Care case → log hành động người  
5. Agent: “vì sao cảnh báo em X?” (grounded)

## Non-goals

Adaptive content, OCR/TTS, career matching, SIS production thật.

## Acceptance

Xem mục Goal + rubric trong [AGENTS.md](../AGENTS.md). Ethics = tiêu chí nghiệm thu, không phải phụ lục.
