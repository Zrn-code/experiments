"""
PDF → Markdown 轉換腳本

將 docs/ 資料夾下的所有 PDF 檔案提取文字並轉換為 Markdown 格式，
輸出到 docs_md/ 資料夾，方便後續 RAG 語料重寫。

Usage:
    python convert_pdf_to_md.py
"""

import os
import sys
from pathlib import Path

import pymupdf


DOCS_DIR = Path(__file__).parent / "docs"
OUTPUT_DIR = Path(__file__).parent / "docs_md"


def extract_text_as_md(pdf_path: str) -> str:
    """用 PyMuPDF 提取 PDF 文字，每頁以分隔線區隔"""
    doc = pymupdf.open(pdf_path)
    pages = []
    for page in doc:
        text = page.get_text().strip()
        if text:
            pages.append(text)
    doc.close()
    return "\n\n---\n\n".join(pages)


def convert_all():
    if not DOCS_DIR.exists():
        print(f"❌ 找不到 docs 資料夾: {DOCS_DIR}")
        sys.exit(1)

    pdf_files = sorted(DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        print("❌ docs/ 資料夾下沒有 PDF 檔案")
        sys.exit(1)

    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"找到 {len(pdf_files)} 個 PDF 檔案，開始轉換...\n")

    success = 0
    empty = []
    failed = []

    for i, pdf_path in enumerate(pdf_files, 1):
        md_name = pdf_path.stem + ".md"
        md_path = OUTPUT_DIR / md_name

        try:
            md_text = extract_text_as_md(str(pdf_path))
            char_count = len(md_text.strip())

            md_path.write_text(md_text, encoding="utf-8")

            status = "⚠️ 空白" if char_count == 0 else "✅"
            print(
                f"  [{i:02d}/{len(pdf_files)}] {status} {pdf_path.name} → {md_name} ({char_count} 字)"
            )

            if char_count == 0:
                empty.append(pdf_path.name)
            else:
                success += 1

        except Exception as e:
            print(f"  [{i:02d}/{len(pdf_files)}] ❌ {pdf_path.name} — 錯誤: {e}")
            failed.append((pdf_path.name, str(e)))

    # 統計
    print(f"\n{'='*50}")
    print(f"轉換完成！")
    print(f"  成功: {success}/{len(pdf_files)}")
    if empty:
        print(f"  空白: {len(empty)} — {', '.join(empty)}")
    if failed:
        print(f"  失敗: {len(failed)}")
        for name, err in failed:
            print(f"    - {name}: {err}")
    print(f"\n輸出資料夾: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
