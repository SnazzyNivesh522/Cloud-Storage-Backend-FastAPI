# FastAPI Application

This is a FastAPI application that provides user authentication and email verification functionalities.

## Project Structure

```
├── app
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── postgres_models.py
│   │   └── schemas.py
│   ├── routers
│   │   ├── auth.py
│   │   ├── file.py
│   │   ├── folder.py
│   │   ├── __init__.py
│   ├── templates
│   │   ├── otp_verification_email.html
│   │   └── thank_you_email.html
│   ├── UPLOADS
│   └── utils
│       ├── email.py
│       ├── hashing.py
│       ├── __init__.py
│       ├── jwt.py
│       ├── oauth.py
│       ├── otp.py
├── db
│   ├── data
│   ├── docker-compose.yml
│   └── README.md
├── README.md
└── requirements.txt
```

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd app
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the `app` directory with the following content:

```env
SECRET_KEY="your_secret_key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
MONGO_URI="mongodb://localhost:27017"
DATABASE_NAME="your_database_name"
FILE_STORAGE_PATH="app/uploads"
MAIL_USERNAME="your_email@example.com"
MAIL_FROM="your_email@example.com"
MAIL_PASSWORD="your_email_password"
MAIL_PORT=587
MAIL_SERVER="smtp.gmail.com"
MAIL_TLS=True
MAIL_SSL=False
```

## Running the Application

You can run your FastAPI application using `uvicorn` directly from the command line:

```bash
cd app
uvicorn main:app --reload
```

## API Endpoints

### Authentication

- **Register User**: `POST /auth/register`
- **Verify OTP**: `POST /auth/verify-otp`
- **Login**: `POST /auth/token`

### Email

- **Send Email**: `POST /email/send`

## Configuration

The application uses environment variables for configuration. These variables are defined in the `.env` file and loaded using `dotenv`.

## Database

The application uses MongoDB as the database. The connection is established using `motor` (an async MongoDB driver).

## Templates

The application uses Jinja2 templates for email content. The template for OTP verification email is located in the `templates` directory.

## Utils

- **Hashing**: Password hashing and verification using `passlib`.
- **JWT**: Functions for creating and decoding JWT tokens.
- **OAuth**: OAuth2 password bearer token dependency.
- **OTP**: Functions for generating and validating OTPs.

## License

This project is licensed under the MIT License.