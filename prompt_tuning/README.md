# Experiment: Prompt Tuning — 對話點餐 Prompt 優化

## 目標

在完全不碰 `src/` 正式程式碼的前提下，針對**點餐兼提供基本資訊的 Agent** 進行 prompt 優化與架構調校，核心目標有二：

1. **簡化點餐流程的 Prompt**：目前 `prompts.py` 中的 `SYSTEM_PROMPT_TEMPLATE` 僅為範例版本（正式版邏輯類似但更多），需簡化冗餘指令、合併重複規則，或調整 Agent 架構（如精簡 tool description、減少 function calling 輪次），以大幅減少 token 消耗量。

2. **模型遷移至 gemini-2.5-flash-lite**：目前使用 gemini-2.5-flash，需設法改用 gemini-2.5-flash-lite 等更輕量的模型，在減少 token 消耗與加速回應的同時，**盡可能保證對於複雜訂單的處理效能是一致的**（多品項點餐、修改、移除、加料等情境）。

3. **多層 Agent（Sub-Agent）架構優化**：除了修改 prompt 本身，也可嘗試將目前的單一 Agent 拆分為**多層 sub-agent 架構**，讓不同的 agent 專責處理不同任務（如意圖分類、點餐執行、閒聊回覆），藉此優化 **token 消耗**、**金錢成本** 與 **回應速度**。

## 核心需求

| 項目 | 說明 |
|------|------|
| Prompt 精簡 | 簡化 `SYSTEM_PROMPT_TEMPLATE`，移除冗餘指令、合併重複規則|
| 架構調整 | 可調整 tool description 精簡、減少 function calling turns 等以降低整體 token 消耗 |
| 多層 Agent 架構 | 將單一 Agent 拆為多個 sub-agent，各自使用最適合的模型與最精簡的 prompt，降低每次請求的 token 總量與延遲（詳見下方「多層 Agent 優化方向」） |
| 模型遷移 | 從 `gemini-2.5-flash` 遷移至 `gemini-2.5-flash-lite`，修改 `config.py` 預設值 |
| 效能保證 | 複雜訂單（多品項、修改、移除、加料）的處理準確度不能下降 |
| Token 消耗追蹤 | 加入 token 使用量的觀測/記錄機制，用以量化優化效果 |
| 回應速度 | 使用 flash-lite 後，回應延遲應明顯降低 |
| 語音多模態輸入 | 由我們提供語音輸入模組（`voice_input.py`），目前使用 Gemini 多模態 API 模擬語音辨識（僅供測試），你也可以替換成其他 ASR 模型（Whisper、SpeechBrain 等） |
| 語音辨識容錯 | 測試並處理語音辨識錯誤（品名近音混淆、甜度/冰塊選項誤判等），可透過 prompt 加入品名/選項對照表、fuzzy matching、或主動確認機制來修正 |

## 驗收標準

- [ ] 成功將模型切換至 `gemini-2.5-flash-lite` 並能正常運作
- [ ] 基本點餐流程測試通過：「我要一杯珍珠奶茶，大杯，半糖少冰」→ 正確加入購物車
- [ ] 複雜訂單測試通過：多品項點餐 + 修改 + 移除 + 加料 → 購物車內容正確
- [ ] 修改 vs 新增判斷準確率不下降：「幫我改成大杯」使用 `update_cart_item` 而非 `add_to_cart`
- [ ] 結帳流程完整可用
- [ ] 閒聊/查詢店家資訊功能正常（營業時間、菜單查詢等）
- [ ] 提供 token / 金錢 消耗的前後對比數據（flash vs flash-lite，優化前 vs 後）
- [ ] 提供回應延遲的前後對比數據
- [ ] 語音輸入測試：透過我們提供的語音模組（目前使用 Gemini 模擬，可替換成其他 ASR 模型），接收音訊並完成點餐流程
- [ ] 語音 vs 文字點餐一致性測試：同一句話的文字輸入與語音輸入應產生相同的購物車結果
- [ ] 語音辨識錯誤容錯測試：品名近音錯誤（如「珍珠奶茶」被辨識為「真主奶茶」）仍能正確匹配商品
- [ ] 語音辨識錯誤容錯測試：選項辨識錯誤（如「半糖」→「伴糖」、「去冰」→「乏冰」）仍能正確處理
- [ ] 提供語音辨識容錯的解決方案說明（架構調整 / prompt 修正 / fuzzy matching 等）

---

## 快速啟動

### 本地運行

```bash
cd experiments/prompt_tuning
python main.py
```

啟動後會詢問輸入模式：

```
========================================
  蟬吃茶 點餐助手 (Ezra)
  模型: gemini-2.5-flash
========================================

請選擇輸入模式：
  1. 文字模式（打字點餐）
  2. 語音輸入模式（音訊 → 語音辨識 → 點餐）
請選擇 (1/2，預設 1)：
```

### 環境安裝

```bash
cd experiments/prompt_tuning
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，至少填入 GEMINI_API_KEY
```

### Docker 運行

```bash
cd experiments/prompt_tuning
docker build -t prompt-tuning .
docker run -it --env-file .env prompt-tuning
```

使用範例：文字模式

```
==================================================
  蟬吃茶 智能點餐助手 (Ezra)
  模型: gemini-2.5-flash
==================================================
輸入對話內容，按 Enter 送出。輸入 quit 或 exit 離開。

你：有什麼推薦的？
  [tools: get_full_menu]
🤖：我們有高山茶系列、蟬吃茶系列、果茶系列...

你：quit
👋 掰掰！
```

---

## 專案結構

```
prompt_tuning/
├── Dockerfile              # Docker 容器化
├── main.py                 # CLI 互動式對話入口
├── ordering_assistant.py   # 🔑 核心：Agentic 對話引擎（function calling）
├── prompts.py              # 📌 系統提示詞（優化重點 1）
├── cart_service.py         # 購物車邏輯（Mock 版）
├── store_info_service.py   # 店家資訊 MCP Tools（Mock 版）
├── mock_data.py            # 所有 Mock 資料（菜單、加料、營業時間）
│├── voice_input.py          # 🎤 語音輸入模組（目前用 Gemini 模擬 ASR，可替換其他模型）
├── config.py               # 環境變數載入
├── .env.example            # 環境變數範本
├── requirements.txt        # Python 依賴
└── README.md               # 你在看的這個檔案
```

---

## 架構簡介

```
用戶輸入 (CLI)
  │
  ├─ 模式選擇：文字 / 語音
  │
  ┬──────── [語音模式] ────────┬
  │                              │
  │  voice_input.py               │
  │  Layer 1: SpeechToTextAgent   │
  │  （音訊 → 文字）               │
  │  ⚠️ 目前用 Gemini 模擬        │
  │     可換 Whisper 等 ASR     │
  └──────────────────────────────┘
  │
  ▼ (純文字)

ordering_assistant.py  Layer 2（Gemini function calling）
  │
  ├─ 判斷是否需要 tool call
  │   ├─ get_product_price      → mock_data
  │   ├─ check_product_availability → mock_data
  │   ├─ get_current_datetime   → Python datetime
  │   ├─ get_store_info / get_full_menu / ... → store_info_service.py → mock_data
  │   ├─ add_to_cart / update / remove / ... → cart_service.py → mock_data
  │   └─ show_*_card            → store_info_service.py (UI card 標記)
  │
  ├─ 執行 tool，取得結果
  │
  └─ 第二輪 LLM：用 tool 結果生成自然語言回應
       │
       ▼
     印到終端機
```

- **外層 LLM**：使用 Gemini API Key 模式（function calling）
- **購物車**：純記憶體（不存 DB），`submit_order` 只回傳模擬結果

---

## 多層 Agent（Sub-Agent）優化方向

除了直接修改 prompt 內容，另一個重要的優化策略是**將單一大 Agent 拆分為多層 sub-agent 架構**。核心思路：不是每個使用者請求都需要完整的 system prompt 和所有 tool definitions — 透過分層處理，可以大幅減少每次 LLM 呼叫所需的 token 量。

### 為什麼 Sub-Agent 能優化成本與速度？

| 問題 | 單一 Agent | 多層 Sub-Agent |
|------|-----------|----------------|
| **每次請求的 prompt 大小** | 完整 system prompt + 所有 tool definitions → token 量大 | 每個 sub-agent 只帶自己需要的 prompt 與 tools → token 量小 |
| **模型選擇** | 統一使用同一個模型 | 不同 agent 可用不同模型：簡單任務用便宜快速的模型，複雜任務才用強模型 |
| **回應延遲** | prompt 越長，首 token 延遲越高 | 每層 prompt 精簡，回應更快；簡單請求可提前返回不進入深層 agent |
| **Function calling 輪次** | 所有 tools 混在一起，模型需從大量 tools 中選擇 | 每層 agent 只暴露少量 tools，選擇更精準、減少誤呼叫 |

### 建議的 Sub-Agent 架構

```
用戶輸入（文字 / 語音轉文字）
  │
  ▼
┌─────────────────────────────────────────────┐
│  Router Agent（意圖分類）                      │
│  模型：gemini-2.5-flash-lite（最輕量）          │
│  Prompt：極精簡，僅做意圖分類                    │
│  Tools：無                                     │
│  輸出：intent = ordering / chitchat / info_query│
└────────────┬────────────────────────────────────┘
             │
     ┌───────┼───────┐
     ▼       ▼       ▼
┌─────────┐ ┌──────────┐ ┌──────────────┐
│ Ordering│ │ Chitchat │ │ Info Query   │
│ Agent   │ │ Agent    │ │ Agent        │
│         │ │          │ │              │
│ flash   │ │flash-lite│ │ flash-lite   │
│ 完整點餐 │ │ 無 tools │ │ 店家資訊     │
│ prompt  │ │ 簡短回覆 │ │ tools only  │
│ + tools │ │          │ │              │
└─────────┘ └──────────┘ └──────────────┘
```

#### 各層 Agent 說明

| Agent | 職責 | 模型建議 | Prompt 大小 | Tools |
|-------|------|---------|------------|-------|
| **Router Agent** | 判斷使用者意圖（點餐 / 閒聊 / 查詢資訊） | `gemini-2.5-flash-lite` | 極小（< 200 tokens） | 無 |
| **Ordering Agent** | 處理點餐、修改、移除、加料、結帳 | `gemini-2.5-flash` | 中等（僅點餐相關規則） | `add_to_cart`, `update_cart_item`, `remove_from_cart`, `get_product_price`, ... |
| **Chitchat Agent** | 閒聊、打招呼、與點餐無關的對話 | `gemini-2.5-flash-lite` | 極小（品牌語調即可） | 無 |
| **Info Query Agent** | 營業時間、菜單查詢、店家資訊 | `gemini-2.5-flash-lite` | 小 | `get_store_info`, `get_full_menu`, `get_store_hours`, ... |

### Token / 成本優化效果預估

以一個典型的「閒聊 → 看菜單 → 點餐」對話流為例：

| 場景 | 單一 Agent（每輪 token） | 多層 Sub-Agent（每輪 token） | 節省比例 |
|------|------------------------|----------------------------|----------|
| 閒聊「你好」 | 完整 prompt ~2000+ tokens | Router ~200 + Chitchat ~300 = ~500 tokens | **~75%** |
| 查菜單 | 完整 prompt ~2000+ tokens | Router ~200 + Info ~500 = ~700 tokens | **~65%** |
| 點餐（複雜） | 完整 prompt ~2000+ tokens | Router ~200 + Ordering ~1500 = ~1700 tokens | **~15%** |
| **混合對話（10 輪）** | 每輪都是 ~2000+ | 依意圖分配，加權平均 ~800 | **~60%** |

> **關鍵洞察**：實際對話中，純點餐操作往往只佔少數輪次，大量輪次是閒聊、確認、查詢。Sub-agent 架構讓這些「輕量輪次」真正變得輕量。

### 回應速度優化

- **Router Agent** 因 prompt 極短，首 token 延遲可控制在 **< 200ms**
- 簡單意圖（閒聊 / 查詢）走輕量 agent，端到端延遲可比單一 Agent 快 **30-50%**
- 複雜點餐仍走完整 Ordering Agent，確保準確度不犧牲

### 實作建議

1. **先實作 Router Agent**：用 `gemini-2.5-flash-lite` + 極簡 prompt 做意圖分類，輸出 JSON `{"intent": "ordering" | "chitchat" | "info_query"}`
2. **拆分現有 tools**：將 `ordering_assistant.py` 中的 tools 依職責分組，各 sub-agent 只註冊自己需要的 tools
3. **對話歷史管理**：Router Agent 只需最近 1-2 輪上下文；Ordering Agent 需要完整點餐上下文（但不需要閒聊歷史）
4. **量測對比**：每層 agent 獨立記錄 `prompt_tokens` / `completion_tokens` / `latency`，與原始單一 Agent 做 A/B 對比
5. **漸進式拆分**：可先從「閒聊分流」開始（效果最顯著），再逐步拆分 info query 與 ordering

