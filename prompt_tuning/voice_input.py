"""
語音輸入模組

提供兩層架構的 Layer 1（語音轉文字）：
  - SpeechToTextAgent：透過 Gemini 將音訊轉寫為文字
  - 音訊擷取：麥克風錄音 / 音檔讀取

Layer 2（OrderingAssistant）在 ordering_assistant.py，
接收純文字後執行點餐 function calling。

⚠️ 注意：目前的 SpeechToTextAgent 使用 Gemini 多模態 API 作為模擬，
   方便在實驗階段快速測試。實際產品會使用專門的語音辨識模型（如 Whisper、SpeechBrain 等）。
   你也可以將 SpeechToTextAgent 替換成任何其他語音辨識模型，
   只要 transcribe() 輸出純文字即可接入 Layer 2。
   使用語音辨識的主要目的是測試 OrderingAssistant 對 ASR 錯誤的容錯能力
   （如品名近音混淆、甜度/冰塊誤判等）。
"""

import io
import os
import wave
import struct
import logging
from pathlib import Path
from typing import Optional, Tuple

from google import genai
from google.genai import types

from config import Config

logger = logging.getLogger(__name__)

# 錄音參數
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit
CHUNK_SIZE = 1024

# 支援的音檔 MIME types
MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
}


def record_from_microphone(duration_seconds: float = 5.0) -> Tuple[bytes, str]:
    """
    從麥克風錄音，回傳 (wav_bytes, mime_type)。

    按 Enter 提前結束錄音（需在另一個執行緒偵測），
    或等待 duration_seconds 秒後自動結束。

    需要安裝 pyaudio：pip install pyaudio
    """
    try:
        import pyaudio
    except ImportError:
        raise RuntimeError("語音錄音需要 pyaudio，請執行：pip install pyaudio")

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )

    total_chunks = int(SAMPLE_RATE / CHUNK_SIZE * duration_seconds)
    frames = []

    print(f"🎙️  錄音中（最長 {duration_seconds} 秒，按 Ctrl+C 提前結束）...")
    try:
        for _ in range(total_chunks):
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            frames.append(data)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

    print("✅ 錄音結束")

    # 組成 WAV bytes
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))

    return wav_buffer.getvalue(), "audio/wav"


def load_audio_file(file_path: str) -> Tuple[bytes, str]:
    """
    從檔案讀取音訊，回傳 (audio_bytes, mime_type)。
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到音檔：{file_path}")

    suffix = path.suffix.lower()
    mime_type = MIME_MAP.get(suffix)
    if not mime_type:
        raise ValueError(
            f"不支援的音檔格式：{suffix}（支援：{', '.join(MIME_MAP.keys())}）"
        )

    audio_bytes = path.read_bytes()
    logger.info(f"📂 載入音檔：{file_path} ({len(audio_bytes)} bytes, {mime_type})")
    return audio_bytes, mime_type


def get_audio_input(
    source: Optional[str] = None, duration: float = 5.0
) -> Tuple[bytes, str]:
    """
    統一介面：取得音訊輸入。

    Args:
        source: 音檔路徑。若為 None 則使用麥克風錄音。
        duration: 麥克風錄音最長秒數（僅在 source=None 時生效）。

    Returns:
        (audio_bytes, mime_type)
    """
    if source:
        return load_audio_file(source)
    else:
        return record_from_microphone(duration)


class SpeechToTextAgent:
    """
    Layer 1 — 語音轉文字 Agent

    使用 Gemini 多模態能力，將音訊 bytes 轉寫為純文字。
    不處理任何點餐邏輯，僅負責 ASR。

    ⚠️ 這是模擬用的語音辨識，方便快速測試 Agent 容錯能力。
    實際產品中會使用專門的 ASR 模型（Whisper、SpeechBrain 等）。
    你也可以替換成任何其他 ASR 模型，只要 transcribe() 回傳純文字即可。
    """

    def __init__(self):
        config = Config()
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_name = config.MODEL_NAME
        self._menu_context = self._build_menu_context()
        logger.info(f"✅ SpeechToTextAgent 初始化完成 (模型: {self.model_name})")

    @staticmethod
    def _build_menu_context() -> str:
        """從 mock_data 取得菜單資訊，提供給 STT 作為轉寫提示"""
        from mock_data import get_menu

        items = get_menu().get("menu", [])
        names = [item["name"] for item in items]
        return "、".join(names)

    def transcribe(self, audio_bytes: bytes, mime_type: str) -> Optional[str]:
        """
        將音訊轉寫為文字。

        Args:
            audio_bytes: 音訊原始 bytes
            mime_type: 音訊 MIME type（如 audio/wav）

        Returns:
            轉寫文字，辨識失敗時回傳 None
        """
        try:
            prompt = (
                f"請將這段語音轉寫為文字，只輸出轉寫結果，不要加任何說明。\n"
                f"\n"
                f"這是一家飲料店的點餐場景，以下是菜單上的商品名稱，請優先對齊這些專有名詞：\n"
                f"{self._menu_context}\n"
                f"\n"
                f"常見選項：大杯/中杯、正常糖/少糖/半糖/微糖/無糖、正常冰/少冰/去冰/溫/熱"
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(
                                data=audio_bytes, mime_type=mime_type
                            ),
                            types.Part(text=prompt),
                        ],
                    )
                ],
            )

            text = (response.text or "").strip()
            if text:
                logger.info(f"🗣️ 轉寫結果：{text}")
                return text

            logger.warning("⚠️ Gemini 回傳空白轉寫結果")
            return None

        except Exception as e:
            logger.error(f"❌ 語音轉文字失敗: {e}", exc_info=True)
            return None
