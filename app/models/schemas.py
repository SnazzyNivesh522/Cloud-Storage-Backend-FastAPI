from pydantic import BaseModel,EmailStr

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
    file_id:str
    file_name:str
    file_type:str
    updated_at:str
    
class TrashFileDetails(BaseModel):
    file_id:str
    file_name:str
    file_type:str
    trashed_at:str
    
class FolderDetails(BaseModel):
    folder_id:str
    folder_name:str
    parent_folder_id:str | None=None
    updated_at:str

class FullFolderDetails(FolderDetails):
    subfolders:list[FolderDetails]
    files:list[FileDetails]
    
class TrashFolderDetails(BaseModel):
    folder_id:str
    folder_name:str
    parent_folder_id:str | None=None
    trashed_at:str

class TrashFullFolderDetails(TrashFolderDetails):
    subfolders:list[TrashFolderDetails] | None=None
    files:list[TrashFileDetails] | None=None