from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi import UploadFile

from fastapi.responses import FileResponse

from models.postgres_models import FileMetadata, Folder
from models.schemas import FileDetails, TrashFileDetails

from utils.oauth import get_current_user

from database import get_session
from sqlalchemy.orm import Session

from uuid import UUID

import os
from datetime import datetime

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not found"}},
)
UPLOAD_FOLDER = "./UPLOADS"


@router.get("/")
async def get_user_files(
    request: Request,
    folder_id: UUID | None = None,
    db: Session = Depends(get_session),
):
    """
    Retrieves all files for the authenticated user or files in a specific folder.

    Args:
        request (Request): The HTTP request object.
        folder_id (UUID | None): The UUID of the folder to retrieve files from. Defaults to None.
        db (Session): The database session dependency.

    Returns:
        List[FileMetadata]: A list of files belonging to the authenticated user or in the specified folder.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    print(folder_id)
    print(user)
    if folder_id:
        folder = (
            db.query(Folder)
            .filter(
                Folder.folder_id == folder_id,
                Folder.user_id == user.uid,
                Folder.is_trashed == False,
            )
            .first()
        )
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found or trashed",
            )
        files = (
            db.query(FileMetadata)
            .filter(
                FileMetadata.user_id == user.uid,
                FileMetadata.folder_id == folder_id,
                FileMetadata.is_trashed == False,
            )
            .all()
        )
    else:
        files = (
            db.query(FileMetadata)
            .filter(FileMetadata.file_name=="/",FileMetadata.user_id == user.uid, FileMetadata.is_trashed == False)
            .all()
        )
    print("Files::", files)
    return files


@router.post(
    "/upload/{folder_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=list[FileDetails],
)
async def upload_files(
    request: Request,
    folder_id: UUID,
    files: list[UploadFile],
    db: Session = Depends(get_session),
):
    """
    Upload multiple files to a given folder (by folder_id).

    Args:
        request (Request): The HTTP request object.
        folder_id (UUID): The UUID of the folder to upload files to.
        files (list[UploadFile]): A list of files to be uploaded.
        db (Session): The database session dependency.

    Returns:
        List[FileDetails]: A list of metadata for the uploaded files.

    Raises:
        HTTPException: If the folder is not found or trashed.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    folder = (
        db.query(Folder)
        .filter(
            Folder.folder_id == folder_id,
            Folder.user_id == user.uid,
            Folder.is_trashed == False,
        )
        .first()
    )
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found or trashed"
        )

    file_metadata_list = []
    folder_path = os.path.join(UPLOAD_FOLDER, str(user.uid), str(folder.folder_id))

    # Ensure directory exists
    os.makedirs(folder_path, exist_ok=True)

    for file in files:
        file_path = os.path.join(folder_path, file.filename)
        # Save the file to disk
        with open(file_path, "wb") as f:
            f.write(await file.read())

        file_metadata = FileMetadata(
            file_name=file.filename,
            file_size=os.path.getsize(file_path),
            file_type=file.content_type,
            storage_location=file_path,
            user_id=user.uid,
            folder_id=folder.folder_id,
        )
        file_metadata_list.append(file_metadata)

    db.add_all(file_metadata_list)
    db.commit()

    # Refresh to get assigned file_id
    for file_metadata in file_metadata_list:
        db.refresh(file_metadata)

    return file_metadata_list


@router.put(
    "/rename/{file_id}", status_code=status.HTTP_200_OK, response_model=FileDetails
)
async def rename_file(
    request: Request,
    file_id: UUID,
    file_name: str,
    db: Session = Depends(get_session),
):
    """
    Renames a specific file.

    Args:
        request (Request): The HTTP request object.
        file_id (UUID): The UUID of the file to rename.
        file_name (str): The new name of the file.
        db (Session): The database session dependency.

    Returns:
        FileDetails: The renamed file object.

    Raises:
        HTTPException: If the file is not found.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    file = (
        db.query(FileMetadata)
        .filter(FileMetadata.file_id == file_id, FileMetadata.user_id == user.uid)
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    file.file_name = file_name
    file.update_timestamp()
    db.commit()
    return file


@router.delete(
    "/delete/{file_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TrashFileDetails,
)
async def delete_file(
    request: Request,
    file_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Trashes a specific file.

    Args:
        request (Request): The HTTP request object.
        file_id (UUID): The UUID of the file to trash.
        db (Session): The database session dependency.

    Returns:
        TrashFileDetails: Details of the trashed file.

    Raises:
        HTTPException: If the file is not found.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    file = (
        db.query(FileMetadata)
        .filter(FileMetadata.file_id == file_id, FileMetadata.user_id == user.uid)
        .first()
    )
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    file.is_trashed = True
    file.trashed_at = datetime.now()
    db.commit()
    return file


@router.get("/download/{file_id}", response_class=FileResponse)
async def download_file(
    request: Request,
    file_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Downloads a specific file.

    Args:
        request (Request): The HTTP request object.
        file_id (UUID): The UUID of the file to download.
        db (Session): The database session dependency.

    Returns:
        FileResponse: The file response object containing the file.

    Raises:
        HTTPException: If the file is not found or if the file is in trash.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    file = (
        db.query(FileMetadata)
        .filter(FileMetadata.file_id == file_id, FileMetadata.user_id == user.uid)
        .first()
    )
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    if file.is_trashed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File is in trash"
        )

    return FileResponse(file.storage_location, filename=file.file_name)


@router.get("/untrash/{file_id}", response_model=FileDetails)
async def restore_file(
    request: Request,
    file_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Restores a trashed file.

    Args:
        request (Request): The HTTP request object.
        file_id (UUID): The UUID of the file to restore.
        db (Session): The database session dependency.

    Returns:
        FileDetails: The restored file object.

    Raises:
        HTTPException: If the file is not found in trash.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    file = (
        db.query(FileMetadata)
        .filter(
            FileMetadata.file_id == file_id,
            FileMetadata.user_id == user.uid,
            FileMetadata.is_trashed == True,
        )
        .first()
    )
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found in trash"
        )
    file.is_trashed = False
    file.trashed_at = None
    db.commit()
    return file


@router.get("/trash", response_model=list[TrashFileDetails])
async def show_trash(request: Request, db: Session = Depends(get_session)):
    """
    Retrieves all trashed files for the authenticated user.

    Args:
        request (Request): The HTTP request object.
        db (Session): The database session dependency.

    Returns:
        List[TrashFileDetails]: A list of trashed files.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    trashed_files = (
        db.query(FileMetadata)
        .filter(FileMetadata.is_trashed == True, FileMetadata.user_id == user.uid)
        .all()
    )
    return trashed_files


@router.delete("/trash/empty", response_model=dict)
async def empty_trash(request: Request, db: Session = Depends(get_session)):
    """
    Empties the trash for the authenticated user.

    Args:
        request (Request): The HTTP request object.
        db (Session): The database session dependency.

    Returns:
        dict: A message indicating the result of the operation.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    folders = (
        db.query(Folder)
        .filter(Folder.user_id == user.uid, Folder.is_trashed == True)
        .all()
    )
    files = (
        db.query(FileMetadata)
        .filter(FileMetadata.user_id == user.uid, FileMetadata.is_trashed == True)
        .all()
    )
    if not folders and not files:
        return {"message": "Trash is already empty"}

    for file in files:
        os.remove(file.storage_location)
        db.delete(file)
        db.commit()

    for folder in folders:
        try:
            from scripts.delete_folder_recursive import delete_folder_recursive

            delete_folder_recursive(f"{UPLOAD_FOLDER}/{user.uid}", folder.folder_id)
        except FileNotFoundError:
            pass
        db.delete(folder)
        db.commit()

    return {"message": "Trash cleaned successfully"}


@router.put("/move/{file_id}", response_model=FileDetails)
async def move_file(
    request: Request,
    file_id: UUID,
    folder_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Moves a file to a new folder.

    Args:
        request (Request): The HTTP request object.
        file_id (UUID): The UUID of the file to move.
        folder_id (UUID): The UUID of the new folder.
        db (Session): The database session dependency.

    Returns:
        FileDetails: The moved file object.

    Raises:
        HTTPException: If the file or folder is not found.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    file = (
        db.query(FileMetadata)
        .filter(FileMetadata.file_id == file_id, FileMetadata.user_id == user.uid)
        .first()
    )
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    folder = db.query(Folder).filter(Folder.folder_id == folder_id).first()
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    file.folder_id = folder_id
    folder.update_timestamp()
    file.update_timestamp()
    db.commit()
    return file
