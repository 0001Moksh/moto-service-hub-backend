import os
import uuid
from datetime import datetime
from fastapi import UploadFile
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Create uploads directory if it doesn't exist
Path(UPLOAD_DIR).mkdir(exist_ok=True)


def allowed_file(filename: str, allowed_extensions: set = {'png', 'jpg', 'jpeg', 'gif'}) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_upload_file(upload_file: UploadFile, subfolder: str = "") -> dict:
    """Save uploaded file and return file info"""
    try:
        # Check file extension
        if not allowed_file(upload_file.filename):
            return {
                "success": False,
                "error": "File type not allowed. Allowed types: png, jpg, jpeg, gif"
            }
        
        # Generate unique filename
        file_extension = upload_file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        
        # Create subfolder path
        if subfolder:
            file_path = os.path.join(UPLOAD_DIR, subfolder)
            os.makedirs(file_path, exist_ok=True)
        else:
            file_path = UPLOAD_DIR
        
        # Full file path
        full_path = os.path.join(file_path, unique_filename)
        
        # Save file
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        logger.info(f"File saved: {full_path}")
        
        return {
            "success": True,
            "original_filename": upload_file.filename,
            "saved_filename": unique_filename,
            "file_path": full_path,
            "relative_path": f"{subfolder}/{unique_filename}" if subfolder else unique_filename,
            "size": os.path.getsize(full_path)
        }
    
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return {"success": False, "error": str(e)}


def delete_file(file_path: str) -> bool:
    """Delete uploaded file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return False


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size: {e}")
        return 0
