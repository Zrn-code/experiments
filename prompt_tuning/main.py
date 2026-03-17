"""
Prompt Tuning 實驗 — 互動式 CLI 點餐

啟動後會詢問輸入模式：
  1. 文字模式：直接打字點餐
  2. 語音輸入模式：音訊 → STT Agent（語音轉文字）→ OrderingAssistant（執行點餐）

語音模式架構（兩層 Agent）：
  Layer 1 — SpeechToTextAgent：接收音訊，透過 Gemini 轉寫為文字
  Layer 2 — OrderingAssistant：接收文字，執行點餐流程（function calling）

⚠️ 注意：目前的語音辨識使用 Gemini 多模態 API 作為模擬，方便快速測試。
   實際產品會使用專門的語音辨識模型（如 Whisper、SpeechBrain 等）。
   語音輸入的主要目的是測試 OrderingAssistant 對 ASR 錯誤的容錯能力。
   你也可以替換成其他語音辨識模型，只要輸出純文字即可。

啟動方式：
  cd experiments/prompt_tuning
  python main.py
"""

import logging

from config import Config
from ordering_assistant import OrderingAssistant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def run_text_mode(assistant: OrderingAssistant):
    """文字輸入模式"""
    print("輸入點餐內容，quit 離開。\n")

    while True:
        try:
            user_input = input("🧑 顧客：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 掰掰！")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 掰掰！")
            break

        result = assistant.chat(user_input)
        _print_result(result)


def run_voice_mode(assistant: OrderingAssistant):
    """
    語音輸入模式（兩層 Agent 架構）

    ⚠️ 目前使用 Gemini 多模態 API 模擬語音辨識，僅供測試用。
    實際產品會使用專門的 ASR 模型，你也可以替換成其他語音辨識模型。
    測試重點：OrderingAssistant 對語音辨識錯誤的容錯能力。

    Layer 1: SpeechToTextAgent — 音訊轉文字
    Layer 2: OrderingAssistant — 文字執行點餐
    """
    from voice_input import get_audio_input, SpeechToTextAgent

    stt_agent = SpeechToTextAgent()
    duration = 5.0

    # 選擇語音來源
    print("\n語音來源：")
    print("  1. 麥克風錄音")
    print("  2. 音檔輸入")
    source_choice = input("請選擇 (1/2，預設 1)：").strip()

    audio_file = None
    if source_choice == "2":
        audio_file = input("請輸入音檔路徑：").strip()
        if not audio_file:
            print("❌ 未輸入音檔路徑，切換至麥克風模式。")

    if audio_file:
        print(f"📂 音檔模式：{audio_file}\n")
    else:
        print(f"\n🎙️  麥克風模式（每次錄音最長 {duration} 秒）")
        print("輸入 quit 離開，按 Enter 開始錄音。\n")

    while True:
        if not audio_file:
            try:
                cmd = input("按 Enter 開始錄音（quit 離開）：").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 掰掰！")
                break
            if cmd.lower() in ("quit", "exit", "q"):
                print("👋 掰掰！")
                break

        # --- Layer 1: 音訊輸入 + 語音轉文字 ---
        try:
            audio_bytes, mime_type = get_audio_input(
                source=audio_file, duration=duration
            )
        except Exception as e:
            print(f"❌ 音訊載入失敗：{e}\n")
            if audio_file:
                break
            continue

        transcription = stt_agent.transcribe(audio_bytes, mime_type)
        if not transcription:
            print("🧑 顧客（語音）：[無法辨識語音內容]\n")
            if audio_file:
                break
            continue

        print(f"🧑 顧客（語音）：{transcription}")

        # --- Layer 2: 轉寫文字 → 點餐助手 ---
        result = assistant.chat(transcription)
        _print_result(result)

        # 音檔模式只處理一次
        if audio_file:
            break


def _print_result(result: dict):
    """列印結果"""
    if result["success"]:
        if result.get("tools_used"):
            print(f"  🔧 {', '.join(result['tools_used'])}")
        print(f"🍵 店員：{result['response']}\n")
    else:
        print(f"❌ {result.get('error', '未知錯誤')}\n")


def main():
    config = Config()
    config.validate()

    print(f"\n{'=' * 40}")
    print(f"  {config.STORE_NAME} 點餐助手 ({config.AGENT_NAME})")
    print(f"  模型: {config.MODEL_NAME}")
    print(f"{'=' * 40}")

    # 互動式模式選擇
    print("\n請選擇輸入模式：")
    print("  1. 文字模式（打字點餐）")
    print("  2. 語音輸入模式（音訊 → 語音辨識 → 點餐）")
    choice = input("請選擇 (1/2，預設 1)：").strip()

    assistant = OrderingAssistant()

    if choice == "2":
        run_voice_mode(assistant)
    else:
        run_text_mode(assistant)


if __name__ == "__main__":
    main()
