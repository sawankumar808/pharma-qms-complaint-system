import os
import json
import re
import httpx
from dotenv import load_dotenv, find_dotenv
from groq import Groq
from app.core.config import get_settings

load_dotenv(find_dotenv(), override=True)

settings = get_settings()

_client: Groq | None = None

def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = (os.getenv("GROQ_API_KEY") or getattr(settings, "groq_api_key", "") or "").strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing! Check backend/.env file.")
        custom_http_client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=15.0),
            verify=False,
            trust_env=False
        )

        _client = Groq(
            api_key=api_key,
            http_client=custom_http_client
        )
    return _client


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass

    return {}


def call_llm_json(system_prompt: str, user_prompt: str, model: str | None = None) -> dict:
    client = get_client()
    response = client.chat.completions.create(
        model=model or settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return _extract_json(content)


def call_llm_text(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=model or settings.groq_context_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=512,
    )
    return (response.choices[0].message.content or "").strip()