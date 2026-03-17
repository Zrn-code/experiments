"""
提示詞與工具宣告
"""

from google.genai import types

# ========================================
# 📌 系統提示詞 — 控制回答風格
# ========================================
SYSTEM_PROMPT = (
    "你是「蟬吃茶」的知識助手，負責回答顧客關於品牌、茶葉知識、產品特色、推薦搭配等問題。\n"
    "回答風格要像真實店員：親切、口語、有溫度。\n"
    "當顧客問到產品或茶葉相關問題時，使用 search_knowledge_base 工具查詢知識庫。\n"
    "如果知識庫沒有相關資訊，坦誠告知並提供你知道的一般性回答。\n"
    "回答控制在 200 字以內。"
)

# RAG 搜尋的系統提示詞（內部用，控制知識庫回傳格式）
RAG_SEARCH_INSTRUCTION = (
    "你是知識庫搜尋助手。請根據檢索到的資訊回答問題，"
    "如果沒有相關資訊，請說「知識庫中沒有找到相關資訊」。"
    "回答要簡潔，控制在 100 字以內。"
)

# Function declaration — 讓 Gemini 知道可以使用這個工具
SEARCH_TOOL_DECLARATION = types.FunctionDeclaration(
    name="search_knowledge_base",
    description="搜尋知識庫獲取茶葉知識、口感特色、品牌故事、產品推薦理由等資訊。當用戶詢問茶葉、產品、品牌相關問題時使用此工具。",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "query": types.Schema(
                type=types.Type.STRING,
                description="搜尋查詢，例如：蜜香紅的口感特色、推薦什麼茶、品牌故事",
            )
        },
        required=["query"],
    ),
)
