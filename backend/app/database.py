from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"statement_cache_size": 0},  # Required for Supabase Supavisor pooler
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Add columns that may be missing on existing tables (no-op if already present)
    _connector_columns = [
        ("auth_method", "VARCHAR(20) NOT NULL DEFAULT 'credential'"),
        ("connection_status", "VARCHAR(20) NOT NULL DEFAULT 'connected'"),
        ("status_message", "VARCHAR(500)"),
        ("external_account_id", "VARCHAR(255)"),
        ("external_account_name", "VARCHAR(255)"),
        ("token_expires_at", "TIMESTAMP"),
        ("last_health_check_at", "TIMESTAMP"),
    ]
    async with engine.begin() as conn:
        for col_name, col_def in _connector_columns:
            try:
                await conn.execute(
                    text(f"ALTER TABLE connectors ADD COLUMN IF NOT EXISTS {col_name} {col_def}")
                )
            except Exception:
                pass  # column already exists or DB doesn't support IF NOT EXISTS
