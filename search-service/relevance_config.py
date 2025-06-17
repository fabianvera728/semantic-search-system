"""
Configuración del Sistema Avanzado de Relevancia Multifacético
============================================================

Este archivo centraliza todos los parámetros configurables del sistema de relevancia
para facilitar el ajuste y optimización según diferentes casos de uso.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os
import json


@dataclass
class RelevanceConfig:
    """Configuración principal del sistema de relevancia avanzada"""
    
    # === CALIBRACIÓN GLOBAL ===
    global_calibration_factor: float = 0.85
    """Factor de calibración global para evitar sobreestimación (rango: 0.1-1.0)"""
    
    # === BOOST LÉXICO ===
    lexical_boost_max: float = 0.15
    """Máximo boost por coincidencias léxicas - hasta 15% adicional"""
    
    # === CALIBRACIÓN DINÁMICA ===
    enable_dynamic_calibration: bool = True
    """Habilitar calibración dinámica para búsquedas híbridas"""
    
    proper_nouns_threshold: float = 0.3
    """Umbral para detectar nombres propios (% palabras con mayúscula inicial)"""
    
    semantic_weight_with_proper_nouns: float = 0.3
    """Peso semántico reducido cuando se detectan nombres propios"""
    
    semantic_weight_normal: float = 0.6
    """Peso semántico normal para consultas conceptuales"""
    
    # === PONDERACIÓN EQUILIBRADA ===
    primary_weight: float = 0.50
    """Peso de la puntuación principal (transformación sigmoide)"""
    
    alternative_1_weight: float = 0.30
    """Peso de la primera métrica alternativa (exponencial)"""
    
    alternative_2_weight: float = 0.20
    """Peso de la segunda métrica alternativa (logarítmica)"""
    
    # === TRANSFORMACIÓN SIGMOIDE ===
    sigmoid_steepness: float = 10.0
    """Pendiente de la función sigmoide (mayor = más contraste)"""
    
    sigmoid_midpoint: float = 0.5
    """Punto medio de la transformación sigmoide"""
    
    # === MÉTRICAS ALTERNATIVAS ===
    exponential_decay_rate: float = 2.0
    """Tasa de decaimiento para la métrica exponencial"""
    
    term_boost_factor: float = 0.3
    """Factor de boost por superposición de términos en métrica alternativa 1"""
    
    optimal_length_ratio: float = 2.0
    """Ratio de longitud óptimo (resultado/consulta)"""
    
    length_variance_tolerance: float = 1.5
    """Tolerancia de varianza para el factor de longitud óptima"""
    
    # === AJUSTES FINALES ===
    min_confidence_threshold: float = 0.1
    """Umbral mínimo de confianza (resultados debajo son penalizados)"""
    
    low_confidence_penalty: float = 0.5
    """Factor de penalización para resultados de baja confianza"""
    
    multiple_methods_boost: float = 0.1
    """Boost para resultados encontrados por múltiples métodos (10%)"""
    
    high_score_compression_threshold: float = 0.95
    """Umbral para compresión de scores muy altos (evitar artificiales)"""
    
    high_score_compression_factor: float = 0.5
    """Factor de compresión para scores superiores al umbral"""
    
    # === PARÁMETROS DE BÚSQUEDA HÍBRIDA ===
    hybrid_min_confidence: float = 0.15
    """Umbral mínimo de confianza para búsquedas híbridas"""
    
    hybrid_calibration_base: float = 0.8
    """Factor base de calibración para búsquedas híbridas"""
    
    hybrid_calibration_range: float = 0.2
    """Rango de ajuste para calibración híbrida"""
    
    # === COINCIDENCIA DE TÉRMINOS ===
    jaccard_weight: float = 0.7
    """Peso de la similitud Jaccard en cálculo de términos"""
    
    exact_match_weight: float = 0.3
    """Peso de coincidencias exactas en cálculo de términos"""
    
    # === OPTIMIZACIÓN DE RENDIMIENTO ===
    candidate_multiplier: int = 3
    """Multiplicador de candidatos para mejor normalización"""
    
    max_candidates_limit: int = 100
    """Límite máximo de candidatos a procesar"""


class ConfigManager:
    """Gestor de configuración del sistema de relevancia"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_file: Ruta al archivo de configuración JSON (opcional)
        """
        self.config_file = config_file or os.getenv('RELEVANCE_CONFIG_FILE', 'relevance_config.json')
        self.config = self._load_config()
    
    def _load_config(self) -> RelevanceConfig:
        """Carga configuración desde archivo o usa valores por defecto"""
        
        # Valores por defecto
        config = RelevanceConfig()
        
        # Intentar cargar desde archivo
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    
                # Actualizar configuración con valores del archivo
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                        
                print(f"✅ Configuración cargada desde: {self.config_file}")
                        
            except Exception as e:
                print(f"⚠️  Error cargando configuración: {e}, usando valores por defecto")
        
        # Cargar desde variables de entorno si están disponibles
        self._load_from_environment(config)
        
        return config
    
    def _load_from_environment(self, config: RelevanceConfig):
        """Carga parámetros desde variables de entorno"""
        
        env_mappings = {
            'RELEVANCE_GLOBAL_CALIBRATION': 'global_calibration_factor',
            'RELEVANCE_LEXICAL_BOOST_MAX': 'lexical_boost_max',
            'RELEVANCE_ENABLE_DYNAMIC_CALIBRATION': 'enable_dynamic_calibration',
            'RELEVANCE_PRIMARY_WEIGHT': 'primary_weight',
            'RELEVANCE_ALT1_WEIGHT': 'alternative_1_weight',
            'RELEVANCE_ALT2_WEIGHT': 'alternative_2_weight',
            'RELEVANCE_SIGMOID_STEEPNESS': 'sigmoid_steepness',
            'RELEVANCE_MIN_CONFIDENCE': 'min_confidence_threshold'
        }
        
        for env_var, config_attr in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # Convertir el tipo apropiado
                    if config_attr == 'enable_dynamic_calibration':
                        value = env_value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        value = float(env_value)
                    
                    setattr(config, config_attr, value)
                    print(f"🔧 Parámetro {config_attr} cargado desde env: {value}")
                    
                except ValueError:
                    print(f"⚠️  Valor inválido para {env_var}: {env_value}")
    
    def save_config(self):
        """Guarda la configuración actual en archivo"""
        
        try:
            config_dict = {
                key: getattr(self.config, key)
                for key in dir(self.config)
                if not key.startswith('_') and not callable(getattr(self.config, key))
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(config_dict, file, indent=2, ensure_ascii=False)
                
            print(f"✅ Configuración guardada en: {self.config_file}")
            
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
    
    def update_config(self, updates: Dict[str, Any]):
        """
        Actualiza parámetros de configuración
        
        Args:
            updates: Diccionario con los parámetros a actualizar
        """
        updated_count = 0
        
        for key, value in updates.items():
            if hasattr(self.config, key):
                # Validar rangos si es necesario
                if self._validate_parameter(key, value):
                    setattr(self.config, key, value)
                    updated_count += 1
                    print(f"✅ {key} actualizado a: {value}")
                else:
                    print(f"❌ Valor inválido para {key}: {value}")
            else:
                print(f"⚠️  Parámetro desconocido: {key}")
        
        print(f"🔧 {updated_count} parámetros actualizados")
        
        # Auto-guardar si hay cambios
        if updated_count > 0:
            self.save_config()
    
    def _validate_parameter(self, key: str, value: Any) -> bool:
        """Valida que un parámetro esté en rango válido"""
        
        validations = {
            'global_calibration_factor': lambda x: 0.1 <= x <= 1.0,
            'lexical_boost_max': lambda x: 0.0 <= x <= 0.5,
            'primary_weight': lambda x: 0.0 <= x <= 1.0,
            'alternative_1_weight': lambda x: 0.0 <= x <= 1.0,
            'alternative_2_weight': lambda x: 0.0 <= x <= 1.0,
            'sigmoid_steepness': lambda x: 1.0 <= x <= 50.0,
            'sigmoid_midpoint': lambda x: 0.0 <= x <= 1.0,
            'min_confidence_threshold': lambda x: 0.0 <= x <= 0.5,
            'proper_nouns_threshold': lambda x: 0.0 <= x <= 1.0
        }
        
        if key in validations:
            return validations[key](value)
        
        return True  # Sin validación específica
    
    def get_tuning_recommendations(self) -> Dict[str, str]:
        """Obtiene recomendaciones para ajuste de parámetros"""
        
        recommendations = {
            "Para mejorar precisión": {
                "sigmoid_steepness": "Aumentar para mayor contraste entre resultados",
                "global_calibration_factor": "Reducir si scores son muy altos sistemáticamente",
                "min_confidence_threshold": "Aumentar para filtrar resultados de baja calidad"
            },
            "Para mejorar recall": {
                "lexical_boost_max": "Aumentar para valorar más coincidencias exactas",
                "sigmoid_steepness": "Reducir para suavizar diferencias",
                "primary_weight": "Reducir y aumentar pesos alternativos"
            },
            "Para consultas con nombres propios": {
                "proper_nouns_threshold": "Ajustar según idioma y dominio",
                "semantic_weight_with_proper_nouns": "Reducir para favorecer exactas"
            },
            "Para optimizar rendimiento": {
                "candidate_multiplier": "Reducir si hay problemas de latencia",
                "max_candidates_limit": "Ajustar según recursos disponibles"
            }
        }
        
        return recommendations
    
    def generate_config_template(self) -> str:
        """Genera template de configuración con documentación"""
        
        template = """
{
  "_metadata": {
    "version": "1.0",
    "description": "Configuración del Sistema Avanzado de Relevancia",
    "last_updated": "2024-01-01"
  },
  
  "_documentation": {
    "global_calibration_factor": "Factor de calibración global (0.1-1.0) - evita sobreestimación",
    "lexical_boost_max": "Boost máximo por coincidencias léxicas (0.0-0.5)",
    "primary_weight": "Peso de puntuación sigmoide (debe sumar 1.0 con alternativas)",
    "alternative_1_weight": "Peso métrica exponencial",
    "alternative_2_weight": "Peso métrica logarítmica",
    "sigmoid_steepness": "Contraste de transformación sigmoide (1.0-50.0)"
  },
  
  "global_calibration_factor": 0.85,
  "lexical_boost_max": 0.15,
  "enable_dynamic_calibration": true,
  "primary_weight": 0.50,
  "alternative_1_weight": 0.30,
  "alternative_2_weight": 0.20,
  "sigmoid_steepness": 10.0,
  "sigmoid_midpoint": 0.5,
  "min_confidence_threshold": 0.1,
  "proper_nouns_threshold": 0.3,
  "semantic_weight_with_proper_nouns": 0.3,
  "semantic_weight_normal": 0.6
}
"""
        return template


# Instancia global del gestor de configuración
config_manager = ConfigManager()

def get_relevance_config() -> RelevanceConfig:
    """Obtiene la configuración actual del sistema de relevancia"""
    return config_manager.config

def update_relevance_config(updates: Dict[str, Any]):
    """Actualiza la configuración del sistema de relevancia"""
    config_manager.update_config(updates)

def reset_to_defaults():
    """Resetea la configuración a valores por defecto"""
    config_manager.config = RelevanceConfig()
    config_manager.save_config()
    print("✅ Configuración reseteada a valores por defecto")


if __name__ == "__main__":
    # Script de utilidad para gestión de configuración
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestor de configuración de relevancia")
    parser.add_argument('--show', action='store_true', help='Mostrar configuración actual')
    parser.add_argument('--template', action='store_true', help='Generar template de configuración')
    parser.add_argument('--reset', action='store_true', help='Resetear a valores por defecto')
    parser.add_argument('--recommendations', action='store_true', help='Mostrar recomendaciones de ajuste')
    
    args = parser.parse_args()
    
    if args.show:
        config = get_relevance_config()
        print("📋 CONFIGURACIÓN ACTUAL:")
        for key in dir(config):
            if not key.startswith('_'):
                value = getattr(config, key)
                print(f"   {key}: {value}")
    
    elif args.template:
        print("📄 TEMPLATE DE CONFIGURACIÓN:")
        print(config_manager.generate_config_template())
    
    elif args.reset:
        reset_to_defaults()
    
    elif args.recommendations:
        recommendations = config_manager.get_tuning_recommendations()
        print("💡 RECOMENDACIONES DE AJUSTE:")
        for category, tips in recommendations.items():
            print(f"\n{category}:")
            for param, desc in tips.items():
                print(f"   • {param}: {desc}")
    
    else:
        print("Usa --help para ver las opciones disponibles") 