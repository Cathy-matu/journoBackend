from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

engine_args = {
    "echo": False,
}

if not DATABASE_URL.startswith("sqlite"):
    engine_args.update({
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10
    })

engine = create_async_engine(DATABASE_URL, **engine_args)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
