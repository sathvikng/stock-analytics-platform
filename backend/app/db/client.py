import asyncpg
import json
import os
from dotenv import load_dotenv

load_dotenv()

_pool: asyncpg.Pool | None = None


async def _init_conn(conn):
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
    await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            os.getenv("SUPABASE_DB_URL"), min_size=2, max_size=10, ssl="require", init=_init_conn
        )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
