from fastapi import APIRouter, HTTPException, status, Depends
from fastapi import UploadFile

from typing import Annotated,Optional

from fastapi.responses import FileResponse

from models.postgres_models import FileMetadata,User,Folder

from utils.oauth import get_current_user

from database import get_session
from sqlalchemy.orm import Session

from uuid import UUID

from datetime import datetime
router=APIRouter(
    prefix="/folder",
    tags=["folder"],
    responses={404: {"description": "Not found"}},
)
UPLOAD_FOLDER="UPLOADS"
@router.get("/")
async def get_user_folders(db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    folders=db.query(Folder).filter(Folder.user_id==user.uid).filter(Folder.is_trashed==False).all()
    return folders

@router.get("/{folder_id}")
async def get_folder(folder_id:UUID,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    folder=db.query(Folder).filter(Folder.folder_id==folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Folder not found")
    return folder

@router.get("/trash/folders")
async def get_trashed_folders(db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    folders=db.query(Folder).filter(Folder.user_id==user.uid).filter(Folder.is_trashed==True).all()
    return folders

@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_folder(folder_name:str,parent_folder:Optional[UUID]=None,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    folder=Folder(folder_name=folder_name,parent_folder=parent_folder,user_id=user.uid)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder

@router.put("/rename/{folder_id}")
async def rename_folder(folder_id:UUID,folder_name:str,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    folder=db.query(Folder).filter(Folder.folder_id==folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Folder not found")
    folder.folder_name=folder_name
    folder.update_timestamp()
    db.commit()
    return {"message":"Folder renamed successfully"}

#move folders and its contents to trash
@router.delete("/delete/{folder_id}")
async def delete_folder(folder_id:UUID,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    folder=db.query(Folder).filter(Folder.folder_id==folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Folder not found")
    files=db.query(FileMetadata).filter(FileMetadata.folder_id==folder_id).all()
    for file in files:
        file.is_trashed=True
        file.trashed_at=datetime.now()
        db.commit()
        # db.delete(file)
    subfolders=db.query(Folder).filter(Folder.parent_folder==folder_id).all()
    for subfolder in subfolders:
        await delete_folder(subfolder.folder_id,db,user)
    folder.is_trashed=True
    folder.trashed_at=datetime.now()
    # db.delete(folder)
    db.commit()
    return {"message": "Folder and its contents deleted successfully"}

@router.put("/move/{folder_id}")
async def move_folder(folder_id:UUID,parent_folder:UUID,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    folder=db.query(Folder).filter(Folder.folder_id==folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Folder not found")
    folder.parent_folder=parent_folder
    folder.update_timestamp()
    db.commit()
    return {"message":"Folder moved successfully"}



