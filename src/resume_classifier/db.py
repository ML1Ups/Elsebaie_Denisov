import asyncpg

from resume_classifier.config import Settings


async def create_pool(settings: Settings) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        database=settings.postgres_db,
        min_size=0,
        max_size=settings.postgres_pool_max_size,
    )


async def fetch_postgres_version(pool: asyncpg.Pool) -> str:
    async with pool.acquire() as connection:
        return await connection.fetchval("SHOW server_version")
