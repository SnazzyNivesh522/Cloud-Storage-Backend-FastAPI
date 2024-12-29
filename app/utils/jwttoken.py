from jose import jwt,JWTError
from datetime import datetime, timedelta,timezone
from fastapi import HTTPException,status
from config import Config
from models.schemas import TokenData

SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = float(Config.ACCESS_TOKEN_EXPIRE_MINUTES)

IST=timezone(timedelta(hours=5,minutes=30))


def create_access_token(data: dict, expire_minutes: float | None =ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode=data.copy()
    expires=datetime.now(tz=IST)+timedelta(minutes=expire_minutes)
    to_encode.update({"exp":expires})
    encoded_jwt=jwt.encode(to_encode,Config.SECRET_KEY,algorithm=Config.ALGORITHM)
    return encoded_jwt

def decode_access_token(token:str,credentials_exception)->str:
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            credentials_exception
        token_data=TokenData(email=email)
        return email
    except JWTError:
        credentials_exception
