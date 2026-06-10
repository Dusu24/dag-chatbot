# scripts/run_ingestion.py
# This is the ONE script you run to go from raw text → searchable database.
# It runs the full pipeline: read → chunk → embed → store

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from ingestion.pipeline import run_pipeline
from ingestion.embedder import embed_chunks
from ingestion.storage import store_chunks


def main():
    print("\n🚀 STARTING FULL INGESTION\n")

    # Step 1: Run the text pipeline (read, split, clean, chunk)
    print("=" * 50)
    print("STEP 1: Text Pipeline")
    print("=" * 50)
    chunks = run_pipeline()
    print(f"Chunks ready to embed: {len(chunks):,}")

    # Step 2: Embed the chunks
    print("\n" + "=" * 50)
    print("STEP 2: Embedding")
    print("=" * 50)
    embedded = embed_chunks(chunks)

    # Step 3: Store in Qdrant
    print("\n" + "=" * 50)
    print("STEP 3: Storing in Qdrant")
    print("=" * 50)
    store_chunks(embedded)

    print("\n✅ INGESTION COMPLETE")
    print(f"   {len(embedded):,} chunks are now searchable in Qdrant.")


if __name__ == "__main__":
    main()