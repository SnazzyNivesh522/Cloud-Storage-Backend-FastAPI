from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from .jwttoken import decode_access_token

from database import get_session

from models.postgres_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_session)):
    credentials_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})
    email= decode_access_token(token,credentials_exception)
    user=db.query(User).filter(User.email==email).first()
    if user is None:
        raise credentials_exception
    return user