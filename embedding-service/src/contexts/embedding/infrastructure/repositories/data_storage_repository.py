import logging
import aiohttp
from typing import Dict, List, Any, Optional

from src.config import AppConfig
from src.contexts.embedding.domain import (
    DataStorageRepository, 
    DataStorageError
)

logger = logging.getLogger(__name__)


class RestDataStorageRepository(DataStorageRepository):
    def __init__(self, config: AppConfig):
        self.config = config
        self.base_url = config.data_storage_url
    
    async def get_dataset_rows(
        self, 
        dataset_id: str, 
        offset: int = 0, 
        limit: int = 100, 
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get dataset rows from data storage service."""
        try:
            url = f"{self.base_url}/api/v1/datasets/{dataset_id}/rows"
            params = {
                "offset": offset,
                "limit": limit,
            }
            
            # Add filter criteria to params if provided
            if filter_criteria:
                for key, value in filter_criteria.items():
                    params[key] = value
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error getting dataset rows: {error_text}")
                        raise DataStorageError(f"Failed to get dataset rows: {error_text}")
                    
                    data = await response.json()
                    return data.get("rows", [])
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error getting dataset rows: {str(e)}")
            raise DataStorageError(f"HTTP error getting dataset rows: {str(e)}", e)
        except Exception as e:
            logger.error(f"Unexpected error getting dataset rows: {str(e)}")
            raise DataStorageError(f"Unexpected error getting dataset rows: {str(e)}", e)
    
    async def get_dataset_row(
        self, 
        dataset_id: str, 
        row_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get specific dataset row from data storage service."""
        try:
            url = f"{self.base_url}/api/v1/datasets/{dataset_id}/rows/{row_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 404:
                        return None
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error getting dataset row: {error_text}")
                        raise DataStorageError(f"Failed to get dataset row: {error_text}")
                    
                    data = await response.json()
                    return data.get("row")
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error getting dataset row: {str(e)}")
            raise DataStorageError(f"HTTP error getting dataset row: {str(e)}", e)
        except Exception as e:
            logger.error(f"Unexpected error getting dataset row: {str(e)}")
            raise DataStorageError(f"Unexpected error getting dataset row: {str(e)}", e)
    
    async def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get dataset information from data storage service."""
        try:
            url = f"{self.base_url}/api/v1/datasets/{dataset_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 404:
                        return None
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error getting dataset info: {error_text}")
                        raise DataStorageError(f"Failed to get dataset info: {error_text}")
                    
                    data = await response.json()
                    return data
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error getting dataset info: {str(e)}")
            raise DataStorageError(f"HTTP error getting dataset info: {str(e)}", e)
        except Exception as e:
            logger.error(f"Unexpected error getting dataset info: {str(e)}")
            raise DataStorageError(f"Unexpected error getting dataset info: {str(e)}", e) 