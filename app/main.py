from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from routers import auth,file,folder,user

from database import create_db_and_tables

import os

from config import CORSOrigins

UPLOAD_FOLDER="UPLOADS"

origins=[CORSOrigins.FRONTEND_URL]

def create_app():
    app=FastAPI(
        openapi_prefix="/api"
    )
    app.include_router(auth.router)
    app.include_router(file.router)
    app.include_router(folder.router)
    app.include_router(user.router)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    create_db_and_tables()
    
    os.makedirs(UPLOAD_FOLDER,exist_ok=True)
    return app
app=create_app()

@app.get("/")
async def root():
    return {"message": "Hello World"}
