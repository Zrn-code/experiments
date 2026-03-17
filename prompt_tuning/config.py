"""
實驗環境設定
從 .env 載入 Gemini 相關設定
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


class Config:
    """簡化版設定，只包含 AI 相關配置"""

    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # 模型設定
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-2.5-flash")

    # 店家資訊（用於 prompt 填入）
    STORE_NAME: str = os.getenv("STORE_NAME", "蟬吃茶")
    AGENT_NAME: str = os.getenv("AGENT_NAME", "Ezra")

    @classmethod
    def validate(cls):
        """驗證必要的設定"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY 未設定，請在 .env 中設定")
        print(f"✅ Config 驗證通過")
        print(f"   模型: {cls.MODEL_NAME}")
        print(f"   店家: {cls.STORE_NAME}")
        print(f"   助手: {cls.AGENT_NAME}")
