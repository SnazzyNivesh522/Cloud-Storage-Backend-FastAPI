import shutil
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi import UploadFile

from typing import Annotated

from fastapi.responses import FileResponse

from models.postgres_models import FileMetadata,User,Folder

from utils.oauth import get_current_user

from database import get_session
from sqlalchemy.orm import Session

from uuid import UUID

import os
from datetime import datetime, timedelta

router=APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not found"}},
)
UPLOAD_FOLDER="./UPLOADS"
TRASH_FOLDER = "TRASH"
TRASH_RETENTION_MINUTES = 30

@router.get("/")
async def get_user_files(db:Session=Depends(get_session),user:User=Depends(get_current_user)):    
    files=db.query(FileMetadata).filter(FileMetadata.user_id==user.uid).all()
    return files

@router.get("/{file_id}")
async def get_file(file_id:str,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    file=db.query(FileMetadata).filter(FileMetadata.file_id==file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File not found")
    return file

@router.post("/upload/{folder_id}",status_code=status.HTTP_201_CREATED)
async def upload_files(folder_id:UUID,files:list[UploadFile],db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    folder = db.query(Folder).filter(Folder.folder_id == folder_id, Folder.user_id == user.uid).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    file_metadata_list=[]
    for file in files:
        file_path=f"{UPLOAD_FOLDER}/{user.uid}/{str(folder.folder_id)}/{file.filename}"
        os.makedirs(os.path.dirname(file_path),exist_ok=True)
        with open(file_path,"wb") as f:
            f.write(await file.read())
        file_metadata=FileMetadata(
            file_name=file.filename,
            file_size=os.path.getsize(file_path),
            file_type=file.content_type,
            storage_location=file_path,
            user_id=user.uid,
            folder_id=folder_id
        )
        file_metadata_list.append(file_metadata)
    
    db.add_all(file_metadata_list)
    db.commit()
    for file_metadata in file_metadata_list:
        db.refresh(file_metadata)
    return {"files":file_metadata_list}
@router.put("/rename/{file_id}")
async def rename_file(file_id:UUID,file_name:str,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    file=db.query(FileMetadata).filter(FileMetadata.file_id==file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File not found")
    file.file_name=file_name
    file.update_timestamp()
    db.commit()
    return  {"message": "File renamed successfully"}

@router.delete("/delete/{file_id}")
async def delete_file(file_id:UUID,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    file=db.query(FileMetadata).filter(FileMetadata.file_id==file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File not found")
    file.is_trashed = True
    file.trashed_at = datetime.utcnow()
    db.commit()
    return {"message":"File moved to trash successfully"}

@router.put("/move/{file_id}")
async def move_file(file_id:UUID,folder_id:UUID,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    file=db.query(FileMetadata).filter(FileMetadata.file_id==file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File not found")
    folder=db.query(Folder).filter(Folder.folder_id==folder_id).first()
    if not folder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Folder not found")
    file.folder_id=folder_id
    folder.update_timestamp()
    db.commit()
    return {"message":"File moved successfully"}

@router.get("/download/{file_id}")
async def download_file(file_id:UUID,db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    file=db.query(FileMetadata).filter(FileMetadata.file_id==file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="File not found")
    return FileResponse(file.storage_location,filename=file.file_name)

@router.get("/trash/files")
async def show_trash(db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    trashed_files = db.query(FileMetadata).filter(FileMetadata.is_trashed == True,FileMetadata.user_id==user.uid).all()
    return trashed_files

#empty trash
@router.delete("/trash/empty")
async def empty_trash(db:Session=Depends(get_session),user:User=Depends(get_current_user)):
    folders=db.query(Folder).filter(Folder.user_id==user.uid).filter(Folder.is_trashed==True).all()
    files=db.query(FileMetadata).filter(FileMetadata.user_id==user.uid).filter(FileMetadata.is_trashed==True).all()
    if not folders and not files:
        return {"message":"Trash is already empty"}
    
    for file in files:
        os.remove(file.storage_location)
        db.delete(file)
        db.commit()
        
    for folder in folders:
        try:
            from scripts.delete_folder_recursive import delete_folder_recursive
            delete_folder_recursive(f"{UPLOAD_FOLDER}/{user.uid}",folder.folder_id)
        except FileNotFoundError:
            pass
        db.delete(folder)
        db.commit()
            
    return {"message":"Trash emptied successfully"}

