"""Single shared Gemini client + model name, read once from env."""

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

GENERATION_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client()
    return _client
