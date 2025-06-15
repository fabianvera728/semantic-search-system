from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EmbeddingId:
    value: UUID


@dataclass(frozen=True)
class DatasetId:
    value: str


@dataclass(frozen=True)
class RowId:
    value: str


@dataclass(frozen=True)
class TextContent:
    value: str
    field_name: str = ""


@dataclass(frozen=True)
class ModelName:
    value: str


@dataclass(frozen=True)
class EmbeddingPromptTemplate:
    """Template para generar texto contextualizado para embeddings"""
    template: str
    description: str
    field_mappings: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def format_with_data(self, row_data: Dict[str, Any]) -> str:
        """Genera el texto final usando el template y los datos del registro"""
        try:
            # Crear datos seguros reemplazando valores None con "N/A"
            safe_data = {}
            for key, value in row_data.items():
                if value is None or value == "":
                    safe_data[key] = "N/A"
                else:
                    safe_data[key] = str(value)
            
            return self.template.format(**safe_data)
        except KeyError as e:
            # Si falta algún campo requerido, usar un formato más simple
            available_fields = ", ".join([f"{k}: {v}" for k, v in row_data.items() if v is not None])
            return f"{self.description}. Datos: {available_fields}"
        except Exception as e:
            # Fallback en caso de error
            return f"{self.description}. Raw data: {str(row_data)}"
    
    def validate_template(self, sample_data: Dict[str, Any]) -> bool:
        """Valida si el template es compatible con los datos de muestra"""
        try:
            self.format_with_data(sample_data)
            return True
        except Exception:
            return False


@dataclass(frozen=True)
class EmbeddingPromptStrategy:
    """Estrategia para generar contenido contextualizado"""
    strategy_type: Literal["concatenate", "simple_prompt", "template"] = "concatenate"
    simple_prompt: Optional[str] = None
    prompt_template: Optional[EmbeddingPromptTemplate] = None
    
    def generate_content(self, row_data: Dict[str, Any], text_fields: Optional[List[str]] = None) -> str:
        """Genera contenido basado en la estrategia configurada"""
        if self.strategy_type == "template" and self.prompt_template:
            return self.prompt_template.format_with_data(row_data)
        
        elif self.strategy_type == "simple_prompt" and self.simple_prompt:
            # Concatenar campos de texto
            if text_fields:
                content = " ".join([
                    str(row_data.get(field, "")) 
                    for field in text_fields 
                    if field in row_data and row_data.get(field)
                ])
            else:
                content = " ".join([
                    str(value) 
                    for key, value in row_data.items() 
                    if isinstance(value, str) and key != "id" and value
                ])
            
            return f"{self.simple_prompt}: {content}" if content.strip() else ""
        
        else:  # concatenate (default)
            if text_fields:
                return " ".join([
                    str(row_data.get(field, "")) 
                    for field in text_fields 
                    if field in row_data and row_data.get(field)
                ])
            else:
                return " ".join([
                    str(value) 
                    for key, value in row_data.items() 
                    if isinstance(value, str) and key != "id" and value
                ])


@dataclass(frozen=True)
class GenerateEmbeddingRequest:
    text: str
    dataset_id: str
    row_id: str
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    batch_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchEmbeddingRequest:
    texts: List[str]
    dataset_id: str
    row_ids: List[str]
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    batch_size: int = 32
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeleteEmbeddingRequest:
    embedding_id: UUID
    dataset_id: str


@dataclass(frozen=True)
class GetEmbeddingRequest:
    embedding_id: UUID
    dataset_id: str


@dataclass(frozen=True)
class ListEmbeddingsRequest:
    dataset_id: str
    limit: int = 100
    offset: int = 0
    filter_criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CreateDatasetRequest:
    dataset_id: str
    name: str
    dimension: int = 384
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessDatasetRowsRequest:
    dataset_id: str
    rows: Optional[List[Dict[str, Any]]] = None
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    text_fields: Optional[List[str]] = None
    batch_size: int = 32
    force_refresh: bool = False
    # Nueva funcionalidad para prompts contextuales
    prompt_strategy: Optional[EmbeddingPromptStrategy] = None


@dataclass(frozen=True)
class EmbeddingResult:
    embedding_id: UUID
    dataset_id: str
    row_id: str
    model_name: str
    dimension: int
    created_at: datetime = field(default_factory=datetime.now)
    status: Literal["success", "error"] = "success"
    error_message: str = "" 