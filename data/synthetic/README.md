# Artifact synthetic đã bị gỡ (M01)

Các CSV scaffold cũ (`students.csv`, `grades_timeseries.csv`, `attendance_timeseries.csv`) và generator (`backend/app/ml/early_warning/`, `scripts/generate_synthetic.py`) đã bị xóa theo task M01. Chúng **không phải input, fixture, evidence, slide hoặc video** của MVP sau quyết định chuyển sang EPU reference; không thêm hoặc regenerate dữ liệu tại đây. Guard test: `backend/tests/test_m01_legacy_quarantine.py`.

M05/M06 sẽ thay thế đường dữ liệu bằng export EPU đã được data owner phê duyệt, pseudonymize và validate theo [hợp đồng tích hợp](../../docs/04-engineering/04-epu-data-integration-contract.md). Raw EPU/reference, mapping `MSSV`, PII và token crawl không được commit vào `data/`.

Cho đến khi handoff đó hoàn tất, consumer phải trả `insufficient_data` thay vì đọc CSV synthetic cũ.
