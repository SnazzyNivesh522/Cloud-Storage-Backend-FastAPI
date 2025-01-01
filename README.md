# FastAPI Cloud Storage Application

A Drive-like cloud storage application built with [FastAPI](https://fastapi.tiangolo.com/). This application provides user authentication, folder and file management, email-based OTP verification, and more. The backend can be easily paired with any frontend client to offer a user-friendly cloud storage experience.

---

## Features

1. **User Authentication & OTP Verification**  
   - Registration with email-based OTP validation.  
   - Secure password hashing using `passlib`.  
   - OAuth2 token-based authentication with JWT.

2. **File Management**  
   - Upload, rename, delete (soft delete), restore, and move files.  
   - Download files directly from the API.  
   - Trash (soft-delete) functionality: restore or permanently empty the trash.

3. **Folder Management**  
   - Create, rename, delete (soft-delete), restore, and move folders.  
   - Recursive trash (folders & subfolders).  
   - Root folder automatically generated upon verification.

4. **Email Notifications**  
   - OTP verification emails.  
   - Thank-you emails upon account verification.  
   - Powered by `fastapi-mail` with customizable templates.

5. **Database Integration**  
   - PostgreSQL (SQLModel + SQLAlchemy) for relational data (users, files, folders, etc.).  
   - Docker support (Postgres + Adminer).

6. **Scalable Project Structure**  
   - Organized code layout with routers, models, templates, utils, etc.  
   - Easily extensible for future enhancements.

---

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
│   │   ├── user.py
│   │   └── __init__.py
│   ├── templates
│   │   ├── otp_verification_email.html
│   │   └── thank_you_email.html
│   ├── UPLOADS
│   └── utils
│       ├── email.py
│       ├── hashing.py
│       ├── __init__.py
│       ├── jwttoken.py
│       ├── oauth.py
│       └── otp.py
├── db
│   ├── data
│   ├── docker-compose.yml
│   └── READMED.md
├── scripts
│   └── delete_folder_recursive.py
├── README.md  <-- (You're here!)
└── requirements.txt
```

### Highlights of Important Files

- **`app/main.py`**: Application entry point; sets up FastAPI, includes routers, and configures CORS.  
- **`app/routers/`**: Houses individual route definitions for authentication, file operations, folder operations, and user profile.  
- **`app/models/postgres_models.py`**: PostgreSQL models (User, FileMetadata, Folder, etc.) using SQLModel.  
- **`app/models/schemas.py`**: Pydantic models (schemas) for validation and serialization.  
- **`app/utils/`**: Utility modules for JWT creation, OTP generation, password hashing, etc.  
- **`db/`**: Contains Docker Compose setup for PostgreSQL and Adminer, plus a data volume for persistence.  
- **`scripts/`**: Additional utility scripts (e.g., `delete_folder_recursive.py`).

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the `app` directory with the following variables:

```env
SECRET_KEY="your_secret_key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Mongo (unused in this demo or for future expansions)
MONGO_URI="mongodb://localhost:27017"
DATABASE_NAME="your_database_name"

# File storage
FILE_STORAGE_PATH="app/uploads"

# Email configuration
MAIL_USERNAME="your_email@example.com"
MAIL_FROM="your_email@example.com"
MAIL_PASSWORD="your_email_password"
MAIL_PORT=587
MAIL_SERVER="smtp.gmail.com"
MAIL_TLS=True
MAIL_SSL=False

# PostgreSQL
DATABASE_URL="postgresql://<user>:<password>@localhost:5432/<database_name>"

# CORS Origins
FRONTEND_URL="http://localhost:3000"
```

> **Note**: Adjust values based on your environment and email provider.

---

## Running the Application

### Option A: Directly with Uvicorn

1. Start your local PostgreSQL database or run the included Docker Compose (see **Docker Setup** below).  
2. From the `app` directory:

   ```bash
   uvicorn main:app --reload
   ```

3. Open your browser at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the automatically generated Swagger UI.

### Option B: Docker Setup for PostgreSQL & Adminer

1. Navigate to the `db/` folder:

   ```bash
   cd db
   ```

2. Bring up Docker containers:

   ```bash
   docker-compose up -d
   ```

3. Verify running containers:

   ```bash
   docker ps
   ```

4. Access the Adminer interface at [http://localhost:8080](http://localhost:8080) for database management.

Then, run the FastAPI application as described in Option A.

---

## API Endpoints

Below are some key endpoints. For a complete list, refer to the `/docs` endpoint once the server is running.

### **Authentication**

- **Register User**: `POST /auth/register`  
  Registers a new user; sends OTP to user’s email.

- **Verify OTP**: `POST /auth/verify-otp`  
  Completes verification using the OTP.

- **Login**: `POST /auth/token`  
  Returns a JWT access token upon successful authentication.

- **Profile**: `GET /auth/me`  
  Retrieves the currently authenticated user’s details.

### **Files**

- **Get Files**: `GET /files/`  
  Retrieves all files in the root folder or specify `folder_id` to list files in a specific folder.

- **Upload Files**: `POST /files/upload/{folder_id}`  
  Upload multiple files to the specified folder.

- **Rename File**: `PUT /files/rename/{file_id}`  
  Rename a file.

- **Delete File (Trash)**: `DELETE /files/delete/{file_id}`  
  Move the file to trash.

- **Restore File**: `GET /files/untrash/{file_id}`  
  Restore a trashed file.

- **Download File**: `GET /files/download/{file_id}`  
  Download a file by its ID.

- **Show Trash**: `GET /files/trash`  
  Show all trashed files.

- **Empty Trash**: `DELETE /files/trash/empty`  
  Permanently delete all trashed files/folders.

- **Move File**: `PUT /files/move/{file_id}`  
  Move a file to another folder.

### **Folders**

- **Create Folder**: `POST /folder/`  
  Creates a new folder (if `parent_folder` is not provided, defaults to root).

- **Get User Folders**: `GET /folder/`  
  Retrieves all folders for the user.

- **Get Root Folder**: `GET /folder/root`  
  Retrieves the user’s root folder.

- **Get Folder Detail**: `GET /folder/{folder_id}`  
  Basic info for a specific folder.

- **Get Full Folder Contents**: `GET /folder/all/{folder_id}`  
  Detailed info (including subfolders and files).

- **Rename Folder**: `PUT /folder/rename/{folder_id}`  
  Rename an existing folder.

- **Delete Folder (Trash)**: `DELETE /folder/delete/{folder_id}`  
  Move folder (and its contents) to trash.

- **Show Trashed Folders**: `GET /folder/trash/`  
  Show all trashed folders.

- **Get Trashed Folder Detail**: `GET /folder/trash/{folder_id}`  
  Detailed info of a trashed folder.

- **Move Folder**: `PUT /folder/move/{folder_id}`  
  Move a folder to a new parent folder.

- **Download Folder**: `GET /folder/download/{folder_id}`  
  Download an entire folder (as a ZIP).

### **User Profile**

- **Upload Profile Picture**: `POST /user/upload-profile-picture/`  
  Upload/update user’s profile picture.

---

## Scripts

Inside the `scripts/` folder, you’ll find useful utilities, such as:

- **`delete_folder_recursive.py`**  
  Recursively deletes specified folders (used by the empty trash routine).

---

## License

This project is licensed under the [MIT License](LICENSE).  
You’re free to modify and distribute this software with proper attribution.

---

## Contributing

We welcome contributions! Feel free to open an issue or submit a pull request.  

---

## Contact

For support or questions, please open an issue on GitHub or contact the maintainer at `niveshpritman@gmail.com`.

Enjoy your new cloud storage solution!