# ingestion/embedder.py
# Converts text chunks into vectors (lists of numbers)
# that capture the meaning of the text.

from openai import OpenAI
from core.models import Chunk, EmbeddedChunk
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 100
MAX_RETRIES = 3


def embed_chunks(chunks: list[Chunk]) -> list[EmbeddedChunk]:
    """
    Sends chunks to OpenAI in batches and gets back vectors.
    Retries automatically if something goes wrong.
    """
    embedded = []
    total = len(chunks)
    print(f"Embedding {total:,} chunks...")

    for batch_start in range(0, total, BATCH_SIZE):
        batch = chunks[batch_start: batch_start + BATCH_SIZE]
        texts = [c.text for c in batch]

        for attempt in range(MAX_RETRIES):
            try:
                response = client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=texts,
                )

                for chunk, embedding_data in zip(batch, response.data):
                    embedded.append(EmbeddedChunk(
                        **chunk.model_dump(),
                        embedding=embedding_data.embedding,
                        embedding_model=EMBEDDING_MODEL,
                        embedding_dimension=EMBEDDING_DIMENSION,
                    ))

                print(f"  Embedded {min(batch_start + BATCH_SIZE, total):,} / {total:,}")
                break

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    print(f"  Error: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"Embedding failed after {MAX_RETRIES} attempts: {e}")

        # Small pause between batches to be kind to the API
        time.sleep(0.2)

    print(f"✅ Embedding complete.")
    return embedded