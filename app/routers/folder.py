import os
from fastapi import APIRouter, HTTPException, Request, status, Depends

from typing import Optional

from fastapi.responses import FileResponse

from models.postgres_models import FileMetadata, Folder
from models.schemas import (
    FolderDetails,
    FullFolderDetails,
    TrashFolderDetails,
    TrashFullFolderDetails,
)

from utils.oauth import get_current_user

from database import get_session
from sqlalchemy.orm import Session

from uuid import UUID

from datetime import datetime

from tempfile import TemporaryDirectory
from shutil import make_archive

router = APIRouter(
    prefix="/folder",
    tags=["folder"],
    responses={404: {"description": "Not found"}},
)
UPLOAD_FOLDER = "UPLOADS"


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=FolderDetails)
async def create_folder(
    request: Request,
    folder_name: str,
    parent_folder: Optional[UUID] = None,
    db: Session = Depends(get_session),
):
    """
    Creates a new folder for the authenticated user.

    Args:
        request (Request): The HTTP request object.
        folder_name (str): The name of the folder to be created.
        parent_folder (Optional[UUID], optional): The UUID of the parent folder. Defaults to None.
        db (Session): The database session dependency.

    Returns:
        Folder: The created folder object.

    Raises:
        HTTPException: If the root folder already exists or if there is an issue with folder creation.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    if folder_name == "/" and parent_folder == None:
        root_folder = (
            db.query(Folder)
            .filter(Folder.folder_name == "/", Folder.user_id == user.uid)
            .first()
        )
        if root_folder:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Root folder already exists",
            )
        else:
            root_folder = Folder(
                folder_name=folder_name, parent_folder=parent_folder, user_id=user.uid
            )
            db.add(root_folder)
            db.commit()
            db.refresh(root_folder)
            return root_folder
    if parent_folder == None:
        parent_folder = (
            db.query(Folder)
            .filter(Folder.folder_name == "/", Folder.user_id == user.uid)
            .first()
            .folder_id
        )
    folder = Folder(
        folder_name=folder_name, parent_folder=parent_folder, user_id=user.uid
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.get("/",response_model=list[FolderDetails])
async def get_user_folders(
    request: Request,
    db: Session = Depends(get_session),
):
    """
    Retrieves all folders for the authenticated user.

    Args:
        request (Request): The HTTP request object.
        db (Session): The database session dependency.

    Returns:
        List[Folder]: A list of folders belonging to the authenticated user.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    folders = (
        db.query(Folder)
        .filter(Folder.user_id == user.uid)
        .filter(Folder.is_trashed == False)
        .all()
    )
    return folders

@router.get("/root", response_model=FolderDetails)
async def get_root_folder(
    request: Request,
    db: Session = Depends(get_session),
):
    """
    Retrieves the root folder for the authenticated user.

    Args:
        request (Request): The HTTP request object.
        db (Session): The database session dependency.

    Returns:
        Folder: The root folder for the authenticated user.

    Raises:
        HTTPException: If the root folder is not found.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    folder = (
        db.query(Folder)
        .filter(Folder.folder_name == "/", Folder.user_id == user.uid)
        .first()
    )
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Root folder not found"
        )
    return folder

@router.get("/{folder_id}", response_model=FolderDetails)
async def get_folder_detail(
    request: Request,
    folder_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Retrieves details of a specific folder by its ID.

    Args:
        request (Request): The HTTP request object.
        folder_id (UUID): The UUID of the folder to retrieve.
        db (Session): The database session dependency.

    Returns:
        Folder: The folder object.

    Raises:
        HTTPException: If the folder is not found.
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    return folder


@router.get("/all/{folder_id}", response_model=FullFolderDetails)
async def get_folder_contents(
    request: Request,
    folder_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Retrieves the contents of a specific folder, including subfolders and files.

    Args:
        request (Request): The HTTP request object.
        folder_id (UUID): The UUID of the folder to retrieve contents for.
        db (Session): The database session dependency.

    Returns:
        dict: A dictionary containing folder details, subfolders, and files.

    Raises:
        HTTPException: If the folder is not found.
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    subfolders = (
        db.query(Folder)
        .filter(Folder.parent_folder == folder_id, Folder.is_trashed == False)
        .all()
    )
    files = (
        db.query(FileMetadata)
        .filter(FileMetadata.folder_id == folder_id, FileMetadata.is_trashed == False)
        .all()
    )
    return {
        "folder_id": folder.folder_id,
        "folder_name": folder.folder_name,
        "parent_folder_id": folder.parent_folder,
        "updated_at": folder.updated_at,
        "subfolders": subfolders,
        "files": files,
    }


@router.put("/rename/{folder_id}", response_model=FolderDetails)
async def rename_folder(
    request: Request,
    folder_id: UUID,
    folder_name: str,
    db: Session = Depends(get_session),
):
    """
    Renames a specific folder.

    Args:
        request (Request): The HTTP request object.
        folder_id (UUID): The UUID of the folder to rename.
        folder_name (str): The new name of the folder.
        db (Session): The database session dependency.

    Returns:
        Folder: The renamed folder object.

    Raises:
        HTTPException: If the folder is not found.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    # rename folder that belongs to user for validations
    folder = (
        db.query(Folder)
        .filter(Folder.folder_id == folder_id, Folder.user_id == user.uid)
        .first()
    )

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    folder.folder_name = folder_name
    folder.update_timestamp()
    db.commit()
    return folder


@router.delete(
    "/delete/{folder_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TrashFullFolderDetails,
)
async def trash_folder(
    folder_id: UUID, request: Request, db: Session = Depends(get_session)
):
    """
    Endpoint to trash a folder and its contents.

    This endpoint marks a folder and all its files and subfolders as trashed.
    It updates the `is_trashed` and `trashed_at` fields for the folder, its files,
    and recursively for its subfolders.

    Args:
        folder_id (UUID): The unique identifier of the folder to be trashed.
        request (Request): The request object containing headers and other metadata.
        db (Session): The database session dependency.

    Returns:
        TrashFullFolderDetails: A response model containing details of the trashed folder,
        including its files and subfolders.

    Raises:
        HTTPException: If the folder is not found, a 404 status code is returned.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    folder = (
        db.query(Folder)
        .filter(Folder.folder_id == folder_id, Folder.user_id == user.uid)
        .first()
    )
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    # trash all files in the folder
    files = db.query(FileMetadata).filter(FileMetadata.folder_id == folder_id).all()
    trashed_files = []
    for file in files:
        file.is_trashed = True
        file.trashed_at = datetime.utcnow()
        trashed_files.append(
            {
                "file_id": str(file.file_id),
                "file_name": file.file_name,
                "trashed_at": file.trashed_at.isoformat(),
            }
        )
    db.commit()

    # trash all subfolders
    subfolders = db.query(Folder).filter(Folder.parent_folder == folder_id).all()
    trashed_subfolders = []
    for subfolder in subfolders:
        trashed_subfolder = await trash_folder(subfolder.folder_id, request, db)
        trashed_subfolders.append(trashed_subfolder)

    folder.is_trashed = True
    folder.trashed_at = datetime.now()
    db.commit()

    return TrashFullFolderDetails(
        folder_id=str(folder.folder_id),
        folder_name=folder.folder_name,
        parent_folder_id=str(folder.parent_folder) if folder.parent_folder else None,
        trashed_at=folder.trashed_at.isoformat(),
        subfolders=trashed_subfolders,
        files=trashed_files,
    )


@router.get("/trash/", response_model=list[TrashFolderDetails])
async def get_trashed_folders(request: Request, db: Session = Depends(get_session)):
    """
    Retrieves all trashed folders for the authenticated user.

    Args:
        request (Request): The HTTP request object.
        db (Session): The database session dependency.

    Returns:
        List[TrashFolderDetails]: A list of trashed folders.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    folders = (
        db.query(Folder)
        .filter(Folder.user_id == user.uid, Folder.is_trashed == True)
        .all()
    )
    return folders


@router.get("/trash/{folder_id}", response_model=TrashFullFolderDetails)
async def get_trash_folder_details(
    folder_id: UUID, request: Request, db: Session = Depends(get_session)
):
    """
    Retrieves details of a specific trashed folder by its ID.

    Args:
        folder_id (UUID): The UUID of the trashed folder to retrieve.
        request (Request): The HTTP request object.
        db (Session): The database session dependency.

    Returns:
        dict: A dictionary containing folder details, subfolders, and files.

    Raises:
        HTTPException: If the folder is not found.
    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    folder = (
        db.query(Folder)
        .filter(
            Folder.folder_id == folder_id,
            Folder.user_id == user.uid,
            Folder.is_trashed == True,
        )
        .first()
    )
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    subfolders = (
        db.query(Folder)
        .filter(Folder.parent_folder == folder_id, Folder.is_trashed == True)
        .all()
    )
    files = (
        db.query(FileMetadata)
        .filter(FileMetadata.folder_id == folder_id, FileMetadata.is_trashed == True)
        .all()
    )
    return {
        "folder_id": folder.folder_id,
        "folder_name": folder.folder_name,
        "parent_folder_id": folder.parent_folder,
        "trashed_at": folder.trashed_at,
        "subfolders": subfolders,
        "files": files,
    }


@router.put("/move/{folder_id}", response_model=FolderDetails)
async def move_folder(
    request: Request,
    folder_id: UUID,
    parent_folder: UUID,
    db: Session = Depends(get_session),
):
    """
    Moves a folder to a new parent folder.

    Args:
        request (Request): The HTTP request object.
        folder_id (UUID): The UUID of the folder to move.
        parent_folder (UUID): The UUID of the new parent folder.
        db (Session): The database session dependency.

    Returns:
        Folder: The moved folder object.

    Raises:
        HTTPException: If the folder is not found.
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    folder.parent_folder = parent_folder
    folder.update_timestamp()
    db.commit()
    return folder


@router.get("/download/{folder_id}", response_class=FileResponse)
async def download_folder(
    request: Request,
    folder_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Download a folder as a zip file.

    Args:
        request (Request): The request object
        folder_id (UUID): The folder_id of the folder to download
        db (Session, optional): The database session. Defaults to Depends(get_session).
    Returns:
        FileResponse: The zip file response object containing the folder

    """
    token = request.headers.get("Authorization").split(" ")[1]
    user = await get_current_user(token, db)
    folder = (
        db.query(Folder)
        .filter(Folder.folder_id == folder_id, Folder.user_id == user.uid)
        .first()
    )
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    folder_name = folder.folder_name
    folder_path = f"{UPLOAD_FOLDER}/{user.uid}/{folder.folder_id}"

    try:
        with TemporaryDirectory() as temp_folder:
            zip_file_path = os.path.join(temp_folder, f"{folder_name}.zip")
            make_archive(
                base_name=zip_file_path[:-4], format="zip", root_dir=folder_path
            )
            return FileResponse(
                path=zip_file_path,
                filename=f"{folder_name}.zip",
                media_type="application/zip",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while preparing the folder for download: {str(e)}",
        )
