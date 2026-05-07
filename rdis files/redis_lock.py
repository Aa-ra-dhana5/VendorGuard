from __future__ import annotations

import hashlib
import redis.asyncio as redis
from sqlmodel.ext.asyncio.session import AsyncSession
import time

# Redis advisory locks for per-order serialization

# Redis connection (initialize once at app startup)
redis_client: redis.Redis | None = None

async def init_redis(redis_url: str = "redis://localhost:6379") -> None:
    global redis_client
    redis_client = await redis.from_url(redis_url)

async def close_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.close()

async def acquire_order_advisory_lock(order_id: str, timeout: int = 30) -> str:
    if not redis_client:
        raise RuntimeError("Redis client not initialized")
    
    lock_key = f"order:lock:{order_id}"
    lock_token = hashlib.sha256(f"{order_id}:{time.time()}".encode()).hexdigest()
    
    # SET NX = only set if key doesn't exist (atomic operation)
    acquired = await redis_client.set(
        lock_key, 
        lock_token, 
        ex=timeout,  # Expire after timeout seconds
        nx=True      # Only set if doesn't exist
    )
    
    if not acquired:
        raise RuntimeError(f"Could not acquire lock for order {order_id}")
    
    return lock_token

async def release_order_advisory_lock(order_id: str, lock_token: str) -> None:
    if not redis_client:
        return
    
    lock_key = f"order:lock:{order_id}"
    
    # Lua script ensures we only delete if we own the lock
    lua_script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """
    
    await redis_client.eval(lua_script, 1, lock_key, lock_token)