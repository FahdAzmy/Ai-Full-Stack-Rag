"""
Context Builder — Assemble the LLM prompt from retrieved chunks.

Builds an OpenAI-compatible message list:
  [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."},       # history
      {"role": "assistant", "content": "..."},   # history
      {"role": "user", "content": "..."},        # current question
  ]
"""

# ── Configuration Constants ──────────────────────────────────────────────────

MAX_CONTEXT_CHUNKS = 8    # Cap retrieved chunks to prevent token explosion
MAX_CHUNK_CHARS = 1200    # Truncate oversized chunks to control token usage


# ── System Prompt Template ───────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are ScholarGPT, an expert academic research assistant.
You help researchers and students find information in their uploaded research papers.

## YOUR RULES:
1. Prefer the provided research context. Answer based only on these sources when possible.
   If the context does not contain the answer, state that the information was not found
   in the uploaded papers.
2. ALWAYS cite which source you used by writing [Source N] in your answer.
3. Be precise, academic, and thorough in your responses.
4. Use clear formatting: bullet points, numbered lists, and headers when appropriate.
5. At the end of your answer, list all sources you referenced under "## References Used".

## RESEARCH CONTEXT FROM USER'S PAPERS:
{context}

## IMPORTANT:
- Do NOT make up information that is not in the context.
- Prefer the provided sources over general knowledge.
- If multiple sources discuss the same topic, synthesize them and cite all.
"""


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_title(chunk: dict, fallback: str | None = None) -> str | None:
    """
    Extract the best available title from a chunk dict.

    Priority: title → file_name → fallback.
    """
    return chunk.get("title") or chunk.get("file_name") or fallback


# ── Public API ───────────────────────────────────────────────────────────────


def build_prompt(
    question: str,
    retrieved_chunks: list[dict],
    conversation_history: list[dict] | None = None,
    max_history_messages: int = 10,
    system_prompt_template: str = SYSTEM_PROMPT_TEMPLATE,
) -> list[dict]:
    """
    Build a structured LLM prompt.

    Args:
        question: The user's current question.
        retrieved_chunks: Results from retrieval_service.search_similar_chunks().
        conversation_history: Previous messages in the chat.
            [{"role": "user"|"assistant", "content": "..."}, ...]
        max_history_messages: Max number of history messages to include.

    Returns:
        OpenAI-compatible message list ready for LLM.
    """
    # Build context string from retrieved chunks
    context = _build_context_string(retrieved_chunks)

    # System message with context injected
    system_content = system_prompt_template.format(context=context)
    messages = [{"role": "system", "content": system_content}]

    # Add conversation history (limited to most recent N messages)
    if conversation_history:
        recent = conversation_history[-max_history_messages:]
        for msg in recent:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

    # Add current question
    messages.append({"role": "user", "content": question})

    return messages


def _build_context_string(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a numbered context string.

    Limits output to MAX_CONTEXT_CHUNKS chunks, each truncated
    to MAX_CHUNK_CHARS characters, to control token usage.

    Example output:
    ---
    [Source 1] "Deep Learning in Medicine" by Smith, John (2020) — Page 15
    Content:
    Convolutional neural networks have shown remarkable performance...
    ---
    """
    if not chunks:
        return "(No relevant context found in uploaded papers.)"

    # Limit to top N chunks to prevent token explosion
    limited_chunks = chunks[:MAX_CONTEXT_CHUNKS]

    parts = []
    for i, chunk in enumerate(limited_chunks, 1):
        # Safe access with sensible fallbacks
        title = _get_title(chunk, fallback="Unknown document")
        author = chunk.get("author") or "Unknown author"
        year = chunk.get("year") or "n.d."
        page = chunk.get("page_number", "?")

        # Truncate oversized chunk content
        content = chunk.get("content", "")[:MAX_CHUNK_CHARS]

        # Build source label (no relevance score — saves tokens for the LLM)
        source_label = f'[Source {i}] "{title}" by {author} ({year}) — Page {page}'

        part = (
            f"---\n"
            f"{source_label}\n"
            f"Content:\n"
            f"{content}"
        )
        parts.append(part)

    return "\n".join(parts) + "\n---"


def get_source_summary(chunks: list[dict]) -> list[dict]:
    """
    Create a concise summary of sources used, for the API response.

    NOTE: Unlike _build_context_string (which uses "Unknown document" as
    final fallback), this function returns None when both title and
    file_name are missing — the API consumer decides how to display it.

    Returns:
        [
            {
                "source_number": 1,
                "title": "Deep Learning in Medicine",
                "author": "Smith, John",
                "year": "2020",
                "page_number": 15,
                "file_name": "deep_learning.pdf",
                "document_id": "a1b2c3d4-...",
                "chunk_id": "e5f6g7h8-...",
                "similarity": 0.87,
                "excerpt": "Convolutional neural networks have shown..."
            },
            ...
        ]
    """
    summaries = []
    for i, chunk in enumerate(chunks, 1):
        # Safe access — avoid KeyError on missing content
        content = chunk.get("content", "")
        excerpt = content[:200] + "..." if len(content) > 200 else content

        summaries.append({
            "source_number": i,
            "title": _get_title(chunk),  # Returns None if both title & file_name are None
            "author": chunk.get("author"),
            "year": chunk.get("year"),
            "page_number": chunk.get("page_number"),
            "file_name": chunk.get("file_name"),
            "document_id": chunk.get("document_id"),
            "chunk_id": chunk.get("chunk_id"),
            "similarity": chunk.get("similarity"),
            "excerpt": excerpt,
        })
    return summaries
