import re
from pathlib import Path
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

epub_path = Path("data/epubs/015-en-catch-the-anointing.epub")
output_file = Path("data/raw/dag_books_v2.txt")

book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})

sections = []

for item in book.get_items():
    if item.get_type() != ebooklib.ITEM_DOCUMENT:
        continue

    base = Path(item.get_name()).name.lower()
    if not re.match(r"^c\d+\.xhtml$", base):
        continue

    soup = BeautifulSoup(item.get_content(), "html.parser")

    # Remove script and style tags
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Get ALL text content — don't filter by tag
    text = soup.get_text(separator="\n", strip=True)
    text = text.replace("\xa0", " ")
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    print(f"  {item.get_name()} → {len(text)} chars")

    if len(text) > 100:
        sections.append(text)

print(f"\nTotal sections: {len(sections)}")

if sections:
    # Remove the previous failed attempt first
    current = output_file.read_text(encoding="utf-8")
    if "--- Catch the Anointing ---" in current:
        # Remove the old one
        current = re.sub(
            r"\n\n--- Catch the Anointing ---\n.*",
            "",
            current,
            flags=re.DOTALL
        )
        output_file.write_text(current, encoding="utf-8")
        print("Removed previous attempt")

    with open(output_file, "a", encoding="utf-8") as f:
        f.write("\n\n--- Catch the Anointing ---\n")
        for section in sections:
            f.write("\n" + section + "\n")
    print(f"✅ Added Catch the Anointing — {len(sections)} chapters")
else:
    print("❌ Still no content found")
