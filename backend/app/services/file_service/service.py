import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    FileTooLargeError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.services.file_service import crud, storage
from app.services.file_service.models import FileMeta
from app.services.file_service.schemas import FileConfirmIn, PresignUploadIn
from app.services.group_service import crud as group_crud
from app.services.task_service import crud as task_crud
from app.services.user_service.models import User
from app.shared.enums import FileStatus, Role

logger = logging.getLogger(__name__)

ALLOWED_MIME_PREFIXES = (
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "text/plain",
    "image/",
    "application/msword",
    "application/vnd.openxmlformats-officedocument",
    "application/vnd.oasis.opendocument",
)


def _ensure_storage_configured() -> None:
    missing = [
        key
        for key, value in {
            "S3_ENDPOINT": settings.S3_ENDPOINT,
            "S3_ACCESS_KEY": settings.S3_ACCESS_KEY,
            "S3_SECRET_KEY": settings.S3_SECRET_KEY,
            "S3_BUCKET": settings.S3_BUCKET,
        }.items()
        if not value
    ]
    if missing:
        raise ValidationError(
            f"Файловое хранилище не настроено на сервере (не хватает: {', '.join(missing)}). "
            "Обратитесь к администратору системы."
        )


def _check_mime(content_type: str) -> None:
    if not content_type.startswith(ALLOWED_MIME_PREFIXES):
        raise ValidationError(f"Тип файла не поддерживается: {content_type}")


async def presign_upload(
    db: AsyncSession, data: PresignUploadIn, user: User
) -> tuple[FileMeta, str, int]:
    _ensure_storage_configured()

    if data.size > settings.max_file_size_bytes:
        raise FileTooLargeError(f"Файл превышает {settings.MAX_FILE_SIZE_MB} МБ")
    _check_mime(data.content_type)

    key = storage.build_s3_key(user.id, data.original_name)

    file = await crud.create(
        db,
        s3_key=key,
        original_name=data.original_name,
        content_type=data.content_type,
        size=data.size,
        uploaded_by_id=user.id,
        status=FileStatus.PENDING,
    )

    upload_url = await storage.generate_upload_url(
        key, data.content_type, settings.max_file_size_bytes
    )
    return file, upload_url, settings.S3_PRESIGN_EXPIRE


async def confirm_upload(
    db: AsyncSession, file_id: int, data: FileConfirmIn, user: User
) -> FileMeta:
    _ensure_storage_configured()

    file = await crud.get_by_id(db, file_id)
    if not file:
        raise NotFoundError("Файл не найден")
    if file.uploaded_by_id != user.id:
        raise ForbiddenError("Это не ваш файл")
    if file.status == FileStatus.UPLOADED:
        raise ConflictError("Файл уже подтверждён")

    head = await storage.head_object(file.s3_key)
    if head is None:
        raise NotFoundError("Объект не найден в S3 — загрузка не удалась")

    real_size = int(head.get("ContentLength", file.size))
    if real_size > settings.max_file_size_bytes:
        await storage.delete_object(file.s3_key)
        await crud.delete(db, file)
        raise FileTooLargeError(f"Файл превышает {settings.MAX_FILE_SIZE_MB} МБ")

    return await crud.mark_uploaded(
        db,
        file,
        size=real_size,
        submission_id=data.submission_id,
        task_id=data.task_id,
    )


async def get_download_url(db: AsyncSession, file_id: int, user: User) -> tuple[str, int]:
    _ensure_storage_configured()

    file = await crud.get_by_id(db, file_id)
    if not file:
        raise NotFoundError("Файл не найден")
    if file.status != FileStatus.UPLOADED:
        raise ConflictError("Файл ещё не загружен")

    allowed = False
    if file.uploaded_by_id == user.id:
        allowed = True
    elif file.task_id:
        # файл задания: доступен преподавателю задания и студентам его групп
        task = await task_crud.get_by_id(db, file.task_id)
        if task:
            if user.role == Role.TEACHER:
                allowed = task.teacher_id == user.id
            else:
                for gid in await task_crud.group_ids_for_task(db, task.id):
                    if await group_crud.get_member(db, gid, user.id):
                        allowed = True
                        break
    elif user.role == Role.TEACHER:
        allowed = True  # legacy: препод может скачивать файлы работ

    if not allowed:
        raise ForbiddenError("Нет доступа к этому файлу")

    url = await storage.generate_download_url(
        file.s3_key, file.original_name, settings.S3_PRESIGN_EXPIRE
    )
    return url, settings.S3_PRESIGN_EXPIRE


async def delete_file(db: AsyncSession, file_id: int, user: User) -> None:
    file = await crud.get_by_id(db, file_id)
    if not file:
        raise NotFoundError("Файл не найден")
    if file.uploaded_by_id != user.id and user.role != Role.TEACHER:
        raise ForbiddenError("Нет доступа к этому файлу")

    try:
        await storage.delete_object(file.s3_key)
    except Exception as e:  # noqa: BLE001
        logger.warning("Не удалось удалить объект из S3 (%s): %s", file.s3_key, e)

    await crud.delete(db, file)


async def list_my_files(db: AsyncSession, user: User) -> list[FileMeta]:
    return await crud.list_by_owner(db, user.id)