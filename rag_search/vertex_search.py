"""
Vertex AI Search RAG 搜尋模組

負責初始化 Vertex AI client 與 Data Store，
以及執行知識庫搜尋（search_knowledge_base）。
"""

import logging
from google import genai
from google.genai import types

from config import Config
from prompts import RAG_SEARCH_INSTRUCTION

logger = logging.getLogger(__name__)

# 全域 client（按需初始化）
_vertex_client = None
_rag_tool = None


def _init_vertex():
    """初始化 Vertex AI client 和 RAG tool"""
    global _vertex_client, _rag_tool

    if _vertex_client is not None:
        return

    cfg = Config()

    _vertex_client = genai.Client(
        vertexai=True,
        api_key=cfg.VERTEX_AI_API_KEY,
    )

    data_store_path = (
        f"projects/{cfg.VERTEX_PROJECT_ID}"
        f"/locations/{cfg.VERTEX_DATA_STORE_LOCATION}"
        f"/collections/default_collection"
        f"/dataStores/{cfg.VERTEX_DATA_STORE_ID}"
    )

    _rag_tool = types.Tool(
        retrieval=types.Retrieval(
            vertex_ai_search=types.VertexAISearch(datastore=data_store_path)
        )
    )

    logger.info(f"✅ Vertex AI Search 已初始化: {cfg.VERTEX_DATA_STORE_ID}")


def get_vertex_client():
    """取得已初始化的 Vertex AI client"""
    _init_vertex()
    return _vertex_client


def search_knowledge_base(query: str, model_name: str) -> dict:
    """
    使用 Vertex AI Search 搜尋知識庫

    Args:
        query: 搜尋查詢內容
        model_name: 使用的模型名稱

    Returns:
        dict: {"answer": str, "has_grounding": bool, "grounding_chunks": list}
    """
    _init_vertex()

    try:
        logger.info(f"🔍 搜尋知識庫: {query}")

        response = _vertex_client.models.generate_content(
            model=model_name,
            contents=f"請根據知識庫回答：{query}",
            config=types.GenerateContentConfig(
                temperature=0,
                tools=[_rag_tool],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(mode="ANY")
                ),
                system_instruction=RAG_SEARCH_INSTRUCTION,
            ),
        )

        answer = response.text.strip() if response.text else ""

        has_grounding = False
        grounding_chunks = []
        if response.candidates and response.candidates[0].grounding_metadata:
            gm = response.candidates[0].grounding_metadata
            if gm.grounding_chunks:
                has_grounding = True
                for chunk in gm.grounding_chunks:
                    grounding_chunks.append(str(chunk))

        level = "有 Grounding" if has_grounding else "無 Grounding"
        logger.info(f"📚 知識庫結果 ({level}): {answer[:80]}...")

        return {
            "answer": answer or "知識庫中沒有找到相關資訊",
            "has_grounding": has_grounding,
            "grounding_chunks": grounding_chunks,
        }

    except Exception as e:
        logger.error(f"搜尋知識庫失敗: {e}")
        error_msg = str(e)
        if "PERMISSION_DENIED" in error_msg:
            hint = (
                "❌ 權限不足 — 請至 GCP Console 確認：\n"
                "   1. 已啟用 Discovery Engine API\n"
                "   2. API Key 沒有限制 Discovery Engine API 的存取\n"
                "   3. Data Store ID 和 Project ID 正確\n"
                "   詳見 README.md 常見問題"
            )
            return {"answer": hint, "has_grounding": False, "grounding_chunks": []}
        return {
            "answer": f"搜尋知識庫時發生錯誤: {e}",
            "has_grounding": False,
            "grounding_chunks": [],
        }
