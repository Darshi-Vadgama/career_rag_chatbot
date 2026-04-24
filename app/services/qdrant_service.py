from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from app.utils.config import settings

client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key
)

model = SentenceTransformer(settings.embed_model)

def search_docs(query, limit=3):
    vector = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    results = client.query_points(
        collection_name=settings.collection,
        query=vector,
        limit=limit
    ).points

    return results