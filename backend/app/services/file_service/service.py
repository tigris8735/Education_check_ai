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
from app.services.file_service.schemas import (
    ALLOWED_MIME_PREFIXES,
    FileConfirmIn,
    PresignUploadIn,
)
from app.services.user_service.models import User
from app.shared.enums import FileStatus, Role

from app.services.submission_service import crud as submission_crud
from app.services.task_service import crud as task_crud

logger = logging.getLogger(__name__)


def _check_mime(content_type: str) -> None:
    if not any(content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES):
        raise ValidationError(f"Недопустимый тип файла: {content_type}")



async def _check_file_access(db, file, user) -> None:
    """Кто имеет право на файл."""
    # владелец — всегда
    if file.uploaded_by_id == user.id:
        return

    # препод — только если файл привязан к submission задания этого препода
    if user.role == Role.TEACHER and file.submission_id is not None:
        sub = await submission_crud.get_by_id(db, file.submission_id)
        if sub:
            task = await task_crud.get_by_id(db, sub.task_id)
            if task and task.teacher_id == user.id:
                return

    raise ForbiddenError("Нет доступа к этому файлу")



async def presign_upload(
    db: AsyncSession, data: PresignUploadIn, user: User
) -> tuple[FileMeta, str, int]:
    if data.size > settings.max_file_size_bytes:
        raise FileTooLargeError(
            f"Файл превышает {settings.MAX_FILE_SIZE_MB} МБ"
        )
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
        # подстраховка от обхода через подмену размера
        await storage.delete_object(file.s3_key)
        await crud.delete(db, file)
        raise FileTooLargeError(
            f"Файл превышает {settings.MAX_FILE_SIZE_MB} МБ"
        )

    # привязку к submission проверим на этапе 7
    return await crud.mark_uploaded(
        db, file, size=real_size, submission_id=data.submission_id
    )


async def get_download_url(db: AsyncSession, file_id: int, user: User) -> tuple[str, int]:
    file = await crud.get_by_id(db, file_id)
    if not file:
        raise NotFoundError("Файл не найден")
    if file.status != FileStatus.UPLOADED:
        raise ConflictError("Файл ещё не загружен")

    # Права:
    #  - владелец — всегда
    #  - преподаватель — пока разрешим скачивать любой файл (на этапе 7 ужесточим
    #    до «только по своим группам/заданиям»)
    if file.uploaded_by_id != user.id and user.role != Role.TEACHER:
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

async def get_download_url(db, file_id, user):
    file = await crud.get_by_id(db, file_id)
    if not file:
        raise NotFoundError("Файл не найден")
    if file.status != FileStatus.UPLOADED:
        raise ConflictError("Файл ещё не загружен")

    await _check_file_access(db, file, user)

    url = await storage.generate_download_url(
        file.s3_key, file.original_name, settings.S3_PRESIGN_EXPIRE
    )
    return url, settings.S3_PRESIGN_EXPIRE


async def list_my_files(db: AsyncSession, user: User) -> list[FileMeta]:
    return await crud.list_by_owner(db, user.id)