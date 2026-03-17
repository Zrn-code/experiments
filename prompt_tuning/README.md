# Experiment: Prompt Tuning — 對話點餐 Prompt 優化

## 目標

在完全不碰 `src/` 正式程式碼的前提下，針對**點餐兼提供基本資訊的 Agent** 進行 prompt 優化與架構調校，核心目標有二：

1. **簡化點餐流程的 Prompt**：目前 `prompts.py` 中的 `SYSTEM_PROMPT_TEMPLATE` 僅為範例版本（正式版邏輯類似但更多），需簡化冗餘指令、合併重複規則，或調整 Agent 架構（如精簡 tool description、減少 function calling 輪次），以大幅減少 token 消耗量。

2. **模型遷移至 gemini-2.5-flash-lite**：目前使用 gemini-2.5-flash，需設法改用 gemini-2.5-flash-lite 等更輕量的模型，在減少 token 消耗與加速回應的同時，**盡可能保證對於複雜訂單的處理效能是一致的**（多品項點餐、修改、移除、加料等情境）。

## 核心需求

| 項目 | 說明 |
|------|------|
| Prompt 精簡 | 簡化 `SYSTEM_PROMPT_TEMPLATE`，移除冗餘指令、合併重複規則|
| 架構調整 | 可調整 tool description 精簡、減少 function calling turns等以降低整體 token 消耗 |
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
- [ ] 提供 token 消耗的前後對比數據（flash vs flash-lite，優化前 vs 後）
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

## 你該改什麼？

### 1. `prompts.py` — 系統提示詞

`AGENTIC_RAG_SYSTEM_PROMPT_TEMPLATE` 定義了 AI 助手的角色、語氣、規則。
修改這裡可以：
- 改變 AI 的個性和語氣
- 調整回覆長度和格式
- 新增或移除行為規則
- 改善推薦邏輯

### 2. `ordering_assistant.py` — 對話引擎

- `_define_function_tools()`：每個 tool 的 `description` 影響 LLM 選擇工具的決策
- `_build_agentic_prompt()`：prompt 結構和指引影響回應品質

### 3. `mock_data.py` — Mock 資料

- 可以新增菜單品項、修改價格、調整加料選項
- 修改 `STORE_INFO` 可改變品牌故事等內容

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

## 不依賴 `src/`

這個實驗資料夾**完全獨立**，不 import `src/` 裡的任何模組。
所有資料都來自 `mock_data.py`，所有邏輯都自包含在此資料夾中。
