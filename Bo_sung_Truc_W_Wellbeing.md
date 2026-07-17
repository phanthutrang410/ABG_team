# BỔ SUNG BRIEF — TRỤC W (WELLBEING): CẢNH BÁO SỚM SINH VIÊN GẶP KHỦNG HOẢNG

> Tài liệu bổ sung cho `Problems_Brief.md`. Hiện brief chỉ có bộ tín hiệu Học vụ (1–12) cho Trục D (dropout); Trục W được nhắc ở nhiều nơi (L3, L5, KPI W1–W2, tiêu chí #21) nhưng **chưa được định nghĩa**. Tài liệu này lấp khoảng trống đó — kèm hướng dẫn ghép từng phần vào brief.
>
> **Vị trí ghép:**
> | Phần trong tài liệu này | Ghép vào brief |
> |:--|:--|
> | §1 — Bộ tín hiệu Wellbeing 13–19 | Thêm thành mục **D.4.1**, ngay sau bảng tín hiệu Học vụ (sau ghi chú false-alarm control) — lấp đúng khoảng trống đánh số 12→20 |
> | §2 — Thang W0–W3 | Thêm thành mục **D.5.2** (mục "Độ phủ & độ sâu dữ liệu" hiện tại đổi số thành D.5.3) |
> | §3 — Sửa quy trình Handoff | Thay bước 3–4 của mục **D.6.1** |
> | Câu đầu mục D.4 | Sửa thành: *"Toàn bộ tín hiệu đầu vào được chia thành hai nhóm, tương ứng với hai trục output (xem D.5): nhóm **Học vụ** (dropout-oriented, tiêu chí 1–12, bảng dưới) — đầu vào chính của Trục D; và nhóm **Wellbeing** (withdrawal-oriented, tiêu chí 13–19, mục D.4.1) — đầu vào của Trục W."* |

---

## §1 — [D.4.1] Nhóm tín hiệu Wellbeing (tiêu chí 13–19): phát hiện "rút lui hành vi đột ngột"

**Ranh giới claim (bắt buộc đọc trước):** Hệ thống **KHÔNG phát hiện trầm cảm hay bắt nạt** — không công cụ metadata nào làm được điều đó, và cố suy diễn trạng thái tâm lý từ dữ liệu vận hành chính là dán nhãn (vi phạm ràng buộc #2). Cái hệ thống phát hiện là **sự rút lui hành vi đột ngột (behavioral withdrawal delta)**: một sinh viên đang hoạt động bình thường bỗng rút lui đồng loạt trên nhiều kênh trong thời gian ngắn, không giải thích được bằng nguyên nhân học vụ. Output duy nhất của trục W là: *"có thay đổi hành vi đáng để một con người hỏi thăm"* — chính cuộc hỏi thăm của con người mới là bước làm rõ, hệ thống chỉ quyết định *ai nên được hỏi thăm trước*.

**Cơ sở khoa học của chuỗi suy luận** (khủng hoảng tâm lý → biểu hiện hành vi đo được trong metadata):

* Trầm cảm ở sinh viên dự báo GPA giảm và xác suất bỏ học tăng — nghiên cứu dọc, kinh điển nhất mảng này (Eisenberg, Golberstein & Hunt, 2009, *B.E. J. Econ. Anal. Policy*); chẩn đoán trầm cảm gắn với sụt ~0.49 điểm GPA (Hysenbegasi, Hass & Rowland, 2005, *J. Ment. Health Policy Econ.*); vấn đề tâm lý ở tân sinh viên làm giảm 2.9–4.7% hiệu suất học tập trong năm (Bruffaerts et al., 2018, *J. Affective Disorders*, WMH-ICS, n=4,921).
* Bị bắt nạt dự báo sụt điểm và sụt engagement (Juvonen, Wang & Espinoza, 2011, *J. Early Adolescence*, n=2,300 — bối cảnh THCS, dùng làm bằng chứng **cơ chế**, không ngoại suy hiệu ứng định lượng); vắng học tránh né là biểu hiện hành vi cốt lõi của lo âu/khủng hoảng học đường (Kearney, 2008, *Clin. Psychol. Review*); internalizing problems là risk domain hiệu ứng lớn của absenteeism (Gubbels, van der Put & Assink, 2019, meta-analysis 75 nghiên cứu, *J. Youth Adolescence*).
* ~50% rối loạn tâm lý khởi phát trước 14 tuổi và ~75% trước 24 tuổi (Kessler et al., 2005, *Arch. Gen. Psychiatry*) — độ tuổi sinh viên chính là cửa sổ khởi phát; và **không thể chờ sinh viên tự lên tiếng**: trong nhóm trầm cảm nặng, chỉ ~36% từng nhận hỗ trợ trong năm (Eisenberg, Golberstein & Gollust, 2007, *Medical Care*).

**Nguyên tắc phân biệt hai trục:** Trục D đo **xu hướng** (trend/level, thang thời gian tháng–học kỳ). Trục W đo **tốc độ thay đổi** (delta đột ngột so với baseline của chính sinh viên, thang thời gian 1–3 tuần), bắt buộc đa kênh. Một tín hiệu có thể xuất hiện ở cả hai trục nhưng với phép đo khác nhau (ví dụ #4 đo LMS sụt theo kỳ, #15 đo LMS gãy trong 2 tuần).

| \# | Nhóm | Tiêu chí | Nội dung ảnh hưởng | Cách chấm điểm | Nguồn dữ liệu (privacy) | Nghiên cứu chứng minh |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| 13 | **Wellbeing** | Vắng cụm đột ngột (clustered absence) | SV vốn chuyên cần bỗng vắng dồn dập trong thời gian ngắn — pattern của né tránh (avoidance), khác về bản chất với vắng rải rác tích lũy (#6). | Baseline chuyên cần ≥90% trong ≥8 tuần, sau đó vắng ≥3 buổi trong 2 tuần → tín hiệu W. Chỉ within-student. | Điểm danh (đã thu cho #6) — không thu thêm gì mới. | Kearney (2008): vắng tránh né gắn lo âu/khủng hoảng. Gubbels et al. (2019): internalizing problems là risk domain hiệu ứng lớn của absenteeism. |
| 14 | **Wellbeing** | Vách nộp bài (submission cliff) | Từ nộp đều chuyển sang bỏ hẳn — đứt gãy, khác với trễ tăng dần (#5); phản ánh mất động lực/năng lượng cấp tính. | Baseline nộp đúng hạn ≥80%, sau đó bỏ ≥2 bài liên tiếp trong ≤3 tuần trên ≥2 môn → tín hiệu W. | LMS gradebook (đã thu cho #5) — metadata. | Bruffaerts et al. (2018): suy giảm academic functioning đo được khi có vấn đề tâm lý. Eisenberg et al. (2009). |
| 15 | **Wellbeing** | Sụt LMS tốc độ cao (engagement cliff) | Hoạt động LMS gãy đột ngột trong 1–2 tuần (khác #4: trend theo kỳ) — phù hợp cơ chế mất động lực cấp tính. | Giảm ≥70% tần suất truy cập trong ≤2 tuần so với baseline 8 tuần của chính SV, trên ≥2 môn có LMS hoạt động. | LMS logs (đã thu cho #4) — chỉ tần suất/thời lượng. | Cùng evidence base #4 (Macfadyen & Dawson 2010; OULAD). Hysenbegasi et al. (2005): trầm cảm → sụt năng suất học tập đo được. |
| 16 | **Wellbeing** | Dịch chuyển nhịp hoạt động (rhythm shift) | Tỷ trọng hoạt động đêm khuya tăng bất thường — proxy yếu của rối loạn nhịp sinh hoạt. **Tín hiệu phụ: không bao giờ đứng một mình**, chỉ cộng hưởng khi đã có tín hiệu khác. | Tỷ trọng hoạt động LMS khung 0–5h tăng ≥3× so baseline chính SV, kéo dài ≥2 tuần → chỉ dùng làm hệ số cộng hưởng, không tự tạo cảnh báo. | Timestamp LMS có sẵn — KHÔNG thu thêm sensor nào. | Wang et al. (2014, StudentLife, UbiComp): rối loạn giấc ngủ/nhịp sinh hoạt tương quan trầm cảm — *lưu ý: nghiên cứu dùng smartphone sensing xâm phạm hơn ta nhiều; chỉ trích làm bằng chứng cơ chế, không claim năng lực tương đương.* |
| 17 | **Wellbeing** | Ngắt kết nối kênh hỗ trợ (support withdrawal) | Delta trên #11: SV trước đây phản hồi đều bỗng hủy hẹn CVHT, ngừng đọc thông báo — rút lui khỏi chính kênh có thể giúp mình. | Baseline có tương tác đều ≥1 học kỳ, sau đó hủy/vắng hẹn đã đặt + không đọc thông báo ≥3 tuần → tín hiệu W. | Log hẹn CVHT + trạng thái đã đọc/chưa đọc (đã thu cho #11) — KHÔNG đọc nội dung. | Tinto (1993): đứt gãy integration. Eisenberg et al. (2007): nhóm cần hỗ trợ nhất là nhóm ít tự tìm hỗ trợ nhất (chỉ ~36% nhóm trầm cảm nặng nhận hỗ trợ) — hệ quả: không thể thiết kế hệ thống chờ SV tự lên tiếng. |
| 18 | **Wellbeing** | Sự kiện học vụ sốc (acute academic shock) | Trượt môn lần đầu, điểm thi sụt mạnh bất thường — stressor cấp tính đúng loại "áp lực thi cử" trong đề bài. **Không phải cảnh báo** — chỉ mở *cửa sổ theo dõi tăng cường*. | Sự kiện: trượt môn đầu tiên / điểm thi lệch mạnh dưới baseline cá nhân → mở cửa sổ 4 tuần trong đó các tín hiệu 13–17 được đánh giá với ngưỡng nhạy hơn. Hết cửa sổ không có tín hiệu → tự đóng, không lưu vết. | Gradebook (đã thu cho #1, #12). | Thiết kế vận hành dựa trên cơ chế stressor cấp tính; nhất quán "exam pressure" trong đề bài. Eisenberg et al. (2009): trầm cảm đồng diễn lo âu dự báo dropout mạnh nhất. |
| 19 | **Wellbeing** | Chỉ số rút lui đa kênh (multi-channel withdrawal composite) | **Tín hiệu chủ lực của trục W** — rút lui đồng thời trên nhiều kênh độc lập là thứ phân biệt "có chuyện" với "bận/ốm/đi làm thêm". Một kênh đơn lẻ KHÔNG bao giờ đủ. | ≥3 tín hiệu trong nhóm {13, 14, 15, 17, #21 (dừng ngoại khóa)} cùng kích hoạt trong cửa sổ 14–21 ngày → W2; kèm mất liên lạc hoàn toàn → xét W3. #16 chỉ làm hệ số cộng hưởng. | Tổng hợp từ các nguồn đã liệt kê — không nguồn mới. | Tinto (1993): social integration failure là cơ chế trung tâm của departure. Nguyên tắc multi-signal + within-student nhất quán yêu cầu kiểm soát false-alarm của đề. |

### Ràng buộc riêng của trục W (chặt hơn trục D)

1. **Chỉ within-student:** mọi tín hiệu W so sánh SV với baseline của chính họ — tuyệt đối không so chéo giữa các SV.
2. **Bắt buộc đa kênh:** không bao giờ tạo cảnh báo W từ một tín hiệu đơn lẻ (#19 là cổng duy nhất sinh cảnh báo W2/W3).
3. **Không nguồn dữ liệu mới:** toàn bộ tiêu chí 13–18 tính từ dữ liệu đã thu cho trục D — không thêm bất kỳ lớp thu thập nào. TUYỆT ĐỐI không chạm dữ liệu tham vấn tâm lý, y tế, nội dung tin nhắn/mạng xã hội (nhất quán ràng buộc #1 và ghi chú tiêu chí 25).
4. **Từ vựng hiển thị được kiểm soát (controlled vocabulary):** giao diện chỉ dùng ngôn ngữ hành vi trung tính — "có thay đổi nhịp học tập gần đây, nên hỏi thăm" — cấm mọi từ ngữ lâm sàng (trầm cảm, khủng hoảng, nguy cơ tâm lý) ở mọi tầng hiển thị.
5. **Giới hạn được công khai, không che giấu:** (a) tín hiệu W là *sensitive-not-specific* — nhạy với "có gì đó thay đổi" nhưng không phân biệt được nguyên nhân (khủng hoảng ≠ đi làm thêm ≠ ốm ≠ chuyện gia đình); PPV thấp là **chấp nhận được có chủ đích** vì hành động đầu ra chỉ là một cuộc hỏi thăm — chi phí false-alarm gần bằng 0 và không gây hại, khác hẳn dán nhãn; (b) hệ thống **mù với "high-functioning distress"** (SV khủng hoảng nhưng vẫn giữ điểm và nếp học) — đây là missing-alarm được thừa nhận công khai; hệ thống mở rộng vùng phủ quan sát chứ không thay thế sự quan tâm trực tiếp của con người.
6. **Retention nghiêm ngặt hơn trục D:** tín hiệu W tự xóa sau 60 ngày nếu không được escalate (cụ thể hóa retention policy ở D.3.1); trạng thái W không bao giờ được ghi vào hồ sơ sinh viên hay chuyển cho bên thứ ba.

---

## §2 — [D.5.2] Trục 2 — Wellbeing Check (W0–W3)

Trục W trả lời một câu hỏi duy nhất: *"Sinh viên này có đang thay đổi hành vi theo cách đáng để một con người hỏi thăm không?"* — không phải "sinh viên này có vấn đề tâm lý không". Thang W vì vậy là thang **mức độ ưu tiên quan tâm**, không phải thang mức độ nghiêm trọng lâm sàng.

| Cấp | Mức ưu tiên quan tâm | Ý nghĩa & hành động gợi ý cho người phụ trách |
| :---- | :---- | :---- |
| W0 | Ổn định | Không có delta bất thường so với baseline cá nhân. Không hành động. |
| W1 | Ghi nhận nội bộ | Delta đơn kênh (1 tín hiệu trong nhóm 13–18) hoặc đang trong cửa sổ theo dõi #18. **Không hiển thị cho bất kỳ ai** — hệ thống tự theo dõi trong cửa sổ 2–4 tuần rồi tự xóa nếu không tiến triển. Đây là cơ chế chống false-alarm chủ động: quan sát thêm thay vì báo sớm. |
| W2 | Nên hỏi thăm | Rút lui đa kênh (#19 kích hoạt: ≥3 kênh trong 14–21 ngày). Người phù hợp nhất (CVHT/GV gần gũi) thực hiện **warm check-in**: hỏi thăm và mở lời hỗ trợ — KHÔNG dò hỏi nguyên nhân, KHÔNG dùng từ ngữ lâm sàng. |
| W3 | Chuyển tuyến ưu tiên | Đứt gãy đồng loạt và sâu (ví dụ vắng cụm + ngừng nộp + ngắt liên lạc hoàn toàn), hoặc W2 không tiếp cận được sau 2 lần thử. Chuyển thẳng bộ phận chuyên trách (CTSV / tham vấn học đường) trong ≤48 giờ — CVHT không phải điểm cuối. |

**Quan hệ giữa hai trục:** độc lập nhưng được đọc cùng nhau. Một SV D0 + W2 vẫn được hỏi thăm (khủng hoảng chưa chạm học vụ); D3 + W0 là ca học vụ thuần (kế hoạch học tập, tài chính); D2 + W2 là ca ưu tiên cao nhất vì hai trục xác nhận chéo. Hệ thống không bao giờ cộng gộp hai trục thành một "điểm rủi ro tổng" — cộng gộp chính là con đường quay lại dán nhãn.

---

## §3 — [D.6.1] Sửa quy trình Handoff (thay bước 3–4)

3. Với ca D1–D2 và **W2**, cuộc tiếp cận là **warm check-in** (hỏi thăm, đề nghị giúp đỡ) — không dò hỏi chẩn đoán, không kỷ luật. Riêng ca W2: người tiếp cận chỉ được biết *"có thay đổi nhịp học tập gần đây"* (controlled vocabulary, xem D.4.1) — không thấy breakdown tín hiệu, để cuộc hỏi thăm diễn ra tự nhiên và không định kiến.

4. Ca D3 hoặc **W3** được **chuyển tuyến chuyên trách** (công tác sinh viên / tham vấn học đường) trong ≤48 giờ. CVHT không phải điểm cuối. Với W3, việc chuyển tuyến kèm nguyên tắc: thông tin chuyển đi là mô tả hành vi quan sát được, không phải suy đoán nguyên nhân.

---

## Phụ lục — Nguồn đã kiểm chứng (17/07/2026, qua web)

| Citation | Nội dung then chốt | Link |
|:--|:--|:--|
| Eisenberg, Golberstein & Hunt (2009), *B.E. J. Econ. Anal. Policy* 9(1), Art. 40 | Trầm cảm dự báo GPA thấp hơn & xác suất dropout cao hơn (mẫu dọc ngẫu nhiên) | [degruyterbrill.com](https://www.degruyterbrill.com/document/doi/10.2202/1935-1682.2191/html) |
| Hysenbegasi, Hass & Rowland (2005), *J. Ment. Health Policy Econ.* 8, 145–151 | Chẩn đoán trầm cảm gắn với sụt ~0.49 GPA | [pubmed](https://pubmed.ncbi.nlm.nih.gov/16278502/) |
| Bruffaerts et al. (2018), *J. Affective Disorders* 225, 97–103 | 1/3 tân SV có vấn đề tâm lý; giảm 2.9–4.7% hiệu suất học tập | [pubmed](https://pubmed.ncbi.nlm.nih.gov/28802728/) |
| Juvonen, Wang & Espinoza (2011), *J. Early Adolescence* 31(1), 152–173 | Victimization dự báo GPA & engagement giảm (n=2,300, THCS) | [sagepub](https://journals.sagepub.com/doi/abs/10.1177/0272431610379415) |
| Kearney (2008), *Clin. Psychol. Review* 28, 451–471 | School refusal/absenteeism gắn lo âu, khủng hoảng | [pubmed](https://pubmed.ncbi.nlm.nih.gov/17720288/) |
| Gubbels, van der Put & Assink (2019), *J. Youth Adolescence* | Meta-analysis 75 nghiên cứu; internalizing problems là risk domain lớn của absenteeism | [springer](https://link.springer.com/article/10.1007/s10964-019-01072-5) |
| Kessler et al. (2005), *Arch. Gen. Psychiatry* 62, 593–602 | ~50% rối loạn khởi phát trước 14t, ~75% trước 24t | [scirp ref](https://www.scirp.org/reference/referencespapers?referenceid=2199582) |
| Eisenberg, Golberstein & Gollust (2007), *Medical Care* 45(7), 594–601 | Chỉ ~36% nhóm trầm cảm nặng nhận hỗ trợ trong năm | [pubmed](https://pubmed.ncbi.nlm.nih.gov/17571007/) |
| Wang et al. (2014), StudentLife, *UbiComp '14* | Sensing hành vi tương quan sức khỏe tâm thần (bằng chứng cơ chế; sensing xâm phạm hơn hệ của ta) | [acm](https://dl.acm.org/doi/10.1145/2632048.2632054) |
