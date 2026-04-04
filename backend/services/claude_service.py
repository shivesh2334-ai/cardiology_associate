"""
AC Agent — Claude Service
All interactions with the Anthropic Claude API.
Single source of truth for AI calls.
"""

import json
import logging
from typing import Any

import anthropic
from fastapi import HTTPException

from config import settings

logger = logging.getLogger(__name__)

# Single client instance
_client = None

def get_claude_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=settings.CLAUDE_TIMEOUT_SECONDS,
        )
    return _client


async def call_claude_json(
    system_prompt: str,
    user_prompt: str,
    model: str = None,
    max_tokens: int = None,
    temperature: float = 0.2,  # Low temperature for clinical consistency
) -> tuple[dict[str, Any], str]:
    """
    Call Claude and return parsed JSON + model used.
    Raises HTTPException on failure.

    Returns: (parsed_dict, model_name)
    """
    model = model or settings.CLAUDE_SONNET_MODEL
    max_tokens = max_tokens or settings.CLAUDE_MAX_TOKENS

    client = get_claude_client()

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = response.content[0].text.strip()

        # Strip any accidental markdown fences
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1])

        parsed = json.loads(raw_text)
        return parsed, model

    except json.JSONDecodeError as e:
        logger.error(f"Claude returned non-JSON response: {e}")
        raise HTTPException(
            status_code=502,
            detail="AI service returned an unexpected format. Please retry."
        )
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=503, detail="Unable to reach AI service. Check connectivity.")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="AI service rate limit reached. Please wait and retry.")
    except anthropic.APIStatusError as e:
        logger.error(f"Claude API error {e.status_code}: {e.message}")
        raise HTTPException(status_code=502, detail=f"AI service error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected Claude error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected AI service error.")


async def call_claude_text(
    system_prompt: str,
    user_prompt: str,
    model: str = None,
    max_tokens: int = 1000,
) -> str:
    """Call Claude and return raw text response."""
    model = model or settings.CLAUDE_HAIKU_MODEL
    client = get_claude_client()
    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Claude text call error: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="AI service error.")
