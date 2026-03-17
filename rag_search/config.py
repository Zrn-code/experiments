"""
RAG Search 實驗環境設定
從 .env 載入 Gemini / Vertex AI Search 相關設定
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """RAG 搜尋實驗設定，只包含 Vertex AI Search 相關配置"""

    # Vertex AI API Key
    VERTEX_AI_API_KEY: str = os.getenv("VERTEX_AI_API_KEY", "")

    # Vertex AI Search
    VERTEX_PROJECT_ID: str = os.getenv("VERTEX_PROJECT_ID", "")
    VERTEX_REGION: str = os.getenv("VERTEX_REGION", "us-central1")
    VERTEX_DATA_STORE_ID: str = os.getenv("VERTEX_DATA_STORE_ID", "")
    VERTEX_DATA_STORE_LOCATION: str = os.getenv("VERTEX_DATA_STORE_LOCATION", "global")

    # 模型設定
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")

    @classmethod
    def validate(cls):
        """驗證必要的設定"""
        if not cls.VERTEX_AI_API_KEY:
            raise ValueError("VERTEX_AI_API_KEY 未設定，請在 .env 中設定")
        if not cls.VERTEX_PROJECT_ID:
            raise ValueError("VERTEX_PROJECT_ID 未設定，請在 .env 中設定")
        if not cls.VERTEX_DATA_STORE_ID:
            raise ValueError("VERTEX_DATA_STORE_ID 未設定，請在 .env 中設定")
        print(f"✅ Config 驗證通過")
        print(f"   模型: {cls.MODEL_NAME}")
        print(
            f"   Vertex AI Search: {cls.VERTEX_DATA_STORE_ID} ({cls.VERTEX_DATA_STORE_LOCATION})"
        )
