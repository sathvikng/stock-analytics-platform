from .client import get_pool


async def run_migrations():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email         VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                display_name  VARCHAR(100),
                created_at    TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
                title      VARCHAR(255) DEFAULT 'New Chat',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id    UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
                role          VARCHAR(20) NOT NULL,
                content       TEXT NOT NULL,
                response_json JSONB,
                created_at    TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id, created_at)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id, updated_at DESC)"
        )
