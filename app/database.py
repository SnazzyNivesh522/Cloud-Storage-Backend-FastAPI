from motor.motor_asyncio import AsyncIOMotorClient
from config import Config


client=AsyncIOMotorClient(Config.MONGO_URI)
db=client[Config.DATABASE_NAME]

users_collection=db["users"]
files_collection=db["files"]
shares_collection=db["shares"]

from config import PostgresSQLConfig
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel,create_engine,Session

DATABASE_URL = PostgresSQLConfig.DATABASE_URL

engine = create_engine(DATABASE_URL,echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
'''
#use when using sqlalchmey models
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base() 
'''
def create_db_and_tables():
    print("Creating tables")
    SQLModel.metadata.create_all(engine)
    print("Tables created")
# def get_db():
#     pg_db = SessionLocal()
#     try:
#         yield pg_db
#     finally:
#         pg_db.close()
def get_session():
    with Session(engine) as session:
        yield session
