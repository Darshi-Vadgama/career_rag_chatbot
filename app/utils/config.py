from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    mistral_api_key = os.getenv("MISTRAL_API_KEY")

    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION")

    embed_model = os.getenv(
        "EMBED_MODEL",
        "BAAI/bge-base-en-v1.5"
    )

    mistral_model = os.getenv(
        "MISTRAL_MODEL",
        "mistral-small-latest"
    )

settings = Settings()