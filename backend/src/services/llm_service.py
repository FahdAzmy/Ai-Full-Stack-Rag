"""
LLM Service — Generate answers using any OpenAI-compatible API.

Supports both complete (blocking) and streaming responses.
Uses AsyncOpenAI to avoid blocking the FastAPI event loop.

Provider-agnostic: set LLM_API_KEY + LLM_BASE_URL in .env to use
any OpenAI-compatible provider (OpenAI, Gemini, DeepSeek, Groq, etc.).
Falls back to OPENROUTER_API_KEY + OPENROUTER_BASE_URL if not set.
"""

from openai import AsyncOpenAI
from src.helpers.config import settings
from src.helpers.logging_config import get_logger

logger = get_logger("llm")

client = AsyncOpenAI(
    api_key=settings.get_llm_api_key(),
    base_url=settings.get_llm_base_url(),
)


async def generate_answer(messages: list[dict]) -> str:
    """
    Generate a complete answer from the LLM.

    Args:
        messages: OpenAI-compatible message list from context_builder.

    Returns:
        The assistant's response text.

    Raises:
        Exception: If the API call fails.
    """
    logger.info("Calling LLM (%s) with %d messages", settings.LLM_MODEL, len(messages))

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            top_p=0.9,
        )

        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else "N/A"
        logger.info("LLM response generated (%s tokens)", tokens_used)

        return answer

    except Exception as e:
        logger.error("LLM API error: %s", str(e))
        raise


async def generate_answer_stream(messages: list[dict]):
    """
    Generate a streaming answer (for Server-Sent Events).

    Yields:
        Chunks of text as they arrive from the LLM.
    """
    logger.info("Calling LLM (%s) with streaming", settings.LLM_MODEL)

    try:
        stream = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            top_p=0.9,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        logger.error("LLM streaming error: %s", str(e))
        raise


async def generate_chat_title(question: str) -> str:
    """
    Auto-generate a short chat title from the first question.

    Returns:
        A 3-6 word title summarizing the question.
    """
    response = await client.chat.completions.create(
        model=settings.LLM_TITLE_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Generate a short title (3-6 words) for a research chat "
                           "based on the user's first question. Return ONLY the title, "
                           "nothing else.",
            },
            {"role": "user", "content": question},
        ],
        temperature=0.5,
        max_tokens=20,
    )
    return response.choices[0].message.content.strip().strip('"')
