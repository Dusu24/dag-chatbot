# orchestration/llm_client.py

from openai import OpenAI
from dotenv import load_dotenv
import os
import re

load_dotenv()

def get_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_book_title(raw_title: str) -> str:
    title = re.sub(r'\(\d{4}\)', '', raw_title).strip()
    title = title.replace('-', ' ').replace('_', ' ')
    words = title.split()
    small_words = {'and', 'or', 'the', 'a', 'an', 'of', 'in', 'to', 'for', 'with'}
    formatted = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in small_words:
            formatted.append(word.capitalize())
        else:
            formatted.append(word.lower())
    return ' '.join(formatted)


def expand_query(question: str) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a search query optimizer for a chatbot about Bishop Dag Heward-Mills' teachings. "
                    "Rewrite the user's question into a detailed search query that will find the most relevant "
                    "passages from his books. Return ONLY the rewritten query, nothing else."
                )
            },
            {"role": "user", "content": f"Rewrite: {question}"}
        ],
        temperature=0.2,
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()


def build_context(chunks: list[dict]) -> str:
    context = ""
    for i, chunk in enumerate(chunks):
        book = format_book_title(chunk['book_title'])
        chapter = chunk.get('chapter_title') or ''
        context += f"[Passage {i+1} — {book}"
        if chapter:
            context += f", {chapter}"
        context += f"]\n{chunk['text']}\n\n"
    return context


def build_prompt(question: str, chunks: list[dict], history: list[dict] = None) -> list[dict]:
    system = {
        "role": "system",
        "content": """You are a knowledgeable assistant specializing in the teachings of Bishop Dag Heward-Mills.

Answer questions using ONLY the provided passages from his books.
- Give rich, thoughtful answers that help the person truly understand the teaching
- Use a warm, pastoral tone
- Always mention the source book
- If passages don't fully answer, say so honestly
- Never fabricate teachings
- Do not use markdown formatting like **bold** or # headers — write in clean flowing prose with natural paragraph breaks
- You may use bold for important terms by wrapping them like this: **term**"""
    }

    context = "Relevant passages from Bishop Dag's books:\n\n" + build_context(chunks)
    messages = [system]
    if history:
        messages.extend(history[-8:])
    messages.append({"role": "user", "content": f"{context}\nQuestion: {question}"})
    return messages


def build_mode_prompt(question: str, chunks: list[dict], history: list[dict], mode: str) -> list[dict]:

    context = "Relevant passages from Bishop Dag's books:\n\n" + build_context(chunks)

    if mode == "devotion":
        system_content = """You are a devotional writer drawing from the teachings of Bishop Dag Heward-Mills.

Using the provided passages, write a rich daily devotional in this exact structure:

**Topic:** [topic title]

**Scripture:** [most relevant scripture from the passages]

**Devotional:**
[3-4 paragraphs of warm, pastoral devotional writing drawn from the passages. Write as if speaking directly to the reader's heart.]

**Key Teaching from Bishop Dag:**
[1-2 paragraphs summarizing the core teaching from the passages]

**Reflection Questions:**
1. [question]
2. [question]
3. [question]

**Prayer:**
[A short heartfelt prayer based on the teaching]

**Source:** [mention the book(s) this teaching comes from]

Write with warmth, depth and spiritual insight. Make it genuinely useful for someone's morning devotion."""

    elif mode == "sermon":
        system_content = """You are a sermon preparation assistant drawing from the teachings of Bishop Dag Heward-Mills.

Using the provided passages, create a detailed sermon outline in this exact structure:

**Sermon Title:** [compelling title]

**Main Scripture:** [key verse from the passages]

**Introduction:**
[2-3 sentences to open the sermon and hook the congregation]

**Main Points:**

Point 1: [title]
- [supporting idea from Bishop Dag's teaching]
- [scripture reference]
- [practical application]

Point 2: [title]
- [supporting idea]
- [scripture reference]
- [practical application]

Point 3: [title]
- [supporting idea]
- [scripture reference]
- [practical application]

**Conclusion:**
[How to close the sermon and call to action]

**Altar Call / Application:**
[Practical steps the congregation can take]

**Sources:** [books referenced]

Make this outline detailed enough that a pastor can preach directly from it."""

    elif mode == "study":
        system_content = """You are a Bible study facilitator drawing from the teachings of Bishop Dag Heward-Mills.

Using the provided passages, create comprehensive study notes in this structure:

**Study Topic:** [topic]

**Overview:**
[2-3 paragraphs giving a thorough overview of what Bishop Dag teaches on this topic]

**Key Teachings:**
[Go through each major point Bishop Dag makes on this topic, with depth and explanation]

**Supporting Scriptures:**
[List the key scriptures related to this teaching with brief explanations]

**Practical Application:**
[How to apply these teachings in ministry and daily life]

**Common Questions on This Topic:**
[2-3 questions people often ask, with answers from the teachings]

**For Further Study:**
[Mention which of Bishop Dag's books cover this topic most deeply]

Make the notes thorough enough for a small group Bible study or personal deep study."""

    else:
        return build_prompt(question, chunks, history)

    messages = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history[-6:])
    messages.append({
        "role": "user",
        "content": f"{context}\n\nCreate a {mode} on this topic: {question}"
    })
    return messages


def generate_answer(question: str, chunks: list[dict], history: list[dict] = None) -> str:
    client = get_client()
    messages = build_prompt(question, chunks, history)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.4,
        max_tokens=900,
    )
    return response.choices[0].message.content.strip()
