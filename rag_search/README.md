# Experiment: RAG Search — 知識庫文件優化

## 目標

透過優化**知識庫文件的內容與結構**，讓 Gemini + Vertex AI Search 的 RAG 能根據**模糊、情境式的顧客提問**精準檢索到對應的產品資訊，並以自然對話的方式呈現結果。

例如，當顧客說：「我比較喜歡溫和順口的飲料，你有什麼推薦嗎？」，Agent 應能從知識庫中找到適合的茶品並像真實店員一樣推薦，而非將搜尋結果一次性列出。

資料庫中的文件應為**真實且完整**的商品資料，可直接作為正式知識庫使用。

架構仿照 ezragt-server：Gemini 作為主控，自動判斷是否需要查詢知識庫（function calling）。

## 核心需求

| 項目 | 說明 |
|------|------|
| 文件內容優化 | 調整 `docs/` 中 45 份商品 PDF 的內容，加入口感描述、風味標籤、適合情境、推薦搭配等，使模糊查詢可被正確檢索 |
| 文件結構優化 | 可重新設計文件結構（如按風味分類、合併相關品項、新增綜合推薦文件），提升 RAG 檢索精準度 |
| 真實完整資料 | 文件內容為真實且完整的商品資料，可直接用作正式知識庫 |
| 對話式呈現 | Agent 回應必須像自然對話，**禁止**把搜尋結果一次性列出，需逐步引導、推薦 |
| 情境式推薦 | 支援風味偏好描述（溫和順口、有蜜香、清爽不甜等）的智慧推薦，而非僅關鍵字匹配 |

## 驗收標準

- [ ] 完成 `docs/` 知識庫文件的內容重構，加入風味描述、適合情境、推薦搭配等結構化資訊
- [ ] 重新思考文件結構（單品 PDF vs 分類文件 vs 綜合推薦文件），使情境式查詢命中率提升
- [ ] 模糊查詢測試：「我比較喜歡溫和順口的飲料」能推薦出合適的茶品
- [ ] 偏好描述測試：「我想要有蜜香的」「清爽不甜的」等描述能找到對應商品
- [ ] Agent 回應風格測試：回答像自然對話，非列表式呈現搜尋結果
- [ ] 優化 `prompts.py` 中的 `SYSTEM_PROMPT` 和 `RAG_SEARCH_INSTRUCTION`，控制回應格式與對話風格
- [ ] 驗證 Vertex AI Search 索引重建後，檢索品質有明顯提升
- [ ] 提供至少 5 個情境式查詢的測試案例與預期結果

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
