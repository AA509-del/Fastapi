import os
import redis.asyncio as aioredis
import hashlib

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = aioredis.from_url(
    REDIS_URL,
    decode_responses=True
)

CACHE_TTL = 300  # 缓存5分钟，可自己改

# ======================
# 改造：支持 session_id + question 一起生成唯一 key
# ======================
def _make_key(session_id: str, question: str) -> str:
    # 同一个问题，不同 session → 缓存不互通
    key_str = f"{session_id}:{question}"
    return "rag:" + hashlib.md5(key_str.encode("utf-8")).hexdigest()

# 查缓存：需要 session_id
async def get_cached_answer(session_id: str, question: str) -> str | None:
    return await redis_client.get(_make_key(session_id, question))

# 写缓存：需要 session_id
async def set_cached_answer(session_id: str, question: str, answer: str) -> None:
    await redis_client.setex(_make_key(session_id, question), CACHE_TTL, answer)