# Problems Brief — Silent Shield

> Bản Markdown dùng làm nguồn yêu cầu cho bài toán và giải pháp đích. Phạm vi MVP đã chốt nằm trong [PRD](../02-product/04-prd.md); các quyết định diễn giải nằm trong [Truy vết yêu cầu](03-traceability.md).

*Hệ thống Cảnh báo Sớm Hỗ trợ Sinh viên dựa trên Tín hiệu Không xâm phạm*

*Non-Invasive Early-Warning System for Student Support*

**Track: Giáo dục & Đào tạo   •   Tài liệu mô tả bài toán & giải pháp**

# **PHẦN A — THÔNG TIN ĐỐI TÁC**

*(Để trống — sẽ được bổ sung sau)*

| Trường thông tin | Nội dung |
| :---- | :---- |
| Tên đối tác / Đơn vị | … |
| Người đại diện | … |
| Vai trò / Phòng ban | … |
| Thông tin liên hệ | … |

# **PHẦN B — TRACK THAM GIA (CHALLENGE TRACK)**

| Hạng mục | Nội dung |
| :---- | :---- |
| Track | Giáo dục và Đào tạo |
| Tên đề bài | Hệ thống cảnh báo sớm giúp nhà trường nhận diện sinh viên có nguy cơ bỏ học hoặc gặp khủng hoảng, dựa trên các tín hiệu không xâm phạm (grade fluctuations, attendance, thay đổi hành vi học tập theo thời gian). |
| Tính chất bài toán | High-consequence, ethically sensitive — ưu tiên cao nhất cho quyền riêng tư trẻ em, kiểm soát false-alarm, và công bằng giữa các nhóm. |

# **PHẦN C — MÔ TẢ ĐỀ BÀI (PROBLEM STATEMENT)**

## **C.1 Bối cảnh**

Tình trạng bỏ học và các vấn đề sức khỏe tinh thần trong trường học — bao gồm bắt nạt (bullying), trầm cảm (depression), và áp lực thi cử (exam pressure) — thường chỉ được phát hiện quá muộn, khi chúng đã trở thành khủng hoảng. Các trường học tại Việt Nam gần như chưa có công cụ cảnh báo sớm dựa trên dữ liệu (data-driven early-warning tools), và phần lớn vẫn phụ thuộc vào quan sát chủ quan của đội ngũ giảng viên chủ nhiệm vốn đã quá tải công việc.

## **C.2 Vấn đề cốt lõi**

Điểm mấu chốt ***không phải*** là giảng viên thiếu năng lực nhận biết dấu hiệu. Trên thực tế, giảng viên chủ nhiệm và chuyên viên hỗ trợ thường **biết rất rõ** các dấu hiệu của một sinh viên đang gặp khó khăn. Vấn đề nằm ở **giới hạn năng lực xử lý do quá tải**: khi một giảng viên phải phụ trách số lượng sinh viên lớn, họ không thể theo sát toàn bộ. Kết quả là nguồn lực chăm sóc chỉ đến được với những sinh viên đã rơi vào giai đoạn **“quá muộn”** — gần nghỉ học, bị cảnh cáo học vụ mức độ cao, trượt nhiều môn, công nợ học phí cao — những trường hợp đã rất khó cứu vãn.

Hệ quả là một khoảng trống hệ thống: những sinh viên có dấu hiệu sớm nhưng chưa “bùng phát” thành khủng hoảng thì *không được ai để mắt tới*, cho đến khi đã quá muộn để can thiệp hiệu quả.

## **C.3 Các ràng buộc bắt buộc (trọng số cao)**

| \# | Ràng buộc bắt buộc | Diễn giải |
| :---- | :---- | :---- |
| 1 | Quyền riêng tư & bảo vệ dữ liệu cá nhân ở mức cao nhất | Tuyệt đối KHÔNG giám sát nội dung riêng tư hay tin nhắn cá nhân của sinh viên. Chỉ dùng dữ liệu vận hành có sẵn ở dạng metadata. |
| 2 | Chỉ hỗ trợ con người, thông qua sự quan tâm (care) | KHÔNG dán nhãn (no labeling), KHÔNG kỷ luật tự động (no automatic disciplinary action), KHÔNG thiên vị chống lại sinh viên yếu thế. |
| 3 | Công bằng (fairness) | Cảnh báo KHÔNG được lệch theo hoàn cảnh kinh tế (economic background) hoặc dân tộc (ethnicity). |

## **C.4 Tiêu chí chấm điểm**

* **Thiết kế đạo đức & bảo vệ quyền riêng tư** (trọng số cao nhất).

* **Độ chính xác cảnh báo sớm, đặc biệt là kiểm soát false-alarm, missing-alarm** — một cảnh báo sai (wrongful label) gây tổn hại thực sự cho sinh viên.

* **Công bằng giữa các nhóm** (fairness across groups).

* **Chất lượng quy trình chuyển giao sang hỗ trợ của con người** (handoff to human support).

# **PHẦN D — MÔ TẢ GIẢI PHÁP**

## **D.1 Tổng quan giải pháp**

Xây dựng một **AI-Agent hỗ trợ cảnh báo sớm** (early-warning support agent) dành cho giảng viên và chuyên viên, giúp họ có được **quan sát sớm và hỗ trợ kịp thời**. Agent này đóng vai trò một lớp lọc và ưu tiên (triage layer) trên nền dữ liệu vận hành sẵn có — giúp người phụ trách biết *nên chú ý đến ai trước*, thay vì phải tự rà soát thủ công toàn bộ sinh viên.

**Ranh giới năng lực (bắt buộc):** Agent KHÔNG tự động chẩn đoán, KHÔNG đưa ra kết luận, KHÔNG dán nhãn và KHÔNG đề xuất bất kỳ hành động kỷ luật nào. Agent chỉ trình bày tín hiệu và mức độ ưu tiên để **con người** ra quyết định và thực hiện chăm sóc.

## **D.2 Người dùng cuối (End-users)**

Đối tượng sử dụng chính của hệ thống là **Ban Lãnh đạo Khoa/Trường** — cấp chịu trách nhiệm về chất lượng đầu ra và phân bổ nguồn lực chăm sóc sinh viên của cả chương trình/đơn vị.

Việc đưa người dùng cuối lên cấp lãnh đạo xuất phát trực tiếp từ vấn đề cốt lõi đã nêu ở Phần C: giảng viên chủ nhiệm **không thiếu năng lực nhận biết dấu hiệu**, mà thiếu **thời gian và băng thông chú ý**. Nếu đặt agent vào tay từng giảng viên chủ nhiệm, hệ thống lại tạo thêm một luồng công việc rà soát mới cho chính những người vốn đã quá tải. Do đó thiết kế đảo chiều: agent tổng hợp tín hiệu và trình một **báo cáo ưu tiên ở cấp toàn chương trình** cho Ban Lãnh đạo, thay vì phát tán danh sách theo dõi tới từng giảng viên.

Với thiết kế này, vai trò của mỗi bên được phân định rạch ròi:

* **Ban Lãnh đạo Khoa/Trường** là người *đọc báo cáo chính* — nhìn toàn cảnh danh sách sinh viên cần quan tâm cùng mức ưu tiên, từ đó ra quyết định và **giao nhiệm vụ cụ thể** cho đúng giảng viên phụ trách.
* **Giảng viên chủ nhiệm / chuyên viên hỗ trợ** chuyển từ vai trò "tự giám sát liên tục" sang vai trò *thực thi theo chỉ đạo* — chỉ tiếp cận và chăm sóc khi được lãnh đạo chỉ định một ca cụ thể, kèm lý do đủ để hành động.

Nguyên tắc thiết kế vì thế là **tiết kiệm attention ở cấp ra quyết định**: gom sự cảnh giác phân tán của nhiều giảng viên thành một tầng quan sát tập trung, biến nỗ lực theo dõi mơ hồ thành các nhiệm vụ chăm sóc **có mục tiêu, có địa chỉ và có căn cứ**. Kết quả là giảm tải cho giảng viên chủ nhiệm — họ không phải "để mắt tới tất cả", mà chỉ tập trung nguồn lực vào đúng số ít sinh viên đã được lãnh đạo sàng lọc và phân công.

## **D.3 Đối tượng phân tích & nguyên tắc dữ liệu**

Đối tượng phân tích là **hành vi học tập của sinh viên** theo thời gian — không phải con người hay đặc điểm cá nhân của họ. Vì đề bài yêu cầu *non-invasive signals*, toàn bộ dữ liệu đầu vào phải là dữ liệu **đã có sẵn trong hệ thống đào tạo** hoặc do giảng viên bộ môn cung cấp (điểm quá trình, điểm danh). **Sinh viên không phải cung cấp bất kỳ thông tin nào và không có nội dung riêng tư nào bị đọc.**

### **D.3.1 Phân tầng quyền sử dụng dữ liệu (data access tiering)**

Để đảm bảo công bằng, bảo mật và tránh bias, quyền truy cập dữ liệu được phân tầng theo vai trò và theo mục đích:

| Tầng | Vai trò | Được thấy gì | KHÔNG được thấy gì |
| :---- | :---- | :---- | :---- |
| T1 | Ban Lãnh đạo Khoa/Trường | Báo cáo tổng hợp: danh sách sinh viên cần chú ý \+ mức ưu tiên \+ nhóm tín hiệu ở dạng tổng hợp (ví dụ 'xu hướng học vụ đi xuống', 'gợi ý cần quan tâm wellbeing'). Dùng để ra quyết định và giao nhiệm vụ. | Điểm rủi ro thô; breakdown chi tiết từng tín hiệu của từng cá nhân.. |
| T2 | Quản trị hệ thống / nhóm phát triển mô hình (Admin) | Dữ liệu đã pseudonymize để huấn luyện & kiểm định fairness; nhật ký vận hành hệ thống. | Danh tính thật gắn với điểm rủi ro. |

**Nguyên tắc xuyên suốt:** purpose limitation (chỉ dùng đúng mục đích quản lý đào tạo & hỗ trợ), data minimization (chỉ metadata), pseudonymization khi huấn luyện, và retention policy (xóa tín hiệu wellbeing sau thời gian ngắn nếu không được escalate).

## **D.4 INPUT — Bảng tiêu chí tín hiệu (hợp nhất)**

Toàn bộ tín hiệu đầu vào được hợp nhất trong bảng dưới. Bảng gồm nhóm **Học vụ** (dropout-oriented, tiêu chí 1–12). Mọi nguồn dữ liệu đều ở dạng metadata, không đọc nội dung.

| \# | Nhóm | Tiêu chí | Nội dung ảnh hưởng | Cách chấm điểm | Nguồn dữ liệu (privacy) | Nghiên cứu chứng minh |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| 1 | **Học vụ** | Xu hướng GPA | GPA thấp và xu hướng giảm là predictor được xác nhận nhất qua meta-analysis; điểm sớm ở năm 1 dự báo persistence mạnh. | Δ GPA giữa 2–3 kỳ (giảm ≥0.5 \= vàng; ≥1.0 \= đỏ) \+ ngưỡng tuyệt đối \< 2.0. | SIS. Pseudonymize khi huấn luyện; phân quyền hiển thị theo vai trò. | Meta-analysis 900+ nghiên cứu: GPA, tín chỉ đạt, giới tính là predictor nhất quán nhất (Csók & Alter, 2024). Aulck et al. (2016). Lưu ý: Vaarma & Li (2024) thấy GPA importance thấp ở ĐH Phần Lan → phụ thuộc bối cảnh. |
| 2 | **Học vụ** | Tín chỉ tích lũy & môn rớt | Tổng tín chỉ đạt và số môn rớt là feature có importance cao nhất trong mô hình ML dropout hiện đại. | % tín chỉ đạt/đăng ký mỗi kỳ; đếm cumulative môn rớt (tăng dần \= xấu hơn). | SIS (dữ liệu học vụ chuẩn). | Vaarma & Li (2024): 'accumulated credits' và 'failed courses' là feature quan trọng nhất. Berens et al. (2018); Behr et al. (2020). |
| 3 | **Học vụ** | Credit momentum (tốc độ tích lũy) | Đăng ký/hoàn thành nhiều tín chỉ hơn ở kỳ đầu → tốt nghiệp cao hơn; là cơ chế nhân quả, không chỉ tương quan. | So % tín chỉ tích lũy với median cohort cùng khóa/ngành; lệch \>15% \= vàng, \>30% \= đỏ. | SIS; chỉ dùng thống kê tổng hợp của cohort (không lộ dữ liệu SV khác). | Attewell & Monaghan (2016), propensity-score matching dữ liệu quốc gia Mỹ. Attewell, Heil & Reisel (2012); Adelman (2006). |
| 4 | **Học vụ** | Hoạt động trên LMS | Behavioral engagement trên LMS chứa tín hiệu sớm về dropout, thường xuất hiện trước khi điểm sụt. | Within-student baseline: sụt \>50% so với chính SV \= cảnh báo (tránh so chéo → giảm bias). | LMS logs — chỉ metadata (tần suất/thời lượng), KHÔNG đọc nội dung. | Macfadyen & Dawson (2010) — foundational. OULAD 2026 (32,593 SV): VLE behavior chiếm 85% predictive power; 'activity span' mạnh nhất (41.3%). |
| 5 | **Học vụ** | Nộp bài & thời điểm nộp | Trễ hạn / không nộp assignment tương quan mạnh với dropout; timing tương đối so peers là feature tốt. | % bài nộp đúng hạn; pattern trễ tăng dần 2 kỳ \= vàng. | LMS gradebook — metadata, không đánh giá nội dung. | Kokoç, Akçapınar & Hasnine (2021); Li et al. (EDM 2022\) — RAST tương quan cao với course grades; Kloft et al. (2014). |
| 6 | **Học vụ** | Chuyên cần & vắng thi | Absenteeism tương quan âm mạnh với kết quả; vắng thi cuối kỳ gần như trực tiếp phản ánh disengagement. | Vắng ≥20% buổi \= vàng; vắng thi không phép \= đỏ. | Điểm danh giảng viên; danh sách vắng thi phòng khảo thí. | Tương quan âm có ý nghĩa thống kê giữa absenteeism và các chỉ báo học tập/hành vi (IJCRT, 2024). Flag: evidence base K-12 nhiều hơn ĐH. |
|  | **Học vụ** | Thời gian vào lớp | Học sinh vào lớp sớm hoặc đúng giờ thì thường ít nghỉ học hơn học sinh đi học muộn thường xuyên | Xu hướng đi muộn so với baseline cá nhân | Điểm danh theo giờ |  |
| 7 | **Học vụ** | Tiến độ so với cohort | Chậm hơn cohort ≥1 kỳ là red flag trước cả khi GPA sụt; phản ánh 'off-track' lộ trình chuẩn. | Lệch % tín chỉ tích lũy so với median cohort (\>15% \= vàng). | SIS; so cohort ẩn danh (thống kê tổng hợp). | Adelman (2006); Attewell, Heil & Reisel (2011). First-year momentum gắn với hành vi/chính sách có thể can thiệp. |
| 8 | **Học vụ** | Hành vi đăng ký học phần | Đăng ký trễ, giảm mạnh khối lượng, rút môn cận deadline phản ánh disengagement và tiền báo late drop. | Cờ: đăng ký sau deadline / \<12 TC / giảm ≥40% khối lượng. | Log hệ thống đăng ký — metadata vận hành. | Cross-lagged 2026 (Trait-Aware LA): delay kỳ t dự báo late-dropped units kỳ t+1. Adelman (2006) về enrollment intensity. |
| 9 | **Học vụ** | Trạng thái học vụ (cảnh báo/probation) | SV bị cảnh báo học vụ có nguy cơ dropout cao hơn; probation vốn được thiết kế như 'official early warning'. | Đang probation \= đỏ; lịch sử bảo lưu \= vàng 2 kỳ sau khi quay lại. | Quyết định hành chính phòng đào tạo. | Operational marker chính thức tại nhiều ĐH (UT Austin, Iowa State, Illinois...). Flag: xem thêm Lindo, Sanders & Oreopoulos (2010) về probation. |
| 10 | **Học vụ** | Chuyển ngành / chuyển hệ | Chuyển ngành nhiều lần → tích lũy tín chỉ dư, kéo dài tốt nghiệp → tăng nguy cơ dropout; declared major \= goal commitment. | Cờ: ≥2 lần chuyển hoặc 1 lần kèm GPA \<2.5. | Hồ sơ hành chính phòng đào tạo. | Liu et al. (2020), community college \+ PSM. Frontiers (2026): declared major là early goal commitment (Cabrera 1992; Tinto 1993). |
| 11 | **Học vụ** | Tương tác với hệ thống hỗ trợ | Không phản hồi thông báo/không gặp CVHT phản ánh thiếu academic integration (Tinto). | Cờ: bỏ ≥2 buổi CVHT bắt buộc / không đọc thông báo học vụ. | Log hẹn CVHT \+ status 'đã đọc/chưa đọc' (KHÔNG đọc nội dung). | Tinto (1975, 1993): persistence được dự báo mạnh bởi academic & social integration. Arnold & Pistilli (2012) — Course Signals. |
| 12 | **Học vụ** | Điểm giữa kỳ (in-semester) | Điểm mid-term/quiz cho phép cảnh báo trong kỳ, không đợi hết kỳ → tăng khả năng can thiệp kịp thời. | ≥2 môn có mid-term \< 4/10 \= cảnh báo giữa kỳ. | Gradebook giảng viên qua LMS. | Arnold & Pistilli (2012): SV tương tác Course Signals retain 87.42% vs peers. Nguyên tắc 'can thiệp càng sớm càng hiệu quả'. |

**Về false-alarm control,** nên dùng trend/velocity (thay đổi so với baseline của chính học sinh đó) thay vì absolute threshold chung → tránh bias với học sinh vốn đã yếu về kinh tế/hoàn cảnh.

## **D.5 OUTPUT — Phân loại sinh viên**

### **D.5.1.  Nguy cơ bỏ học (Dropout Risk)**

| Cấp | Nhãn | Ý nghĩa & hành động gợi ý cho người phụ trách |
| :---- | :---- | :---- |
| D0 | Ổn định | Không có tín hiệu bất thường. Không cần hành động. |
| D1 | Cần theo dõi | 1–2 tín hiệu học vụ chớm xuất hiện. Ghi nhận, quan sát tiếp ở chu kỳ sau. |
| D2 | Cần chú ý | Cụm tín hiệu học vụ đi xuống có xu hướng. Gợi ý CVHT chủ động liên hệ, tìm hiểu nguyên nhân học tập. |
| D3 | Ưu tiên cao | Nhiều tín hiệu mạnh đồng thời (ví dụ đang probation \+ nợ môn tăng \+ off-track). Ưu tiên tiếp cận sớm, xem xét kế hoạch học tập. |

### **D.5.2 Độ phủ & độ sâu dữ liệu (data coverage & depth)**

Do các môn học có tiêu chí, cách học và yêu cầu khác nhau, một tín hiệu chỉ đáng tin khi có **đủ độ phủ**. Hệ thống phải gắn mỗi cảnh báo với một **confidence/coverage score**:

* Nếu chỉ có dữ liệu từ 1 môn có LMS đầy đủ, tín hiệu LMS chỉ mang tính cục bộ → hạ confidence, không kết luận toàn cục.

* Chuẩn hóa **within-student** (so sinh viên với chính họ) được ưu tiên hơn so sánh chéo giữa các sinh viên, để giảm bias do khác biệt môn học và giảm disparate impact.

* Khi độ phủ dữ liệu thấp, hệ thống thà *im lặng* còn hơn tạo cảnh báo sai — nhất quán với yêu cầu kiểm soát false-alarm.

# **PHẦN E — KẾT QUẢ MONG ĐỢI (EXPECTED OUTCOME)**

## **E.1 Tác động trực tiếp**

* **Mở rộng vùng phủ chăm sóc:** giúp giảng viên quá tải tiếp cận được nhiều sinh viên hơn ở **giai đoạn sớm**, thay vì chỉ những ca đã 'quá muộn'.

* **Giảm tỷ lệ bỏ học (dropout rate):** nhờ can thiệp sớm khi tình huống còn cứu vãn được.

* **Phát hiện nhóm 'quiet middle':** những sinh viên chưa bùng phát khủng hoảng nhưng có dấu hiệu sớm — nhóm bị bỏ sót nhiều nhất trong mô hình thủ công.

* **Bảo toàn đạo đức & công bằng:** hỗ trợ mà không giám sát nội dung, không dán nhãn, không thiên vị nhóm yếu thế.

## **E.2 Cơ chế dài hạn: sự hài lòng → gắn bó → giảm bỏ học**

Một yếu tố quan trọng giúp sinh viên gắn bó với trường lâu hơn là **sự hài lòng về chất lượng dịch vụ**. Khi nhà trường chủ động quan tâm và hỗ trợ kịp thời, trải nghiệm dịch vụ được cải thiện, từ đó nâng cao sự hài lòng, lòng trung thành và khả năng ở lại của sinh viên. Bằng chứng học thuật:

* **Nghiên cứu trên bối cảnh Việt Nam (PLS-SEM, mẫu lớn):** sự hài lòng của sinh viên là **biến trung gian then chốt** giữa chất lượng dịch vụ của trường với kết quả học tập và **lòng trung thành với nhà trường (institutional loyalty)**; một môi trường dịch vụ tích cực làm tăng cam kết, gắn kết và hiệu suất của sinh viên *(Nghiên cứu case study tại Việt Nam, ScienceDirect, 2025).*

* **Bằng chứng quốc tế:** sự hài lòng được xác định là **yếu tố quyết định mạnh nhất** của lòng trung thành, đóng vai trò trung gian giữa chất lượng dịch vụ và loyalty; nhiều nghiên cứu cho thấy hài lòng là mắt xích trung gian cần thiết dẫn tới **giữ chân sinh viên (retention)** (Tegowati et al., 2020, dẫn lại trong tổng quan service-quality–loyalty).

**Suy luận cho hệ thống:** cảnh báo sớm không chỉ 'cứu' từng ca riêng lẻ, mà còn là một hình thức nâng cao chất lượng dịch vụ chăm sóc sinh viên ở cấp hệ thống — qua đó củng cố sự hài lòng và gắn bó, tạo hiệu ứng giảm bỏ học bền vững hơn so với can thiệp đơn lẻ.

## **E.3 Chỉ số đo lường đề xuất (KPI)**

| Nhóm | Chỉ số | Ý nghĩa |
| :---- | :---- | :---- |
| Hiệu quả | Tỷ lệ ca được tiếp cận ở giai đoạn sớm (D1–D2/W1–W2) so với tổng ca. | Đo mức độ dịch chuyển từ 'quá muộn' sang 'sớm'. |
| Chất lượng cảnh báo | False-alarm rate; precision ở nhóm ưu tiên cao. | Kiểm soát tổn hại do cảnh báo sai (trọng số cao). |
| Công bằng | Chênh lệch tỷ lệ cảnh báo giữa các nhóm (cohort/ngành/hệ). | Phát hiện & ngăn bias. |
| Handoff | Tỷ lệ ca escalate được con người tiếp nhận & phản hồi. | Đo chất lượng chuyển giao sang hỗ trợ. |
| Dài hạn | Retention rate; điểm hài lòng dịch vụ sinh viên. | Đo tác động gắn bó theo cơ chế E.2. |

**— HẾT —**

## **ĐỀ XUẤT CHỈ TIÊU BỔ SUNG**

| \# | Tên tiêu chí | Nội dung ảnh hưởng | Cách chấm điểm (bất đối xứng) | Nguồn dữ liệu (privacy) | Nghiên cứu chứng minh |
| ----- | ----- | ----- | ----- | ----- | ----- |
| 20 | Tham gia CLB / tổ chức sinh viên | Tham gia CLB tạo social integration → cơ chế trung tâm của Tinto & Astin. Dùng để *giảm* severity cảnh báo học vụ khi có bằng chứng SV vẫn engage. | Buffer \+1 nếu là thành viên ≥1 CLB có hoạt động; buffer \+2 nếu tham gia ≥2 event/kỳ. KHÔNG tạo điểm trừ khi vắng. | Đăng ký thành viên CLB (Đoàn/Hội); log check-in event qua QR. Chỉ metadata (có/không tham gia). | Astin (1984, 1999\) — Student Involvement Theory. Kuh et al. (2006): SV dành 6–20h/tuần cho co-curricular retain gấp 2 lần so với ≤5h; 21+h retain còn cao hơn. |
| 21 | Dừng đột ngột hoạt động ngoại khóa (delta — behavioral withdrawal) | Delta signal: SV có *lịch sử* tham gia rồi dừng hẳn — dấu hiệu withdrawal có ý nghĩa (khác hoàn toàn với SV chưa bao giờ tham gia). Đây là signal cho trục Wellbeing, không phải Dropout. | Không tham gia event nào trong ≥6 tuần SAU KHI có lịch sử ≥1 event/tháng trước đó → tín hiệu W1. Chỉ áp dụng within-student, không so chéo. | Log check-in event, so sánh với chính SV trước đó. | Tinto (1993): social integration failure là cơ chế trung tâm của departure. Meta-analysis burnout 2024 (Educ. Psych. Review): withdrawal khỏi tương tác xã hội là core behavioral indicator. |
| 22 | Sử dụng thư viện | Library use là predictor mạnh và được xác lập của retention & GPA — đặc biệt hữu ích cho môn offline không có LMS. | Có checkout tài liệu / đặt phòng học nhóm trong kỳ \= buffer \+1. Vắng thư viện KHÔNG là điểm trừ (commuter students, SV học ở nhà). | Log mượn/trả thư viện; hệ thống đặt phòng học nhóm. Chỉ metadata tần suất, không danh sách sách mượn. | Soria, Fransen & Nackerud (2013, 2014): first-year SV có dùng thư viện retain năm 2 gấp 9.54 lần. Stemmer & Mahan (2016). Nghiên cứu tổng hợp: library use predict GPA & 1-year retention có ý nghĩa thống kê. |
| 23 | Có mặt trên campus (physical presence) | SV có mặt campus nhiều thể hiện investment of physical energy (Astin). Đặc biệt quan trọng khi môn học offline không sinh clickstream. | Trung bình có mặt campus ≥3 ngày/tuần (từ WiFi auth) \= buffer \+1. KHÔNG dùng làm negative signal — commuter/working students không được penalize. | WiFi authentication logs; thẻ SV RFID quẹt cổng. Metadata (có/không kết nối), không tracking chi tiết vị trí. | Astin (1984, 1999): presence là proxy cho investment of physical & psychological energy — điều kiện tiên quyết của involvement. |
| 24 | Tham gia hoạt động học thuật ngoài lớp (workshop, seminar) | Attendance workshop/hội thảo học thuật là proxy cho academic involvement — nhánh riêng của Astin's theory, khác social involvement. Tương quan mạnh với goal commitment. | Có tham gia ≥1 workshop/seminar học thuật trong kỳ \= buffer \+1. | QR check-in event học thuật do trường/khoa tổ chức. | Astin (1984): academic involvement là 1 trong 2 nhánh chính của involvement theory. Frontiers (2024): declared major & academic engagement là early forms of goal commitment (Cabrera 1992; Tinto 1993). |
| 25 | Tương tác chủ động với dịch vụ hỗ trợ học tập / hướng nghiệp | SV chủ động tìm career center, tutoring, mentoring thể hiện self-agency — tương quan tích cực với persistence. Meeting with faculty và student-advisor interaction là một trong những involvement practices tốt nhất cho retention. | Có sử dụng career center / tutoring / mentoring trong kỳ \= buffer \+1. | Log lịch hẹn tại career center, tutoring lab. TUYỆT ĐỐI KHÔNG chạm dữ liệu tham vấn tâm lý — đây là dữ liệu sức khỏe nhạy cảm theo Nghị định 13/2023. | Astin's I-E-O model: student-advisor interaction là top involvement practice cho retention (nghiên cứu tổng hợp BGSU). Course Signals (Arnold & Pistilli 2012). |

### Buffer chỉ *điều chỉnh xuống* điểm rủi ro, không bao giờ thay thế signal chính. Công thức đề xuất:

### Final\_D \= Base\_D\_score − min(Buffer\_total, cap)

### Final\_W \= Base\_W\_score − min(Buffer\_total, cap\_W)

<!-- Kết thúc nội dung nguồn. -->
