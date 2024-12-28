from dotenv import dotenv_values

config = dotenv_values(".env")
class Config:
    SECRET_KEY=config['SECRET_KEY']
    ALGORITHM=config['ALGORITHM']
    ACCESS_TOKEN_EXPIRE_MINUTES=config['ACCESS_TOKEN_EXPIRE_MINUTES']
    MONGO_URI=config['MONGO_URI']
    DATABASE_NAME=config['DATABASE_NAME']
    FILE_STORAGE_PATH=config['FILE_STORAGE_PATH']
    
class GmailConfig:
    MAIL_USERNAME=config['MAIL_USERNAME']
    MAIL_FROM=config['MAIL_FROM']
    MAIL_PASSWORD=config['MAIL_PASSWORD']
    MAIL_SERVER=config['MAIL_SERVER']
    MAIL_PORT=config['MAIL_PORT']
    MAIL_TLS=config['MAIL_TLS']
    MAIL_SSL=config['MAIL_SSL']

class PostgresSQLConfig:
    DATABASE_URL=config['DATABASE_URL']
    
class CORSOrigins:
    FRONTEND_URL=config['FRONTEND_URL']
    

