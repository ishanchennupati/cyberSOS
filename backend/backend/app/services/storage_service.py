"""
Evidence file storage.

Wraps Supabase Storage (private bucket, signed URLs only) behind a small
interface. When SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY aren't configured
(local dev, tests, a judge running this without a Supabase project), it
falls back to a local-disk store under LOCAL_STORAGE_ROOT so the rest of
the Evidence Vault still works end to end.

Callers never see a public URL. Previews are served through our own API
route (GET /api/v1/evidence/{id}/file), which either proxies a short-lived
Supabase signed URL or streams from local disk — the frontend never talks
to storage directly.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

from app.core.config import get_settings

settings = get_settings()


class StorageError(Exception):
    """Raised with a user-safe message."""


def build_storage_path(incident_id: uuid.UUID, evidence_id: uuid.UUID, filename: str) -> str:
    """
    demo/{incident_id}/evidence/{evidence_id}/original_file

    The evidence_id segment guarantees a unique path even if two evidence
    items share a filename (spec section 16 / 32 "unique storage names").
    """
    safe_name = filename.replace("/", "_").replace("\\", "_").strip() or "original_file"
    return f"demo/{incident_id}/evidence/{evidence_id}/{safe_name}"


class StorageBackend(ABC):
    @abstractmethod
    def upload(self, path: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    def download(self, path: str) -> bytes: ...

    @abstractmethod
    def delete(self, path: str) -> None: ...

    @abstractmethod
    def signed_url(self, path: str, expires_in: int = 3600) -> str | None:
        """Returns a short-lived URL, or None if the backend can't produce
        one (local backend — caller should stream via download() instead)."""
        ...


class SupabaseStorageBackend(StorageBackend):
    def __init__(self) -> None:
        if not settings.supabase_configured:
            raise StorageError("Supabase Storage is not configured.")
        self.base_url = settings.SUPABASE_URL.rstrip("/")  # type: ignore[union-attr]
        self.bucket = settings.SUPABASE_EVIDENCE_BUCKET
        self._headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY or "",
        }

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{path}"
        try:
            resp = httpx.post(
                url,
                content=data,
                headers={
                    **self._headers,
                    "Content-Type": content_type,
                    "x-upsert": "false",
                },
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise StorageError("Storage unavailable. Please try again.") from exc
        if resp.status_code >= 400:
            raise StorageError("We couldn't store this file. Please try again.")

    def download(self, path: str) -> bytes:
        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{path}"
        try:
            resp = httpx.get(url, headers=self._headers, timeout=30.0)
        except httpx.HTTPError as exc:
            raise StorageError("Storage unavailable. Please try again.") from exc
        if resp.status_code >= 400:
            raise StorageError("This file could not be retrieved.")
        return resp.content

    def delete(self, path: str) -> None:
        url = f"{self.base_url}/storage/v1/object/{self.bucket}"
        try:
            httpx.request(
                "DELETE",
                url,
                json={"prefixes": [path]},
                headers=self._headers,
                timeout=30.0,
            )
        except httpx.HTTPError:
            # Deletion is best-effort; the DB row is still removed by the
            # caller so the evidence disappears from the app either way.
            pass

    def signed_url(self, path: str, expires_in: int = 3600) -> str | None:
        url = f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{path}"
        try:
            resp = httpx.post(
                url, json={"expiresIn": expires_in}, headers=self._headers, timeout=15.0
            )
        except httpx.HTTPError:
            return None
        if resp.status_code >= 400:
            return None
        signed_path = resp.json().get("signedURL")
        if not signed_path:
            return None
        return f"{self.base_url}/storage/v1{signed_path}"


class LocalDiskStorageBackend(StorageBackend):
    """Dev/test fallback. Never used when Supabase is configured."""

    def __init__(self) -> None:
        self.root = Path(settings.LOCAL_STORAGE_ROOT)
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        full = (self.root / path).resolve()
        if self.root.resolve() not in full.parents and full != self.root.resolve():
            raise StorageError("Invalid storage path.")
        return full

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        full = self._resolve(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)

    def download(self, path: str) -> bytes:
        full = self._resolve(path)
        if not full.exists():
            raise StorageError("This file could not be retrieved.")
        return full.read_bytes()

    def delete(self, path: str) -> None:
        full = self._resolve(path)
        if full.exists():
            full.unlink()

    def signed_url(self, path: str, expires_in: int = 3600) -> str | None:
        return None  # caller streams via download() through our own API route


def get_storage_backend() -> StorageBackend:
    if settings.supabase_configured:
        return SupabaseStorageBackend()
    return LocalDiskStorageBackend()
