from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = "mysql+asyncmy://devuser:devpassword@localhost:3306/playground_db"

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Generate database session dependency
async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        

