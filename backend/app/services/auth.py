import os
import bcrypt
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
_ALGO = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_jwt(user_id: str) -> str:
    exp = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({"sub": user_id, "exp": exp}, _SECRET, algorithm=_ALGO)


def decode_jwt(token: str) -> str:
    payload = jwt.decode(token, _SECRET, algorithms=[_ALGO])
    return payload["sub"]
