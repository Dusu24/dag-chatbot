import re
from pathlib import Path
from ingestion.pipeline import read_file, split_into_books, split_into_chapters, clean_text, chunk_text

DATA_FILE = Path("data/raw/dag_books_v2.txt")
BOOK_TO_CHECK = "Why Loyalty"

raw_text = read_file(DATA_FILE)
books = split_into_books(raw_text)

for book_title, book_text in books:
    if BOOK_TO_CHECK.lower() in book_title.lower():
        print(f"Book: {book_title}")
        print(f"Total characters: {len(book_text):,}")
        print()

        # Show the first 50 lines of the raw book text
        print("FIRST 50 LINES OF RAW BOOK TEXT:")
        print("="*50)
        lines = book_text.split("\n")
        for i, line in enumerate(lines[:50]):
            print(f"{i+1:3}: {repr(line)}")
        break
