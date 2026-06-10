import re
from pathlib import Path
from ingestion.pipeline import read_file, split_into_books, split_into_chapters, clean_text, chunk_text

DATA_FILE = Path("data/raw/dag_books_v2.txt")
BOOK_TO_CHECK = "Why Loyalty"

raw_text = read_file(DATA_FILE)
books = split_into_books(raw_text)

for book_title, book_text in books:
    if BOOK_TO_CHECK.lower() in book_title.lower():
        segments = split_into_chapters(book_title, book_text)

        print(f"Number of segments: {len(segments)}")
        for i, seg in enumerate(segments):
            print(f"\nSegment {i+1}:")
            print(f"  Chapter number: {seg.chapter_number}")
            print(f"  Chapter title: {seg.chapter_title}")
            print(f"  Text length: {len(seg.raw_text)}")
            print(f"  First 100 chars: {repr(seg.raw_text[:100])}")

        print("\n--- ALL CHUNKS ---")
        all_chunks = []
        for seg in segments:
            cleaned = clean_text(seg.raw_text)
            chunks = chunk_text(cleaned)
            all_chunks.extend(chunks)

        print(f"Total chunks: {len(all_chunks)}")
        for i, chunk in enumerate(all_chunks[:5]):
            print(f"\nChunk {i+1} ({len(chunk)} chars):")
            print(chunk[:200])
        break
