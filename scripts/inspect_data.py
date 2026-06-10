# scripts/inspect.py
# Run this first before building anything.
# It tells you how your data is structured so you can build around it.

from pathlib import Path
import re

def inspect_file(filepath: str):
    text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    print("=" * 50)
    print("BASIC STATS")
    print("=" * 50)
    print(f"Total characters : {len(text):,}")
    print(f"Total lines      : {len(lines):,}")
    print(f"Non-empty lines  : {sum(1 for l in lines if l.strip()):,}")
    print()

    print("=" * 50)
    print("FIRST 30 LINES (to see how the file starts)")
    print("=" * 50)
    for i, line in enumerate(lines[:30]):
        print(f"{i+1:3}: {repr(line)}")
    print()

    print("=" * 50)
    print("LINES THAT LOOK LIKE CHAPTER HEADINGS")
    print("=" * 50)
    chapter_lines = [
        (i+1, l) for i, l in enumerate(lines)
        if re.match(r"(?i)^(chapter|ch\.?)\s*\d", l.strip())
    ]
    print(f"Found: {len(chapter_lines)}")
    for lineno, line in chapter_lines[:30]:
        print(f"  Line {lineno}: {repr(line.strip())}")
    print()

    print("=" * 50)
    print("ALL-CAPS LINES (often book titles or major headings)")
    print("=" * 50)
    caps_lines = [
        (i+1, l) for i, l in enumerate(lines)
        if l.strip().isupper() and 5 < len(l.strip()) < 80
    ]
    print(f"Found: {len(caps_lines)}")
    for lineno, line in caps_lines[:30]:
        print(f"  Line {lineno}: {repr(line.strip())}")
    print()

    print("=" * 50)
    print("LINES WITH NUMBERS AT START (numbered sections?)")
    print("=" * 50)
    numbered = [
        (i+1, l) for i, l in enumerate(lines)
        if re.match(r"^\d+[\.\)]\s+[A-Z]", l.strip())
    ]
    print(f"Found: {len(numbered)}")
    for lineno, line in numbered[:20]:
        print(f"  Line {lineno}: {repr(line.strip())}")

if __name__ == "__main__":
    inspect_file("data/raw/dag_books_v2.txt")