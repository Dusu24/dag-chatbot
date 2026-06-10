# Shows the first 60 lines of a specific book so we can see
# how its chapters are actually formatted in the file.

from pathlib import Path
import re

text = Path("data/raw/dag_books_v2.txt").read_text(encoding="utf-8", errors="replace")

# Find a specific book and show its first 60 lines
BOOK_TO_CHECK = "Rules of Church Work"

pattern = r"---\s+(.+?)\s+---"
parts = re.split(pattern, text)

for i in range(1, len(parts) - 1, 2):
    title = parts[i].strip()
    content = parts[i + 1].strip()
    if BOOK_TO_CHECK.lower() in title.lower():
        print(f"BOOK: {title}")
        print("=" * 50)
        lines = content.split("\n")
        for j, line in enumerate(lines[:60]):
            print(f"{j+1:3}: {repr(line)}")
        break
