from pydantic import BaseModel,EmailStr

from datetime import datetime

from uuid import UUID
class UserCreate(BaseModel):
    email:EmailStr
    password:str
    username:str

class Token(BaseModel):
    access_token:str
    token_type:str
    
class TokenData(BaseModel):
    email:EmailStr | None=None
    
class EmailSchema(BaseModel):
    email:EmailStr
    otp:str | None=None
    expiration_time:int | None=None
    
class UserSchema(UserCreate):
    is_verified:bool=False
    otp:str | None=None
    
class FileCreate(BaseModel):
    file_name:str
    file_size:int
    file_type:str
    file_path:str
    
class UserDetails(BaseModel):
    email:EmailStr
    username:str
    profileImage:str | None=None
    
class FileDetails(BaseModel):
    file_id:UUID
    file_name:str
    file_type:str
    updated_at:datetime
    
class TrashFileDetails(BaseModel):
    file_id:UUID
    file_name:str
    file_type:str
    trashed_at:datetime
    
class FolderDetails(BaseModel):
    folder_id:UUID
    folder_name:str
    parent_folder:UUID | None=None
    updated_at:datetime

class FullFolderDetails(FolderDetails):
    subfolders:list[FolderDetails]
    files:list[FileDetails]
    
class TrashFolderDetails(BaseModel):
    folder_id:UUID
    folder_name:str
    parent_folder:UUID | None=None
    trashed_at:datetime

class TrashFullFolderDetails(TrashFolderDetails):
    subfolders:list[TrashFolderDetails] | None=None
    files:list[TrashFileDetails] | None=None