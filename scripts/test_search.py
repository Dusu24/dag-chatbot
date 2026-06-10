# scripts/test_search.py
# Tests that Qdrant is returning relevant results for real questions.

import sys, os
sys.path.insert(0, os.path.abspath("."))

from openai import OpenAI
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60,
)

COLLECTION_NAME = "dag_books"
EMBEDDING_MODEL = "text-embedding-3-small"


def search(question: str, top_k: int = 3):
    """
    Takes a question, converts it to a vector,
    and finds the most relevant chunks in Qdrant.
    """
    print(f"\n{'='*55}")
    print(f"QUESTION: {question}")
    print(f"{'='*55}")

    # Convert the question into a vector
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=question,
    )
    question_vector = response.data[0].embedding

    # Search Qdrant for the most similar chunks
    results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=question_vector,
        limit=top_k,
    )

    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} (score: {result.score:.3f}) ---")
        print(f"Book   : {result.payload['book_title']}")
        print(f"Chapter: {result.payload['chapter_number']} — {result.payload['chapter_title']}")
        print(f"Text   : {result.payload['text'][:300]}...")


if __name__ == "__main__":
    # Test with 3 different questions
    search("What does Bishop Dag say about loyalty?")
    search("How should a Christian pray?")
    search("What is the anointing of the Holy Spirit?")