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
        case = parameters.get("case", "lower")
        
        case_func = str.lower if case == "lower" else str.upper if case == "upper" else str.title
        
        return preprocessor._apply_to_columns(
            data,
            columns,
            lambda text: preprocessor.normalize_text(case_func(text))
        )

class TextTokenizationOperation(PreprocessingOperation):
    """Operation for tokenizing text data."""
    
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process data by tokenizing text."""
        preprocessor = Preprocessor()
        columns = parameters.get("columns", [])
        join_tokens = parameters.get("join_tokens", True)
        
        return preprocessor._apply_to_columns(
            data,
            columns,
            lambda text: " ".join(preprocessor.tokenize_text(text)) if join_tokens else preprocessor.tokenize_text(text)
        )

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

class ColumnMappingOperation(PreprocessingOperation):
    """Operation for mapping column names and data types."""
    
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map column names and transform data types according to dataset schema."""
        column_mappings = parameters.get("column_mappings", {})  # {"old_name": "new_name"}
        type_conversions = parameters.get("type_conversions", {})  # {"column": "target_type"}
        default_values = parameters.get("default_values", {})  # {"column": "default_value"}
        
        result = []
        for row in data:
            new_row = {}
            
            # Apply column mappings
            for old_name, value in row.items():
                new_name = column_mappings.get(old_name, old_name)
                new_row[new_name] = value
            
            # Apply type conversions
            for column, target_type in type_conversions.items():
                if column in new_row:
                    try:
                        if target_type == "string":
                            new_row[column] = str(new_row[column]) if new_row[column] is not None else ""
                        elif target_type == "number":
                            new_row[column] = float(new_row[column]) if new_row[column] not in [None, ""] else 0.0
                        elif target_type == "boolean":
                            new_row[column] = bool(new_row[column]) if new_row[column] is not None else False
                        elif target_type == "date":
                            # Basic date handling - can be enhanced
                            new_row[column] = str(new_row[column]) if new_row[column] is not None else ""
                    except (ValueError, TypeError):
                        # Use default value if conversion fails
                        new_row[column] = default_values.get(column, None)
            
            # Add default values for missing columns
            for column, default_value in default_values.items():
                if column not in new_row:
                    new_row[column] = default_value
            
            result.append(new_row)
        
        return result

class DataFilteringOperation(PreprocessingOperation):
    """Operation for filtering data rows based on conditions."""
    
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter data rows based on specified conditions."""
        filters = parameters.get("filters", [])  # [{"column": "name", "operator": "contains", "value": "test"}]
        
        result = []
        for row in data:
            should_include = True
            
            for filter_condition in filters:
                column = filter_condition.get("column")
                operator = filter_condition.get("operator", "equals")
                value = filter_condition.get("value")
                
                if column not in row:
                    continue
                
                row_value = row[column]
                
                if operator == "equals" and row_value != value:
                    should_include = False
                    break
                elif operator == "not_equals" and row_value == value:
                    should_include = False
                    break
                elif operator == "contains" and value not in str(row_value):
                    should_include = False
                    break
                elif operator == "not_contains" and value in str(row_value):
                    should_include = False
                    break
                elif operator == "starts_with" and not str(row_value).startswith(str(value)):
                    should_include = False
                    break
                elif operator == "ends_with" and not str(row_value).endswith(str(value)):
                    should_include = False
                    break
            
            if should_include:
                result.append(row)
        
        return result

class DataValidationOperation(PreprocessingOperation):
    """Operation for validating data against dataset schema."""
    
    def process(self, data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate data rows against dataset schema and fix common issues."""
        required_columns = parameters.get("required_columns", [])
        column_types = parameters.get("column_types", {})  # {"column": "expected_type"}
        remove_invalid = parameters.get("remove_invalid", False)
        
        result = []
        for row in data:
            is_valid = True
            fixed_row = row.copy()
            
            # Check required columns
            for req_column in required_columns:
                if req_column not in fixed_row or fixed_row[req_column] in [None, ""]:
                    if remove_invalid:
                        is_valid = False
                        break
                    else:
                        # Add empty value for missing required column
                        fixed_row[req_column] = ""
            
            # Validate and fix column types
            for column, expected_type in column_types.items():
                if column in fixed_row:
                    try:
                        if expected_type == "string":
                            fixed_row[column] = str(fixed_row[column]) if fixed_row[column] is not None else ""
                        elif expected_type == "number":
                            fixed_row[column] = float(fixed_row[column]) if fixed_row[column] not in [None, ""] else None
                        elif expected_type == "boolean":
                            fixed_row[column] = bool(fixed_row[column]) if fixed_row[column] is not None else False
                    except (ValueError, TypeError):
                        if remove_invalid:
                            is_valid = False
                            break
                        else:
                            # Keep original value if conversion fails
                            pass
            
            if is_valid:
                result.append(fixed_row)
        
        return result

class PreprocessingFactory:
    """Factory for creating preprocessing operations."""
    
    def __init__(self):
        # Initialize operations
        self.operations = {
            "text-cleaning": TextCleaningOperation(),
            "text-normalization": TextNormalizationOperation(),
            "text-tokenization": TextTokenizationOperation(),
            "missing-data": MissingDataOperation(),
            "data-transformation": DataTransformationOperation(),
            "column-mapping": ColumnMappingOperation(),
            "data-filtering": DataFilteringOperation(),
            "data-validation": DataValidationOperation()
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
                "description": "Clean text data by removing HTML, URLs, and special characters",
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
                "description": "Normalize text data by converting case and standardizing format",
                "parameters": {
                    "columns": "array",
                    "case": "string"
                }
            },
            {
                "id": "text-tokenization",
                "name": "Text Tokenization",
                "description": "Tokenize text data into individual words or tokens",
                "parameters": {
                    "columns": "array",
                    "join_tokens": "boolean"
                }
            },
            {
                "id": "missing-data",
                "name": "Missing Data Handling",
                "description": "Handle missing data by removing or filling empty values",
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
            },
            {
                "id": "column-mapping",
                "name": "Column Mapping",
                "description": "Map column names and convert data types to match dataset schema",
                "parameters": {
                    "column_mappings": "object",
                    "type_conversions": "object",
                    "default_values": "object"
                }
            },
            {
                "id": "data-filtering",
                "name": "Data Filtering",
                "description": "Filter data rows based on specified conditions",
                "parameters": {
                    "filters": "array"
                }
            },
            {
                "id": "data-validation",
                "name": "Data Validation",
                "description": "Validate data against dataset schema and fix common issues",
                "parameters": {
                    "required_columns": "array",
                    "column_types": "object",
                    "remove_invalid": "boolean"
                }
            }
        ] 