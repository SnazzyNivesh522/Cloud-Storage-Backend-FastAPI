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