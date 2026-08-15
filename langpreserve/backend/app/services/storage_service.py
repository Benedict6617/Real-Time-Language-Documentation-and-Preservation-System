"""Media object storage abstraction — S3-compatible (incl. self-hosted MinIO)
or local filesystem, selected via STORAGE_BACKEND.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import boto3
from botocore.client import Config as BotoConfig

from app.config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self) -> None:
        self.backend = settings.storage_backend
        if self.backend == "s3":
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
                config=BotoConfig(signature_version="s3v4"),
            )
            self._ensure_bucket()
        else:
            Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=settings.s3_bucket)
        except Exception:
            self._client.create_bucket(Bucket=settings.s3_bucket)

    def build_key(self, *, language_id: str, kind: str, extension: str) -> str:
        return f"{language_id}/{kind}/{uuid.uuid4()}.{extension.lstrip('.')}"

    def put_object(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        if self.backend == "s3":
            self._client.put_object(
                Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type
            )
        else:
            path = Path(settings.local_storage_path) / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def get_object(self, key: str) -> bytes:
        if self.backend == "s3":
            obj = self._client.get_object(Bucket=settings.s3_bucket, Key=key)
            return obj["Body"].read()
        path = Path(settings.local_storage_path) / key
        return path.read_bytes()

    def presigned_url(self, key: str, expires_in: int = 3600) -> str:
        if self.backend == "s3":
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.s3_bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        return f"file://{os.path.join(settings.local_storage_path, key)}"


_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
