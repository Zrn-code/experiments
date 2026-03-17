# Chinese ASR Server — 中文語音辨識模型伺服器

## 目標

建立一個**自建的中文語音辨識（ASR）模型伺服器**，部署至 GCP 環境，提供即時語音轉文字服務。系統需支援**熱詞（Hot Words / Boosting）**功能，將蟬吃茶的產品名稱設定為熱詞，確保在聽到商品相關語句時能正確辨識，不發生錯誤。

## 核心需求

| 項目 | 說明 | 優先級 |
|------|------|--------|
| 自建模型 | 使用開源 ASR 模型，自行部署推論服務 | 必要 |
| 中文辨識 | 支援中文語音辨識 | 必要 |
| 熱詞支援 | 可**動態**定義熱詞清單，提升特定詞彙的辨識準確度（見 `hotwords/` 目錄） | 必要 |
| Batch 辨識 | **優先實作**——接收完整音訊檔，回傳辨識結果 | 必要 |
| Streaming 辨識 | 串流即時辨識，低延遲回應（加分項） | 加分 |
| GCP 部署 | 部署至 GCP 環境，**資源用量需精簡**，支撐 1000 人同時使用 | 必要 |
| 壓力測試 | 提供壓測腳本，驗證 1000 並發下的穩定性與延遲 | 必要 |

## 熱詞（Hot Words）管理

熱詞清單以**獨立 JSON 檔案**管理，存放於 `hotwords/` 目錄下。
服務啟動時會自動載入該目錄下所有 `.json` 檔案，並支援**動態更新**——透過 API 即可新增、刪除或重新載入熱詞，無需重啟服務。

### 設計原則

- **動態可配置**：熱詞清單可透過 API 或直接修改 JSON 檔案後呼叫 reload 端點來更新
- **多檔案支援**：不同店家 / 場景可維護各自的熱詞檔案（如 `chan_chi_cha.json`、`custom.json`）
- **範例檔案**：`hotwords/chan_chi_cha_example.json` 為範例，包含蟬吃茶產品名稱，實際使用時可自行調整

### 檔案格式

詳見 [`hotwords/chan_chi_cha_example.json`](hotwords/chan_chi_cha_example.json)，結構如下：

```json
{
  "description": "熱詞清單說明",
  "hotwords": [
    { "phrase": "珍珠奶茶", "boost": 10.0 },
    ...
  ]
}
```

- `phrase`：要加權的詞彙
- `boost`：加權分數（越高 → 辨識時越優先匹配該詞）

## API 設計（草案）

### Batch 辨識（優先）

```
POST /api/v1/transcribe
  Content-Type: multipart/form-data
  Body:
    audio: <音訊檔 wav/mp3/ogg>
    language: "zh"  (optional, default: zh)
    hotword_files: ["chan_chi_cha_example"]  (optional, 指定載入哪些熱詞檔)
  Response:
    { "text": "我要一杯大杯珍珠奶茶少冰半糖", "segments": [...], "duration": 3.2 }
```

### Streaming 辨識（加分項）

```
WS /api/v1/stream
  → Client 送出音訊 chunks（16kHz, 16bit, mono PCM）
  ← Server 回傳即時辨識結果 { "partial": "...", "is_final": false }
  ← 最終結果 { "text": "...", "is_final": true }
```

## 壓力測試

目標：驗證系統在 **1000 人同時使用** 下的穩定性與回應品質。

### 測試指標

| 指標 | Batch 目標 | Streaming 目標（加分） |
|------|-----------|----------------------|
| 並發數 | 1000 requests 同時送出 | 1000 WebSocket 連線 |
| 成功率 | > 99% | > 95% |
| P50 延遲 | < 3s（5 秒音訊） | < 500ms（首字回應） |
| P99 延遲 | < 10s | < 2s |
| 錯誤率 | < 1% | < 5% |
| 熱詞辨識正確率 | > 95% | > 90% |

### 測試場景

1. **基準測試**：單一請求延遲與辨識準確度
2. **階梯加壓**：50 → 100 → 200 → 500 → 1000 並發，觀察延遲曲線
3. **持續壓力**：500 並發持續 10 分鐘，觀察記憶體 / GPU 使用率是否穩定
4. **熱詞壓測**：1000 並發全部使用含產品名稱的音訊，驗證熱詞辨識不退化
5. **混合場景**：70% batch + 30% streaming（如有實作 streaming）


### 資源效率要求

部署資源需精簡控制，避免過度配置：

| 項目 | 約束 |
|------|------|
| GPU | 單張 T4 / L4 為上限（或純 CPU 方案） |
| 記憶體 | 單實例 < 8GB |
| 水平擴展 | 透過 Cloud Run / GKE autoscaler，依負載自動伸縮 |
| 空閒縮零 | Cloud Run 無請求時 scale-to-zero，不消耗資源 |
| 並發設定 | 單實例處理多請求（Cloud Run concurrency ≥ 10） |

## 驗收標準

### 必要
- [ ] 完成模型選型，確定 ASR 引擎（含熱詞方案）
- [ ] 建立 ASR 推論 Server（FastAPI），支援 Batch 辨識
- [ ] 熱詞以獨立 JSON 檔案管理，支援動態載入 / API 更新
- [ ] 熱詞辨識正確率 > 95%（使用範例熱詞測試）
- [ ] 容器化（Docker），可在本地測試
- [ ] 部署至 GCP（Cloud Run 為首選），資源用量精簡

### 加分
- [ ] 支援 Streaming（WebSocket）辨識
- [ ] Streaming 壓測：1000 並發 WebSocket 連線穩定
- [ ] 混合場景壓測（batch + streaming）
