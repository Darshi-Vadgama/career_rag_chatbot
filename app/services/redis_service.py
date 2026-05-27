import redis

r = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)

def get_cache(question: str):
    return r.get(f"cache:{question}")

def set_cache(question: str, answer: str):
    r.setex(
        f"cache:{question}",
        3600,  
        answer
    )

def save_memory(session_id: str, message: str):
    key = f"memory:{session_id}"
    r.rpush(key, message)
    r.ltrim(key, -20, -1)           
    r.expire(key, 60 * 60 * 24 * 7) 

def get_memory(session_id: str):
    key = f"memory:{session_id}"
    return r.lrange(key, 0, -1)

def delete_memory(session_id: str):
    r.delete(f"memory:{session_id}")

def get_last_n_messages(session_id: str, n: int = 6):
    """
    Returns last N messages as a formatted string for prompt injection.
    Skips empty messages.
    """
    messages = get_memory(session_id)
    last = messages[-n:] if len(messages) > n else messages
    return "\n".join([m for m in last if m.strip()])