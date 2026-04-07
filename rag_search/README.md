# Experiment: RAG Search — 知識庫檢索品質驗證

## 目標

驗證 Gemini + Vertex AI Search 的兩層 RAG 架構能否可靠地：

1. **該查就查** — 產品相關問題必須呼叫 `search_knowledge_base`（grounding search），不能靠幻覺回答
2. **查得到** — Vertex AI Search 從 `docs_rag/` 45 份文件中檢索到正確內容
3. **答得準** — 最終回答包含知識庫中的具體事實（茶底、風味、原料等）

| 失敗模式 | 現象 | 判定 |
|----------|------|------|
| 不查就幻覺 | LLM 沒呼叫工具，直接回答 | `tool_used=False` |
| 查了沒命中 | 工具有呼叫，但回答缺少預期關鍵字 | `tool_used=True` 但 `answer` 缺少預期內容 |

---

## 架構

Vertex AI Search 的 `retrieval` tool **不能與 `function_declarations` 混用**，因此架構強制切分兩層：

```
顧客提問
  │
  ▼
[第一層] rag_search.py — Turn 1
  工具: function_declarations
  職責: 判斷是否需要查知識庫，決定查詢詞
  │
  ├─ 不需要 → 直接回答（閒聊/打招呼）
  │
  └─ 需要 → search_knowledge_base(query)
               │
               ▼
             [第二層] vertex_search.py
               工具: retrieval（Vertex AI Search grounding search）
               職責: 從 Data Store 檢索文件，回傳 grounding 結果
               │
               ▼
             [第一層] rag_search.py — Turn 2
               工具: 無（純文字生成）
               職責: 根據 RAG 結果生成回答
```

---

## 驗收標準

所有判定基於 `chat()` 回傳欄位，不依賴主觀感受。

### A. 直接產品查詢（必須查詢 + 命中正確文件）

| # | 輸入 | `answer` 必須包含 | 來源文件 |
|---|------|------------------|----------|
| A1 | 珍珠奶茶有什麼特色？ | 「金玉紅茶」或「紐西蘭奶粉」 | `item_39_珍珠奶茶.txt` |
| A2 | 蜜香紅茶是什麼茶？ | 「小綠葉蟬」或「全發酵」 | `item_08_蟬吃蜜香紅茶.txt` |
| A3 | 高山冷泓青的口感如何？ | 「花香」「不苦不澀」「回甘」之一 | `item_01_高山冷泓青.txt` |
| A4 | 黑糖薑紅茶適合什麼時候喝？ | 「薑」「暖」「冬」之一 | `item_21_黑糖薑紅茶.txt` |
| A5 | 珍珠黑糖鮮奶用的是什麼奶？ | 「鮮奶」或「鮮乳」 | `item_45_珍珠黑糖鮮奶.txt` |

全部要求 `tool_used=True`。**Pass：5 題至少 4 題滿足。**

### B. 模糊 / 情境查詢（必須查詢 + 推薦合理產品）

| # | 輸入 | 合理回答範圍 |
|---|------|-------------|
| B1 | 有蜜香的茶推薦嗎？ | 蜜香紅茶、蜂蜜紅、金玉紅茶 之一 |
| B2 | 想喝清爽不甜的 | 冷泓青、烏龍綠、鮮翠烏龍 之一 |
| B3 | 天氣冷想喝暖的 | 薑茶系列（黑糖薑茶/薑紅茶/烏龍薑）之一 |
| B4 | 有沒有適合小朋友喝的？ | 不推薦高咖啡因純茶；優先蜂蜜水、蜂蜜檸檬汁等 |
| B5 | 不想喝甜的但又不想太苦 | 冷泓青、蜜香紅茶、烏龍 之一 |

全部要求 `tool_used=True`。**Pass：5 題至少 3 題滿足。**

### C. 負向測試（不應查詢）

| # | 輸入 | 預期 |
|---|------|------|
| C1 | 你好 | `tool_used=False` |
| C2 | 今天天氣如何？ | `tool_used=False` |
| C3 | 謝謝你的推薦 | `tool_used=False` |

**Pass：3 題至少 2 題 `tool_used=False`。**

### 整體通過條件

> A、B、C 三類全部 Pass = 驗收通過。任一 Fail 需調整後重測。

---

## 調整與排查

驗收未通過時，依失敗類型對照調整：

### 不查詢就幻覺（A/B 類 `tool_used=False`）

| 調整項目 | 位置 | 方向 |
|----------|------|------|
| `SYSTEM_PROMPT` | `prompts.py:11` | 「**必須**使用工具」vs「可以使用」差異極大 |
| `SEARCH_TOOL_DECLARATION.description` | `prompts.py:28` | 描述太窄（只提「產品特色」）→ 模糊查詢不觸發。加入「推薦」「風味偏好」等詞 |
| `SEARCH_TOOL_DECLARATION.parameters` | `prompts.py:33` | query 參數描述影響 LLM 生成的查詢詞品質 |
| `tool_config` 設為 `ANY` | `rag_search.py` Turn 1 | 強制使用工具，但 C 類負向測試也會觸發，需權衡 |

### 查了但答案缺關鍵字（`tool_used=True` 但 answer 不對）

可能是**檢索層**（Vertex AI Search 沒找到）或**回答生成層**（找到了但 LLM 沒引用）。

> **診斷方式**：用 `main.py` CLI 觀察 `grounding_chunks`。有正確 chunks → 問題在回答生成層；沒有 → 問題在檢索層。

**檢索層調整：**

| 調整項目 | 位置 | 方向 |
|----------|------|------|
| 索引狀態 | GCP Console | Data Store 是否顯示「Indexing complete」 |
| `search_query` | `chat()` 回傳值 | LLM 可能改寫查詢詞導致搜不到 |
| 文件關鍵字 | `docs_rag/*.txt` | 文件是否含顧客用語？如「清爽」「暖身」等情境詞 |
| 綜合分類文件 | `docs_rag/` | 新增「清爽茶品推薦.txt」等，讓情境查詢直接命中 |
| chunk 切分 | `docs_rag/*.txt` | 結構化 `##` 標題有助切出語意完整 chunk |
| `RAG_SEARCH_INSTRUCTION` | `prompts.py:20` | 第二層 system prompt，太簡短會導致過度摘要 |
| 查詢前綴 | `vertex_search.py:79` | `"請根據知識庫回答：{query}"` 影響檢索行為 |

**回答生成層調整：**

| 調整項目 | 位置 | 方向 |
|----------|------|------|
| `final_prompt` | `rag_search.py:96-100` | 需明確要求「引用知識庫中的具體事實」 |
| `temperature` | `rag_search.py:104` | 目前 0.3，越低越忠實於 RAG 結果 |
| Turn 2 system prompt | `rag_search.py:105` | 目前複用 `SYSTEM_PROMPT`，可考慮設專用 prompt |

---

## 快速啟動

```bash
cd experiments/rag_search
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env           # 填入 API Key 和 Vertex AI Search 設定
python main.py
```

Docker：
```bash
docker build -t rag-search .
docker run -it --env-file .env rag-search
```

輸出範例：
```
==================================================
  蟬吃茶知識助手 — RAG Search 實驗
  模型: gemini-2.5-flash-lite
==================================================

🧑 顧客：你知道什麼是蜜香紅嗎？

🍵 店員：蜜香紅是我們很受歡迎的一款茶哦！...
   📚 知識庫查詢：蜜香紅的口感特色
   Grounding: ✅ 有｜來源片段數: 3
```

---

## 專案結構

```
rag_search/
├── main.py             # CLI 入口
├── rag_search.py       # 二階段 function calling 編排
├── vertex_search.py    # Vertex AI Search grounding 模組
├── prompts.py          # 提示詞與工具宣告
├── config.py           # 環境變數
├── docs_rag/           # 知識庫文件（45 份，上傳到 Cloud Storage）
├── .env.example
├── requirements.txt
└── Dockerfile
```

---

## Vertex AI Search 設定

### 1. Cloud Storage Bucket

[Cloud Storage](https://console.cloud.google.com/storage/browser) → Create bucket → 將 `docs_rag/` 文件上傳。

### 2. Data Store

[Agent Builder → Data Stores](https://console.cloud.google.com/gen-app-builder/data-stores) → Create → Cloud Storage → Documents → 指向 bucket → Location `global` → 記下 **Data Store ID**。

> 索引需等待完成（幾分鐘～半小時），頁面顯示「Indexing complete」即可。

### 3. .env

```bash
cp .env.example .env
```

| 變數 | 說明 | 在哪裡找 |
|------|------|--------|
| `VERTEX_AI_API_KEY` | API Key | GCP Console → Credentials |
| `VERTEX_PROJECT_ID` | 專案 ID | Console 首頁 |
| `VERTEX_REGION` | 區域（通常 `us-central1`） | Console |
| `VERTEX_DATA_STORE_ID` | Data Store ID | Agent Builder → Data Stores |
| `VERTEX_DATA_STORE_LOCATION` | Data Store 位置（通常 `global`） | 建立時選的 |

---

## 常見問題

### Data Store 建完搜不到東西？

索引需要時間，等頁面顯示「Indexing complete」。

### 403 PERMISSION_DENIED `discoveryengine.servingConfigs.search`？

1. **啟用 Discovery Engine API**
   ```bash
   gcloud services enable discoveryengine.googleapis.com --project=YOUR_PROJECT_ID
   ```
2. **檢查 API Key 限制** — [Credentials](https://console.cloud.google.com/apis/credentials) 頁面確認 Key 包含 **Discovery Engine API** + **Vertex AI API**
3. **確認 Data Store** — `.env` 中的 ID、Project、Location 與 GCP Console 一致
