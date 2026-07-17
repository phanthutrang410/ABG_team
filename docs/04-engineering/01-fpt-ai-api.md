# Hướng dẫn FPT AI API

> FPT AI Inference **tương thích chuẩn OpenAI API** — dùng y hệt cách gọi OpenAI, chỉ đổi `base_url`.

- **Base URL:** `https://mkp-api.fptcloud.com`
- **Endpoint chat:** `POST /v1/chat/completions`
- **Xác thực:** header `Authorization: Bearer <API_KEY>`

> ⚠️ **KHÔNG commit API key vào Git.** Repo này public — dán key thật lên là lộ, ai cũng xài được và cháy hết credit. Luôn để key trong `.env` (đã gitignore) hoặc biến môi trường.

---

## 1. Chuẩn bị key an toàn

Tạo file `.env` ở gốc project (đừng đưa lên Git):

```env
FPT_API_KEY=sk-your-real-key-here
FPT_BASE_URL=https://mkp-api.fptcloud.com
```

Thêm vào `.gitignore` nếu chưa có:

```gitignore
.env
```

---

## 2. Gọi bằng Python (OpenAI SDK)

Cài thư viện:

```bash
pip install openai python-dotenv
```

Code:

```python
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # đọc .env

client = OpenAI(
    api_key=os.environ["FPT_API_KEY"],
    base_url=os.environ["FPT_BASE_URL"],  # https://mkp-api.fptcloud.com
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3",       # đổi model tùy nhu cầu (xem bảng dưới)
    messages=[
        {"role": "system", "content": "Bạn là trợ lý tiếng Việt."},
        {"role": "user", "content": "Xin chào, giới thiệu bản thân đi"},
    ],
    temperature=0.7,
)

print(response.choices[0].message.content)
```

### Streaming (in dần từng chữ)

```python
stream = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3",
    messages=[{"role": "user", "content": "Viết đoạn giới thiệu 3 câu"}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

---

## 3. Gọi bằng cURL

```bash
curl https://mkp-api.fptcloud.com/v1/chat/completions \
  -H "Authorization: Bearer $FPT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-V3",
    "messages": [{"role": "user", "content": "Xin chào"}]
  }'
```

> Trên PowerShell, set biến trước: `$env:FPT_API_KEY = "sk-..."` rồi thay `$FPT_API_KEY` ở trên.

---

## 4. Gọi bằng JavaScript / Node (OpenAI SDK)

```bash
npm install openai dotenv
```

```javascript
import "dotenv/config";
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.FPT_API_KEY,
  baseURL: "https://mkp-api.fptcloud.com",
});

const res = await client.chat.completions.create({
  model: "deepseek-ai/DeepSeek-V3",
  messages: [{ role: "user", content: "Xin chào" }],
});

console.log(res.choices[0].message.content);
```

---

## 5. Các model có thể chọn

| Model | Context | Hợp cho |
|:--|:--|:--|
| `GLM-4.7` | 128K | Tổng quát, dễ bắt đầu |
| `meta-llama/Llama-4-Scout-17B-16E-Instruct` | 128K | Task nhanh, gọn |
| `meta-llama/Llama-4-Maverick-17B-128E-Instruct` | 1M | Context dài, task phức tạp |
| `Qwen/Qwen3-32B` | 128K | Tool calling, output có cấu trúc |
| `deepseek-ai/DeepSeek-V3` | 64K | Code, phân tích |
| `deepseek-ai/DeepSeek-R1` | 64K | Reasoning từng bước |

> Danh sách đầy đủ: xem tại [marketplace.fptcloud.com](https://marketplace.fptcloud.com). Có thể liệt kê bằng API: `GET /v1/models`.

**Gợi ý chọn model:**
- Cần **tool calling / output JSON có cấu trúc** → `Qwen/Qwen3-32B`.
- **Context siêu dài** (tài liệu lớn, nhiều file) → `Llama-4-Maverick` (1M).
- **Code / phân tích** → `DeepSeek-V3`.
- **Suy luận từng bước** (toán, logic) → `DeepSeek-R1`.

---

## 6. Theo dõi credit đã dùng

Xem đã tiêu / còn lại bao nhiêu tại:
`marketplace.fptcloud.com/my-account?tab=my-usage`

> Kiểm tra định kỳ để tránh cháy hết credit mà không biết.

---

## 7. Lỗi thường gặp

| Triệu chứng | Nguyên nhân thường gặp | Cách xử lý |
|:--|:--|:--|
| `401 Unauthorized` | Sai/thiếu key, key bị xoá | Kiểm tra `Authorization: Bearer`, tạo key mới |
| `404 model not found` | Sai tên model | Copy đúng tên từ bảng trên (phân biệt hoa/thường, có prefix `deepseek-ai/`...) |
| `429 Too Many Requests` | Vượt rate limit | Thêm retry + backoff, giảm tần suất gọi |
| Hết tiền / `insufficient credit` | Cháy $30 credit | Xem tab usage, nạp thêm |
