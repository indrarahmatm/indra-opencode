import bcrypt
from database import get_user_by_username

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def login(username: str, password: str) -> bool:
    user = get_user_by_username(username)
    if user and verify_password(password, user.password_hash):
        return True
    return False