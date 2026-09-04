"""Dev-time script: embeds every named entity in the dataset with
gemini-embedding-001 and writes data/embeddings.npz (committed to the repo).

Runtime code never calls this - it only embeds the incoming notice text and
compares against these precomputed vectors, keeping startup fast and the
per-request Gemini call count low.

Run: python data/build_index.py   (needs GEMINI_API_KEY in .env)
"""

import sqlite3
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

DB_PATH = Path(__file__).parent / "distributor.db"
OUT_PATH = Path(__file__).parent / "embeddings.npz"
DIM = 768


def collect_entities(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """Returns (entity_key, text_to_embed) pairs. entity_key = 'type:id'."""
    entities: list[tuple[str, str]] = []

    for row in conn.execute("SELECT id, name, location, category FROM suppliers"):
        text = f"{row[1]}, {row[2]}, supplies {row[3]}"
        entities.append((f"supplier:{row[0]}", text))

    for row in conn.execute("SELECT id, name, category, sku FROM products"):
        text = f"{row[1]}, {row[2]}, SKU {row[3]}"
        entities.append((f"product:{row[0]}", text))

    for row in conn.execute("SELECT id, name, location FROM customers"):
        text = f"{row[1]}, {row[2]}"
        entities.append((f"customer:{row[0]}", text))

    carriers = {r[0] for r in conn.execute("SELECT DISTINCT carrier FROM shipments")}
    for carrier in sorted(carriers):
        entities.append((f"carrier:{carrier}", carrier))

    return entities


def embed_all(client: genai.Client, texts: list[str]) -> np.ndarray:
    from google.genai import types

    vectors = []
    # Embed one at a time: dataset is small (~30 entities) and this keeps the
    # dev-time script simple; runtime code embeds only the single notice text.
    for text in texts:
        resp = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=DIM),
        )
        vectors.append(resp.embeddings[0].values)
    return np.array(vectors, dtype=np.float32)


def build():
    conn = sqlite3.connect(DB_PATH)
    entities = collect_entities(conn)
    conn.close()

    keys = [k for k, _ in entities]
    texts = [t for _, t in entities]

    client = genai.Client()
    vectors = embed_all(client, texts)

    np.savez(OUT_PATH, keys=np.array(keys), texts=np.array(texts), vectors=vectors)
    print(f"Embedded {len(keys)} entities -> {OUT_PATH} (dim={DIM})")


if __name__ == "__main__":
    build()
