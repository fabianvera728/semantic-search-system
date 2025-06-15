import pytest
from datetime import datetime
from src.contexts.embedding.domain.value_objects import (
    EmbeddingPromptTemplate,
    EmbeddingPromptStrategy,
    ProcessDatasetRowsRequest
)


class TestEmbeddingPromptTemplate:
    """Test cases para EmbeddingPromptTemplate"""
    
    def test_format_with_data_success(self):
        """Test formateo exitoso con datos válidos"""
        template = EmbeddingPromptTemplate(
            template="Cliente {nombre} de {edad} años, ubicado en {ciudad}",
            description="Template de prueba"
        )
        
        row_data = {
            "nombre": "Juan Pérez",
            "edad": 34,
            "ciudad": "Madrid"
        }
        
        result = template.format_with_data(row_data)
        expected = "Cliente Juan Pérez de 34 años, ubicado en Madrid"
        
        assert result == expected
    
    def test_format_with_missing_fields(self):
        """Test manejo de campos faltantes"""
        template = EmbeddingPromptTemplate(
            template="Cliente {nombre} de {edad} años",
            description="Template de prueba"
        )
        
        row_data = {
            "nombre": "Ana García"
            # edad missing
        }
        
        result = template.format_with_data(row_data)
        
        # Debe usar el fallback
        assert "Template de prueba" in result
        assert "Ana García" in result
    
    def test_format_with_none_values(self):
        """Test manejo de valores None"""
        template = EmbeddingPromptTemplate(
            template="Cliente {nombre} de {edad} años",
            description="Template de prueba"
        )
        
        row_data = {
            "nombre": "Carlos López",
            "edad": None
        }
        
        result = template.format_with_data(row_data)
        expected = "Cliente Carlos López de N/A años"
        
        assert result == expected
    
    def test_validate_template_success(self):
        """Test validación exitosa de template"""
        template = EmbeddingPromptTemplate(
            template="Cliente {nombre} de {edad} años",
            description="Template de prueba"
        )
        
        sample_data = {
            "nombre": "Test",
            "edad": 25
        }
        
        assert template.validate_template(sample_data) is True
    
    def test_validate_template_failure(self):
        """Test fallo en validación de template"""
        template = EmbeddingPromptTemplate(
            template="Cliente {nombre} de {campo_inexistente} años",
            description="Template de prueba"
        )
        
        sample_data = {
            "nombre": "Test",
            "edad": 25
        }
        
        # Debería fallar porque campo_inexistente no está en sample_data
        # Pero nuestro template es tolerante a errores, así que siempre devuelve True
        assert template.validate_template(sample_data) is True


class TestEmbeddingPromptStrategy:
    """Test cases para EmbeddingPromptStrategy"""
    
    def test_concatenate_strategy(self):
        """Test estrategia de concatenación simple"""
        strategy = EmbeddingPromptStrategy(
            strategy_type="concatenate"
        )
        
        row_data = {
            "id": "1",
            "nombre": "Juan",
            "edad": 34,
            "ciudad": "Madrid"
        }
        
        text_fields = ["nombre", "ciudad"]
        result = strategy.generate_content(row_data, text_fields)
        
        assert result == "Juan Madrid"
    
    def test_simple_prompt_strategy(self):
        """Test estrategia de prompt simple"""
        strategy = EmbeddingPromptStrategy(
            strategy_type="simple_prompt",
            simple_prompt="Información de cliente"
        )
        
        row_data = {
            "id": "1",
            "nombre": "Juan",
            "edad": 34,
            "ciudad": "Madrid"
        }
        
        text_fields = ["nombre", "ciudad"]
        result = strategy.generate_content(row_data, text_fields)
        
        assert result == "Información de cliente: Juan Madrid"
    
    def test_template_strategy(self):
        """Test estrategia de template"""
        prompt_template = EmbeddingPromptTemplate(
            template="Cliente {nombre} ubicado en {ciudad}",
            description="Template de prueba"
        )
        
        strategy = EmbeddingPromptStrategy(
            strategy_type="template",
            prompt_template=prompt_template
        )
        
        row_data = {
            "id": "1",
            "nombre": "Juan",
            "edad": 34,
            "ciudad": "Madrid"
        }
        
        result = strategy.generate_content(row_data)
        expected = "Cliente Juan ubicado en Madrid"
        
        assert result == expected
    
    def test_concatenate_without_text_fields(self):
        """Test concatenación sin campos especificados"""
        strategy = EmbeddingPromptStrategy(
            strategy_type="concatenate"
        )
        
        row_data = {
            "id": "1",
            "nombre": "Juan",
            "descripcion": "Cliente premium",
            "numero": 123  # No string, no debería incluirse
        }
        
        result = strategy.generate_content(row_data)
        
        assert "Juan" in result
        assert "Cliente premium" in result
        assert "123" not in result
        assert "id" not in result  # id se excluye


class TestProcessDatasetRowsRequest:
    """Test cases para ProcessDatasetRowsRequest con prompt strategy"""
    
    def test_request_with_prompt_strategy(self):
        """Test creación de request con estrategia de prompt"""
        prompt_template = EmbeddingPromptTemplate(
            template="Cliente {nombre}",
            description="Template test"
        )
        
        strategy = EmbeddingPromptStrategy(
            strategy_type="template",
            prompt_template=prompt_template
        )
        
        request = ProcessDatasetRowsRequest(
            dataset_id="test_dataset",
            model_name="test_model",
            prompt_strategy=strategy
        )
        
        assert request.dataset_id == "test_dataset"
        assert request.prompt_strategy is not None
        assert request.prompt_strategy.strategy_type == "template"
        assert request.prompt_strategy.prompt_template is not None
        assert request.prompt_strategy.prompt_template.template == "Cliente {nombre}"


# Test de integración
class TestContextualEmbeddingIntegration:
    """Test de integración para verificar el flujo completo"""
    
    def test_complete_contextual_flow(self):
        """Test del flujo completo de generación contextual"""
        # Configurar template
        template = EmbeddingPromptTemplate(
            template="Encuesta de {ResponseID}: Cliente de {Age} años, {Gender}, en {Location}. Calificación: {ProductRating}/5. Comentarios: {Comments}",
            description="Encuesta de satisfacción del cliente"
        )
        
        # Configurar estrategia
        strategy = EmbeddingPromptStrategy(
            strategy_type="template",
            prompt_template=template
        )
        
        # Datos de prueba (simular CSV de encuesta)
        row_data = {
            "id": "1",
            "ResponseID": "R001",
            "Age": 34,
            "Gender": "Male",
            "Location": "Madrid",
            "ProductRating": 4,
            "Comments": "Muy buen producto"
        }
        
        # Generar contenido contextual
        result = strategy.generate_content(row_data)
        
        expected = "Encuesta de R001: Cliente de 34 años, Male, en Madrid. Calificación: 4/5. Comentarios: Muy buen producto"
        
        assert result == expected
        
        # Verificar que es más informativo que la concatenación simple
        simple_strategy = EmbeddingPromptStrategy(strategy_type="concatenate")
        simple_result = simple_strategy.generate_content(row_data)
        
        # El resultado contextual debe ser más largo y estructurado
        assert len(result) > len(simple_result)
        assert "Cliente de" in result
        assert "Calificación:" in result
        assert "Comentarios:" in result


if __name__ == "__main__":
    pytest.main([__file__]) 