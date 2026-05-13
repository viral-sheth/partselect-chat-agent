import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from config import get_settings
from functools import lru_cache

settings = get_settings()

_chroma_client = None
_embedding_model = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.embedding_model)
    return _embedding_model


def embed(texts):  # type: (list) -> list
    model = get_embedding_model()
    return model.encode(texts, normalize_embeddings=True).tolist()


def get_products_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="product_descriptions",
        metadata={"hnsw:space": "cosine"},
    )


def get_guides_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="installation_guides",
        metadata={"hnsw:space": "cosine"},
    )
