from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, ChatSession, Message

async def get_or_create_user(db: AsyncSession, anonymous_id: str):
    # Simple implementation - can be expanded
    return {"id": 1, "anonymous_id": anonymous_id}