"""
店家資訊服務（自包含版本）
所有資料來源使用 mock_data，不依賴 Firestore
"""

import json as _json
import logging
from typing import Dict, Any, List, Optional

from mock_data import (
    STORE_INFO,
    BUSINESS_HOURS,
    EXCEPTION_DATES,
    PLATFORMS,
    get_menu,
    get_all_options,
)

logger = logging.getLogger(__name__)


class MCPToolsService:
    """MCP 工具服務類（自包含版本）"""

    def __init__(self):
        logger.info("✅ MCP Tools (experiment) 初始化完成")

    def _get_store_display_name(self) -> str:
        name = STORE_INFO.get("name", "")
        name_en = STORE_INFO.get("name_en", "")
        return f"{name} {name_en}".strip() if name_en else (name or "飲料店")

    # ==================== 店家資訊工具 ====================

    def get_store_info(self, info_type: str = "all") -> str:
        try:
            result_parts = []
            if info_type in ["all", "basic"]:
                result_parts.append(self._get_basic_store_info())
            if info_type in ["all", "business_hours"]:
                result_parts.append(self._get_business_hours_info())
            if info_type in ["all", "location"]:
                result_parts.append(self._get_location_info())
            if info_type in ["all", "contact"]:
                result_parts.append(self._get_contact_info())
            if info_type in ["all", "platforms"]:
                result_parts.append(self._get_platforms_info())

            result = "\n\n".join([p for p in result_parts if p])
            return result if result else "目前無法取得店家資訊"
        except Exception as e:
            logger.error(f"獲取店家資訊失敗: {e}")
            return "查詢店家資訊時發生錯誤，請稍後再試"

    def _get_basic_store_info(self) -> str:
        name = STORE_INFO.get("name", "")
        name_en = STORE_INFO.get("name_en", "")
        brand_story = STORE_INFO.get("brand_story", "")
        features = STORE_INFO.get("features", [])

        display_name = f"{name} {name_en}".strip() if name_en else name or "本店"
        lines = [f"【{display_name}】"]
        if brand_story:
            lines.append(f"🏪 品牌故事：{brand_story}")
        if features:
            lines.append(f"🍵 特色：{'、'.join(features)}")
        return "\n".join(lines)

    def _get_business_hours_info(self) -> str:
        lines = ["【營業時間】"]
        for h in BUSINESS_HOURS:
            day = h.get("day", "")
            is_open = h.get("is_open", True)
            if is_open:
                ranges = h.get("ranges", [])
                if ranges:
                    time_str = "、".join([f"{r['start']}-{r['end']}" for r in ranges])
                    lines.append(f"📅 {day}: {time_str}")
                else:
                    lines.append(f"📅 {day}: 營業中")
            else:
                lines.append(f"📅 {day}: 公休")

        if EXCEPTION_DATES:
            lines.append("\n【特殊公告】")
            for ex in EXCEPTION_DATES[:3]:
                date = ex.get("date", "")
                reason = ex.get("reason", "")
                ex_type = ex.get("type", "closed")
                if ex_type == "closed":
                    lines.append(f"⚠️ {date}: {reason}")
                else:
                    lines.append(f"📢 {date}: {reason}")

        return "\n".join(lines)

    def _get_location_info(self) -> str:
        address = STORE_INFO.get("address", "")
        name = STORE_INFO.get("name", "本店")
        google_maps_query = STORE_INFO.get("google_maps_query", name)

        lines = ["【店家位置】"]
        if address:
            lines.append(f"📍 地址：{address}")
        lines.append("🚗 交通方式：")
        lines.append("   - 捷運：步行約 5-10 分鐘")
        lines.append("   - 公車：門口設有公車站")
        lines.append("   - 開車：附近有收費停車場")
        if google_maps_query:
            lines.append(f"\n🗺️ Google 地圖搜尋「{google_maps_query}」即可導航")
        return "\n".join(lines)

    def _get_contact_info(self) -> str:
        lines = ["【聯絡方式】"]
        phone = STORE_INFO.get("phone", "")
        if phone:
            lines.append(f"📞 電話：{phone}")
        else:
            lines.append("📞 電話：(可於營業時間內來電)")

        line_id = STORE_INFO.get("line_id", "")
        if line_id:
            lines.append(f"📱 LINE 官方帳號：{line_id}")

        lines.append("\n💬 如有訂位、大量訂購需求，歡迎提前聯繫！")
        return "\n".join(lines)

    def _get_platforms_info(self) -> str:
        lines = ["【訂購管道】"]
        platform_names = {
            "onsite": "🏪 現場點餐",
            "online": "📱 線上訂餐",
            "mall": "🛒 美食街",
            "delivery": "🚴 外送平台",
        }
        for key, name in platform_names.items():
            is_open = PLATFORMS.get(key, False)
            status = "✅ 開放中" if is_open else "❌ 暫停服務"
            lines.append(f"{name}: {status}")
        return "\n".join(lines)

    # ==================== 菜單資訊工具 ====================

    def _get_menu_data(self) -> List[Dict[str, Any]]:
        return get_menu().get("menu", [])

    def _get_available_series(self) -> List[str]:
        menu_items = self._get_menu_data()
        series_set = set(
            item.get("series") for item in menu_items if item.get("series")
        )
        return sorted(list(series_set))

    def get_full_menu(
        self, series: Optional[str] = None, include_prices: bool = True
    ) -> str:
        try:
            menu_items = self._get_menu_data()
            if not menu_items:
                return "目前無法取得菜單資訊"

            if series:
                menu_items = [
                    item
                    for item in menu_items
                    if series.lower() in item.get("series", "").lower()
                ]
                if not menu_items:
                    available_series = self._get_available_series()
                    return f"找不到「{series}」系列的商品。\n\n可用系列：{', '.join(available_series)}"

            return self._format_menu_display(menu_items, include_prices)
        except Exception as e:
            logger.error(f"獲取菜單失敗: {e}")
            return "查詢菜單時發生錯誤，請稍後再試"

    def get_menu_by_series(self, series: str) -> str:
        return self.get_full_menu(series=series)

    def get_menu_categories(self) -> str:
        series = self._get_available_series()
        if not series:
            return "目前無法取得菜單分類"

        store_name = self._get_store_display_name()
        lines = [f"【{store_name} 菜單分類】\n"]
        series_emojis = {
            "高山茶": "🏔️",
            "蟬吃茶": "🦗",
            "拿鐵飲": "🥛",
            "果茶系列": "🍋",
            "口感Q": "🧋",
        }
        for s in series:
            emoji = series_emojis.get(s, "🍵")
            count = len(
                [item for item in self._get_menu_data() if item.get("series") == s]
            )
            lines.append(f"{emoji} {s} ({count} 款)")
        lines.append("\n💡 說「我想看 XX 系列」可以查看該系列的詳細菜單")
        return "\n".join(lines)

    def get_product_details(self, product_name: str) -> str:
        menu_items = self._get_menu_data()

        for item in menu_items:
            if item.get("name") == product_name:
                return self._format_product_detail(item)

        for item in menu_items:
            name = item.get("name", "")
            if product_name in name or name in product_name:
                return self._format_product_detail(item)

        for item in menu_items:
            aliases = item.get("aliases", [])
            if product_name in aliases:
                return self._format_product_detail(item)

        return f"找不到「{product_name}」這個商品，請確認商品名稱或嘗試其他關鍵字"

    def get_toppings_info(self) -> str:
        toppings = []
        other_options = []
        all_options = get_all_options()
        for opt in all_options:
            opt_type = opt.get("type", "")
            label = opt.get("label", "")
            price = opt.get("price", 0)
            if opt_type == "topping" and label:
                toppings.append({"label": label, "price": price})
            elif opt_type == "extra" and label:
                other_options.append(label)

        toppings_emojis = {
            "珍珠": "⚫",
            "小芋圓": "🟣",
            "混珠": "⚪",
            "仙草": "🟢",
            "蜂蜜": "🍯",
            "小紫蘇": "🌿",
        }

        lines = ["【加料選項】\n"]
        for t in toppings:
            emoji = toppings_emojis.get(t["label"], "➕")
            price_str = f"（+${t['price']}）" if t["price"] > 0 else "（免費）"
            lines.append(f"{emoji} {t['label']} {price_str}")

        if other_options:
            lines.append("\n【其他選項】")
            for opt in other_options:
                lines.append(f"📝 {opt}")

        return "\n".join(lines)

    def _format_menu_display(
        self, menu_items: List[Dict[str, Any]], include_prices: bool
    ) -> str:
        series_groups: Dict[str, List[Dict]] = {}
        for item in menu_items:
            series = item.get("series", "其他")
            if series not in series_groups:
                series_groups[series] = []
            series_groups[series].append(item)

        store_name = self._get_store_display_name()
        lines = [f"🍵 【{store_name} 完整菜單】\n"]

        for series_name, items in series_groups.items():
            lines.append(f"━━━ {series_name} ━━━")
            for item in items:
                name = item.get("name")
                sold_out = item.get("sold_out", False)
                if include_prices:
                    prices = item.get("prices", {})
                    if isinstance(prices, dict):
                        price_str = " / ".join(
                            [f"{size}${price}" for size, price in prices.items()]
                        )
                    else:
                        price_str = f"${prices}"
                    if sold_out:
                        lines.append(f"  ❌ {name} - {price_str}（售罄）")
                    else:
                        lines.append(f"  • {name} - {price_str}")
                else:
                    if sold_out:
                        lines.append(f"  ❌ {name}（售罄）")
                    else:
                        lines.append(f"  • {name}")
            lines.append("")

        lines.append("💡 可加料：珍珠、小芋圓、仙草等（+$10）")
        lines.append("📝 甜度：正常/少甜/半糖/微糖/無糖")
        lines.append("🧊 冰塊：正常冰/少冰/微冰/去冰/溫/熱")
        return "\n".join(lines)

    def _format_product_detail(self, item: Dict[str, Any]) -> str:
        name = item.get("name")
        series = item.get("series")
        prices = item.get("prices", {})
        aliases = item.get("aliases", [])
        sold_out = item.get("sold_out", False)

        lines = [f"🍵 【{name}】\n"]
        lines.append(f"📂 系列：{series}")

        if isinstance(prices, dict):
            price_str = " / ".join(
                [f"{size}: ${price}" for size, price in prices.items()]
            )
        else:
            price_str = f"${prices}"
        lines.append(f"💰 價格：{price_str}")

        if sold_out:
            lines.append("⚠️ 狀態：今日售罄")
        else:
            lines.append("✅ 狀態：供應中")

        if aliases:
            lines.append(f"🏷️ 別名：{', '.join(aliases)}")

        lines.append("\n【客製化選項】")
        lines.append("🍬 甜度：正常/少甜/半糖/微糖/無糖")
        lines.append("🧊 冰塊：正常冰/少冰/微冰/去冰/溫/熱")
        lines.append("➕ 加料：珍珠/小芋圓/混珠/仙草/蜂蜜/小紫蘇（+$10）")
        return "\n".join(lines)

    # ==================== UI 卡片顯示工具 ====================

    def show_business_hours_card(self) -> str:
        logger.info("🕐 [MCP] 觸發營業時間卡片顯示")
        try:
            store_name = self._get_store_display_name()
            hours_list = []
            for h in BUSINESS_HOURS:
                is_open = h.get("is_open", True)
                ranges = h.get("ranges", [])
                if is_open and ranges:
                    hours_str = ", ".join(
                        f"{r.get('start', '')}-{r.get('end', '')}" for r in ranges
                    )
                else:
                    hours_str = ""
                hours_list.append(
                    {
                        "day": h.get("day", ""),
                        "hours": hours_str,
                        "is_closed": not is_open,
                    }
                )
            data = _json.dumps(
                {"store_name": store_name, "hours": hours_list},
                ensure_ascii=False,
            )
            return f"__UI_CARD__:business_hours:{data}|好的，這是我們的營業時間資訊"
        except Exception as e:
            logger.error(f"❌ [MCP] 獲取營業時間失敗: {e}")
            return "__UI_CARD__:business_hours|好的，這是我們的營業時間資訊"

    def show_full_menu_card(self) -> str:
        logger.info("📋 [MCP] 觸發完整菜單卡片顯示")
        try:
            store_name = self._get_store_display_name()
            menu_items = self._get_menu_data()

            series_groups: Dict[str, List[Dict[str, Any]]] = {}
            for item in menu_items:
                series = item.get("series", "其他")
                if series not in series_groups:
                    series_groups[series] = []
                series_groups[series].append(item)

            categories = []
            for series_name, items in series_groups.items():
                products = []
                for item in items:
                    p: Dict[str, Any] = {"name": item.get("name", "")}
                    prices = item.get("prices", {})
                    if isinstance(prices, dict):
                        p["price"] = (
                            prices.get("M")
                            or prices.get("m")
                            or next(iter(prices.values()), None)
                        )
                    else:
                        p["price"] = prices
                    if item.get("sold_out"):
                        p["description"] = "售罄"
                    products.append(p)
                categories.append({"category": series_name, "products": products})

            data = _json.dumps(
                {"store_name": store_name, "categories": categories},
                ensure_ascii=False,
            )
            return f"__UI_CARD__:full_menu:{data}|請看我們的完整菜單"
        except Exception as e:
            logger.error(f"❌ [MCP] 建構完整菜單卡片失敗: {e}")
            return "__UI_CARD__:full_menu|請看我們的完整菜單"

    def show_category_menu_card(self, category: str) -> str:
        logger.info(f"📜 [MCP] 觸發 {category} 系列菜單卡片顯示")
        try:
            menu_items = self._get_menu_data()
            filtered = [
                item
                for item in menu_items
                if category.lower() in item.get("series", "").lower()
            ]
            products = []
            for item in filtered:
                p: Dict[str, Any] = {"name": item.get("name", "")}
                prices = item.get("prices", {})
                if isinstance(prices, dict):
                    p["price"] = (
                        prices.get("M")
                        or prices.get("m")
                        or next(iter(prices.values()), None)
                    )
                else:
                    p["price"] = prices
                if item.get("sold_out"):
                    p["description"] = "售罄"
                products.append(p)

            data = _json.dumps(
                {"category": category, "products": products},
                ensure_ascii=False,
            )
            return f"__UI_CARD__:category_menu:{data}|這是 {category} 系列的飲品"
        except Exception as e:
            logger.error(f"❌ [MCP] 建構 {category} 系列菜單卡片失敗: {e}")
            return f"__UI_CARD__:category_menu|這是 {category} 系列的飲品"

    def show_map_info_card(self) -> str:
        logger.info("🗺️ [MCP] 觸發地圖資訊卡片顯示")
        return "__UI_CARD__:map_info|這是我們的門市位置資訊"
