from typing import Optional
import datetime

from sqlalchemy import Column, Index, String, TIMESTAMP, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlmodel import Field, SQLModel

# 1. THE BASE: Shared user fields
class UserBase(SQLModel):
    email: str = Field(max_length=255)
    full_name: str = Field(max_length=100)

# 2. CREATE DTO: What the client sends when registering
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)
    
# 3. LOGIN DTO: What the client sends to log in
class UserLogin(SQLModel):
    email: str
    password: str

# 4. READ DTO: What we return (NEVER include the password here)
class UserRead(UserBase):
    id: int
    created_at: Optional[datetime.datetime]

# 5. DATABASE MODEL: What is actually saved in MySQL
class User(UserBase, table=True):
    __table_args__ = (
        Index('email', 'email', unique=True),
    )
    
    id: int = Field(sa_column=Column('id', BIGINT(unsigned=True), primary_key=True, autoincrement=True))
    email: str = Field(sa_column=Column('email', String(255), nullable=False))
    full_name: str = Field(sa_column=Column('full_name', String(100), nullable=False))
    
    # NEW: We add a hashed_password column to the database
    hashed_password: str = Field(sa_column=Column('hashed_password', String(255), nullable=False))
    
    created_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column('created_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')))
