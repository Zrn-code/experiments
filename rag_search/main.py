"""
RAG Search 實驗 — 知識助手 CLI

結合 Gemini + Vertex AI Search，模擬店員回答顧客問題。
Gemini 自動判斷是否需要查詢知識庫（function calling）。

使用方式：
  python main.py
"""

import logging

from config import Config
from rag_search import chat

# ==================== Logging ====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """互動式知識助手"""
    config = Config()
    config.validate()

    print("\n" + "=" * 50)
    print("  蟬吃茶知識助手 — RAG Search 實驗")
    print(f"  模型: {config.MODEL_NAME}")
    print("=" * 50)
    print("像顧客一樣提問，助手會自動判斷是否需要查詢知識庫。")
    print("輸入 quit 或 exit 離開。\n")

    while True:
        try:
            query = input("🧑 顧客：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 掰掰！")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("👋 掰掰！")
            break

        result = chat(query)

        print(f"\n🍵 店員：{result['answer']}")
        # 顯示是否使用了知識庫
        if result["tool_used"]:
            print(f"   📚 知識庫查詢：{result['search_query']}")
            print(f"   Grounding: {'✅ 有' if result['has_grounding'] else '❌ 無'}")
            if result["grounding_chunks"]:
                print(f"   來源片段數: {len(result['grounding_chunks'])}")
        else:
            print("   💬 直接回答（未查詢知識庫）")
        print()


if __name__ == "__main__":
    main()
