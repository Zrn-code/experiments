# Experiment: RAG Search — 知識庫檢索品質驗證

## 目標

確保 Gemini + Vertex AI Search 的 RAG 架構能**可靠地**完成以下行為：

1. **該查就查**：當顧客詢問產品相關問題時，LLM 必須呼叫 `search_knowledge_base` 工具，而非靠自身知識（幻覺）回答。
2. **查得到、查得對**：Vertex AI Search 必須從 `docs_rag/` 的 45 份產品文件中檢索到正確的文件，回傳結果帶有 grounding。
3. **答得準**：最終回答必須包含知識庫文件中的具體事實（茶底、風味、原料等），而非泛泛而談。

### 要解決的兩個核心問題

| 失敗模式 | 現象 | 判定方式 |
|----------|------|----------|
| **不查詢就幻覺** | 問「珍珠奶茶」相關問題，LLM 沒有呼叫工具，直接用幻覺回答 | `chat()` 回傳 `tool_used=False` |
| **查了但沒命中** | LLM 呼叫了工具，但 Vertex AI Search 沒有檢索到對應文件或回傳不相關的內容 | `tool_used=True` 但 `has_grounding=False`，或 `answer` 中缺少預期關鍵字 |

架構仿照 ezragt-server：Gemini 作為主控，自動判斷是否需要查詢知識庫（function calling）。  
知識庫文件（`docs_rag/`）已完成重寫，內容為真實完整的商品資料，可直接用作正式知識庫。

---

## 驗收標準

所有測試案例的 Pass / Fail 皆基於 `chat()` 回傳的欄位判定，不依賴主觀感受。

### A. 直接產品查詢（必須查詢 + 必須命中正確文件）

| # | 輸入問句 | `tool_used` | `has_grounding` | `answer` 必須包含 | 驗證依據（docs_rag） |
|---|---------|:-----------:|:---------------:|------------------|---------------------|
| A1 | 珍珠奶茶有什麼特色？ | ✅ True | ✅ True | 「金玉紅茶」「紐西蘭奶粉」其中至少一個 | `item_39_珍珠奶茶.txt`：茶底為金玉紅茶、原料含紐西蘭奶粉 |
| A2 | 蜜香紅茶是什麼茶？ | ✅ True | ✅ True | 「小綠葉蟬」「全發酵」其中至少一個 | `item_08_蟬吃蜜香紅茶.txt`：小綠葉蟬吸食、100% 全發酵 |
| A3 | 高山冷泓青的口感如何？ | ✅ True | ✅ True | 「花香」「不苦不澀」「回甘」其中至少一個 | `item_01_高山冷泓青.txt`：淡雅花香、不苦不澀、尾韻回甘 |
| A4 | 黑糖薑紅茶適合什麼時候喝？ | ✅ True | ✅ True | 「薑」「暖」或「冬」其中至少一個 | `item_21_黑糖薑紅茶.txt` |
| A5 | 珍珠黑糖鮮奶用的是什麼奶？ | ✅ True | ✅ True | 「鮮奶」或「鮮乳」 | `item_45_珍珠黑糖鮮奶.txt` |

**Pass 定義**：5 題中至少 4 題同時滿足三個欄位條件。

### B. 模糊 / 情境式查詢（必須查詢 + 推薦合理產品）

| # | 輸入問句 | `tool_used` | `has_grounding` | `answer` 合理回答範圍 |
|---|---------|:-----------:|:---------------:|---------------------|
| B1 | 有蜜香的茶推薦嗎？ | ✅ True | ✅ True | 應提及：蜜香紅茶、蜂蜜紅、金玉紅茶 其中至少一項 |
| B2 | 想喝清爽不甜的 | ✅ True | ✅ True | 應提及：冷泓青、烏龍綠、鮮翠烏龍 其中至少一項 |
| B3 | 天氣冷想喝暖的 | ✅ True | ✅ True | 應提及：薑茶系列（黑糖薑茶/薑紅茶/烏龍薑）其中至少一項 |
| B4 | 有沒有適合小朋友喝的？ | ✅ True | ✅ True | 不應推薦高咖啡因的純茶；優先推薦蜂蜜水、蜂蜜檸檬汁等 |
| B5 | 不想喝甜的，但又不想太苦 | ✅ True | ✅ True | 應提及：冷泓青、蜜香紅茶、烏龍 其中至少一項（這些無糖也不苦澀） |

**Pass 定義**：5 題中至少 3 題同時滿足 `tool_used=True` + `has_grounding=True` + 推薦產品在合理範圍內。

### C. 非知識庫問題 — 負向測試（不應查詢）

| # | 輸入問句 | `tool_used` | 說明 |
|---|---------|:-----------:|------|
| C1 | 你好 | ❌ False | 打招呼，不需要查詢知識庫 |
| C2 | 今天天氣如何？ | ❌ False | 與產品無關的閒聊 |
| C3 | 謝謝你的推薦 | ❌ False | 禮貌性回覆 |

**Pass 定義**：3 題中至少 2 題 `tool_used=False`。

### D. 整體通過條件

> **A、B、C 三類全部 Pass，即為驗收通過。**
>
> 若任一類 Fail，需依照下方「已知問題與排查」對應調整後重新測試。

---

## 已知問題與排查

### 問題 1：LLM 不呼叫工具，直接幻覺回答（A/B 類 `tool_used=False`）

**原因**：Gemini 認為自己已經知道答案，不需要查詢。

**排查方向**：
1. **檢查 `prompts.py` 的 `SYSTEM_PROMPT`** — 是否有明確指示「當顧客問到產品時**必須**使用工具查詢」，而非「可以使用」。
2. **檢查 `SEARCH_TOOL_DECLARATION` 的 `description`** — 描述是否涵蓋了測試問句的語意範圍。例如，若顧客問「清爽不甜的」，description 中是否提到「風味偏好」「推薦」等詞。
3. **考慮在 `GenerateContentConfig` 中設定 `tool_config` 為 `ANY` 模式**（強制使用工具），但這會讓 C 類負向測試也呼叫工具，需權衡。

### 問題 2：工具有呼叫，但 Vertex AI Search 沒有 grounding（A/B 類 `has_grounding=False`）

**原因**：Vertex AI Search 的檢索結果與查詢不匹配，或索引尚未完成。

**排查方向**：
1. **確認索引狀態** — Data Store 頁面是否顯示「Indexing complete」。上傳或更新文件後需等待重新索引。
2. **檢查 `search_query`** — `chat()` 回傳的 `search_query` 是否合理？LLM 可能改寫了查詢（例如把「珍珠奶茶」改寫為過於抽象的查詢詞），導致 Vertex AI Search 找不到。
3. **檢查文件關鍵字覆蓋** — 對應的 `docs_rag/` 文件中是否包含與查詢相關的詞彙？例如，B2「清爽不甜」對應的文件中是否出現「清爽」「不甜」「不苦不澀」等詞。
4. **檢查 `RAG_SEARCH_INSTRUCTION`** — 搜尋用的 system prompt 是否干擾了檢索結果的呈現。

### 問題 3：有 grounding 但答案缺少預期關鍵字（A 類 `answer` 不含關鍵字）

**原因**：Vertex AI Search 檢索到了文件但 LLM 沒有引用其中的關鍵事實。

**排查方向**：
1. **檢查 `rag_search.py` Turn 2 的 `final_prompt`** — 是否足夠明確要求 LLM「根據知識庫搜尋結果中的具體資訊回答」。
2. **檢查 `temperature`** — Turn 2 的 temperature 是否過高（目前 0.3），導致 LLM 自由發揮過多。
3. **檢查 grounding_chunks 內容** — 用 `main.py` 的 CLI 輸出觀察取回的 chunks 是否確實包含預期文件的內容。

---

## 運作架構

```
顧客提問 → Gemini (Turn 1: 判斷是否需要查知識庫)
              │
              ├─ 需要 → search_knowledge_base() → Vertex AI Search RAG
              │                                         │
              │         Gemini (Turn 2: 根據 RAG 結果生成店員語氣回答)
              │
              └─ 不需要 → Gemini 直接回答
```

---

## 快速啟動

### 本地運行

```bash
cd experiments/rag_search
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，填入 VERTEX_AI_API_KEY 和 Vertex AI Search 設定

python main.py
```

### Docker 運行

```bash
cd experiments/rag_search
docker build -t rag-search .
docker run -it --env-file .env rag-search
```

### 使用範例

```
==================================================
  蟬吃茶知識助手 — RAG Search 實驗
  模型: gemini-2.5-flash
==================================================
像顧客一樣提問，助手會自動判斷是否需要查詢知識庫。
輸入 quit 或 exit 離開。

🧑 顧客：你知道什麼是蜜香紅嗎？

🍵 店員：蜜香紅是我們很受歡迎的一款茶哦！它有獨特的蜜香風味...
   📚 知識庫查詢：蜜香紅的口感特色
   Grounding: ✅ 有
   來源片段數: 3

```

---

## 專案結構

```
rag_search/
├── Dockerfile          # Docker 容器化
├── main.py             # CLI 互動知識助手入口
├── rag_search.py       # 對話編排：二階段 function calling
├── vertex_search.py    # Vertex AI Search RAG 搜尋模組
├── prompts.py          # 系統提示詞與工具宣告
├── config.py           # 環境變數載入
├── .env.example        # 環境變數範本
├── requirements.txt    # Python 依賴
├── docs/               # 📌 知識庫文件（上傳到 Cloud Storage 的來源）
└── README.md
```

---

## Vertex AI Search 設定流程

### Step 1：建立 Cloud Storage Bucket

1. 前往 [Cloud Storage](https://console.cloud.google.com/storage/browser)
2. 點擊「Create」建立新 bucket
3. 設定 bucket 名稱（例如 `rag_restorage`）
4. 將 `docs/` 資料夾中的文件上傳到 bucket

### Step 2：建立資料儲存庫（Data Store）

1. 前往 [Agent Builder — Data Stores](https://console.cloud.google.com/gen-app-builder/data-stores)
2. 點擊「Create data store」
3. 選擇 **Cloud Storage** 作為資料來源
4. 選擇「**文件（Documents）**」
5. 指向 Step 1 建立的 bucket
6. 設定：
   - **Location**：建議選 `global`
   - **Data store name**：自訂名稱
7. 建立後，記下 **Data Store ID**

> 上傳文件後需等待索引完成（通常幾分鐘到半小時），頁面顯示「Indexing complete」即可。

### Step 3：填寫 .env

```bash
cp .env.example .env
```

```env
VERTEX_AI_API_KEY=your-vertex-ai-api-key

VERTEX_PROJECT_ID=your-gcp-project-id
VERTEX_REGION=us-central1
VERTEX_DATA_STORE_ID=your-datastore-id
VERTEX_DATA_STORE_LOCATION=global
```

| 變數 | 說明 | 在哪裡找 |
|------|------|--------|
| `VERTEX_AI_API_KEY` | Vertex AI API Key | GCP Console → API & Services → Credentials |
| `VERTEX_PROJECT_ID` | GCP 專案 ID | Console 首頁 / 專案選擇器 |
| `VERTEX_REGION` | Vertex AI 區域 | 通常 `us-central1` |
| `VERTEX_DATA_STORE_ID` | Data Store 的 ID | Agent Builder → Data Stores → 點進去看 URL |
| `VERTEX_DATA_STORE_LOCATION` | Data Store 的位置 | 建立時選的 location，通常 `global` |

---

## 常見問題

### Q: Data Store 建立後搜不到東西？

索引需要時間。上傳文件後，等待頁面顯示「Indexing complete」。

### Q: 出現 403 PERMISSION_DENIED `discoveryengine.servingConfigs.search`？

這是最常見的問題。Vertex AI API Key 預設可能沒有 Discovery Engine 的存取權限。

**修復步驟：**

1. **啟用 Discovery Engine API**
   ```bash
   gcloud services enable discoveryengine.googleapis.com --project=YOUR_PROJECT_ID
   ```

2. **檢查 API Key 限制**
   - 前往 [GCP Console → API & Services → Credentials](https://console.cloud.google.com/apis/credentials)
   - 點進你使用的 API Key
   - 確認「API restrictions」不是「Restrict key」，或已包含 **Discovery Engine API** 和 **Vertex AI API**
   - 如果有限制，加入這兩個 API 後儲存

3. **確認 Data Store 存在**
   - 前往 [Agent Builder → Data Stores](https://console.cloud.google.com/gen-app-builder/data-stores)
   - 確認 `.env` 中的 `VERTEX_DATA_STORE_ID` 和 `VERTEX_PROJECT_ID` 與實際一致
   - 確認 Data Store 的 location 與 `VERTEX_DATA_STORE_LOCATION` 一致（通常是 `global`）
