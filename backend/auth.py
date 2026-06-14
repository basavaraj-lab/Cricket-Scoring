from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    payload = {
        "sub": str(data),
        "exp": datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
