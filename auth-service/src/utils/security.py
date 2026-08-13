import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    # 1. Pre-hash to a 64-character string using SHA-256
    pre_hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    # 2. Hash the result with bcrypt
    print(f"Pre-hashed password: {pre_hashed}")  # Debugging line
    print(f"Final hashed password: {pwd_context.hash(pre_hashed)}")  # Debugging line
    return pwd_context.hash(pre_hashed)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 1. Pre-hash the incoming password the exact same way
    pre_hashed = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    # 2. Verify against the database hash
    return pwd_context.verify(pre_hashed, hashed_password)