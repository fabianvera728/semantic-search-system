from uuid import UUID


class DatasetException(Exception):
    """Base exception for all dataset-related errors"""
    pass


class DatasetNotFoundError(DatasetException):
    """Exception raised when a dataset is not found"""
    def __init__(self, dataset_id: UUID):
        self.dataset_id = dataset_id
        super().__init__(f"Dataset with ID {dataset_id} not found")


class DatasetValidationError(DatasetException):
    """Exception raised when dataset validation fails"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UnauthorizedAccessError(DatasetException):
    """Exception raised when a user tries to access a dataset they don't have permission for"""
    def __init__(self, user_id: str, dataset_id: UUID):
        self.user_id = user_id
        self.dataset_id = dataset_id
        super().__init__(f"User {user_id} is not authorized to access dataset {dataset_id}")


class ColumnNotFoundError(DatasetException):
    """Exception raised when a column is not found in a dataset"""
    def __init__(self, column_name: str, dataset_id: UUID):
        self.column_name = column_name
        self.dataset_id = dataset_id
        super().__init__(f"Column {column_name} not found in dataset {dataset_id}") 