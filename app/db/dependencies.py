from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.lifetime import session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create and get database session.
    :param request: current request.
    :yield: database session.
    """
    session: AsyncSession = session_factory()

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
    finally:
        await session.close()
