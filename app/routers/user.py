from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from database import get_session

from models.postgres_models import User
from utils.oauth import get_current_user

from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


@router.post("/upload-profile-picture/")
async def upload_profile_picture(
    file: UploadFile,
    db:Session=Depends(get_session),
    user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.uid == user.uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(status_code=400, detail="Invalid image type")
    
    user.profile_picture = await file.read()
    db.commit()
    db.refresh(user)
    
    return {"message": "Profile picture updated successfully"}