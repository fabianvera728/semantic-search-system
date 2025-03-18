from uuid import UUID
from typing import Optional


class EmbeddingServiceException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EmbeddingGenerationError(EmbeddingServiceException):
    def __init__(self, text: str, model: str, error_message: Optional[str] = None):
        message = f"Failed to generate embedding for text using model {model}"
        if error_message:
            message += f": {error_message}"
        super().__init__(message)
        self.text = text
        self.model = model
        self.error_message = error_message


class EmbeddingNotFoundError(EmbeddingServiceException):
    def __init__(self, embedding_id: UUID, dataset_id: Optional[str] = None):
        if dataset_id:
            message = f"Embedding with ID {embedding_id} not found in dataset {dataset_id}"
        else:
            message = f"Embedding with ID {embedding_id} not found"
        super().__init__(message)
        self.embedding_id = embedding_id
        self.dataset_id = dataset_id


class ModelNotFoundError(EmbeddingServiceException):
    def __init__(self, model_name: str):
        super().__init__(f"Embedding model '{model_name}' not found")
        self.model_name = model_name


class DatasetNotFoundError(EmbeddingServiceException):
    def __init__(self, dataset_id: str):
        super().__init__(f"Dataset with ID {dataset_id} not found")
        self.dataset_id = dataset_id


class DataStorageError(EmbeddingServiceException):
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(f"Data storage error: {message}")
        self.original_error = original_error


class InvalidRequestError(EmbeddingServiceException):
    def __init__(self, message: str):
        super().__init__(f"Invalid request: {message}")


class UnauthorizedError(EmbeddingServiceException):
    def __init__(self, message: Optional[str] = None):
        if message:
            super().__init__(f"Unauthorized: {message}")
        else:
            super().__init__("Unauthorized access")


class VectorDBError(EmbeddingServiceException):
    def __init__(self, message: str, db_type: str, original_error: Optional[Exception] = None):
        super().__init__(f"Vector database ({db_type}) error: {message}")
        self.db_type = db_type
        self.original_error = original_error 