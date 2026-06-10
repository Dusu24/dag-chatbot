# Checks every book for content that appears before the first chapter heading
# These are books where Chapter 1 content was previously being lost

import re
from pathlib import Path
from ingestion.pipeline import read_file, split_into_books, split_into_chapters

DATA_FILE = Path("data/raw/dag_books_v2.txt")

raw_text = read_file(DATA_FILE)
books = split_into_books(raw_text)

chapter_pattern = re.compile(
    r"^(CHAPTER|Chapter)\s+(\d+)\s*[:\-]?\s*(.*)$",
    re.MULTILINE
)

print(f"Checking {len(books)} books for missing pre-chapter content...\n")

books_with_missing = []
books_ok = []

for book_title, book_text in books:
    matches = list(chapter_pattern.finditer(book_text))

    if not matches:
        # No chapter headings — handled by Strategy 2 or 3
        continue

    pre_chapter_text = book_text[:matches[0].start()].strip()

    if len(pre_chapter_text) > 200:
        books_with_missing.append({
            "title": book_title,
            "pre_chars": len(pre_chapter_text),
            "first_chapter": matches[0].group(0).strip(),
            "preview": pre_chapter_text[:100]
        })
    else:
        books_ok.append(book_title)

print(f"✅ Books where Chapter 1 is fine: {len(books_ok)}")
print(f"⚠️  Books with content before first chapter heading: {len(books_with_missing)}")
print()

for b in books_with_missing:
    print(f"Book: {b['title']}")
    print(f"  Pre-chapter content: {b['pre_chars']:,} chars")
    print(f"  First heading found: {b['first_chapter']}")
    print(f"  Preview: {repr(b['preview'])}")
    print()
