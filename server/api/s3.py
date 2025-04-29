from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from fastapi import UploadFile, File, Form
from io import BytesIO

from cloud_storage.S3Uploader import S3Uploader
from core.dependecies import get_s3_uploader

router = APIRouter()

@router.post("/upload")
async def upload_file_to_s3(
    file: UploadFile = File(...),
    uploader: S3Uploader = Depends(get_s3_uploader)
):
    try:
        file_bytes = await file.read()
        byte_stream = BytesIO(file_bytes)
        key = await uploader.upload_file(byte_stream, file.filename)
        return {"key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/url")
async def get_presigned_url(key: str, expiration: Optional[int] = 3600, uploader: S3Uploader = Depends(get_s3_uploader)):
    try:
        url = uploader.generate_presigned_url(key, expiration)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
async def delete_file_from_s3(key: str = Form(...), uploader: S3Uploader = Depends(get_s3_uploader)):
    try:
        await uploader.delete_file_by_key(key)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
