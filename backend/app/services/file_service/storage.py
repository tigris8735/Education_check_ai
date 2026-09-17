import uuid
from contextlib import asynccontextmanager

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


_session = aioboto3.Session()


def _client_config() -> Config:
    return Config(
        signature_version="s3v4",
        s3={"addressing_style": "virtual"},  # для R2 нужен virtual-hosted style
        retries={"max_attempts": 3, "mode": "standard"},
    )


@asynccontextmanager
async def _s3_client():
    async with _session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=_client_config(),
    ) as client:
        yield client


def build_s3_key(owner_id: int, original_name: str) -> str:
    """files/<user_id>/<uuid>.<ext>"""
    ext = ""
    if "." in original_name:
        ext = "." + original_name.rsplit(".", 1)[-1].lower()
    return f"files/{owner_id}/{uuid.uuid4().hex}{ext}"


async def generate_upload_url(
    key: str, content_type: str, max_size: int
) -> str:
    """Presigned PUT для прямой загрузки с фронта."""
    async with _s3_client() as s3:
        return await s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.S3_BUCKET,
                "Key": key,
                "ContentType": content_type,
                # Ограничение размера: подписываем Content-Length через policy нельзя,
                # но R2/S3 корректно обработает любой размер; контроль делаем на фронте + confirm.
            },
            ExpiresIn=settings.S3_PRESIGN_EXPIRE,
            HttpMethod="PUT",
        )


async def generate_download_url(
    key: str, filename: str, expires: int | None = None
) -> str:
    """Presigned GET с Content-Disposition, чтобы браузер скачивал с именем."""
    disposition = f'attachment; filename="{filename}"'
    async with _s3_client() as s3:
        return await s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": settings.S3_BUCKET,
                "Key": key,
                "ResponseContentDisposition": disposition,
            },
            ExpiresIn=expires or settings.S3_PRESIGN_EXPIRE,
            HttpMethod="GET",
        )


async def head_object(key: str) -> dict | None:
    """Проверить, что объект существует. Возвращает метаданные или None."""
    async with _s3_client() as s3:
        try:
            return await s3.head_object(Bucket=settings.S3_BUCKET, Key=key)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NoSuchKey", "NotFound"):
                return None
            raise


async def delete_object(key: str) -> None:
    async with _s3_client() as s3:
        await s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)