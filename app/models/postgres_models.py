from sqlmodel import SQLModel, Field, Relationship, ForeignKey
import uuid
from datetime import datetime


class User(SQLModel, table=True):
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(max_length=50, nullable=False)
    email: str = Field(max_length=320, nullable=False)
    profile_picture: bytes = Field(default=None, nullable=True)
    hashed_password: str
    is_verified: bool = Field(default=False)
    otp: str = Field(default=None, max_length=6,nullable=True)
    

    files: list["FileMetadata"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    folders: list["Folder"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def __repr__(self) -> str:
        return f"<User(username={self.username})>"


class FileMetadata(SQLModel, table=True):
    __tablename__ = "file_metadata"
    file_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    folder_id: uuid.UUID = Field(
        default=None, foreign_key="folder.folder_id", index=True
    )
    user_id: uuid.UUID = Field(foreign_key="user.uid", nullable=False, index=True)
    file_name: str = Field(max_length=255, nullable=False)
    file_size: int = Field(nullable=False)
    file_type: str = Field(max_length=50, nullable=False)
    storage_location: str = Field(nullable=False)
    uploaded_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)
    is_trashed: bool = Field(default=False, nullable=False)
    trashed_at: datetime = Field(default=None, nullable=True)

    user: "User" = Relationship(
        back_populates="files", sa_relationship_kwargs={"lazy": "selectin"}
    )
    folder: "Folder" = Relationship(
        back_populates="files", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def update_timestamp(self):
        self.updated_at = datetime.now()

    def __repr__(self) -> str:
        return f"<FileMetadata(file_name={self.file_name})>"


class SharedFile(SQLModel, table=True):
    __tablename__ = "shared_file"
    share_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    file_id: uuid.UUID = Field(foreign_key="file_metadata.file_id", nullable=False, index=True)
    shared_with: uuid.UUID = Field(foreign_key="user.uid", nullable=False, index=True)
    shared_by: uuid.UUID = Field(foreign_key="user.uid", nullable=False, index=True)
    access_level: str = Field(max_length=20, nullable=False)
    shared_at: datetime = Field(default_factory=datetime.now, nullable=False)

    file: "FileMetadata" = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    shared_with_user: "User" = Relationship(
        sa_relationship_kwargs={"lazy": "selectin","foreign_keys":"SharedFile.shared_with"}
    )
    shared_by_user: "User" = Relationship(
        sa_relationship_kwargs={"lazy": "selectin","foreign_keys":"SharedFile.shared_by"}
    )

    def __repr__(self) -> str:
        return f"<SharedFile(file_id={self.file_id}, shared_with={self.shared_with})>"


class Folder(SQLModel, table=True):
    __tablename__ = "folder"
    folder_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.uid", nullable=False, index=True)
    folder_name: str = Field(max_length=255, nullable=False)
    parent_folder: uuid.UUID = Field(default=None,nullable=True)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)
    is_trashed: bool = Field(default=False, nullable=False)
    trashed_at: datetime = Field(default=None, nullable=True)

    user: "User" = Relationship(
        back_populates="folders", sa_relationship_kwargs={"lazy": "selectin"}
    )
    files: list["FileMetadata"] = Relationship(
        back_populates="folder", sa_relationship_kwargs={"lazy": "selectin"}
    )

    def update_timestamp(self):
        self.updated_at = datetime.now()
    def __repr__(self) -> str:
        return f"<Folder(folder_name={self.folder_name})>"
