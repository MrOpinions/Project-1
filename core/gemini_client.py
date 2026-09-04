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
# high-demand 503s before the SDK's own backoff gave up.
#
# A single request touches up to 3 Gemini calls (extraction, one batched
# mention-embedding, narrative). Worst case per call here is
# timeout*attempts + backoff =~ 10s*2 + 0.5s =~ 20.5s; two essential calls
# (extraction, embedding) plus the narrative call's own tighter 8s/1-attempt
# budget (see report.py) totals ~49s worst case, leaving headroom under the
# 60s-per-request ceiling instead of eating it entirely on retries.
_RETRY_OPTIONS = {"attempts": 2, "initial_delay": 0.5, "max_delay": 1.5, "exp_base": 2.0}
_TIMEOUT_MS = 10_000


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
