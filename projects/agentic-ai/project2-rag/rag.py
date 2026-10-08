import glob
import os

import numpy as np
import voyageai

EMBED_MODEL = "voyage-3.5"
CHUNK_SIZE = 800      # characters per chunk
CHUNK_OVERLAP = 100   # characters shared between neighbouring chunks
BATCH_SIZE = 128      # max texts per Voyage request

vo = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])


def chunk_text(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


class VectorIndex:
    def __init__(self):
        self.chunks: list[dict] = []
        self.vectors: np.ndarray | None = None

    def build(self, docs_dir: str) -> None:
        paths = sorted(glob.glob(f"{docs_dir}/*.md") + glob.glob(f"{docs_dir}/*.txt"))
        for path in paths:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for chunk in chunk_text(text):
                self.chunks.append({"source": os.path.basename(path), "text": chunk})

        if not self.chunks:
            raise RuntimeError(f"No .md or .txt documents found in {docs_dir}/")

        texts = [c["text"] for c in self.chunks]
        vectors = []
        for i in range(0, len(texts), BATCH_SIZE):
            result = vo.embed(texts[i:i + BATCH_SIZE], model=EMBED_MODEL, input_type="document")
            vectors.extend(result.embeddings)
        self.vectors = np.array(vectors)

    def search(self, query: str, k: int = 3) -> list[dict]:
        q = vo.embed([query], model=EMBED_MODEL, input_type="query").embeddings[0]
        scores = self.vectors @ np.array(q)   # Voyage vectors are normalized: dot product = cosine
        top = np.argsort(scores)[::-1][:k]
        return [{**self.chunks[i], "score": float(scores[i])} for i in top]


index = VectorIndex()
