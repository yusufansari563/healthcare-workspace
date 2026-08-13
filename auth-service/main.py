from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.database import get_session
from src.utils.security import get_password_hash, verify_password
from src.models.models import User, UserCreate, UserRead, UserLogin

app = FastAPI()

@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, 
    session: AsyncSession = Depends(get_session)
):
    # 1. Check if user already exists
    statement = select(User).where(User.email == user_in.email)
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    # 2. Hash the password
    hashed_pw = get_password_hash(user_in.password)
    print(f"Hashed password for {user_in.email}: {hashed_pw}")  # Debugging line
    # 3. Create the DB Model (Excluding the raw password, adding the hashed one)
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=user_in.password  # Store the hashed password
    )

    # 4. Save to Database
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user


@app.post("/auth/login")
async def login_user(
    user_in: UserLogin, 
    session: AsyncSession = Depends(get_session)
):
    # 1. Find user by email
    statement = select(User).where(User.email == user_in.email)
    result = await session.exec(statement)
    user = result.first()

    # 2. Verify existence and password
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. (Optional but expected in production) Generate a JWT token here
    # For now, we return a success message
    return {"message": "Login successful!", "user_id": user.id}