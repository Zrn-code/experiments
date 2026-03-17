# Experiments — AI 對話點餐實驗環境

本 repo 包含多個獨立實驗，用於優化 AI 對話點餐系統的不同面向。
每個實驗都是**完全自包含**的，可以獨立運行，不依賴主程式碼庫。

## 目錄

| 資料夾 | 說明 |
|--------|------|
| [prompt_tuning/](prompt_tuning/) | Prompt 優化、function-calling 調校（只需 Gemini API Key） |
| [rag_search/](rag_search/) | Vertex AI Search RAG 品質調校（需 Gemini API Key + GCP） |
| [wake_word/](wake_word/) | 本地端中文喚醒詞偵測（離線模型 + Flutter/Android 整合） |
| [chinese_asr/](chinese_asr/) | 中文語音辨識模型伺服器（熱詞支援 + GCP 部署） |

詳細說明請參考各資料夾內的 README。
