# scripts/extract_epubs.py
# Extracts text from epub files using the spine (correct reading order)

import re
from pathlib import Path
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

EPUB_FOLDER = Path("data/epubs")
OUTPUT_FILE = Path("data/raw/dag_books_v2.txt")

EPUB_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_book_title(book: epub.EpubBook, filename: str) -> str:
    try:
        title = book.get_metadata("DC", "title")
        if title and title[0][0]:
            return title[0][0].strip()
    except Exception:
        pass
    name = Path(filename).stem
    name = re.sub(r"^\d+[\.\-\s]+", "", name)
    name = name.replace("-", " ").replace("_", " ")
    return name.strip()


def is_skippable_item(name: str, text: str) -> bool:
    """Returns True if this epub item should be skipped."""
    name_lower = name.lower()

    # Skip by filename
    skip_names = [
        "toc", "cover", "copyright", "references", "ref.",
        "acknowledgement", "dedication", "preface", "foreword",
        "bibliography", "index", "about"
    ]
    for skip in skip_names:
        if skip in name_lower:
            return True

    if not text or len(text.strip()) < 100:
        return True

    # Skip if it looks like a table of contents
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) > 2:
        chapter_refs = sum(1 for l in lines if re.match(r"(?i)^chapter\s+\d+", l))
        if chapter_refs / len(lines) > 0.35:
            return True

    # Skip boilerplate first lines
    first_line = lines[0] if lines else ""
    skip_starts = [
        "unless otherwise stated",
        "first published",
        "find out more",
        "all scripture",
        "published by",
        "copyright",
        "references",
        "contents",
        "table of contents",
    ]
    for s in skip_starts:
        if first_line.lower().startswith(s):
            return True

    return False


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\u2019", "'")
    text = text.replace("\u2018", "'")
    text = text.replace("\u201c", '"')
    text = text.replace("\u201d", '"')
    text = re.sub(r"(?m)^.*?ISBN.*$", "", text)
    text = re.sub(r"(?m)^\s*www\.\S+\s*$", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"(?m)^.*Copyright.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?m)^.*?Published by.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?m)^.*?All rights reserved.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?m)^.*?First published.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?m)^.*?Find out more.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?m)^.*?Unless otherwise stated.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
    text = re.sub(r"(?m)^\s*[\*\-\_\=]{3,}\s*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def extract_epub(epub_path: Path) -> list[dict]:
    """
    Extracts content from epub in correct reading order using the spine.
    Each spine item becomes one section.
    """
    try:
        book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

    # Build a map of all document items by id AND by filename
    items_by_id = {}
    items_by_name = {}
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            items_by_id[item.get_id()] = item
            # Also index by base filename (e.g. "C1.xhtml")
            base_name = Path(item.get_name()).name
            items_by_name[base_name] = item

    # Get spine order (correct reading order)
    spine = book.spine
    if spine:
        ordered_items = []
        for item_id, _ in spine:
            if item_id in items_by_id:
                ordered_items.append(items_by_id[item_id])
            elif item_id in items_by_name:
                # Fall back to matching by filename
                ordered_items.append(items_by_name[item_id])
    else:
        ordered_items = list(items_by_id.values())

    sections = []

    for item in ordered_items:
        item_name = item.get_name().lower()

        try:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            raw_text = soup.get_text(separator="\n", strip=True)

            if is_skippable_item(item_name, raw_text):
                continue

            # Get section title from heading
            title = ""
            for tag in ["h1", "h2", "h3"]:
                heading = soup.find(tag)
                if heading:
                    t = heading.get_text(strip=True)
                    if t and len(t) < 120:
                        title = t
                        break

            # Extract paragraphs in order
            paragraphs = []
            for el in soup.find_all(["h1", "h2", "h3", "h4", "p"]):
                t = el.get_text(separator=" ", strip=True)
                if t and len(t) > 15:
                    paragraphs.append(t)

            if not paragraphs:
                continue

            full_text = "\n".join(paragraphs)
            cleaned = clean_text(full_text)

            if len(cleaned) < 150:
                continue

            sections.append({
                "title": title,
                "text": cleaned,
            })

        except Exception:
            continue

    return sections


def main():
    epub_files = sorted(EPUB_FOLDER.glob("*.epub"))

    if not epub_files:
        print(f"No epub files found in {EPUB_FOLDER}")
        print("Please copy your epub files into data/epubs/ and run again.")
        return

    print(f"Found {len(epub_files)} epub files")
    print(f"Output: {OUTPUT_FILE}\n")

    total_sections = 0
    no_content = []
    output_lines = []

    for i, epub_path in enumerate(epub_files):
        print(f"[{i+1}/{len(epub_files)}] {epub_path.name}")

        try:
            book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
            book_title = get_book_title(book, epub_path.name)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        sections = extract_epub(epub_path)

        if not sections:
            print(f"  WARNING: No content extracted")
            no_content.append(epub_path.name)
            continue

        output_lines.append(f"\n\n--- {book_title} ---\n")

        for section in sections:
            if section["title"]:
                output_lines.append(f"\n{section['title']}\n")
            output_lines.append(section["text"] + "\n")
            total_sections += 1

        print(f"  Sections: {len(sections)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)

    print(f"\n{'='*50}")
    print(f"EXTRACTION COMPLETE")
    print(f"Books processed  : {len(epub_files)}")
    print(f"Sections kept    : {total_sections:,}")
    print(f"Output file size : {file_size_mb:.1f} MB")
    print(f"Output file      : {OUTPUT_FILE}")
    if no_content:
        print(f"\nBooks with no content ({len(no_content)}):")
        for name in no_content:
            print(f"  - {name}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
