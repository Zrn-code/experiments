"""
Mock 資料
提供菜單、店家資訊、選項、促銷規則等模擬資料
"""

# ==================== 常數 ====================

VALID_SIZES = ["中杯", "大杯"]
VALID_SWEETNESS = ["正常糖", "多糖", "少糖", "半糖", "微糖", "無糖"]
VALID_ICE_LEVELS = ["正常冰", "多冰", "少冰", "去冰", "常溫", "溫", "熱"]

SUGAR_ALIASES = {
    "正常": "正常糖",
    "全糖": "正常糖",
    "少甜": "少糖",
    "7分糖": "少糖",
    "七分糖": "少糖",
    "5分糖": "半糖",
    "五分糖": "半糖",
    "3分糖": "微糖",
    "三分糖": "微糖",
    "微甜": "微糖",
    "不要糖": "無糖",
    "去糖": "無糖",
    "0糖": "無糖",
}

ICE_ALIASES = {
    "正常": "正常冰",
    "全冰": "正常冰",
    "半冰": "少冰",
    "沒有冰": "去冰",
    "不要冰": "去冰",
    "溫的": "溫",
    "熱的": "熱",
    "燙": "熱",
}

SIZE_ALIASES = {
    "M": "中杯",
    "L": "大杯",
    "中": "中杯",
    "大": "大杯",
    "中杯": "中杯",
    "大杯": "大杯",
}

# ==================== 菜單資料 ====================

MENU_ITEMS = [
    # ── 高山茶 ──
    {
        "id": 1,
        "name": "高山冷泓青",
        "prices": {"大杯": 40},
        "series": "高山茶",
        "sold_out": False,
        "aliases": ["青茶", "冷泓青"],
    },
    {
        "id": 2,
        "name": "蟬吃金玉紅",
        "prices": {"大杯": 40},
        "series": "高山茶",
        "sold_out": False,
        "aliases": ["紅茶", "金玉紅"],
    },
    {
        "id": 3,
        "name": "蟬吃烏龍綠",
        "prices": {"大杯": 35},
        "series": "高山茶",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 4,
        "name": "決明子紅茶",
        "prices": {"大杯": 35},
        "series": "高山茶",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 5,
        "name": "黑糖金玉紅",
        "prices": {"中杯": 40, "大杯": 50},
        "series": "高山茶",
        "sold_out": False,
        "aliases": [],
    },
    # ── 蟬吃茶 ──
    {
        "id": 6,
        "name": "蟬吃鮮翠烏龍茶",
        "prices": {"大杯": 60},
        "series": "蟬吃茶",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 7,
        "name": "蟬吃炭焙烏龍茶",
        "prices": {"大杯": 60},
        "series": "蟬吃茶",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 8,
        "name": "蟬吃手採蜜香紅",
        "prices": {"大杯": 65},
        "series": "蟬吃茶",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 9,
        "name": "蟬吃手採佳葉龍",
        "prices": {"大杯": 65},
        "series": "蟬吃茶",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 10,
        "name": "蟬吃手採紅玉紅",
        "prices": {"大杯": 65},
        "series": "蟬吃茶",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 11,
        "name": "蟬吃玉山烏龍茶",
        "prices": {"大杯": 85},
        "series": "蟬吃茶",
        "sold_out": False,
        "aliases": [],
    },
    # ── 拿鐵飲 ──
    {
        "id": 12,
        "name": "蟬吃烏龍拿鐵",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "拿鐵飲",
        "sold_out": False,
        "aliases": ["烏龍拿鐵"],
    },
    {
        "id": 13,
        "name": "金玉紅茶拿鐵",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "拿鐵飲",
        "sold_out": False,
        "aliases": ["紅茶拿鐵"],
    },
    {
        "id": 14,
        "name": "黑糖金玉拿鐵",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "拿鐵飲",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 15,
        "name": "黑糖薑紅拿鐵",
        "prices": {"中杯": 70, "大杯": 80},
        "series": "拿鐵飲",
        "sold_out": False,
        "aliases": [],
    },
    # ── 乳特調 ──
    {
        "id": 16,
        "name": "蟬吃烏龍奶綠",
        "prices": {"中杯": 50, "大杯": 60},
        "series": "乳特調",
        "sold_out": False,
        "aliases": ["奶綠"],
    },
    {
        "id": 17,
        "name": "蟬吃金玉奶茶",
        "prices": {"中杯": 50, "大杯": 60},
        "series": "乳特調",
        "sold_out": False,
        "aliases": ["奶茶"],
    },
    {
        "id": 18,
        "name": "黑糖金玉奶茶",
        "prices": {"中杯": 50, "大杯": 60},
        "series": "乳特調",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 19,
        "name": "黑糖薑紅奶茶",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "乳特調",
        "sold_out": False,
        "aliases": [],
    },
    # ── 果茶系列 ──
    {
        "id": 20,
        "name": "鮮檸冷泓青",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "果茶系列",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 21,
        "name": "生機檸檬綠",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "果茶系列",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 22,
        "name": "生機檸檬紅",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "果茶系列",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 23,
        "name": "百香果綠茶",
        "prices": {"大杯": 70},
        "series": "果茶系列",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 45,
        "name": "火龍檸檬青",
        "prices": {"大杯": 70},
        "series": "果茶系列",
        "sold_out": False,
        "aliases": [],
    },
    # ── 暖呼呼 ──
    {
        "id": 24,
        "name": "蟬吃黑糖薑茶",
        "prices": {"中杯": 55, "大杯": 65},
        "series": "暖呼呼",
        "sold_out": False,
        "aliases": ["黑糖薑茶"],
    },
    {
        "id": 25,
        "name": "蟬吃黑糖薑紅",
        "prices": {"中杯": 55, "大杯": 65},
        "series": "暖呼呼",
        "sold_out": False,
        "aliases": ["黑糖薑紅"],
    },
    {
        "id": 26,
        "name": "蟬吃烏龍薑茶",
        "prices": {"中杯": 55, "大杯": 65},
        "series": "暖呼呼",
        "sold_out": False,
        "aliases": ["烏龍薑茶"],
    },
    {
        "id": 27,
        "name": "蟬吃黑龍薑茶",
        "prices": {"中杯": 55, "大杯": 65},
        "series": "暖呼呼",
        "sold_out": False,
        "aliases": ["黑龍薑茶"],
    },
    # ── 蜜茶園 ──
    {
        "id": 28,
        "name": "養顏蜂蜜水",
        "prices": {"中杯": 55, "大杯": 65},
        "series": "蜜茶園",
        "sold_out": False,
        "aliases": ["蜂蜜水"],
    },
    {
        "id": 29,
        "name": "蟬吃蜂蜜綠",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "蜜茶園",
        "sold_out": False,
        "aliases": ["蜂蜜綠"],
    },
    {
        "id": 30,
        "name": "蜂蜜冷泓青",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "蜜茶園",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 31,
        "name": "蟬吃蜂蜜紅",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "蜜茶園",
        "sold_out": False,
        "aliases": ["蜂蜜紅"],
    },
    {
        "id": 32,
        "name": "蜂蜜檸檬汁",
        "prices": {"中杯": 80, "大杯": 90},
        "series": "蜜茶園",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 33,
        "name": "蜂蜜檸檬綠",
        "prices": {"中杯": 80, "大杯": 90},
        "series": "蜜茶園",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 34,
        "name": "蜂蜜檸檬青",
        "prices": {"中杯": 80, "大杯": 90},
        "series": "蜜茶園",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 35,
        "name": "蜂蜜檸檬紅",
        "prices": {"中杯": 80, "大杯": 90},
        "series": "蜜茶園",
        "sold_out": False,
        "aliases": [],
    },
    # ── 口感 Q ──
    {
        "id": 36,
        "name": "珍珠金玉紅拿鐵",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "口感 Q",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 37,
        "name": "珍珠黑玉紅拿鐵",
        "prices": {"中杯": 60, "大杯": 70},
        "series": "口感 Q",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 38,
        "name": "珍珠奶茶",
        "prices": {"中杯": 50, "大杯": 60},
        "series": "口感 Q",
        "sold_out": False,
        "aliases": ["珍奶"],
    },
    {
        "id": 39,
        "name": "珍珠奶綠",
        "prices": {"中杯": 50, "大杯": 60},
        "series": "口感 Q",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 40,
        "name": "小芋圓珍奶",
        "prices": {"中杯": 50, "大杯": 60},
        "series": "口感 Q",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 41,
        "name": "小芋圓珍奶綠",
        "prices": {"中杯": 50, "大杯": 60},
        "series": "口感 Q",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 42,
        "name": "冷泓綠纖子",
        "prices": {"中杯": 40, "大杯": 50},
        "series": "口感 Q",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 43,
        "name": "珍珠黑糖牛乳",
        "prices": {"中杯": 70, "大杯": 80},
        "series": "口感 Q",
        "sold_out": False,
        "aliases": [],
    },
    {
        "id": 44,
        "name": "珍珠黑糖鮮奶",
        "prices": {"中杯": 80, "大杯": 90},
        "series": "口感 Q",
        "sold_out": True,
        "aliases": [],
    },
]

# ==================== 加料/選項資料 ====================

TOPPING_OPTIONS = [
    {"type": "topping", "label": "珍珠", "price": 10},
    {"type": "topping", "label": "小芋圓", "price": 10},
    {"type": "topping", "label": "混珠", "price": 10},
    {"type": "topping", "label": "仙草", "price": 10},
    {"type": "topping", "label": "蜂蜜", "price": 30},
    {"type": "topping", "label": "小紫蘇", "price": 10},
]

EXTRA_OPTIONS = [
    {"type": "extra", "label": "自帶杯"},
    {"type": "extra", "label": "料多"},
    {"type": "extra", "label": "料少"},
    {"type": "extra", "label": "無茶"},
    {"type": "extra", "label": "全茶"},
]

ALL_OPTIONS = TOPPING_OPTIONS + EXTRA_OPTIONS

# ==================== 店家資訊 ====================

STORE_INFO = {
    "name": "蟬吃茶",
    "name_en": "Chan Chih Tea",
    "display_name": "蟬吃茶 Chan Chih Tea",
    "brand_story": "蟬吃茶致力於提供高品質的台灣茶飲，選用台灣在地茶葉，堅持新鮮現泡。將台灣茶文化以年輕、時尚的方式傳遞給每位顧客。",
    "features": ["高山茶系列", "蟬吃茶系列手採茶葉"],
    "address": "台灣",
    "google_maps_query": "蟬吃茶",
    "phone": "",
    "line_id": "",
    "email": "",
    "website": "https://www.organic-naturetea.com",
}

BUSINESS_HOURS = [
    {"day": "星期一", "is_open": True, "ranges": [{"start": "10:00", "end": "22:00"}]},
    {"day": "星期二", "is_open": True, "ranges": [{"start": "10:00", "end": "22:00"}]},
    {"day": "星期三", "is_open": True, "ranges": [{"start": "10:00", "end": "22:00"}]},
    {"day": "星期四", "is_open": True, "ranges": [{"start": "10:00", "end": "22:00"}]},
    {"day": "星期五", "is_open": True, "ranges": [{"start": "10:00", "end": "23:00"}]},
    {"day": "星期六", "is_open": True, "ranges": [{"start": "09:00", "end": "23:00"}]},
    {"day": "星期日", "is_open": True, "ranges": [{"start": "09:00", "end": "22:00"}]},
]

EXCEPTION_DATES = [
    {"date": "2026-04-04", "reason": "清明節公休", "type": "closed"},
]

PLATFORMS = {
    "onsite": True,
    "online": True,
    "mall": False,
    "delivery": True,
}

PAYMENT_METHODS = {
    "pos": ["現金付款", "LINE Pay", "信用卡", "悠遊卡", "街口支付"],
    "online": ["現金付款", "LINE Pay"],
}

AI_CONFIG = {
    "agent_name": "Ezra",
    "greeting_messages": [
        "您好！歡迎光臨蟬吃茶，請問想喝點什麼呢？",
        "嗨！歡迎來到蟬吃茶，今天想點什麼飲料？",
        "您好！蟬吃茶為您服務，有什麼想喝的嗎？",
    ],
}

# ==================== 促銷規則 ====================

PROMOTION_RULES = [
    {
        "name": "自帶杯優惠",
        "type": "discount_fixed",
        "discount": 5,
        "condition": "自帶杯",
        "enabled": True,
    },
    {
        "name": "拿鐵飲/乳特調 加料免費",
        "description": "拿鐵飲、乳特調系列的飲品加料免費",
        "type": "free_topping",
        "condition_series": ["拿鐵飲", "乳特調"],
        "enabled": True,
    },
]

# ==================== 業務規則 ====================

BUSINESS_RULES = {
    "default_sweetness": "正常糖",
    "default_ice": "正常冰",
    "default_cup_size": "大杯",
    "thick_straw_toppings": ["珍珠", "芋圓", "混珠", "芋頭", "粉圓"],
    "own_cup_skip_straw": True,
}


# ==================== 便利函式 ====================


def get_menu() -> dict:
    """回傳菜單"""
    series_set = sorted(set(item["series"] for item in MENU_ITEMS))
    return {"menu": MENU_ITEMS, "series_list": series_set}


def get_all_options() -> list:
    """回傳選項"""
    return ALL_OPTIONS


def get_topping_prices() -> dict:
    """回傳 {label: price} 格式的加料價格表"""
    return {o["label"]: o["price"] for o in TOPPING_OPTIONS}


def find_product(product_name: str) -> dict | None:
    """查找商品（精確 → 模糊 → 別名）"""
    for item in MENU_ITEMS:
        if item["name"] == product_name:
            return item
    for item in MENU_ITEMS:
        if product_name in item["name"] or item["name"] in product_name:
            return item
    for item in MENU_ITEMS:
        if product_name in item.get("aliases", []):
            return item
    return None
