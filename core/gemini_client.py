"""Single shared Gemini client + model name, read once from env."""

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

GENERATION_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768

_client: genai.Client | None = None

# Default SDK retry (5 attempts, up to 60s max delay) can alone exceed the
# hackathon's 60s-per-request budget on a transient 503 - observed directly
# during development, where flash-lite intermittently took 90s+ under
# high-demand 503s before the SDK's own backoff gave up. Tightened globally,
# and the narrative call (the one non-essential Gemini call in the pipeline)
# uses an even tighter per-call override with a fallback - see report.py.
_RETRY_OPTIONS = {"attempts": 2, "initial_delay": 1.0, "max_delay": 3.0, "exp_base": 2.0}
_TIMEOUT_MS = 15_000


def get_client() -> genai.Client:
    global _client
    if _client is None:
        from google.genai import types

        _client = genai.Client(
            http_options=types.HttpOptions(
                timeout=_TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(**_RETRY_OPTIONS),
            )
        )
    return _client
