from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from database import get_session
from models.schemas import UserCreate, Token, EmailSchema, UserDetails
from models.postgres_models import User
from base64 import b64encode

from utils.hashing import get_password_hash, verify_password
from utils.otp import generate_otp, validate_otp
from utils.jwttoken import create_access_token, decode_access_token
from utils.email import send_confirmation_email, send_thank_you_email

from sqlalchemy.orm import Session
import uuid

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register")
async def register_user(user: UserCreate, db: Session = Depends(get_session)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        if existing_user.is_verified:
            return {"message": "Email already registered"}
        else:
            return {"message": "Registered but not verified"}

    hashed_password = get_password_hash(user.password)
    otp = generate_otp()
    user_doc = User(
        uid=str(uuid.uuid4()),
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        otp=otp,
    )
    print(f"OTP for {user.email} is {otp}")
    db.add(user_doc)
    db.commit()
    db.refresh(user_doc)

    email_payload = EmailSchema(email=user.email, otp=otp, expiration_time=5)
    # Send email
    email_response = await send_confirmation_email(email_payload)
    if email_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending email, code: {email_response.status_code}",
        )

    return {"message": "User registered successfully. Verify with OTP sent to your email"}


@router.post("/verify-otp")
async def verify_otp(email: str, otp: str, db: Session = Depends(get_session)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not validate_otp(user.otp, otp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
    user.is_verified = True
    user.otp = None
    db.commit()

    email_payload = EmailSchema(email=email)
    email_response = await send_thank_you_email(email_payload)
    if email_response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending email, code: {email_response.status_code}",
        )

    return {"message": "Account verified successfully"}


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password")
    if not user.is_verified:
        return {"message": "Account not verified"}
    access_token = create_access_token(data={"sub": user.email})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me")
async def read_user(request:Request, db: Session = Depends(get_session)):
    authorization = request.headers.get("Authorization")
    print("authorization", authorization)
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized! Authorization header missing"
        )
    try:
        token_type, token = authorization.split(" ")
        print(token_type, token)
        if token_type.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Unauthorized! Invalid token type"
            )
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        email = decode_access_token(token, credentials_exception)
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception

        profile_image = (
            b64encode(user.profile_picture).decode('utf-8') if user.profile_picture else None
        )
        return UserDetails(
            email=user.email,
            username=user.username,
            profileImage=profile_image
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized! Invalid token"
        )
