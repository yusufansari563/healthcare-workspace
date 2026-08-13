from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.models.models import Appointment, AppointmentCreate, AppointmentRead, User, UserCreate, UserRead, UserLogin
from src.config.database import get_session, engine # Make sure to import 'engine'
from src.config.admin import setup_admin # Import the setup function
from src.utils.security import get_password_hash, verify_password


app = FastAPI()

# Initialize the admin panel and attach it to this app instance
setup_admin(app, engine)

@app.get('/')
async def ping():
    return {'message': "pong"}

@app.post('/appointments', response_model=AppointmentRead)
async def create_appointment(
    appointment_in: AppointmentCreate, # 1. Validate incoming JSON
    session: AsyncSession = Depends(get_session)
):
    # 2. Convert the valid DTO into a database object
    appointment = Appointment.model_validate(appointment_in) 
    
    # 3. Save to the database
    session.add(appointment)
    await session.commit()
    await session.refresh(appointment)
    
    # 4. FastAPI will automatically convert 'appointment' to 'AppointmentRead' before returning
    return appointment

@app.get('/appointments', response_model=List[AppointmentRead])
async def get_all_appointments(
    session: AsyncSession = Depends(get_session)
):
    """
    retreive a list of appointment
    """
    statement = select(Appointment)
    result = await session.exec(statement)
    appts = result.all()
    return appts

@app.get('/appointments', response_model=List[AppointmentRead])
async def get_all_appointments(
    session: AsyncSession = Depends(get_session)
):
    """
    retreive a list of appointment
    """
    statement = select(Appointment)
    result = await session.exec(statement)
    appts = result.all()
    return appts

@app.get('/appointments/{appointment_id}', response_model=AppointmentRead)
async def get_appointment_by_id(
    appointment_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    get a appointment by id
    """
    appointment = await session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="appointment not found")
    
    return appointment

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
        hashed_password=hashed_pw
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