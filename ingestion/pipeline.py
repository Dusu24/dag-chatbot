# ingestion/pipeline.py
# This is the heart of the ingestion process.
# Run this once (or whenever you update your dataset)
# and it will fill your database with searchable chunks.

import re
import uuid
from pathlib import Path
from core.models import RawSegment, Chunk

# ── SETTINGS ──────────────────────────────────────────────
DATA_FILE = Path("data/raw/dag_books_v2.txt")

# How large each chunk should be (in characters)
# 800 chars ≈ 150-200 words ≈ a good paragraph or two
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100   # how much the end of one chunk repeats in the next
                      # this prevents losing meaning at chunk boundaries
MIN_CHUNK_SIZE = 150  # throw away anything shorter than this


# ── STAGE 1: READ THE FILE ────────────────────────────────

def read_file(filepath: Path) -> str:
    """Read the raw text file."""
    print(f"Reading file: {filepath}")
    text = filepath.read_text(encoding="utf-8", errors="replace")
    print(f"  Total characters: {len(text):,}")
    return text


# ── STAGE 2: SPLIT INTO BOOKS ─────────────────────────────

def split_into_books(text: str) -> list[tuple[str, str]]:
    """
    Splits the file at book boundary markers.
    Supports both formats:
      --- 58. bookname.epub ---   (old format)
      --- Book Title ---          (new format)
    """
    # This pattern matches both old and new formats
    pattern = r"---\s+(.+?)\s+---"

    parts = re.split(pattern, text)

    books = []
    for i in range(1, len(parts) - 1, 2):
        title = parts[i].strip()
        content = parts[i + 1].strip()

        # Clean up old-format titles like "58. bookname.epub"
        title = re.sub(r"^\d+[\.\s]+", "", title)  # remove leading numbers
        title = re.sub(r"\.epub$", "", title)        # remove .epub extension
        title = title.strip()

        if content and len(content) > 100:
            books.append((title, content))

    print(f"Total books found: {len(books)}")
    return books

# ── STAGE 3: SPLIT EACH BOOK INTO CHAPTERS ────────────────

def split_into_chapters(book_title: str, book_text: str) -> list[RawSegment]:
    """
    Splits a book into segments. Tries multiple strategies:
    1. "Chapter X" headings (most books)
    2. Standalone title lines (books without chapter labels)
    """
    segments = []

    # ── STRATEGY 1: Look for "Chapter X" headings ──
    chapter_pattern = re.compile(
        r"^(CHAPTER|Chapter)\s+(\d+)\s*[:\-]?\s*(.*)$",
        re.MULTILINE
    )
    matches = list(chapter_pattern.finditer(book_text))

    if matches:
        # Capture content BEFORE the first chapter heading
        # This is Chapter 1 content in books that don't label their first chapter
        pre_chapter_text = book_text[:matches[0].start()].strip()
        if len(pre_chapter_text) > 200:
            segments.append(RawSegment(
                book_title=book_title,
                chapter_number=1,
                chapter_title=None,
                raw_text=pre_chapter_text
            ))

        # Standard chapter splitting
        for i, match in enumerate(matches):
            chapter_num_str = match.group(2)
            chapter_title_inline = match.group(3)
            chapter_num = int(chapter_num_str) if chapter_num_str else None

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(book_text)
            chapter_text = book_text[start:end].strip()

            chapter_title = chapter_title_inline
            if not chapter_title and chapter_text:
                first_line = chapter_text.split("\n")[0].strip()
                if first_line and len(first_line) < 80 and not first_line[0].isdigit():
                    chapter_title = first_line
                    chapter_text = chapter_text[len(first_line):].strip()

            if len(chapter_text) < 50:
                continue

            segments.append(RawSegment(
                book_title=book_title,
                chapter_number=chapter_num,
                chapter_title=chapter_title,
                raw_text=chapter_text
            ))
        return segments

    # ── STRATEGY 2: Look for standalone section title lines ──
    # A section title is a short line (under 80 chars) that:
    # - is NOT a numbered point like "1. Do this"
    # - is NOT a scripture reference
    # - is followed by actual paragraph content
    lines = book_text.split("\n")
    section_positions = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        is_short = len(stripped) < 80
        is_not_numbered_point = not re.match(r"^\d+[\.\)]\s+", stripped)
        is_not_scripture = not re.match(r"^(And |But |For |The |In |He |She |They |We |I )", stripped)
        is_not_sentence = not stripped.endswith(".")
        is_capitalized = stripped[0].isupper()
        next_lines_have_content = any(
            lines[j].strip() for j in range(i+1, min(i+4, len(lines)))
        )

        if (is_short and is_not_numbered_point and is_not_scripture
                and is_not_sentence and is_capitalized
                and next_lines_have_content
                and len(stripped) > 8):
            section_positions.append((i, stripped))

    if len(section_positions) >= 3:
        # Use section titles as segment boundaries
        for idx, (line_pos, section_title) in enumerate(section_positions):
            next_pos = section_positions[idx + 1][0] if idx + 1 < len(section_positions) else len(lines)
            section_lines = lines[line_pos + 1: next_pos]
            section_text = "\n".join(section_lines).strip()

            if len(section_text) < 100:
                continue

            segments.append(RawSegment(
                book_title=book_title,
                chapter_number=idx + 1,
                chapter_title=section_title,
                raw_text=section_text
            ))

        if segments:
            return segments

    # ── STRATEGY 3: Split by large text blocks ──
    # For books that have no detectable structure at all,
    # split the whole text into reasonably sized segments
    print(f"    INFO: No structure found in '{book_title}' — splitting by text blocks")
    paragraphs = [p.strip() for p in book_text.split("\n\n") if p.strip()]

    TARGET_SEGMENT_SIZE = 3000  # chars per segment
    current_text = []
    current_len = 0
    segment_num = 1

    for para in paragraphs:
        if current_len + len(para) > TARGET_SEGMENT_SIZE and current_text:
            segments.append(RawSegment(
                book_title=book_title,
                chapter_number=segment_num,
                chapter_title=None,
                raw_text="\n\n".join(current_text)
            ))
            segment_num += 1
            current_text = [para]
            current_len = len(para)
        else:
            current_text.append(para)
            current_len += len(para)

    if current_text:
        segments.append(RawSegment(
            book_title=book_title,
            chapter_number=segment_num,
            chapter_title=None,
            raw_text="\n\n".join(current_text)
        ))

    return segments

# ── STAGE 4: CLEAN THE TEXT ───────────────────────────────

def clean_text(text: str) -> str:
    """
    Remove noise from the text without destroying the content.
    """
    # Replace non-breaking spaces with regular spaces
    text = text.replace("\xa0", " ")

    # Remove ISBN lines
    text = re.sub(r"(?m)^.*?ISBN.*$", "", text)

    # Remove lines that are just URLs
    text = re.sub(r"(?m)^\s*www\.\S+\s*$", "", text)

    # Remove copyright lines
    text = re.sub(r"(?m)^.*?Copyright.*$", "", text, flags=re.IGNORECASE)

    # Remove standalone page numbers
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)

    # Remove decorative lines (asterisks, dashes)
    text = re.sub(r"(?m)^\s*[\*\-]{3,}\s*$", "", text)

    # Remove "For a complete list of titles..." lines
    text = re.sub(r"(?m)^For a complete list.*$", "", text, flags=re.IGNORECASE)

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces into one
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


# ── STAGE 5: SPLIT CHAPTERS INTO CHUNKS ──────────────────

def chunk_text(text: str) -> list[str]:
    """
    Split a chapter into small overlapping chunks.
    Handles both single and double newline paragraph separators.
    """
    # Normalize: treat single newlines as paragraph breaks too
    # First collapse multiple newlines into double newline
    text = re.sub(r'\n{2,}', '\n\n', text)
    # Then treat single newlines as paragraph breaks
    text = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', text)

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        # Skip very short paragraphs that are just noise
        if len(para) < 20:
            continue

        para_length = len(para)

        if current_length + para_length > CHUNK_SIZE and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            overlap_text = current_chunk[-1] if current_chunk else ""
            current_chunk = [overlap_text, para] if overlap_text else [para]
            current_length = len(overlap_text) + para_length
        else:
            current_chunk.append(para)
            current_length += para_length

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    chunks = [c for c in chunks if len(c) >= MIN_CHUNK_SIZE]

    return chunks

# These are section types we want to skip entirely
SKIP_PATTERNS = [
    r"(?i)^dedication",
    r"(?i)^foreword",
    r"(?i)^contents",
    r"(?i)^acknowledgement",
    r"(?i)^introduction\s*$",
    r"(?i)^preface",
]

def is_skip_segment(text: str) -> bool:
    """Returns True if this segment is boilerplate we should skip."""
    first_line = text.strip().split("\n")[0].strip()
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, first_line):
            return True
    return False


def run_pipeline() -> list[Chunk]:
    """
    Runs all stages in order and returns a list of Chunks
    ready to be embedded and stored.
    """
    run_id = str(uuid.uuid4())
    print(f"\n{'='*50}")
    print(f"INGESTION PIPELINE STARTING")
    print(f"Run ID: {run_id}")
    print(f"{'='*50}\n")

    # Stage 1: Read
    raw_text = read_file(DATA_FILE)

    # Stage 2: Split into books
    print("\n--- Splitting into books ---")
    books = split_into_books(raw_text)

    # Stage 3 + 4 + 5: Per book, split chapters, clean, chunk
    all_chunks = []
    skipped_segments = 0

    for book_title, book_text in books:
        print(f"\nProcessing: {book_title}")

        # Split into chapters
        segments = split_into_chapters(book_title, book_text)
        print(f"  Chapters: {len(segments)}")

        for segment in segments:
            # Skip boilerplate sections (dedications, forewords, etc.)
            if is_skip_segment(segment.raw_text):
                skipped_segments += 1
                continue

            # Clean the text
            cleaned = clean_text(segment.raw_text)

            # Skip if cleaning left us with almost nothing
            if len(cleaned) < MIN_CHUNK_SIZE:
                skipped_segments += 1
                continue

            # Split into chunks
            text_chunks = chunk_text(cleaned)

            # Create Chunk objects
            for i, chunk_text_content in enumerate(text_chunks):
                all_chunks.append(Chunk(
                    source_segment_id=segment.segment_id,
                    book_title=segment.book_title,
                    chapter_number=segment.chapter_number,
                    chapter_title=segment.chapter_title,
                    text=chunk_text_content,
                    char_count=len(chunk_text_content),
                    chunk_index=i,
                    ingestion_run_id=run_id,
                ))

    print(f"\n{'='*50}")
    print(f"PIPELINE COMPLETE")
    print(f"Total chunks created : {len(all_chunks):,}")
    print(f"Segments skipped     : {skipped_segments}")
    print(f"{'='*50}\n")

    return all_chunks


if __name__ == "__main__":
    chunks = run_pipeline()

    # Preview the first 3 chunks so you can see what was created
    print("\nPREVIEW — First 3 chunks:\n")
    for chunk in chunks[:3]:
        print(f"Book   : {chunk.book_title}")
        print(f"Chapter: {chunk.chapter_number} — {chunk.chapter_title}")
        print(f"Length : {chunk.char_count} chars")
        print(f"Text   : {chunk.text[:300]}...")
        print("-" * 40)

    # Show chunk size distribution so we can verify sizes are healthy
    print("\nCHUNK SIZE DISTRIBUTION:")
    tiny    = sum(1 for c in chunks if c.char_count < 200)
    small   = sum(1 for c in chunks if 200 <= c.char_count < 500)
    medium  = sum(1 for c in chunks if 500 <= c.char_count < 1000)
    large   = sum(1 for c in chunks if 1000 <= c.char_count < 2000)
    toobig  = sum(1 for c in chunks if c.char_count >= 2000)
    print(f"  Tiny   (<200 chars) : {tiny}")
    print(f"  Small  (200-500)    : {small}")
    print(f"  Medium (500-1000)   : {medium}  ← ideal range")
    print(f"  Large  (1000-2000)  : {large}")
    print(f"  Too big (2000+)     : {toobig}  ← should be low")# patch applied via append — ignore this
