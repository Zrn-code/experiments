"""
點餐助手（Prompt Tuning 實驗）

架構：
- Content/Part multi-turn 對話歷史
- Function calling loop（最多 5 輪）
- 全工具集（查詢 + 購物車 + 結帳），全部使用 mock 資料
- ThinkingConfig 適配 gemini-2.5-flash thinking model
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from google import genai
from google.genai import types

from config import Config
from mock_data import get_menu, find_product
from prompts import build_system_prompt
from store_info_service import MCPToolsService
from cart_service import MCPOrderToolsService, new_cart

logger = logging.getLogger(__name__)


class OrderingAssistant:
    """點餐助手：Content/Part multi-turn + function calling + mock tools"""

    def __init__(self):
        self.config = Config()
        self.client = genai.Client(api_key=self.config.GEMINI_API_KEY)
        self.model_name = self.config.MODEL_NAME
        self.cart = new_cart()
        self.order_tools = MCPOrderToolsService()
        self.store_tools = MCPToolsService()
        self.tools = self._define_tools()
        self.system_prompt = self._build_system_prompt()
        self.history: List[types.Content] = []

        # 售罄商品列表
        self._sold_out_products: List[str] = [
            item["name"] for item in get_menu().get("menu", []) if item.get("sold_out")
        ]

        logger.info(f"✅ OrderingAssistant 初始化完成 (模型: {self.model_name})")

    # ==================== System Prompt ====================

    def _build_system_prompt(self) -> str:
        return build_system_prompt(
            store_name=self.config.STORE_NAME,
            agent_name=self.config.AGENT_NAME,
            menu_text=self._format_menu(),
        )

    def _format_menu(self) -> str:
        """將菜單格式化為精簡文字，嵌入 system prompt"""
        items = get_menu().get("menu", [])
        current_series = ""
        lines = []
        for item in items:
            series = item.get("series", "")
            if series != current_series:
                current_series = series
                lines.append(f"\n【{series}】")
            name = item["name"]
            prices = item.get("prices", {})
            if isinstance(prices, dict):
                price_str = "/".join(f"{s}${p}" for s, p in prices.items())
            else:
                price_str = f"${prices}"
            sold_out = "（售罄）" if item.get("sold_out") else ""
            lines.append(f"  {name}: {price_str}{sold_out}")
        return "\n".join(lines)

    # ==================== Tool Declarations ====================

    def _define_tools(self) -> types.Tool:
        """定義全部工具（查詢 + 購物車 + 結帳）"""

        # --- 基本查詢工具 ---
        get_product_price = types.FunctionDeclaration(
            name="get_product_price",
            description="查詢指定商品的價格。當用戶詢問某商品多少錢時使用此工具。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_name": types.Schema(
                        type=types.Type.STRING,
                        description="商品名稱，例如：高山冷泓青、黑糖金玉紅茶",
                    )
                },
                required=["product_name"],
            ),
        )

        check_product_availability = types.FunctionDeclaration(
            name="check_product_availability",
            description="檢查指定商品今天是否有供應（是否售罄）。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_name": types.Schema(
                        type=types.Type.STRING, description="商品名稱"
                    )
                },
                required=["product_name"],
            ),
        )

        get_current_datetime = types.FunctionDeclaration(
            name="get_current_datetime",
            description="獲取當前的日期和時間。",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}, required=[]),
        )

        # --- 店家資訊工具 ---
        get_store_info = types.FunctionDeclaration(
            name="get_store_info",
            description="獲取店家資訊（營業時間、位置、聯絡方式等）。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "info_type": types.Schema(
                        type=types.Type.STRING,
                        description="資訊類型：all / business_hours / location / contact",
                        enum=["all", "business_hours", "location", "contact"],
                    )
                },
                required=[],
            ),
        )

        get_full_menu = types.FunctionDeclaration(
            name="get_full_menu",
            description="獲取完整菜單。可指定系列查看特定分類。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "series": types.Schema(
                        type=types.Type.STRING,
                        description="系列名稱（可選）：高山茶、蟬吃茶、拿鐵飲、果茶系列、口感Q",
                    ),
                },
                required=[],
            ),
        )

        get_menu_categories = types.FunctionDeclaration(
            name="get_menu_categories",
            description="獲取菜單分類列表。",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}, required=[]),
        )

        get_product_details = types.FunctionDeclaration(
            name="get_product_details",
            description="獲取特定商品的詳細資訊（價格、系列、可客製選項等）。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_name": types.Schema(
                        type=types.Type.STRING, description="商品名稱"
                    )
                },
                required=["product_name"],
            ),
        )

        get_toppings_info = types.FunctionDeclaration(
            name="get_toppings_info",
            description="獲取加料選項和客製化資訊。",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}, required=[]),
        )

        # --- 購物車工具 ---
        add_to_cart = types.FunctionDeclaration(
            name="add_to_cart",
            description="將飲料加入購物車。顧客說「我要」「來一杯」「幫我加」時使用。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "product_name": types.Schema(
                        type=types.Type.STRING, description="商品名稱"
                    ),
                    "size": types.Schema(
                        type=types.Type.STRING,
                        description="尺寸：M（中杯）或 L（大杯），預設 M",
                        enum=["M", "L"],
                    ),
                    "sugar": types.Schema(
                        type=types.Type.STRING,
                        description="甜度",
                        enum=["正常糖", "少糖", "半糖", "微糖", "無糖"],
                    ),
                    "ice": types.Schema(
                        type=types.Type.STRING,
                        description="冰塊",
                        enum=["正常冰", "少冰", "去冰", "溫", "熱"],
                    ),
                    "toppings": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(type=types.Type.STRING),
                        description="加料列表",
                    ),
                    "quantity": types.Schema(
                        type=types.Type.INTEGER, description="數量，預設 1"
                    ),
                },
                required=["product_name"],
            ),
        )

        update_cart_item = types.FunctionDeclaration(
            name="update_cart_item",
            description="修改購物車中已有品項的甜度、冰塊、尺寸或數量。用戶說「改成」「換成」時使用。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "item_index": types.Schema(
                        type=types.Type.INTEGER,
                        description="品項編號（從 1 開始）",
                    ),
                    "size": types.Schema(
                        type=types.Type.STRING,
                        description="新尺寸",
                        enum=["M", "L"],
                    ),
                    "sugar": types.Schema(type=types.Type.STRING, description="新甜度"),
                    "ice": types.Schema(type=types.Type.STRING, description="新冰塊"),
                    "quantity": types.Schema(
                        type=types.Type.INTEGER, description="新數量"
                    ),
                },
                required=["item_index"],
            ),
        )

        remove_from_cart = types.FunctionDeclaration(
            name="remove_from_cart",
            description="從購物車移除品項。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "item_index": types.Schema(
                        type=types.Type.INTEGER,
                        description="品項編號（從 1 開始）",
                    ),
                },
                required=["item_index"],
            ),
        )

        clear_cart = types.FunctionDeclaration(
            name="clear_cart",
            description="清空購物車。用戶說「清空」「重新點」時使用。",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}, required=[]),
        )

        get_cart_summary = types.FunctionDeclaration(
            name="get_cart_summary",
            description="查看購物車內容和總金額。",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}, required=[]),
        )

        checkout = types.FunctionDeclaration(
            name="checkout",
            description="結帳送出訂單。用戶說「結帳」「下單」「就這樣」時使用。",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}, required=[]),
        )

        return types.Tool(
            function_declarations=[
                # 基本查詢
                get_product_price,
                check_product_availability,
                get_current_datetime,
                # 店家資訊
                get_store_info,
                get_full_menu,
                get_menu_categories,
                get_product_details,
                get_toppings_info,
                # 購物車/訂單
                add_to_cart,
                update_cart_item,
                remove_from_cart,
                clear_cart,
                get_cart_summary,
                checkout,
            ]
        )

    # ==================== Tool Execution ====================

    def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """執行 function call，全部使用 mock 服務"""

        # --- 基本查詢 ---
        if name == "get_product_price":
            product = find_product(args.get("product_name", ""))
            if not product:
                return f"找不到「{args.get('product_name', '')}」的價格資訊"
            prices = product.get("prices", {})
            if isinstance(prices, dict):
                price_str = "、".join(f"{s} ${p}" for s, p in prices.items())
                return f"「{product['name']}」的價格：{price_str}"
            return f"「{product['name']}」的價格資訊不完整"

        elif name == "check_product_availability":
            product = find_product(args.get("product_name", ""))
            if not product:
                return f"菜單上沒有「{args.get('product_name', '')}」這個商品"
            if product["name"] in self._sold_out_products:
                return f"「{product['name']}」今天已經售罄了"
            return f"「{product['name']}」今天有供應，可以點喔！"

        elif name == "get_current_datetime":
            now = datetime.now()
            weekdays = [
                "星期一",
                "星期二",
                "星期三",
                "星期四",
                "星期五",
                "星期六",
                "星期日",
            ]
            return f"現在是 {now.year}年{now.month}月{now.day}日 {weekdays[now.weekday()]}，{now.hour}:{now.minute:02d}"

        # --- 店家資訊（委託 mock 服務）---
        elif name == "get_store_info":
            return self.store_tools.get_store_info(args.get("info_type", "all"))
        elif name == "get_full_menu":
            return self.store_tools.get_full_menu(series=args.get("series"))
        elif name == "get_menu_categories":
            return self.store_tools.get_menu_categories()
        elif name == "get_product_details":
            return self.store_tools.get_product_details(args.get("product_name", ""))
        elif name == "get_toppings_info":
            return self.store_tools.get_toppings_info()

        # --- 購物車（委託 mock 服務）---
        elif name == "add_to_cart":
            return self.order_tools.add_to_cart(
                cart=self.cart,
                product_name=args.get("product_name", ""),
                size=args.get("size", "M"),
                sugar=args.get("sugar", "正常糖"),
                ice=args.get("ice", "正常冰"),
                toppings=args.get("toppings", []),
                quantity=args.get("quantity", 1),
            )
        elif name == "update_cart_item":
            return self.order_tools.update_cart_item(
                cart=self.cart,
                item_index=args.get("item_index"),
                size=args.get("size"),
                sugar=args.get("sugar"),
                ice=args.get("ice"),
                quantity=args.get("quantity"),
            )
        elif name == "remove_from_cart":
            return self.order_tools.remove_from_cart(
                cart=self.cart,
                item_index=args.get("item_index"),
            )
        elif name == "clear_cart":
            return self.order_tools.clear_cart(self.cart)
        elif name == "get_cart_summary":
            return self.order_tools.get_cart_summary(self.cart)
        elif name == "checkout":
            result = self.order_tools.submit_order(self.cart)
            return result[0] if isinstance(result, tuple) else result

        return f"未知工具: {name}"

    # ==================== Chat ====================

    def chat(self, user_input: str) -> Dict[str, Any]:
        """
        處理一輪對話

        - 歷史以 Content/Part 物件保存（支援多輪對話記憶）
        - Function calling loop 中間狀態不寫入永久歷史
        - 最終只保留 user/model 文字訊息
        """
        try:
            # 加入用戶訊息到歷史
            self.history.append(
                types.Content(role="user", parts=[types.Part(text=user_input)])
            )

            tools_used = []
            # 複製歷史進行 function calling loop（不汙染永久歷史）
            contents = list(self.history)
            for turn in range(5):
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        tools=[self.tools],
                        thinking_config=types.ThinkingConfig(thinking_budget=2048),
                    ),
                )

                # 提取 function calls（跳過 thinking model 的 thought parts）
                function_calls = []
                text_parts = []

                parts = (
                    response.candidates[0].content.parts
                    if (
                        response.candidates
                        and response.candidates[0].content
                        and response.candidates[0].content.parts
                    )
                    else []
                )

                for part in parts:
                    fc = getattr(part, "function_call", None)
                    is_thought = getattr(part, "thought", False)
                    if fc and getattr(fc, "name", None):
                        function_calls.append(fc)
                    elif getattr(part, "text", None) and not is_thought:
                        text_parts.append(part.text)

                # 沒有 function call → 回傳文字
                if not function_calls:
                    response_text = " ".join(text_parts).strip()
                    if not response_text:
                        response_text = (response.text or "").strip()
                    break

                # 執行 function calls
                fc_response_parts = []
                for fc in function_calls:
                    args_dict = dict(fc.args) if fc.args else {}
                    logger.info(f"🔧 {fc.name}({args_dict})")
                    result = self._execute_tool(fc.name, args_dict)
                    tools_used.append(fc.name)
                    fc_response_parts.append(
                        types.Part.from_function_response(
                            name=fc.name, response={"result": result}
                        )
                    )

                # 把 model response + function results 加入 contents 繼續對話
                contents.append(response.candidates[0].content)
                contents.append(types.Content(role="user", parts=fc_response_parts))
            else:
                response_text = "抱歉，處理時遇到問題，請再試一次。"

            # 空回應 fallback
            if not response_text:
                response_text = "不好意思，我沒聽清楚，可以再說一次嗎？"

            # 將最終文字回應加入永久歷史
            self.history.append(
                types.Content(role="model", parts=[types.Part(text=response_text)])
            )

            return {
                "success": True,
                "response": response_text,
                "tools_used": tools_used,
            }

        except Exception as e:
            logger.error(f"❌ 生成回應失敗: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": "抱歉，發生錯誤，請稍後再試。",
            }
