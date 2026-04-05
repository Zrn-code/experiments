"""
RAG 語料重寫腳本

將 docs_md/ 下的 Q&A 格式文件，用 Gemini 重寫為結構化知識文件，
適合 Vertex AI Search RAG 檢索。

輸出到 docs_rag/ 資料夾。

Usage:
    python rewrite_docs_for_rag.py
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

DOCS_MD_DIR = Path(__file__).parent / "docs_md"
OUTPUT_DIR = Path(__file__).parent / "docs_rag"

MODEL = os.getenv("MODEL_NAME", "gemini-3.1-pro-preview")


# ── Gemini client ──────────────────────────────────────────
def get_client():
    api_key = os.getenv("VERTEX_AI_API_KEY", "")
    if not api_key:
        print("❌ VERTEX_AI_API_KEY 未設定，請在 .env 中設定")
        sys.exit(1)
    return genai.Client(vertexai=True, api_key=api_key)


# ── 重寫 prompt ────────────────────────────────────────────
REWRITE_SYSTEM_PROMPT = """\
你是「蟬吃茶」品牌的知識文件編輯。你的任務是將原始的 Q&A 對話稿，\
重寫為一份結構化的產品知識文件，用於 RAG（Retrieval-Augmented Generation）知識庫。

## 重寫原則

1. **去除所有 Q&A 格式**：不要保留問題、版本標記（回答版本1/2）、空白問答。
2. **萃取事實與知識**：把散落在各問答裡的資訊整合成連貫的知識段落。
3. **使用結構化標題**：用 Markdown 標題組織內容，方便 RAG 系統做 chunk 切分。
4. **關鍵字豐富**：自然地包含口感描述詞（清爽、甜潤、回甘、順口…）、\
場景詞（夏天、飯後、提神…）、成分詞（烏龍、紅茶、蜂蜜、鮮奶…），\
提高語義檢索命中率。
5. **每個產品獨立完整**：即使原稿說「同 XX 產品」，也要寫出完整介紹，\
不要引用其他文件。
6. **語氣客觀、像產品百科**：不要用對話語氣，但可以保留品牌特色用語。
7. **不要捏造資訊**：只使用原稿和參考資料中提供的事實。如果資訊不足，就簡短帶過。
8. **不要用 code fence**：不要用 ```markdown 或 ``` 包裹輸出，直接輸出 Markdown 內容。

## 輸出格式（嚴格遵守，直接輸出，不要用 code fence 包裹）

# {產品名稱}

## 產品簡介
{1-2 句話的核心介紹，包含茶種、特色}

## 茶底與原料
- 茶種：{具體茶種}
- 原料：{蜂蜜/黑糖/鮮奶/奶粉等}
- 產地來源：{如有提及}

## 風味特色
- 茶湯色澤：{顏色}
- 香氣：{花香/蜜香/焙火香等}
- 口感：{甜潤/清爽/厚實等描述}
- 整體風味：{一句話總結}

## 推薦甜度與冰量
- 甜度：{建議}
- 冰量：{建議}
- 可做熱飲：{是/否，原因}

## 加料搭配
- {適合的加料與延伸飲品}

## 咖啡因與飲用建議
- 咖啡因：{有/無，含量}
- 適合場景：{時間、情境}
- 注意事項：{不適合的族群}

## 保存建議
- {室溫/冷藏保存時間}

若某個區塊沒有足夠資訊，可以省略該區塊，但核心區塊（產品簡介、風味特色）必須保留。
"""

# ── 引用偵測 ───────────────────────────────────────────────
# Placeholder 文件常引用的產品名 → 文件 stem 映射
REF_KEYWORDS = {
    "蟬吃金玉奶茶": "item_29_蟬吃金玉奶茶",
    "金玉奶茶": "item_29_蟬吃金玉奶茶",
    "蟬吃烏龍奶綠": "item_28_蟬吃烏龍奶綠",
    "烏龍奶綠": "item_28_蟬吃烏龍奶綠",
    "黑糖金玉拿鐵": "item_26_黑糖金玉拿鐵",
    "黑糖薑紅拿鐵": "item_27_黑糖薑紅拿鐵",
    "蜂蜜檸檬綠": "item_17_蜂蜜檸檬綠",
    "鮮檸冷泓青": "item_32_鮮檸冷泓青",
    "黑糖薑紅": "item_21_黑糖薑紅茶",
    "蟬吃金玉紅": "item_02_蟬吃金玉紅",
    "金玉紅茶拿鐵": "item_25_金玉紅茶拿鐵",
    "冷泓青": "item_01_高山冷泓青",
    "蜂蜜綠": "item_13_蟬吃蜂蜜綠",
    "珍珠奶茶": "item_39_珍珠奶茶",
    "蟬吃烏龍綠": "item_03_蟬吃烏龍綠",
    "養顏蜂蜜水": "item_12_養顏蜂蜜水",
    "蟬吃蜜香紅茶": "item_08_蟬吃蜜香紅茶",
    "炭焙烏龍": "item_07_炭焙烏龍",
    "鮮翠烏龍": "item_06_蟬吃鮮翠烏龍",
    "珍珠黑糖牛乳": "item_44_珍珠黑糖牛乳",
    "珍珠黑糖鮮奶": "item_45_珍珠黑糖鮮奶",
}


def load_all_docs():
    """載入所有 docs_md 文件"""
    docs = {}
    for md_file in sorted(DOCS_MD_DIR.glob("*.md")):
        docs[md_file.stem] = md_file.read_text(encoding="utf-8")
    return docs


def find_references(content, stem, all_docs):
    """偵測 placeholder 文件的引用，附上被引用產品的完整內容"""
    refs = []
    seen = set()
    for keyword, doc_key in REF_KEYWORDS.items():
        if doc_key == stem:
            continue  # 不引用自己
        if keyword in content and doc_key in all_docs and doc_key not in seen:
            refs.append(f"--- 參考產品：{doc_key} ---\n{all_docs[doc_key]}")
            seen.add(doc_key)
    return "\n\n".join(refs) if refs else ""


def rewrite_doc(client, product_name, raw_content, ref_content):
    """用 Gemini 重寫單一產品文件"""
    user_prompt = f"請將以下「{product_name}」的原始 Q&A 資料重寫為結構化知識文件。\n\n"
    user_prompt += f"--- 原始資料 ---\n{raw_content}\n"

    if ref_content:
        user_prompt += (
            "\n以下是被引用的相關產品資料，"
            "請參考其中的知識來補充本產品的介紹：\n"
            f"{ref_content}\n"
        )

    response = client.models.generate_content(
        model=MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            system_instruction=REWRITE_SYSTEM_PROMPT,
        ),
    )
    return response.text


def main():
    if not DOCS_MD_DIR.exists():
        print(f"❌ 找不到 docs_md 資料夾: {DOCS_MD_DIR}")
        sys.exit(1)

    all_docs = load_all_docs()
    if not all_docs:
        print("❌ docs_md/ 下沒有 .md 檔案")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)
    client = get_client()

    print(f"找到 {len(all_docs)} 個文件，使用 {MODEL} 重寫...\n")

    success = 0
    failed = []

    for i, (stem, raw_content) in enumerate(sorted(all_docs.items()), 1):
        product_name = stem.split("_", 2)[-1] if "_" in stem else stem
        out_path = OUTPUT_DIR / f"{stem}.txt"

        try:
            ref_content = find_references(raw_content, stem, all_docs)
            rewritten = rewrite_doc(client, product_name, raw_content, ref_content)

            out_path.write_text(rewritten, encoding="utf-8")
            char_count = len(rewritten.strip())
            has_ref = " (含參考)" if ref_content else ""
            print(
                f"  [{i:02d}/{len(all_docs)}] ✅ {stem}.txt ({char_count} 字){has_ref}"
            )
            success += 1

            # Rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"  [{i:02d}/{len(all_docs)}] ❌ {stem} — {e}")
            failed.append((stem, str(e)))

    print(f"\n{'='*50}")
    print(f"重寫完成！成功: {success}/{len(all_docs)}")
    if failed:
        print(f"失敗: {len(failed)}")
        for name, err in failed:
            print(f"  - {name}: {err}")
    print(f"\n輸出資料夾: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
