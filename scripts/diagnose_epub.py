# Diagnoses why certain epubs aren't extracting properly

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path

EPUB_FOLDER = Path("data/epubs")

# Check one "no content" book and one "sections: 1" book
CHECK_THESE = [
    "085-en-awake-o-sleeper.epub",
    "018-en-the-art-of-shepherding.epub",
    "050-en-make-yourselves-saviours-of-men.epub",
    "015-en-sweet-influences-of-the-anointing.epub",
]

for filename in CHECK_THESE:
    epub_path = EPUB_FOLDER / filename
    if not epub_path.exists():
        print(f"NOT FOUND: {filename}")
        continue

    print(f"\n{'='*60}")
    print(f"FILE: {filename}")
    print(f"{'='*60}")

    book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})

    items = list(book.get_items())
    doc_items = [i for i in items if i.get_type() == ebooklib.ITEM_DOCUMENT]
    print(f"Total document items: {len(doc_items)}")

    for i, item in enumerate(doc_items[:5]):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        raw_text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in raw_text.split("\n") if l.strip()]

        print(f"\n  Item {i+1}: {item.get_name()}")
        print(f"  Characters: {len(raw_text)}")
        print(f"  Non-empty lines: {len(lines)}")
        print(f"  First 5 lines:")
        for line in lines[:5]:
            print(f"    {repr(line[:100])}")

        # Check what HTML tags are used
        tags_used = set(tag.name for tag in soup.find_all())
        print(f"  HTML tags found: {sorted(tags_used)}")
