"""Validated server-side ImageKit upload boundary."""
import hashlib
import io
import re
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from app.config.settings import settings

ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

async def validate_image_upload(file: UploadFile):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Image must be JPEG, PNG, or WebP")
    data = await file.read(settings.MAX_IMAGE_FILE_BYTES + 1)
    if not data or len(data) > settings.MAX_IMAGE_FILE_BYTES:
        raise HTTPException(413, "Image exceeds the configured size limit")
    try:
        image = Image.open(io.BytesIO(data)); image.verify()
        image = Image.open(io.BytesIO(data)); image.load()
        if image.width < 1 or image.height < 1 or image.width * image.height > settings.MAX_IMAGE_PIXELS:
            raise HTTPException(400, "Image dimensions are outside the supported range")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(400, "Uploaded file is not a valid image") from exc
    original = Path(file.filename or "image").name
    safe_stem = re.sub(r"[^A-Za-z0-9_-]", "-", Path(original).stem).strip("-") or "image"
    return data, f"{safe_stem[:80]}-{uuid.uuid4().hex}{ALLOWED_TYPES[file.content_type]}", hashlib.sha256(data).hexdigest()

async def upload_image(file: UploadFile):
    data, safe_name, checksum = await validate_image_upload(file)
    if settings.IMAGE_STORAGE_PROVIDER != "imagekit":
        raise HTTPException(503, "Image storage is not configured for ImageKit")
    if not all((settings.IMAGEKIT_PUBLIC_KEY, settings.IMAGEKIT_PRIVATE_KEY, settings.IMAGEKIT_URL_ENDPOINT)):
        raise HTTPException(503, "ImageKit is not configured; normal material imports remain available")
    try:
        from imagekitio import ImageKit
        client = ImageKit(private_key=settings.IMAGEKIT_PRIVATE_KEY, public_key=settings.IMAGEKIT_PUBLIC_KEY, url_endpoint=settings.IMAGEKIT_URL_ENDPOINT)
        result = client.upload_file(file=io.BytesIO(data), file_name=safe_name, options={"folder": "/numm/material-images", "use_unique_file_name": False})
        url, file_id = result.response_metadata.raw["url"], result.response_metadata.raw["fileId"]
    except Exception as exc:
        raise HTTPException(502, "ImageKit upload failed; material data was not changed") from exc
    return {"image_url": url, "imagekit_file_id": file_id, "checksum": checksum, "original_filename": Path(file.filename or "image").name}
