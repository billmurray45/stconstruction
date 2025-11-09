from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from .models import News


class NewsRepository:
    @staticmethod
    async def create_news(session: AsyncSession, news: News) -> News:
        session.add(news)
        await session.commit()
        await session.refresh(news)
        return news

    @staticmethod
    async def get_news_by_id(session: AsyncSession, news_id: int) -> Optional[News]:
        result = await session.execute(select(News).where(News.id == news_id))
        news = result.scalars().first()
        return news

    @staticmethod
    async def get_news_by_slug(session: AsyncSession, slug: str) -> Optional[News]:
        result = await session.execute(select(News).where(News.slug == slug))
        news = result.scalars().first()
        return news

    @staticmethod
    async def get_all_news(session: AsyncSession, published_only: bool = False) -> list[News]:
        query = select(News).order_by(News.created_at.desc())
        if published_only:
            query = query.where(News.is_published == True)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_news(session: AsyncSession, limit: int = 3, published_only: bool = True) -> list[News]:
        query = select(News).order_by(News.created_at.desc()).limit(limit)
        if published_only:
            query = query.where(News.is_published == True)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_news(session: AsyncSession, news: News) -> News:
        await session.commit()
        await session.refresh(news)
        return news

    @staticmethod
    async def delete_news(session: AsyncSession, news: News) -> None:
        await session.delete(news)
        await session.commit()
