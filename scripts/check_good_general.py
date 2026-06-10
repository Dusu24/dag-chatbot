import re
from pathlib import Path
from ingestion.pipeline import read_file, split_into_books, split_into_chapters, clean_text, chunk_text

DATA_FILE = Path("data/raw/dag_books_v2.txt")

raw_text = read_file(DATA_FILE)
books = split_into_books(raw_text)

for book_title, book_text in books:
    if "good general" in book_title.lower():
        print(f"Book: {book_title}")
        print(f"Total chars: {len(book_text):,}")

        segments = split_into_chapters(book_title, book_text)
        print(f"Total segments: {len(segments)}")

        all_chunks = []
        for seg in segments:
            cleaned = clean_text(seg.raw_text)
            chunks = chunk_text(cleaned)
            all_chunks.extend(chunks)

        print(f"Total chunks: {len(all_chunks)}")
        print()
        print("First 5 segments:")
        for i, seg in enumerate(segments[:5]):
            print(f"  Segment {i+1}: Ch{seg.chapter_number} — {seg.chapter_title} ({len(seg.raw_text)} chars)")
        print()
        print("Last 5 segments:")
        for i, seg in enumerate(segments[-5:]):
            print(f"  Segment {len(segments)-4+i}: Ch{seg.chapter_number} — {seg.chapter_title} ({len(seg.raw_text)} chars)")
        break
