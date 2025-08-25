import base64
from typing import Optional
from flask import current_app
from openai import OpenAI

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = current_app.config.get("OPENAI_API_KEY", "")
        _client = OpenAI(api_key=api_key)
    return _client


def b64(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode("utf-8")
