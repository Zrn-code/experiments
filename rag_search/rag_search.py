"""
RAG Search 知識助手 — 對話編排

仿照 ezragt-server 的架構，透過 function calling 二階段處理：
  1. Gemini 判斷是否需要搜尋知識庫
  2. 若需要，呼叫 search_knowledge_base 取得 RAG 結果
  3. Gemini 根據 RAG 結果生成像店員的自然回應
"""

import logging
from google.genai import types

from config import Config
from prompts import SYSTEM_PROMPT, SEARCH_TOOL_DECLARATION
from vertex_search import get_vertex_client, search_knowledge_base

logger = logging.getLogger(__name__)


def chat(query: str, model_name: str = None) -> dict:
    """
    知識助手對話 — 二階段 function calling 架構

    Turn 1: Gemini 判斷是否需要搜尋知識庫，若需要則呼叫 search_knowledge_base
    Turn 2: 根據工具結果，生成像店員的自然語言回應

    Args:
        query: 使用者的問題
        model_name: 模型名稱

    Returns:
        dict: {
            "answer": str,
            "tool_used": bool,
            "search_query": str | None,
            "has_grounding": bool,
            "grounding_chunks": list,
            "model": str,
        }
    """
    cfg = Config()
    _model = model_name or cfg.MODEL_NAME
    client = get_vertex_client()

    # ==========================================
    # Turn 1: Gemini 判斷是否需要呼叫工具
    # ==========================================
    function_tools = types.Tool(function_declarations=[SEARCH_TOOL_DECLARATION])

    try:
        response = client.models.generate_content(
            model=_model,
            contents=query,
            config=types.GenerateContentConfig(
                temperature=0,
                tools=[function_tools],
                system_instruction=SYSTEM_PROMPT,
            ),
        )
    except Exception as e:
        logger.error(f"Turn 1 失敗: {e}")
        return {
            "answer": f"發生錯誤: {e}",
            "tool_used": False,
            "search_query": None,
            "has_grounding": False,
            "grounding_chunks": [],
            "model": _model,
        }

    # 檢查是否有 function call
    tool_used = False
    search_query = None
    search_result = None

    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                if fc.name == "search_knowledge_base":
                    tool_used = True
                    search_query = dict(fc.args).get("query", query)
                    search_result = search_knowledge_base(search_query, _model)
                    logger.info(
                        f"🔧 Tool called: search_knowledge_base({search_query})"
                    )

    # ==========================================
    # Turn 2: 根據結果生成自然回應
    # ==========================================
    if tool_used and search_result:
        tool_context = f"【知識庫搜尋結果】\n{search_result['answer']}"

        final_prompt = (
            f"顧客問題：{query}\n\n"
            f"{tool_context}\n\n"
            f"請根據上述知識庫搜尋結果，用親切的店員語氣回答顧客。"
            f"如果搜尋結果有相關資訊就據此回答，沒有的話就坦誠告知。"
            f"只輸出自然語言回應，不要輸出 JSON 或技術細節。"
        )

        try:
            final_response = client.models.generate_content(
                model=_model,
                contents=final_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    system_instruction=SYSTEM_PROMPT,
                ),
            )
            answer = (
                final_response.text.strip()
                if final_response.text
                else search_result["answer"]
            )
        except Exception as e:
            logger.error(f"Turn 2 失敗: {e}")
            answer = search_result["answer"]

        return {
            "answer": answer,
            "tool_used": True,
            "search_query": search_query,
            "has_grounding": search_result["has_grounding"],
            "grounding_chunks": search_result["grounding_chunks"],
            "model": _model,
        }

    # Gemini 直接回答（沒有呼叫工具）
    answer = response.text.strip() if response.text else "抱歉，我沒有理解你的問題。"
    return {
        "answer": answer,
        "tool_used": False,
        "search_query": None,
        "has_grounding": False,
        "grounding_chunks": [],
        "model": _model,
    }
