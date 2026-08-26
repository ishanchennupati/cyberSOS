"""
Evidence file validation.

Deliberately conservative: an explicit allow-list of extensions and MIME
types, plus a magic-byte sniff so a renamed executable can't slip through
just because someone changed the extension. Never a deny-list — deny-lists
always miss something.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings

settings = get_settings()


class FileValidationError(Exception):
    """Raised with a user-safe message — never leaks internals."""


@dataclass(frozen=True)
class AllowedType:
    extensions: tuple[str, ...]
    mime_types: tuple[str, ...]
    # First few bytes that must appear at the start of the file.
    # None means "don't sniff" (used for plain text).
    signatures: tuple[bytes, ...] | None


ALLOWED_TYPES: dict[str, AllowedType] = {
    "png": AllowedType(("png",), ("image/png",), (b"\x89PNG\r\n\x1a\n",)),
    "jpg": AllowedType(
        ("jpg", "jpeg"), ("image/jpeg",), (b"\xff\xd8\xff",)
    ),
    "pdf": AllowedType(("pdf",), ("application/pdf",), (b"%PDF-",)),
    # Optional per spec section 4.
    "mp4": AllowedType(
        ("mp4",),
        ("video/mp4",),
        (b"\x00\x00\x00\x18ftyp", b"\x00\x00\x00\x1cftyp", b"ftyp"),
    ),
    "txt": AllowedType(("txt",), ("text/plain",), None),
}

# Extensions that must never be accepted, checked explicitly so a mistake in
# ALLOWED_TYPES above can't accidentally open the door to executables.
BLOCKED_EXTENSIONS = {
    "exe", "bat", "cmd", "sh", "apk", "dll", "msi", "com", "scr", "js",
    "vbs", "ps1", "jar", "app", "bin", "deb", "rpm",
}


def _extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower().strip()


def validate_evidence_file(
    *,
    filename: str,
    mime_type: str,
    file_bytes: bytes,
    max_size_bytes: int | None = None,
) -> None:
    """
    Raises FileValidationError with a message safe to show the citizen.
    Checks, in order: extension allow-list, blocked-extension guard,
    declared MIME type, magic-byte signature, and size.
    """

    max_size = max_size_bytes or settings.max_evidence_file_size_bytes
    ext = _extension(filename)

    if not ext:
        raise FileValidationError("This file doesn't have a recognizable file type.")

    if ext in BLOCKED_EXTENSIONS:
        raise FileValidationError(
            "This file type isn't accepted. Executable and script files can't "
            "be uploaded as evidence."
        )

    matching = next(
        (t for t in ALLOWED_TYPES.values() if ext in t.extensions), None
    )
    if matching is None:
        accepted = ", ".join(sorted({e for t in ALLOWED_TYPES.values() for e in t.extensions}))
        raise FileValidationError(
            f"'.{ext}' files aren't supported yet. Accepted types: {accepted}."
        )

    if mime_type not in matching.mime_types:
        raise FileValidationError(
            "This file's format doesn't match its extension. Please upload the "
            "original file."
        )

    if matching.signatures is not None:
        if not any(file_bytes.startswith(sig) or sig in file_bytes[:64] for sig in matching.signatures):
            raise FileValidationError(
                "This file doesn't look like a valid "
                f"{ext.upper()} file. It may be corrupted or renamed."
            )

    if len(file_bytes) == 0:
        raise FileValidationError("This file is empty.")

    if len(file_bytes) > max_size:
        limit_mb = max_size / (1024 * 1024)
        raise FileValidationError(
            f"This file is too large. Evidence files must be under {limit_mb:.0f} MB."
        )


def is_previewable_image(mime_type: str) -> bool:
    return mime_type in ("image/png", "image/jpeg")


def is_previewable_pdf(mime_type: str) -> bool:
    return mime_type == "application/pdf"
