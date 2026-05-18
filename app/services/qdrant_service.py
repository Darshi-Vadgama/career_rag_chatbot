import os
import logging
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

QDRANT_URL        = os.getenv("QDRANT_URL")
QDRANT_API_KEY    = os.getenv("QDRANT_API_KEY")
COLLECTION        = os.getenv("QDRANT_COLLECTION")
SCORE_THRESHOLD   = 0.75  # only use docs with similarity > 75%

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Same embedding model you used when ingesting docs into Qdrant
# Make sure this matches what you used during ingestion!
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def search_docs(query: str, top_k: int = 5):
    """
    Search Qdrant for documents relevant to the query.
    Uses vector similarity search (not scroll).
    Only returns docs above SCORE_THRESHOLD to avoid irrelevant context.

    Args:
        query  : User's question
        top_k  : Max number of results to fetch

    Returns:
        List of ScoredPoint objects with .score and .payload
        Empty list if no relevant docs found
    """
    try:
        # Convert query to vector using same model used during ingestion
        query_vector = embedder.encode(query).tolist()

        results = client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=SCORE_THRESHOLD,  # filters out irrelevant docs
            with_payload=True,
        )

        if not results:
            logger.info(f"No relevant docs found for query: '{query}'")
            return []

        logger.info(f"Found {len(results)} relevant docs for query: '{query}'")
        for r in results:
            logger.debug(f"  score={r.score:.3f} | text={r.payload.get('text','')[:80]}")

        return results

    except Exception as e:
        logger.error(f"Qdrant search error: {e}")
        return []