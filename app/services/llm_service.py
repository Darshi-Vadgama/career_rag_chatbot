import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "qwen2.5:7b"  


async def ask_llm_stream(prompt: str, temperature: float = 0.7, num_ctx: int = 4096):
    """
    Stream a response from Ollama LLM token by token.

    Args:
        prompt      : Full prompt string (already built by rag_pipeline.py)
        temperature : Creativity level (0.0 = deterministic, 1.0 = creative)
        num_ctx     : Context window size in tokens
    
    Yields:
        str: Individual response tokens as they arrive
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_ctx": num_ctx,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", OLLAMA_URL, json=payload) as response:

                # Check HTTP-level errors before streaming
                if response.status_code != 200:
                    logger.error(f"Ollama returned HTTP {response.status_code}")
                    yield f"\n[Error: Ollama returned HTTP {response.status_code}]"
                    return

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse line from Ollama: {line}")
                        continue

                    # Handle Ollama-level errors
                    if "error" in data:
                        logger.error(f"Ollama error: {data['error']}")
                        yield f"\n[LLM Error: {data['error']}]"
                        return

                    # Yield response token
                    if "response" in data:
                        yield data["response"]

                    # Stop cleanly when Ollama signals done
                    if data.get("done"):
                        logger.info("Ollama stream completed successfully.")
                        break

    except httpx.ConnectError:
        logger.error("Could not connect to Ollama. Is the container running?")
        yield "\n[Error: Could not connect to Ollama. Please check if the service is running.]"

    except httpx.ReadTimeout:
        logger.error("Ollama stream timed out.")
        yield "\n[Error: LLM response timed out. Please try again.]"

    except Exception as e:
        logger.exception(f"Unexpected error in ask_llm_stream: {e}")
        yield f"\n[Error: Unexpected error — {str(e)}]"