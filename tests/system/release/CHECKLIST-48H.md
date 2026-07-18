# Checklist nghiệm thu checkpoint 48h

Checklist này dùng sau khi cổng tự động đã pass. Người duyệt ghi đường dẫn bằng chứng và kết luận thực tế; không đánh dấu đạt nếu chưa mở và kiểm tra artifact.

## A. Cổng kỹ thuật tự động

- [ ] `npm test --prefix frontend` pass: unit test và Playwright frontend.
- [ ] Backend pytest mặc định pass, không tính test `slow` và `eval`.
- [ ] `.\tests\system\run.ps1` pass với PostgreSQL, FastAPI và Next.js thật.
- [ ] `.\tests\system\release\run.ps1 ...` pass ở chế độ mặc định, không dùng `-AllowUnavailableAi`.
- [ ] `npm run build --prefix frontend` và `git diff --check` pass.

## B. Triển khai kỹ thuật và chiều sâu kỹ thuật — 20 điểm

- [ ] Demo online mở được ở cửa sổ ẩn danh; frontend, backend và database đều sẵn sàng.
- [ ] Luồng cốt lõi đi từ dữ liệu đã import đến tín hiệu, chi tiết case, giải thích và thao tác của người có thẩm quyền.
- [ ] Có bằng chứng test cho happy path, lỗi, dữ liệu cũ, thiếu dữ liệu, chuyển trạng thái bị cấm và lỗi dependency.
- [ ] Sơ đồ kiến trúc khớp với code đang chạy; không trình bày thành phần chưa được triển khai như tính năng hoàn tất.

Đường dẫn bằng chứng:

- Demo online:
- Báo cáo test:
- Sơ đồ kiến trúc:

## C. Kiến trúc AI-Native và đổi mới sáng tạo — 20 điểm

- [ ] Video cho thấy agent giải thích một case thật trên bản online, không chỉ hiển thị mockup.
- [ ] Giải thích tách rõ dữ kiện, yếu tố mô hình, giới hạn dữ liệu và quyền quyết định của con người.
- [ ] Có minh họa refusal đối với yêu cầu lộ điểm, chẩn đoán hoặc tự quyết định hành động.
- [ ] Nêu rõ LLM không tham gia tính điểm, không tự chuyển trạng thái và không tự gửi liên hệ.

Đường dẫn bằng chứng:

- Đoạn video AI:
- Test grounding/refusal:

## D. Khả thi kinh doanh và lộ trình pilot — 20 điểm

- [ ] Xác định rõ nhóm sử dụng, người ra quyết định và vấn đề vận hành cần giải quyết.
- [ ] Pilot nêu phạm vi dữ liệu, đơn vị tham gia, thời gian, trách nhiệm và tiêu chí thành công.
- [ ] Có phương án triển khai thực tế, vận hành, mở rộng và xử lý khi nguồn dữ liệu hoặc AI gián đoạn.
- [ ] USP được so sánh với quy trình hiện tại hoặc lựa chọn thay thế bằng bằng chứng cụ thể.
- [ ] Tiềm năng phát triển thương mại có giả định, phân khúc và bước kiểm chứng; không dùng tuyên bố chung chung.

Đường dẫn bằng chứng:

- Slide pilot:
- Slide USP và thị trường:

## E. Trải nghiệm người dùng AI-Native và tư duy thiết kế — 15 điểm

- [ ] Luồng chính hoàn tất được trên desktop mà không cần thao tác ngoài kịch bản demo.
- [ ] Các trạng thái loading, empty, stale, error và insufficient data có nội dung rõ ràng.
- [ ] Người dùng phân biệt được tín hiệu hỗ trợ rà soát với kết luận về sinh viên.
- [ ] Bản nháp và hành động có ảnh hưởng đều cần người có thẩm quyền xác nhận.
- [ ] Video sử dụng giao diện đang chạy thật và chữ đủ đọc ở độ phân giải trình chiếu.

Đường dẫn bằng chứng:

- Video luồng chính:
- Kết quả kiểm tra UX:

## F. An toàn AI, grounding và độ tin cậy — 15 điểm

- [ ] Không lộ PII, raw score, xác suất, trọng số, nhãn outcome hoặc thuộc tính kiểm toán trên public surface.
- [ ] Fairness đóng an toàn khi chưa có thuộc tính kiểm toán được phê duyệt; không công bố chỉ số thiếu căn cứ.
- [ ] Agent chỉ dùng context do backend cấp và không nhận context do browser tự gửi.
- [ ] Có model version, dataset version, threshold version, coverage, freshness và limitations tại nơi phù hợp.
- [ ] Video và slide không khẳng định hệ thống chẩn đoán, dự đoán chắc chắn hoặc thay thế con người.

Đường dẫn bằng chứng:

- Kết quả test an toàn:
- Slide giới hạn:

## G. Thuyết trình, demo và khả năng bảo vệ giải pháp — 10 điểm

- [ ] Pitch deck có đủ thứ tự: Vấn đề → Giải pháp → Demo → Kiến trúc → Lộ trình pilot.
- [ ] Video ngắn, rõ, có phụ đề hoặc lời dẫn phù hợp và thể hiện sản phẩm thực tế.
- [ ] Kịch bản demo có dữ liệu sẵn, tài khoản phù hợp và phương án dự phòng khi mạng lỗi.
- [ ] Nhóm trả lời được câu hỏi về khả năng triển khai, mở rộng, USP, thị trường, an toàn và giới hạn.
- [ ] Mọi số liệu, tuyên bố và trạng thái hoàn thành đều truy được về code, test, tài liệu hoặc artifact cụ thể.

Đường dẫn bằng chứng:

- Pitch deck:
- Video:
- Kịch bản demo và bản dự phòng:

## Kết luận duyệt

- Người duyệt:
- Thời điểm:
- Commit/tag được duyệt:
- Kết quả: Đạt / Chưa đạt
- Hạng mục còn thiếu:
