# scripts/setup_qdrant.py
# Run this ONCE to create your collection in Qdrant.
# Think of it as creating the database table before inserting data.

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv
import os

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

COLLECTION_NAME = "dag_books"

# Check if collection already exists
existing = [c.name for c in client.get_collections().collections]

if COLLECTION_NAME in existing:
    print(f"Collection '{COLLECTION_NAME}' already exists.")
else:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1536,        # OpenAI text-embedding-3-small produces 1536 numbers
            distance=Distance.COSINE,  # measures similarity between vectors
        ),
    )
    print(f"✅ Collection '{COLLECTION_NAME}' created successfully.")

# Confirm it's there
collections = [c.name for c in client.get_collections().collections]
print(f"Your collections: {collections}")
