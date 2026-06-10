# retrieval/engine.py

from openai import OpenAI
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60,
)

COLLECTION_NAME = "dag_books"
EMBEDDING_MODEL = "text-embedding-3-small"


def embed(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def search_chunks(question: str, top_k: int = 5, expanded_query: str = None) -> list[dict]:
    """
    Searches using both the original question and an expanded query.
    Combines results and deduplicates for better coverage.
    """
    # Search with original question
    original_vector = embed(question)
    results_original = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=original_vector,
        limit=15,
    )

    # If we have an expanded query, search with that too
    all_results = list(results_original)
    if expanded_query and expanded_query != question:
        expanded_vector = embed(expanded_query)
        results_expanded = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=expanded_vector,
            limit=15,
        )
        all_results += list(results_expanded)

    # Sort by score, deduplicate by text, diversify by book
    seen_texts = set()
    seen_books = {}
    selected = []

    # Sort highest score first
    all_results.sort(key=lambda r: r.score, reverse=True)

    for r in all_results:
        text = r.payload["text"]
        book = r.payload["book_title"]

        # Skip duplicates
        if text in seen_texts:
            continue

        # Max 2 chunks per book
        if seen_books.get(book, 0) >= 2:
            continue

        selected.append({
            "text":           text,
            "book_title":     book,
            "chapter_number": r.payload["chapter_number"],
            "chapter_title":  r.payload["chapter_title"],
            "score":          r.score,
        })

        seen_texts.add(text)
        seen_books[book] = seen_books.get(book, 0) + 1

        if len(selected) >= top_k:
            break

    return selected