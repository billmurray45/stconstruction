from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import NewsCreate, NewsUpdate
from .models import News
from .repository import NewsRepository


async def create_news(session: AsyncSession, news_data: NewsCreate) -> News:
    if await NewsRepository.get_news_by_slug(session, news_data.slug):
        raise HTTPException(409, "Новость с таким slug уже существует")

    news = News(
        title=news_data.title,
        slug=news_data.slug,
        description=news_data.description,
        content=news_data.content,
        image_path=news_data.image_path,
        is_published=news_data.is_published,
    )

    return await NewsRepository.create_news(session, news)


async def get_news_by_id(session: AsyncSession, news_id: int) -> News:
    news = await NewsRepository.get_news_by_id(session, news_id)
    if not news:
        raise HTTPException(404, "Новость не найдена")
    return news


async def get_news_by_slug(session: AsyncSession, slug: str) -> News:
    news = await NewsRepository.get_news_by_slug(session, slug)
    if not news:
        raise HTTPException(404, "Новость не найдена")
    return news


async def get_all_news(session: AsyncSession, published_only: bool = False) -> list[News]:
    return await NewsRepository.get_all_news(session, published_only)


async def get_latest_news(session: AsyncSession, limit: int = 3) -> list[News]:
    """Получить последние N новостей для главной страницы"""
    return await NewsRepository.get_latest_news(session, limit=limit, published_only=True)


async def update_news_service(session: AsyncSession, news_id: int, news_data: NewsUpdate) -> News:
    news = await NewsRepository.get_news_by_id(session, news_id)

    if not news:
        raise HTTPException(404, "Новость не найдена")

    news_data_dict = news_data.model_dump(exclude_unset=True)

    if "slug" in news_data_dict and news_data_dict["slug"] != news.slug:
        existing_news = await NewsRepository.get_news_by_slug(session, news_data_dict["slug"])
        if existing_news:
            raise HTTPException(409, "Новость с таким slug уже существует")

    for field, value in news_data_dict.items():
        setattr(news, field, value)

    return await NewsRepository.update_news(session, news)


async def delete_news_service(session: AsyncSession, news_id: int) -> None:
    news = await NewsRepository.get_news_by_id(session, news_id)

    if not news:
        raise HTTPException(404, "Новость не найдена")

    await NewsRepository.delete_news(session, news)
