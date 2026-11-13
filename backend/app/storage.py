"""Local storage for uploaded video files."""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .config import settings

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm"}
CHUNK = 1024 * 1024


def _dir() -> Path:
    d = Path(settings.upload_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def path_of(name: str | None) -> Path | None:
    """Absolute path of a stored file by its stored name (None if absent)."""
    if not name:
        return None
    p = _dir() / Path(name).name  # strip any directory parts
    return p if p.is_file() else None


def save_upload(file: UploadFile) -> str:
    """Stream an upload to disk, enforcing type and size limits. Returns the stored file name."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported file type; use " + ", ".join(sorted(ALLOWED_EXTENSIONS)))
    name = uuid.uuid4().hex + ext
    dest = _dir() / name
    limit = settings.max_upload_mb * 1024 * 1024
    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := file.file.read(CHUNK):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, f"File too large (max {settings.max_upload_mb} MB)")
                out.write(chunk)
        if size == 0:
            raise HTTPException(400, "Empty file")
    except BaseException:
        dest.unlink(missing_ok=True)
        raise
    return name


def delete(name: str | None) -> None:
    p = path_of(name)
    if p:
        p.unlink(missing_ok=True)
