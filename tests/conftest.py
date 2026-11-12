import asyncio
import os
import sys
from typing import AsyncGenerator

# Disable rate limiting for functional tests so it doesn't throttle rapid test runs
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.db.session import get_db
from app.main import app


pytest_plugins = ("pytest_asyncio",)


# Встановити політику event loop для Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


_test_engine: AsyncEngine | None = None
_session_maker = None


async def get_or_create_engine():
    """Отримати або створити тестовий engine."""
    global _test_engine, _session_maker
    
    if _test_engine is not None:
        return _test_engine, _session_maker
    
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "mysql+aiomysql://root@127.0.0.1:3307/gadget_zone_test",
    )
    
    _test_engine = create_async_engine(
        test_db_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        connect_args={
            "autocommit": False,
        },
    )
    
    _session_maker = async_sessionmaker(
        bind=_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Налаштування схеми
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    return _test_engine, _session_maker


@pytest.fixture(scope="session")
async def session_engine():
    """Сесійний engine для всіх тестів."""
    engine, session_maker = await get_or_create_engine()
    yield engine
    
    # Синхронно очистити при завершенні
    # Диспозувати усі з'єднання перед закриттям event loop
    if engine is not None:
        await engine.dispose()
        global _test_engine, _session_maker
        _test_engine = None
        _session_maker = None


@pytest.fixture
async def test_session(session_engine) -> AsyncGenerator[AsyncSession, None]:
    """Тестова сесія для кожного тесту."""
    engine, session_maker = await get_or_create_engine()
    session = session_maker()
    
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@pytest.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP клієнт для тестів."""
    app.dependency_overrides[get_db] = lambda: test_session
    
    try:
        transport = __import__("httpx").ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as ac:
            ac.app = app
            yield ac
    finally:
        app.dependency_overrides.clear()
