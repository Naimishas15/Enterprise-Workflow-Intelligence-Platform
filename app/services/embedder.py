from sentence_transformers import SentenceTransformer
from app.config import settings

_model = None

def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def embed(text: str) -> list[float]:
    model = get_embedder()
    return model.encode(text).tolist()