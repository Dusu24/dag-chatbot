# ingestion/storage.py

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from dotenv import load_dotenv
import os
import uuid
import time

load_dotenv()

COLLECTION_NAME = "dag_books"

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60,  # wait up to 60 seconds per request
)


def store_chunks(embedded_chunks: list) -> None:
    """
    Stores embedded chunks in Qdrant with retry logic.
    Uses smaller batches to avoid timeouts.
    """
    BATCH_SIZE = 50   # reduced from 100 to avoid timeouts
    MAX_RETRIES = 3
    total = len(embedded_chunks)
    print(f"Storing {total:,} chunks in Qdrant...")

    for batch_start in range(0, total, BATCH_SIZE):
        batch = embedded_chunks[batch_start: batch_start + BATCH_SIZE]

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=chunk.embedding,
                payload={
                    "chunk_id":         chunk.chunk_id,
                    "book_title":       chunk.book_title,
                    "chapter_number":   chunk.chapter_number,
                    "chapter_title":    chunk.chapter_title,
                    "text":             chunk.text,
                    "char_count":       chunk.char_count,
                    "chunk_index":      chunk.chunk_index,
                    "ingestion_run_id": chunk.ingestion_run_id,
                }
            )
            for chunk in batch
        ]

        for attempt in range(MAX_RETRIES):
            try:
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points,
                )
                break  # success — move to next batch
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait = 3 * (attempt + 1)
                    print(f"  Timeout on batch {batch_start} — retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"Failed to upload batch at {batch_start} after {MAX_RETRIES} attempts: {e}")

        uploaded_so_far = min(batch_start + BATCH_SIZE, total)
        if uploaded_so_far % 500 == 0 or uploaded_so_far == total:
            print(f"  Uploaded {uploaded_so_far:,} / {total:,}")

        time.sleep(0.1)  # small pause between batches

    print(f"✅ All chunks stored successfully.")