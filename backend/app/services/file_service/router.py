from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.file_service import service as file_service
from app.services.file_service.schemas import (
    DownloadUrlOut,
    FileConfirmIn,
    FileOut,
    PresignUploadIn,
    PresignUploadOut,
)
from app.services.user_service.models import User
from app.shared.permissions import get_current_user

router = APIRouter()


@router.get("", response_model=list[FileOut])
async def list_my_files(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await file_service.list_my_files(db, current_user)


@router.post(
    "/presign-upload",
    response_model=PresignUploadOut,
    status_code=status.HTTP_201_CREATED,
)
async def presign_upload(
    payload: PresignUploadIn,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    file, url, expires = await file_service.presign_upload(db, payload, current_user)
    return PresignUploadOut(
        file_id=file.id,
        upload_url=url,
        s3_key=file.s3_key,
        expires_in=expires,
    )


@router.post("/{file_id}/confirm", response_model=FileOut)
async def confirm_upload(
    file_id: int,
    payload: FileConfirmIn,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await file_service.confirm_upload(db, file_id, payload, current_user)


@router.get("/{file_id}/download-url", response_model=DownloadUrlOut)
async def download_url(
    file_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    url, expires = await file_service.get_download_url(db, file_id, current_user)
    return DownloadUrlOut(url=url, expires_in=expires)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await file_service.delete_file(db, file_id, current_user)