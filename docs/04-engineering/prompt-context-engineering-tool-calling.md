# Tổng hợp Day 04: Prompt, Context Engineering và Tool Calling

## 1. Phạm vi tài liệu

Tài liệu này tổng hợp nội dung chính của `day04.pdf` — *Prompt & Context Engineering — Day 04 (v2.1)*. Trọng tâm là cách thiết kế một AI agent đáng tin cậy thông qua bốn lớp:

| Lớp | Câu hỏi cần trả lời | Artifact thường sửa |
|---|---|---|
| Prompt | Chỉ dẫn nhiệm vụ đã rõ chưa? | `system_prompt.md`, examples, output schema |
| Context | Model đã nhận đủ thông tin đúng nguồn, đúng thời điểm chưa? | context packet, memory summary, retrieval policy |
| Tool | Agent có chọn đúng công cụ, tham số và quyền không? | agent spec, `tools.yaml`, tool declaration, result processor |
| Control | Hành động có được phê duyệt, kiểm soát và ghi log không? | approval flow, permission gate, retry, timeout, logging |

Một lớp bổ sung xuyên suốt là **eval và versioning**: thay đổi mới có thực sự tốt hơn phiên bản cũ và có thể rollback hay không.

Nguyên tắc chẩn đoán quan trọng nhất: không phải lỗi nào cũng là lỗi prompt. Trước khi sửa, cần xác định lỗi nằm ở prompt, context, tool, control hay eval/versioning.

## 2. Prompt và context

### 2.1. Prompt chỉ là một phần của context

Context là toàn bộ “bàn làm việc” mà model nhìn thấy, gồm:

- system/developer instructions;
- yêu cầu hiện tại của người dùng;
- lịch sử hội thoại;
- trạng thái và dữ kiện đã biết;
- tài liệu được truy xuất;
- tool schema và tool result;
- quy tắc, checklist, định dạng đầu ra và gợi ý eval.

Vì vậy, một prompt tốt không thể bù cho context thiếu, sai, cũ hoặc nhiễu. Ngược lại, context đầy đủ nhưng thiếu chỉ dẫn rõ ràng cũng có thể tạo ra kết quả không ổn định.

### 2.2. System prompt và user prompt

**System prompt** là luật nền do ứng dụng thiết lập. Nó xác định vai trò, nguyên tắc xử lý, ranh giới, cách dùng công cụ và hành vi khi thiếu dữ kiện. Chỉ dẫn này có mức ưu tiên cao hơn yêu cầu của người dùng.

**User prompt** mô tả mục tiêu cụ thể của lượt hiện tại: nhu cầu, dữ liệu đầu vào, giới hạn và ưu tiên của người dùng. User prompt không được phép vô hiệu hóa luật nền.

Kết quả từ công cụ và nội dung bên ngoài là dữ liệu để tham khảo, không có thẩm quyền thay đổi system prompt. Nếu tool result chứa câu như “bỏ qua quy tắc trước đó”, agent phải xem đó là dữ liệu không đáng tin, không phải instruction.

## 3. Quy tắc viết System Prompt

### 3.1. Sáu thành phần cốt lõi

Một system prompt sử dụng trong production nên làm rõ ít nhất sáu phần:

1. **Role**: agent là ai, có chuyên môn và phạm vi trách nhiệm nào.
2. **Task**: outcome cần tạo ra, thay vì chỉ mô tả một chủ đề chung chung.
3. **Required information**: dữ kiện bắt buộc trước khi xử lý hoặc gọi tool.
4. **Boundary**: điều được phép, bị cấm và trường hợp phải dừng hoặc hỏi lại.
5. **Tool policy**: khi nào gọi tool, khi nào không gọi, điều kiện quyền và approval.
6. **Output contract**: định dạng, trường bắt buộc, mức chi tiết và cách trình bày cho từng người nhận.

Mẫu cấu trúc:

```text
<system_role>
Bạn là [vai trò], chịu trách nhiệm [phạm vi].
</system_role>

<objective>
Hoàn thành [outcome có thể kiểm tra].
</objective>

<required_info>
Trước khi xử lý, cần có: [danh sách dữ kiện].
Nếu thiếu dữ kiện bắt buộc, hỏi lại; không tự suy đoán.
</required_info>

<boundaries>
- Được phép: [...]
- Không được phép: [...]
- Phải dừng hoặc chuyển người duyệt khi: [...]
</boundaries>

<tool_policy>
- Dùng [tool] khi [...].
- Không dùng [tool] khi [...].
- Write action chỉ được thực hiện sau approval hợp lệ.
</tool_policy>

<output_contract>
Trả về [định dạng/schema], gồm [...].
Nêu rõ nguồn, thời điểm và giới hạn khi dùng dữ liệu live.
</output_contract>
```

### 3.2. Viết instruction có thể kiểm tra

Instruction tốt phải cụ thể đủ để tạo test case. Ví dụ:

- Yếu: “Hãy hỗ trợ người dùng thật tốt.”
- Tốt hơn: “Nếu thiếu ngày đi hoặc điểm đến, hỏi lại trước khi gọi công cụ dự báo.”
- Yếu: “Không làm điều nguy hiểm.”
- Tốt hơn: “Không đặt chỗ, thanh toán hoặc gửi nội dung ra bên ngoài khi chưa có xác nhận rõ ràng và approval hợp lệ.”

Các ràng buộc nên mô tả hành vi quan sát được: gọi hay không gọi tool, trường nào phải có, lúc nào hỏi lại, lúc nào dừng, output phải chứa gì.

### 3.3. Cân chỉnh độ chi tiết

Ba trạng thái thường gặp:

- **Quá ít chỉ dẫn**: vai trò và mục tiêu chung chung, thiếu tín hiệu để model quyết định.
- **Quá nhiều chỉ dẫn**: nhồi nhiều nhánh `if/else`, quy tắc trùng lặp hoặc mâu thuẫn, khó bảo trì và tốn context.
- **Đủ dùng**: rõ vai trò, mục tiêu, dữ kiện bắt buộc, ranh giới, chính sách tool và output contract.

Không biến system prompt thành toàn bộ business logic. Các điều kiện an toàn quan trọng cần được enforce bằng code, permission gate và approval flow, không chỉ bằng câu chữ.

### 3.4. Tách output theo người nhận

Một agent thường có nhiều output trung gian:

1. Model phân tích intent và dữ kiện còn thiếu.
2. Model tạo tool call theo schema máy đọc.
3. Ứng dụng trả tool result đã chuẩn hóa.
4. Model tạo câu trả lời cuối cho người dùng.

Không dùng một định dạng cho mọi bước. JSON nội bộ cần chặt chẽ để validate và log; câu trả lời cuối cần rõ ràng, tự nhiên và không làm lộ chi tiết orchestration không cần thiết.

### 3.5. Decompose khi nhiệm vụ phức tạp

Với tác vụ nhiều bước, có thể tách pipeline:

```text
intent → missing facts → context/tool → final answer → self-check
```

Lợi ích là dễ debug, eval từng bước và chạy song song các phần độc lập. Đổi lại, orchestration phức tạp hơn, có thể tăng latency và số lần gọi model/tool. Chỉ tách khi lợi ích kiểm soát lớn hơn chi phí.

### 3.6. Zero-shot, few-shot, CoT và ToT

Thứ tự áp dụng hợp lý:

1. Bắt đầu bằng zero-shot với instruction và output contract rõ.
2. Thêm few-shot examples khi định dạng hoặc routing chưa ổn định.
3. Chỉ dùng reasoning scaffold khi tác vụ thật sự cần nhiều bước hoặc so sánh nhiều phương án.

Few-shot example nên:

- đại diện cho case thật;
- bao phủ cả positive, negative và boundary case;
- ngắn, nhất quán với schema;
- không chứa dữ liệu bịa hoặc pattern vô tình cần học;
- được đánh giá bằng eval, không thêm theo cảm tính.

**Chain of Thought (CoT)** phù hợp khi cần một luồng phân tích nhiều bước. **Tree of Thoughts (ToT)** phù hợp khi cần tạo nhiều hướng, đánh giá theo rubric rồi chọn. ToT tốn token và orchestration hơn, không nên dùng cho tác vụ đơn giản.

Trong hệ thống production, nên yêu cầu kết luận, tiêu chí và bằng chứng có thể kiểm tra thay vì phụ thuộc vào việc hiển thị toàn bộ suy luận nội bộ.

### 3.7. Versioning prompt

Prompt production là một artifact có vòng đời:

```text
Design → Evaluate → Deploy → Observe → Improve hoặc Rollback
```

Mỗi phiên bản nên lưu:

- version và owner;
- giả thuyết thay đổi;
- model/provider liên quan;
- input/output schema;
- bộ eval đã chạy;
- kết quả trước và sau, gồm delta;
- quyết định keep, revise hoặc rollback.

Một prompt mới pass vài ví dụ tự chọn chưa đủ để release. Cần holdout/cross-eval để phát hiện regression trên nhóm case khác.

## 4. Context Engineering

### 4.1. Chọn đúng thông tin, không nhồi toàn bộ

Context engineering là quyết định thông tin nào được đặt vào context, lấy từ đâu, ở thời điểm nào, theo thứ tự nào và bị loại bỏ khi nào.

Một context packet tốt cần trả lời:

- Đã biết điều gì?
- Dữ kiện đến từ nguồn nào?
- Được cập nhật lúc nào, còn mới không?
- Còn thiếu thông tin nào?
- Cần gọi tool nào để bổ sung?
- Hành động nào bị cấm hoặc cần approval?

### 4.2. Freshness và provenance

Dữ liệu có tính thời điểm như giá, thời tiết, trạng thái booking hoặc tồn kho phải kèm:

- nguồn;
- thời điểm truy xuất;
- phạm vi hoặc kỳ hiệu lực;
- trạng thái stale nếu quá hạn;
- caveat khi dùng cache hoặc fallback.

Không biến dữ liệu cũ thành sự thật hiện tại. Nếu cần dữ liệu live mà chưa có tool result hợp lệ, agent phải gọi tool hoặc nói rõ giới hạn.

### 4.3. Quản lý token budget

Context dài không đồng nghĩa với context tốt. Nên ưu tiên:

- system rules và safety boundary;
- yêu cầu hiện tại;
- state tóm tắt có cấu trúc;
- tài liệu liên quan nhất;
- tool schema cần cho lượt hiện tại;
- tool result đã lọc và chuẩn hóa.

Nên loại hoặc nén:

- lời chào và hội thoại lặp;
- raw tool output dài;
- dữ liệu stale;
- tài liệu không liên quan;
- tool schema không dùng trong lượt hiện tại.

Thông tin quan trọng không nên bị chôn giữa context dài. Có thể nhắc lại ngắn gọn constraint then chốt gần nơi model phải ra quyết định.

### 4.4. Multi-turn và external memory

Không nên đưa toàn bộ lịch sử vào mọi lượt. Hãy duy trì state summary có cấu trúc, ví dụ: intent, facts, constraints, missing fields, decisions, source và timestamp.

External memory có thể là database row, user profile hoặc cached tool result. Memory chỉ là dữ liệu; cần kiểm tra quyền, freshness và mức liên quan trước khi đưa vào context.

## 5. Tool Calling

### 5.1. Hai chiều của thiết kế tool

Tool calling gồm hai bài toán riêng:

1. **Request side**: agent có cần gọi tool không, chọn tool nào, tạo arguments ra sao và có đủ quyền hay chưa.
2. **Response side**: tool result được parse, validate, lọc, gắn nguồn và đưa lại vào context như thế nào.

Tool call thành công về mặt kỹ thuật chưa chắc là tool call đúng. Nó phải đúng công cụ, dữ kiện, schema, quyền và thời điểm.

### 5.2. Phân loại tool theo tác động

| Loại | Mục đích | Ví dụ | Kiểm soát chính |
|---|---|---|---|
| Knowledge tool | Đọc hoặc truy xuất thông tin | search, weather, database read | freshness, source, scope |
| Capability tool | Mở rộng năng lực xử lý | parser, calculator, code execution | validation, resource limit, sandbox |
| Write action | Thay đổi trạng thái bên ngoài | gửi tin, đặt chỗ, thanh toán, hủy | quyền, approval, logging, confirmation |

Tên gọi không quyết định mức rủi ro; tác động thật mới quyết định. `search_flights` là read tool, còn `hold_booking` là write action.

### 5.3. Registry, agent toolset và turn toolset

Nên tách ba lớp:

- **Global registry**: toàn bộ công cụ của sản phẩm.
- **Agent allowed toolset**: bộ công cụ phù hợp vai trò của agent.
- **Turn allowed tools**: công cụ agent thực sự nhìn thấy trong lượt hiện tại, dựa trên stage, quyền và rủi ro.

Mở ít tool nhưng đúng tool giúp giảm nhầm routing, giảm token và giảm bề mặt rủi ro. Khi thư viện lớn, dùng routing layer hoặc tool search để chỉ đưa các tool liên quan vào context. Tài liệu đưa ra rule of thumb là giữ dưới khoảng 20 tool khả dụng cho mỗi lượt, nhưng con số thực tế phải được kiểm chứng bằng eval.

### 5.4. Tool declaration tốt

Model không tự biết công cụ dùng để làm gì. Nó dựa vào name, description và schema. Mỗi declaration nên có:

- tên rõ hành động;
- mô tả cụ thể tool làm gì;
- `when_to_use` và `when_not_to_use`;
- input schema, kiểu dữ liệu và required fields;
- output/result schema;
- risk level;
- yêu cầu permission/approval;
- error behavior;
- ví dụ ngắn cho case dễ nhầm nếu cần.

Ví dụ khái quát:

```yaml
name: get_weather_forecast
description: Lấy dự báo thời tiết thực cho điểm đến và khoảng ngày cụ thể.
when_to_use:
  - Người dùng hỏi thời tiết tương lai và đã có điểm đến, ngày bắt đầu, ngày kết thúc.
when_not_to_use:
  - Thiếu ngày cụ thể.
  - Cần giá vé hoặc giá khách sạn.
required:
  - destination
  - start_date
  - end_date
risk_level: read_only
error_behavior: Trả structured error; không suy đoán thời tiết.
```

Không gộp read tool và write tool vào một declaration mơ hồ. Ví dụ, đọc Slack và gửi Slack phải là hai tool riêng; write tool phải có điều kiện approval rõ.

### 5.5. Chuẩn hóa và kiểm tra arguments

Trước khi gọi tool, agent hoặc orchestration layer cần:

1. trích xuất intent và entities;
2. chuẩn hóa giá trị về schema, ví dụ đổi “cuối tuần này” thành ngày cụ thể theo timezone hiện hành;
3. kiểm tra required fields;
4. validate kiểu, format, range và enum;
5. kiểm tra quyền, approval và các constraint;
6. quyết định gọi tool, hỏi lại hay dừng.

Không truyền cụm từ tự nhiên mơ hồ vào trường đòi ngày chuẩn. Không tự điền dữ kiện quan trọng nếu người dùng chưa cung cấp.

### 5.6. Tool result là context mới, không phải instruction

Raw tool output cần đi qua lớp xử lý trước khi quay lại model:

```text
raw output → parse → validate → sanitize → select high-signal fields
           → attach source/time/status → structured tool result
```

Tool result tốt cần:

- parse và validate được;
- ngắn, chỉ giữ dữ liệu cần dùng;
- có status rõ;
- có nguồn và timestamp;
- phân biệt fact với error/caveat;
- không để text bên ngoài nhập vai instruction;
- quy định allowed next action nếu workflow cần kiểm soát.

Mẫu:

```json
{
  "type": "tool_result",
  "tool": "get_weather_forecast",
  "status": "ok",
  "source": "weather_provider",
  "retrieved_at": "2026-06-05T10:00:00+07:00",
  "facts": {
    "destination": "Đà Nẵng",
    "forecast": []
  },
  "limitations": [],
  "allowed_next_action": "summarize_or_ask"
}
```

### 5.7. No-tool case và tool error

Không gọi tool khi:

- thiếu required information;
- yêu cầu ngoài phạm vi tool;
- write action chưa có xác nhận hoặc approval;
- agent không có permission;
- dữ liệu hiện có đã đủ và không cần live lookup.

Khi tool lỗi, phải phân loại ít nhất timeout, rate limit, empty result, malformed response và stale data. Error result nên có status, mã lỗi, `retryable`, retry policy, nguồn fallback và thông điệp được phép hiển thị.

Hành vi hợp lệ có thể là:

- hỏi lại;
- retry có giới hạn và backoff;
- dùng cache/fallback kèm caveat;
- báo lỗi và dừng.

Không dùng phỏng đoán để che tool failure.

## 6. Approval và ranh giới read/write

Write tool thay đổi trạng thái thật nên cần quy trình:

```text
Draft action → Hiển thị tác động → User xác nhận → App kiểm tra quyền/approval
→ Gọi write tool → Ghi audit log → Trả confirmation theo trạng thái thật
```

Approval phải được enforce ở tầng ứng dụng. Chỉ viết “hãy xin approval” trong prompt nhưng vẫn để write tool gọi tự do không tạo ra rào chắn thực tế.

Audit log nên ghi:

- ai yêu cầu và ai phê duyệt;
- phê duyệt lúc nào, phạm vi gì;
- tool và arguments đã gọi;
- kết quả thành công, thất bại hoặc pending;
- correlation/trace ID;
- bước khắc phục hoặc rollback nếu có.

Mức kiểm soát tăng theo tác động: read-only → tạo draft → hành động có thể đảo ngược → hành động khó đảo ngược như thanh toán, hủy hoặc hoàn tiền.

## 7. Anti-patterns và cách khắc phục

| Anti-pattern | Hậu quả | Cách khắc phục |
|---|---|---|
| Coi mọi lỗi là lỗi prompt | Sửa sai lớp, prompt ngày càng dài | Chẩn đoán theo Prompt–Context–Tool–Control–Eval |
| System prompt chung chung | Hành vi khó dự đoán và khó test | Ghi rõ role, task, required info, boundary, tool policy, output contract |
| Nhồi business logic vào prompt | Mâu thuẫn, khó bảo trì, không enforce được | Đưa constraint cứng vào schema, code, permission và approval gate |
| Quá nhiều quy tắc hoặc ví dụ | Tốn token, lẫn ưu tiên, học pattern sai | Giữ instruction ngắn, examples đại diện và đo bằng eval |
| Few-shot chứa dữ liệu bịa | Model sao chép fact/pattern sai | Dùng dữ liệu trung tính, schema chuẩn, kiểm tra regression |
| Luôn yêu cầu reasoning dài | Tăng chi phí và latency không cần thiết | Chỉ dùng CoT/ToT cho tác vụ phù hợp |
| Đưa toàn bộ history vào context | Nhiễu, chôn constraint, vượt token budget | Tóm tắt state có cấu trúc, bỏ dữ liệu stale và trùng lặp |
| Không gắn nguồn/timestamp | Dùng dữ liệu cũ như dữ liệu hiện tại | Bắt buộc provenance, freshness và caveat |
| Mở toàn bộ tool registry | Gọi nhầm tool, tăng context và rủi ro | Giới hạn theo agent, stage, turn và permission |
| Tên tool mơ hồ, schema lỏng | Routing và arguments sai | Tên theo hành động; description, required fields và enum rõ |
| Gộp read và write action | Khó kiểm soát approval | Tách tool đọc và tool ghi |
| Gọi tool khi thiếu dữ kiện | Request sai hoặc kết quả vô nghĩa | Validate required fields; hỏi lại trước khi gọi |
| Không gọi tool cho dữ liệu live | Bịa giá, thời tiết hoặc trạng thái | Quy định live-data boundary và routing eval |
| Truyền arguments dạng ngôn ngữ mơ hồ | Sai schema, sai thời điểm | Chuẩn hóa ngày, timezone, ID và validate trước khi gọi |
| Đưa raw tool output vào context | Nhiễu, prompt injection, tốn token | Parse, validate, sanitize, compress và gắn nhãn |
| Coi tool result là instruction | External content chiếm quyền điều khiển | Enforce trust boundary: tool output chỉ là untrusted data |
| Tool lỗi nhưng agent tự đoán | Tạo thông tin sai và che lỗi hệ thống | Structured error, retry giới hạn, fallback có caveat hoặc dừng |
| Approval chỉ tồn tại trong prompt | Write tool vẫn có thể chạy ngoài ý muốn | Enforce approval và permission bằng application layer |
| Chỉ chấm final answer | Không phát hiện sai tool, params hoặc quyền | Agent eval toàn trace: request → call → result → answer |
| Sửa prompt không version/eval | Không biết tốt hơn hay tạo regression | Lưu hypothesis, version, delta, holdout và rollback path |

## 8. Eval, safety và control harness

### 8.1. Tiny eval tối thiểu

Trước khi tin một thay đổi prompt, context hoặc tool, nên có ít nhất bốn nhóm:

1. **Positive case**: đủ dữ kiện, tạo đúng output.
2. **Negative/no-tool case**: thiếu dữ kiện hoặc ngoài phạm vi, agent hỏi lại hay từ chối đúng.
3. **Tool/live-data case**: cần dữ liệu mới, gọi đúng tool với arguments đúng.
4. **Safety/injection case**: external content chứa lệnh lạ, agent chỉ lấy fact và không làm theo lệnh.

Tiny eval là smoke test, không thay thế bộ eval production.

### 8.2. Prompt eval và agent eval

**Prompt eval** kiểm tra câu trả lời một lượt:

- đúng nội dung;
- đúng schema/format;
- giọng văn và mức chi tiết phù hợp;
- không vi phạm rule.

**Agent eval** kiểm tra toàn bộ đường đi:

- có chọn đúng tool hoặc đúng quyết định no-tool không;
- arguments có đúng schema và giá trị không;
- có đúng permission/approval không;
- tool result và error có được xử lý đúng không;
- final answer có grounded trên kết quả không;
- case cũ có regression không.

Trace kỳ vọng nên mô tả:

```text
user request → tool decision → validated arguments → tool result/error
→ result processing → final answer
```

### 8.3. Control harness

Harness là lớp ứng dụng quyết định:

- context packet nào được lắp;
- tool nào được mở;
- tool call được validate ra sao;
- khi nào yêu cầu approval;
- timeout, retry và fallback;
- trace nào được log;
- eval nào phải chạy trước release.

Các cơ chế production cần có:

- logging đủ để tái dựng đường đi;
- retry có giới hạn, chỉ cho lỗi tạm thời;
- timeout để một tool không treo toàn workflow;
- cache có freshness và provenance;
- permission và approval gate;
- validation của input, tool call, tool result và final output;
- rollback khi phiên bản mới tạo regression.

Nếu không log tool calls và outputs, khi kết quả sai đội phát triển chỉ còn phỏng đoán.

## 9. Checklist triển khai

### 9.1. System Prompt

- [ ] Vai trò và phạm vi trách nhiệm rõ.
- [ ] Outcome có thể kiểm tra.
- [ ] Dữ kiện bắt buộc được liệt kê.
- [ ] Có hành vi rõ khi thiếu dữ kiện.
- [ ] Điều được phép, bị cấm và điều kiện dừng rõ.
- [ ] Chính sách dùng tool và live data rõ.
- [ ] Write action yêu cầu approval.
- [ ] Output contract có schema hoặc mẫu ngắn.
- [ ] Instruction không trùng lặp hoặc mâu thuẫn.
- [ ] Prompt có version, owner và eval cases.

### 9.2. Context

- [ ] Chỉ đưa thông tin liên quan vào context.
- [ ] Dữ liệu có source và timestamp.
- [ ] Dữ liệu stale được loại hoặc gắn caveat.
- [ ] History được tóm tắt thành state có cấu trúc.
- [ ] Tool schemas không dùng trong lượt đã bị loại.
- [ ] Constraint quan trọng không bị chôn trong context dài.
- [ ] External content được gắn nhãn untrusted data.

### 9.3. Tool Declaration và Tool Call

- [ ] Tool name mô tả đúng hành động.
- [ ] Có `when_to_use` và `when_not_to_use`.
- [ ] Required fields, type, enum và range rõ.
- [ ] Read và write tool được tách riêng.
- [ ] Risk level, permission và approval được khai báo.
- [ ] Arguments được chuẩn hóa và validate trước khi gọi.
- [ ] Có test cho đúng tool, sai tool, no-tool và missing fields.

### 9.4. Tool Result

- [ ] Raw output được parse và validate.
- [ ] Chỉ giữ high-signal fields.
- [ ] Có status, source và `retrieved_at`.
- [ ] Error được chuẩn hóa và phân loại retryable.
- [ ] Text bên ngoài không được xem là instruction.
- [ ] Cache/fallback có caveat và freshness.

### 9.5. Control và Eval

- [ ] Approval được enforce bằng code.
- [ ] Write action có audit log đầy đủ.
- [ ] Retry có giới hạn và timeout.
- [ ] Có positive, negative, tool và injection cases.
- [ ] Agent eval kiểm tra cả trace, không chỉ final answer.
- [ ] Có holdout/regression test.
- [ ] Mỗi thay đổi có version, delta và rollback decision.

## 10. Quy trình debug đề xuất

Khi AI app trả kết quả không đáng tin, xử lý theo thứ tự:

1. Mô tả lỗi bằng hành vi quan sát được và tạo eval case tái hiện.
2. Xác định lớp lỗi: prompt, context, tool request, tool result, control hay eval/versioning.
3. Sửa artifact nhỏ nhất đúng với lớp lỗi.
4. Chạy targeted eval và regression/holdout cases.
5. So sánh phiên bản cũ và mới bằng metric hoặc rubric đã định.
6. Ghi version, thay đổi, delta và quyết định keep/revise/rollback.
7. Quan sát trace production để phát hiện lỗi mới.

Tư tưởng xuyên suốt của tài liệu: một agent đáng tin không chỉ “biết chạy”. Agent cần nhận chỉ dẫn rõ, được cấp context đúng, chỉ nhìn thấy công cụ phù hợp, gọi công cụ với tham số và quyền hợp lệ, coi tool result là dữ liệu không đáng tin mặc định, và dừng đúng lúc khi cần con người kiểm soát.

## 11. Nguồn

- Tài liệu gốc: `D:\ABG_requirement\day04.pdf`, 74 trang, tiêu đề *Prompt & Context Engineering — Day 04 (v2.1)*.
- Bản tổng hợp này diễn giải và hệ thống hóa nội dung phục vụ học tập và áp dụng; không phải bản chép nguyên văn từng slide.
