import re
from pathlib import Path
from ingestion.pipeline import read_file, split_into_books, split_into_chapters, clean_text, chunk_text

DATA_FILE = Path("data/raw/dag_books_v2.txt")

raw_text = read_file(DATA_FILE)
books = split_into_books(raw_text)

print(f"{'Book':<55} {'Segments':>9} {'Chunks':>7}")
print("-" * 75)

total_chunks = 0
zero_chunk_books = []

for book_title, book_text in books:
    segments = split_into_chapters(book_title, book_text)
    all_chunks = []
    for seg in segments:
        cleaned = clean_text(seg.raw_text)
        chunks = chunk_text(cleaned)
        all_chunks.extend(chunks)

    total_chunks += len(all_chunks)

    if len(all_chunks) == 0:
        zero_chunk_books.append(book_title)

    print(f"{book_title[:55]:<55} {len(segments):>9} {len(all_chunks):>7}")

print("-" * 75)
print(f"{'TOTAL':<55} {'':>9} {total_chunks:>7}")

if zero_chunk_books:
    print(f"\n⚠️  Books with ZERO chunks:")
    for b in zero_chunk_books:
        print(f"  - {b}")
else:
    print(f"\n✅ All books have chunks. Ready for ingestion.")
