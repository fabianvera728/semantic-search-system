from typing import Dict, Any, List
from preprocessing.preprocessor import Preprocessor
from preprocessing.preprocessing_operation import PreprocessingOperation

class TextCleaningOperation(PreprocessingOperation):
    """Operation for cleaning text data."""
    
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process data by cleaning text."""
        preprocessor = Preprocessor()
        columns = parameters.get("columns", [])
        remove_html = parameters.get("remove_html", True)
        remove_urls = parameters.get("remove_urls", True)
        remove_special_chars = parameters.get("remove_special_chars", True)
        
        return preprocessor._apply_to_columns(
            data, 
            columns, 
            lambda text: preprocessor.clean_text(
                text, 
                remove_html=remove_html, 
                remove_urls=remove_urls, 
                remove_special_chars=remove_special_chars
            )
        )

class TextNormalizationOperation(PreprocessingOperation):
    """Operation for normalizing text data."""
    
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process data by normalizing text."""
        preprocessor = Preprocessor()
        columns = parameters.get("columns", [])
        lowercase = parameters.get("lowercase", True)
        remove_accents = parameters.get("remove_accents", True)
        remove_stopwords = parameters.get("remove_stopwords", False)
        
        return preprocessor._apply_to_columns(
            data, 
            columns, 
            lambda text: preprocessor.normalize_text(
                text, 
                lowercase=lowercase, 
                remove_accents=remove_accents, 
                remove_stopwords=remove_stopwords
            )
        )

class TextTokenizationOperation(PreprocessingOperation):
    """Operation for tokenizing text data."""
    
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process data by tokenizing text."""
        preprocessor = Preprocessor()
        columns = parameters.get("columns", [])
        tokenize_type = parameters.get("tokenize_type", "word")
        min_token_length = parameters.get("min_token_length", 2)
        
        result = []
        for row in data:
            new_row = row.copy()
            for column in columns:
                if column in row:
                    new_row[f"{column}_tokens"] = preprocessor.tokenize_text(
                        row[column], 
                        tokenize_type=tokenize_type, 
                        min_token_length=min_token_length
                    )
            result.append(new_row)
        
        return result

class MissingDataOperation(PreprocessingOperation):
    """Operation for handling missing data."""
    
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process data by handling missing values."""
        preprocessor = Preprocessor()
        strategy = parameters.get("strategy", "remove")
        fill_value = parameters.get("fill_value", "")
        
        return preprocessor.handle_missing_data(data, strategy=strategy, fill_value=fill_value)

class DataTransformationOperation(PreprocessingOperation):
    """Operation for transforming data."""
    
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process data by applying transformations."""
        preprocessor = Preprocessor()
        method = parameters.get("method", "clean_text")
        columns = parameters.get("columns", [])
        
        return preprocessor.transform_data(data, method=method, columns=columns)

class PreprocessingFactory:
    """Factory for creating preprocessing operations."""
    
    def __init__(self):
        # Initialize operations
        self.operations = {
            "text-cleaning": TextCleaningOperation(),
            "text-normalization": TextNormalizationOperation(),
            "text-tokenization": TextTokenizationOperation(),
            "missing-data": MissingDataOperation(),
            "data-transformation": DataTransformationOperation()
        }
    
    def get_operation(self, operation_id: str) -> PreprocessingOperation:
        """Get a preprocessing operation by ID."""
        if operation_id not in self.operations:
            raise ValueError(f"Preprocessing operation with ID {operation_id} not found")
        
        return self.operations[operation_id]
    
    def get_available_operations(self) -> List[Dict[str, Any]]:
        """Get all available preprocessing operations."""
        return [
            {
                "id": "text-cleaning",
                "name": "Text Cleaning",
                "description": "Clean text data by removing special characters, HTML tags, etc.",
                "parameters": {
                    "columns": "array",
                    "remove_html": "boolean",
                    "remove_urls": "boolean",
                    "remove_special_chars": "boolean"
                }
            },
            {
                "id": "text-normalization",
                "name": "Text Normalization",
                "description": "Normalize text by converting to lowercase, removing accents, etc.",
                "parameters": {
                    "columns": "array",
                    "lowercase": "boolean",
                    "remove_accents": "boolean",
                    "remove_stopwords": "boolean"
                }
            },
            {
                "id": "text-tokenization",
                "name": "Text Tokenization",
                "description": "Tokenize text into words or sentences",
                "parameters": {
                    "columns": "array",
                    "tokenize_type": "string",
                    "min_token_length": "number"
                }
            },
            {
                "id": "missing-data",
                "name": "Missing Data Handling",
                "description": "Handle missing data in the dataset",
                "parameters": {
                    "strategy": "string",
                    "fill_value": "string"
                }
            },
            {
                "id": "data-transformation",
                "name": "Data Transformation",
                "description": "Transform data using various methods",
                "parameters": {
                    "method": "string",
                    "columns": "array"
                }
            }
        ] 