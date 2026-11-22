
from sentence_transformers import SentenceTransformer

EMBEDDING_DIM = 768

# Load the local embedding model
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")


def generate_embedding(text):
    """
    Generate a 768-dimensional embedding locally.
    No API key or billing required.
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()
