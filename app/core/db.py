from collections.abc import AsyncGenerator

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def get_asyncpg_url(database_url: str) -> URL:
    """Translate libpq's ``sslmode`` query option for asyncpg."""
    url = make_url(database_url)
    sslmode = url.query.get("sslmode")

    if sslmode is None:
        return url

    url = url.difference_update_query(["sslmode"])
    if "ssl" not in url.query:
        url = url.update_query_dict({"ssl": sslmode})

    return url


engine = create_async_engine(get_asyncpg_url(settings.database_url), echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
