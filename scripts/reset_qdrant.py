# scripts/reset_qdrant.py
# Deletes the old collection and creates a fresh one.

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv
import os

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60,
)

COLLECTION_NAME = "dag_books"

print("Deleting old collection...")
client.delete_collection(COLLECTION_NAME)

print("Creating fresh collection...")
client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
    ),
)

print("✅ Fresh collection ready.")
