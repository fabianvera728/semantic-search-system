import os
import shutil
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import UploadFile

class FileUtils:
    """Utility functions for file operations."""
    
    @staticmethod
    def ensure_upload_dir() -> str:
        """Ensure the upload directory exists and return its path."""
        upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        return upload_dir
    
    @staticmethod
    async def save_upload_file(upload_file: UploadFile, directory: Optional[str] = None) -> Dict[str, Any]:
        """Save an uploaded file and return its information."""
        # Ensure upload directory exists
        if directory is None:
            directory = FileUtils.ensure_upload_dir()
        
        # Generate a unique filename
        filename = upload_file.filename
        name, extension = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex}{extension}"
        file_path = os.path.join(directory, unique_filename)
        
        # Save the file
        with open(file_path, "wb") as f:
            content = await upload_file.read()
            f.write(content)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_info = {
            "filename": filename,
            "unique_filename": unique_filename,
            "path": file_path,
            "size": file_size,
            "extension": extension,
            "upload_time": datetime.utcnow().isoformat()
        }
        
        return file_info
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete a file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a file."""
        try:
            if not os.path.exists(file_path):
                return None
            
            filename = os.path.basename(file_path)
            name, extension = os.path.splitext(filename)
            file_size = os.path.getsize(file_path)
            modified_time = os.path.getmtime(file_path)
            
            return {
                "filename": filename,
                "path": file_path,
                "size": file_size,
                "extension": extension,
                "modified_time": datetime.fromtimestamp(modified_time).isoformat()
            }
        except Exception as e:
            print(f"Error getting file info for {file_path}: {str(e)}")
            return None
    
    @staticmethod
    def list_files(directory: str, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files in a directory."""
        try:
            if not os.path.exists(directory) or not os.path.isdir(directory):
                return []
            
            files = []
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    if pattern is None or pattern in filename:
                        file_info = FileUtils.get_file_info(file_path)
                        if file_info:
                            files.append(file_info)
            
            return files
        except Exception as e:
            print(f"Error listing files in {directory}: {str(e)}")
            return [] 