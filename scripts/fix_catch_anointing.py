import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path

epub_path = Path("data/epubs/015-en-catch-the-anointing.epub")
book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})

print("SPINE ORDER:")
for item_id, linear in book.spine:
    print(f"  id={item_id}, linear={linear}")

print("\nALL DOCUMENT ITEMS:")
for item in book.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        soup = BeautifulSoup(item.get_content(), "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if l.strip()]
        print(f"\n  Name: {item.get_name()}")
        print(f"  ID: {item.get_id()}")
        print(f"  Chars: {len(text)}")
        print(f"  First 3 lines: {lines[:3]}")
