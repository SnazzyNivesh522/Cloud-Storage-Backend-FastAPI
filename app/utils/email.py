from fastapi import Depends,status
from starlette.responses import JSONResponse

from models.schemas import EmailSchema
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig,MessageType
from config import GmailConfig

conf=ConnectionConfig(
    MAIL_USERNAME=GmailConfig.MAIL_USERNAME,
    MAIL_PASSWORD=GmailConfig.MAIL_PASSWORD,
    MAIL_FROM=GmailConfig.MAIL_FROM,
    MAIL_PORT=GmailConfig.MAIL_PORT,
    MAIL_SERVER=GmailConfig.MAIL_SERVER,
    MAIL_STARTTLS=GmailConfig.MAIL_TLS,
    MAIL_SSL_TLS=GmailConfig.MAIL_SSL,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER="templates"
    
)


async def send_confirmation_email(email:EmailSchema = Depends())->JSONResponse:
    try:
        template_body={
            "email": email.email,
            "otp": email.otp,
            "service_name": "Storage Service",
            "validity_minutes": email.expiration_time,
            "support_email": "niveshpritmani@gmail.com",
            "year": 2024,
        }
        
        message=MessageSchema(
            subject="Verify your email",
            recipients=[email.email],
            template_body=template_body,
            subtype=MessageType.html,        
        )
        fm=FastMail(conf)
        await fm.send_message(message,template_name="otp_verification_email.html")
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "email has been sent"})

    except Exception as e:
        print(str(e))
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": f"Error sending email: {str(e)}"})
    
async def send_thank_you_email(email:EmailSchema = Depends())->JSONResponse:
    try:
        template_body={
            "logo_url":"",
            "user_name":email.email,
            "company_name": "Storage Service",
            "support_email": "niveshpritmani@gmail.com",
            "year": 2024,
            "dashboard_url": "https://localhost:8000/",
        }
        
        message=MessageSchema(
            subject="Welcome to Storage Service!",
            recipients=[email.email],
            template_body=template_body,
            subtype=MessageType.html,        
        )
        fm=FastMail(conf)
        print(await fm.send_message(message,template_name="thank_you_email.html"))
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "email has been sent"})

    except Exception as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": f"Error sending email: {str(e)}"})
    
    
    
    