from abc import ABC, abstractmethod
from typing import List, Dict, Any

class PreprocessingOperation(ABC):
    """Interface for preprocessing operations."""
    
    @abstractmethod
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process data using the operation."""
        pass 