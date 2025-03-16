from typing import Optional


class SearchException(Exception):
    """Excepción base para todas las excepciones relacionadas con la búsqueda"""
    pass


class DatasetNotFoundException(SearchException):
    """Excepción lanzada cuando no se encuentra un dataset"""
    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        super().__init__(f"Dataset con ID {dataset_id} no encontrado")


class EmbeddingModelNotFoundException(SearchException):
    """Excepción lanzada cuando no se encuentra un modelo de embedding"""
    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(f"Modelo de embedding {model_name} no encontrado")


class EmbeddingGenerationException(SearchException):
    """Excepción lanzada cuando hay un error al generar embeddings"""
    def __init__(self, message: str, model_name: Optional[str] = None):
        self.model_name = model_name
        self.message = message
        msg = f"Error al generar embeddings"
        if model_name:
            msg += f" con el modelo {model_name}"
        msg += f": {message}"
        super().__init__(msg)


class SearchExecutionException(SearchException):
    """Excepción lanzada cuando hay un error al ejecutar una búsqueda"""
    def __init__(self, message: str, dataset_id: Optional[str] = None):
        self.dataset_id = dataset_id
        self.message = message
        msg = f"Error al ejecutar la búsqueda"
        if dataset_id:
            msg += f" en el dataset {dataset_id}"
        msg += f": {message}"
        super().__init__(msg)


class InvalidSearchTypeException(SearchException):
    """Excepción lanzada cuando se especifica un tipo de búsqueda inválido"""
    def __init__(self, search_type: str):
        self.search_type = search_type
        super().__init__(f"Tipo de búsqueda inválido: {search_type}")


class DataStorageConnectionException(SearchException):
    """Excepción lanzada cuando hay un error al conectar con el servicio de almacenamiento de datos"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Error al conectar con el servicio de almacenamiento de datos: {message}")


class EmptyQueryException(SearchException):
    """Excepción lanzada cuando se proporciona una consulta vacía"""
    def __init__(self):
        super().__init__("La consulta de búsqueda no puede estar vacía") 