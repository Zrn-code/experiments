"""
購物車服務（自包含版本）
所有資料來源使用 mock_data，不依賴 Firestore
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from mock_data import (
    SUGAR_ALIASES,
    ICE_ALIASES,
    SIZE_ALIASES,
    VALID_SWEETNESS,
    VALID_ICE_LEVELS,
    find_product,
    get_menu,
    get_topping_prices,
)

logger = logging.getLogger(__name__)


@dataclass
class CartItem:
    """購物車品項"""

    item_id: str
    product_id: str
    name: str
    size: str
    sugar: str
    ice: str
    toppings: List[str]
    price: int
    quantity: int
    note: str = ""
    series: str = ""
    base_price: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "product_id": self.product_id,
            "name": self.name,
            "size": self.size,
            "sugar": self.sugar,
            "ice": self.ice,
            "toppings": self.toppings,
            "price": self.price,
            "quantity": self.quantity,
            "note": self.note,
            "series": self.series,
            "total_price": self.price * self.quantity,
        }


@dataclass
class Cart:
    """購物車"""

    cart_id: str
    customer_id: str
    customer_name: str
    items: List[CartItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total(self) -> int:
        return sum(item.price * item.quantity for item in self.items)

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cart_id": self.cart_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "items": [item.to_dict() for item in self.items],
            "total": self.total,
            "item_count": self.item_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class MCPOrderToolsService:
    """MCP 訂單工具服務（自包含版本，使用 mock_data）"""

    SUGAR_OPTIONS = VALID_SWEETNESS
    ICE_OPTIONS = VALID_ICE_LEVELS

    def __init__(self):
        logger.info("✅ MCP Order Tools (experiment) 初始化完成")

    # ==================== 標準化 ====================

    def _normalize_sugar(self, sugar: str) -> str:
        sugar = sugar.strip()
        if sugar in self.SUGAR_OPTIONS:
            return sugar
        return SUGAR_ALIASES.get(sugar, "正常糖")

    def _normalize_ice(self, ice: str) -> str:
        ice = ice.strip()
        if ice in self.ICE_OPTIONS:
            return ice
        return ICE_ALIASES.get(ice, "正常冰")

    @staticmethod
    def _normalize_size(size: str) -> str:
        return SIZE_ALIASES.get(size, "中杯")

    # ==================== 價格計算 ====================

    def _get_base_price(self, product: Dict[str, Any], size: str) -> int:
        prices = product.get("prices", {})
        normalized_size = self._normalize_size(size)
        if isinstance(prices, dict):
            base = prices.get(normalized_size)
            if base is None:
                available = list(prices.keys())
                base = prices[available[0]] if available else 0
        else:
            base = int(prices)
        return base

    def _calculate_price(
        self, product: Dict[str, Any], size: str, toppings: List[str]
    ) -> int:
        base = self._get_base_price(product, size)
        topping_prices = get_topping_prices()
        for t in toppings:
            base += topping_prices.get(t, 10)
        return base

    # ==================== MCP Tools ====================

    def add_to_cart(
        self,
        cart: Cart,
        product_name: str,
        size: str = "中杯",
        sugar: str = "正常糖",
        ice: str = "正常冰",
        toppings: List[str] = None,
        quantity: int = 1,
        note: str = "",
    ) -> str:
        try:
            product = find_product(product_name)
            if not product:
                return f"❌ 找不到「{product_name}」這個商品，請確認商品名稱"

            if product.get("sold_out", False):
                return f"❌ 「{product['name']}」今日已售罄，很抱歉"

            sugar = self._normalize_sugar(sugar)
            ice = self._normalize_ice(ice)
            toppings = toppings or []
            normalized_size = self._normalize_size(size)

            prices = product.get("prices", {})
            if isinstance(prices, dict) and normalized_size not in prices:
                available_sizes = list(prices.keys())
                if available_sizes:
                    normalized_size = available_sizes[0]

            price = self._calculate_price(product, normalized_size, toppings)

            cart_item = CartItem(
                item_id=f"item_{uuid.uuid4().hex[:8]}",
                product_id=str(product.get("id", product["name"])),
                name=product["name"],
                size=normalized_size,
                sugar=sugar,
                ice=ice,
                toppings=toppings,
                price=price,
                quantity=quantity,
                note=note,
                series=product.get("series", ""),
                base_price=self._get_base_price(product, normalized_size),
            )

            cart.items.append(cart_item)
            cart.updated_at = datetime.now()

            size_label = normalized_size
            toppings_text = f"、加{'/'.join(toppings)}" if toppings else ""
            options_text = f"{sugar}/{ice}{toppings_text}"

            response_lines = [
                f"✅ 已加入購物車！",
                f"",
                f"📝 {product['name']} ({size_label})",
                f"   {options_text}",
                f"   ${price} x {quantity} = ${price * quantity}",
            ]
            if note:
                response_lines.append(f"   備註：{note}")
            response_lines.extend(
                [
                    f"",
                    f"🛒 購物車目前有 {cart.item_count} 件商品，總計 ${cart.total}",
                ]
            )

            logger.info(
                f"🛒 [Add to Cart] {product['name']} x{quantity} -> ${price * quantity}"
            )
            return "\n".join(response_lines)

        except Exception as e:
            logger.error(f"加入購物車失敗: {e}")
            return f"❌ 加入購物車時發生錯誤：{str(e)}"

    def update_cart_item(
        self,
        cart: Cart,
        item_id: str = None,
        item_index: int = None,
        product_name: str = None,
        quantity: int = None,
        size: str = None,
        sugar: str = None,
        ice: str = None,
        toppings: List[str] = None,
        note: str = None,
    ) -> str:
        try:
            if not cart or not cart.items:
                return "❌ 購物車是空的，請先加入商品"

            target_item = None
            found_index = None

            if item_id:
                for idx, item in enumerate(cart.items):
                    if item.item_id == item_id:
                        target_item = item
                        found_index = idx + 1
                        break
            elif item_index and 0 < item_index <= len(cart.items):
                target_item = cart.items[item_index - 1]
                found_index = item_index
            elif product_name:
                product_name_lower = product_name.lower()
                for idx, item in enumerate(cart.items):
                    item_name_lower = item.name.lower()
                    if (
                        product_name_lower in item_name_lower
                        or item_name_lower in product_name_lower
                    ):
                        target_item = item
                        found_index = idx + 1
                        break
                if not target_item:
                    cart_items = ", ".join(
                        [f"{i+1}.{item.name}" for i, item in enumerate(cart.items)]
                    )
                    return f"❌ 找不到「{product_name}」，購物車中有: {cart_items}"
            else:
                target_item = cart.items[-1]
                found_index = len(cart.items)

            if not target_item:
                return "❌ 找不到指定的購物車項目"

            updated_fields = []

            if quantity is not None:
                target_item.quantity = quantity
                updated_fields.append(f"數量: {quantity}")

            if size:
                normalized_new_size = self._normalize_size(size)
                old_size = target_item.size
                target_item.size = normalized_new_size
                product = find_product(target_item.name)
                if product:
                    new_price = self._calculate_price(
                        product, normalized_new_size, target_item.toppings
                    )
                    if new_price == 0:
                        target_item.size = old_size
                        return f"❌ 無法將「{target_item.name}」改成{normalized_new_size}，該商品可能沒有此尺寸"
                    target_item.price = new_price
                else:
                    target_item.size = old_size
                    return f"❌ 找不到商品「{target_item.name}」的資訊，無法更新尺寸"
                updated_fields.append(
                    f"尺寸: {normalized_new_size} (${target_item.price})"
                )

            if sugar:
                target_item.sugar = self._normalize_sugar(sugar)
                updated_fields.append(f"糖度: {target_item.sugar}")

            if ice:
                target_item.ice = self._normalize_ice(ice)
                updated_fields.append(f"冰塊: {target_item.ice}")

            if toppings is not None:
                target_item.toppings = toppings
                product = find_product(target_item.name)
                if product:
                    target_item.price = self._calculate_price(
                        product, target_item.size, toppings
                    )
                updated_fields.append(
                    f"加料: {', '.join(toppings) if toppings else '無'}"
                )

            if note is not None:
                target_item.note = note
                updated_fields.append(f"備註: {note}")

            if not updated_fields:
                return "❌ 沒有指定要更新的項目"

            cart.updated_at = datetime.now()

            return (
                f"✅ 已更新「{target_item.name}」：\n"
                + "\n".join(f"   {f}" for f in updated_fields)
                + f"\n\n🛒 購物車總計 ${cart.total}"
            )

        except Exception as e:
            logger.error(f"更新購物車失敗: {e}")
            return f"❌ 更新購物車時發生錯誤：{str(e)}"

    def remove_from_cart(
        self,
        cart: Cart,
        item_id: str = None,
        item_index: int = None,
        product_name: str = None,
    ) -> str:
        try:
            if not cart or not cart.items:
                return "❌ 購物車是空的"

            target_item = None
            target_index = -1

            if item_id:
                for i, item in enumerate(cart.items):
                    if item.item_id == item_id:
                        target_item = item
                        target_index = i
                        break
            elif item_index and 0 < item_index <= len(cart.items):
                target_index = item_index - 1
                target_item = cart.items[target_index]
            elif product_name:
                for i, item in enumerate(cart.items):
                    if product_name in item.name or item.name in product_name:
                        target_item = item
                        target_index = i
                        break

            if target_item is None or target_index < 0:
                return "❌ 找不到指定的購物車項目"

            removed_item = cart.items.pop(target_index)
            cart.updated_at = datetime.now()

            if not cart.items:
                return f"✅ 已移除「{removed_item.name}」\n\n🛒 購物車現在是空的"

            return f"✅ 已移除「{removed_item.name}」\n\n🛒 購物車還有 {cart.item_count} 件商品，總計 ${cart.total}"

        except Exception as e:
            logger.error(f"移除購物車項目失敗: {e}")
            return f"❌ 移除項目時發生錯誤：{str(e)}"

    def clear_cart(self, cart: Cart) -> str:
        try:
            if cart:
                cart.items.clear()
                cart.updated_at = datetime.now()
            return "✅ 購物車已清空"
        except Exception as e:
            logger.error(f"清空購物車失敗: {e}")
            return f"❌ 清空購物車時發生錯誤：{str(e)}"

    def get_cart_summary(self, cart: Cart) -> str:
        try:
            if not cart or not cart.items:
                return (
                    "🛒 購物車是空的\n\n💡 告訴我您想點什麼，例如：「我要一杯珍珠奶茶」"
                )

            lines = ["🛒 【購物車】\n"]

            for i, item in enumerate(cart.items, 1):
                toppings_text = f"+{'/'.join(item.toppings)}" if item.toppings else ""
                options_text = f"{item.sugar}/{item.ice}{toppings_text}"
                size_display = item.size

                lines.append(f"{i}. {item.name} ({size_display})")
                lines.append(f"   {options_text}")
                lines.append(
                    f"   ${item.price} x {item.quantity} = ${item.price * item.quantity}"
                )

                if item.note:
                    lines.append(f"   📝 {item.note}")
                lines.append("")

            lines.append(f"━━━━━━━━━━━━━")
            lines.append(f"📦 共 {cart.item_count} 件商品")
            lines.append(f"💰 總計：${cart.total}")
            lines.append("")
            lines.append("💡 說「送出訂單」即可下單，或繼續點餐")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"獲取購物車摘要失敗: {e}")
            return f"❌ 查看購物車時發生錯誤：{str(e)}"

    def get_cart_data(self, cart: Cart) -> Optional[Dict[str, Any]]:
        if not cart:
            return None
        return cart.to_dict()

    def submit_order(
        self,
        cart: Cart,
        customer_id: str = "",
        customer_name: str = "",
        customer_phone: str = "",
        pickup_method: str = "自取",
        pickup_time: str = "",
        note: str = "",
    ) -> tuple:
        """送出訂單（Mock 版本 — 不寫入 Firestore，只回傳模擬結果）"""
        try:
            if not cart or not cart.items:
                return "❌ 購物車是空的，請先加入商品", None

            # 生成模擬訂單號
            order_no = f"EXP{datetime.now().strftime('%m%d%H%M')}{uuid.uuid4().hex[:4].upper()}"
            order_id = f"order_{uuid.uuid4().hex[:12]}"

            final_total = cart.total
            pickup_time_display = f"預約 {pickup_time}" if pickup_time else "立即取餐"
            item_count = cart.item_count

            lines = [
                "✅ 訂單已送出！（實驗模式 — 未實際儲存）",
                "",
                f"📋 訂單編號：{order_no}",
                f"📦 共 {item_count} 件商品",
                f"💰 總計：${final_total}",
                f"🚶 取餐方式：{pickup_method}",
                f"⏰ 取餐時間：{pickup_time_display}",
            ]
            if note:
                lines.append(f"📝 備註：{note}")
            lines.extend(
                [
                    "",
                    "⏳ 訂單狀態：等待店家確認",
                ]
            )

            # 清空購物車
            cart.items.clear()

            logger.info(
                f"📦 [Submit Order] Mock 訂單已建立: {order_no}, 總計: ${final_total}"
            )

            return "\n".join(lines), {
                "order_id": order_id,
                "order_no": order_no,
                "total": final_total,
                "item_count": item_count,
            }

        except Exception as e:
            logger.error(f"送出訂單失敗: {e}")
            return f"❌ 送出訂單時發生錯誤：{str(e)}", None

    def get_order_status(self, order_id: str = None, order_no: str = None) -> str:
        """查詢訂單狀態（Mock 版本）"""
        if not order_id and not order_no:
            return "❌ 請提供訂單編號或訂單 ID"
        return f"⏳ 訂單 {order_no or order_id} 目前狀態：等待店家確認（實驗模式 — 無實際訂單）"


def new_cart(customer_id: str = "guest", customer_name: str = "顧客") -> Cart:
    """建立一個新的空購物車"""
    return Cart(
        cart_id=f"cart_{uuid.uuid4().hex[:8]}",
        customer_id=customer_id,
        customer_name=customer_name,
    )
