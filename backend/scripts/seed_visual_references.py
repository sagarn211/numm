"""Explicitly import the checked-in visual reference dataset into NUMM.

Run inside the backend container. It never creates materials unless
--demo-create-missing is supplied, and skipped records are reported.
"""
import argparse
import base64
import hashlib
import io
import os
from pathlib import Path
import sys

import httpx
import pandas as pd
from PIL import Image, UnidentifiedImageError

# ``python scripts/seed_visual_references.py`` sets sys.path to /app/scripts.
# Include the backend application root before importing NUMM modules.
APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.config.database import SessionLocal
from app.config.settings import settings
from app.models.cpse import CPSE
from app.models.material import Material
from app.models.material_image import MaterialImage

ROOT = Path(os.getenv("VISUAL_REFERENCE_DIR", "/reference-data"))


def upload_to_imagekit(data: bytes, filename: str):
    if not all((settings.IMAGEKIT_PRIVATE_KEY, settings.IMAGEKIT_URL_ENDPOINT)):
        raise RuntimeError("ImageKit credentials are not configured")
    response = httpx.post(
        "https://upload.imagekit.io/api/v1/files/upload",
        auth=(settings.IMAGEKIT_PRIVATE_KEY, ""),
        data={"file": base64.b64encode(data).decode("ascii"), "fileName": filename, "folder": "/numm/reference-materials", "useUniqueFileName": "true"},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["url"], payload["fileId"]


def ensure_valid_image(path: Path):
    data = path.read_bytes()
    try:
        image = Image.open(io.BytesIO(data)); image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("invalid image") from exc
    return data, hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-create-missing", action="store_true")
    args = parser.parse_args()
    csv_path, images_dir = ROOT / "materials.csv", ROOT / "images"
    if not csv_path.exists() or not images_dir.is_dir():
        raise SystemExit(f"Reference dataset is unavailable under {ROOT}")
    rows = pd.read_csv(csv_path, dtype=str).fillna("")
    db = SessionLocal(); summary = {"indexed": 0, "duplicates": 0, "missing_material": 0, "missing_cpse": 0, "bad_image": 0, "index_failures": 0}
    try:
        for _, row in rows.iterrows():
            cpse = db.query(CPSE).filter(CPSE.code == row["manufacturer"].strip().upper()).first()
            if not cpse:
                summary["missing_cpse"] += 1; continue
            material = db.query(Material).filter(Material.cpse_id == cpse.id, Material.material_code == row["material_code"].strip()).first()
            if not material and args.demo_create_missing:
                material = Material(cpse_id=cpse.id, material_code=row["material_code"].strip(), description=row["description"].strip(), category=row["category"].strip() or None, unit=row["unit"].strip() or None, manufacturer=row["manufacturer"].strip(), source="REFERENCE_DATASET")
                db.add(material); db.flush()
            if not material:
                summary["missing_material"] += 1; continue
            path = images_dir / Path(row["image"]).name
            try:
                data, checksum = ensure_valid_image(path)
            except (OSError, ValueError):
                summary["bad_image"] += 1; continue
            if db.query(MaterialImage.id).filter(MaterialImage.material_id == material.id, MaterialImage.checksum == checksum).first():
                summary["duplicates"] += 1; continue
            url, file_id = upload_to_imagekit(data, path.name)
            primary = not bool(db.query(MaterialImage.id).filter(MaterialImage.material_id == material.id, MaterialImage.is_primary.is_(True)).first())
            record = MaterialImage(material_id=material.id, image_url=url, imagekit_file_id=file_id, image_type="OTHER", source_type="REFERENCE_DATASET", verification_status="VERIFIED", is_primary=primary, checksum=checksum, original_filename=path.name)
            db.add(record); db.commit(); db.refresh(record)
            try:
                response = httpx.post(f"{settings.AI_SERVICE_URL}/api/v1/visual-index", files={"file": (path.name, data, "image/jpeg")}, data={"material_image_id": record.id, "material_id": material.id}, timeout=90)
                response.raise_for_status(); summary["indexed"] += 1
            except Exception:
                summary["index_failures"] += 1
        print(summary)
    finally:
        db.close()


if __name__ == "__main__":
    main()
