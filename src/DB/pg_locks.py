from __future__ import annotations

import hashlib

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

# PostgreSQL advisory locks for per-order serialization (no Redis required)

def _is_postgres(session: AsyncSession) -> bool:
    bind = session.get_bind()
    return getattr(bind.dialect, "name", None) == "postgresql"


async def acquire_order_advisory_xact_lock(session: AsyncSession, order_id: str) -> None:
    if not _is_postgres(session):
        return
    h = hashlib.sha256(order_id.encode("utf-8")).digest()
    k1 = int.from_bytes(h[0:4], "big") & 0x7FFFFFFF
    k2 = int.from_bytes(h[4:8], "big") & 0x7FFFFFFF
    await session.exec(
        text("SELECT pg_advisory_xact_lock(CAST(:k1 AS int), CAST(:k2 AS int))").bindparams(k1=k1, k2=k2)
    )
