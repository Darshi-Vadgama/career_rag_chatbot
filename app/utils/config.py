import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION")

    embed_model = os.getenv("EMBED_MODEL")

    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "Qwen2.5:7B")

settings = Settings()