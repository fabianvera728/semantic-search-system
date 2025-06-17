from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Tuple, Optional
import numpy as np
import logging
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScoringMetrics:
    """Métricas detalladas de puntuación"""
    semantic_score: float
    term_overlap_score: float
    length_penalty: float
    diversity_bonus: float
    alternative_metric_1: float
    alternative_metric_2: float
    lexical_boost: float
    final_score: float
    calibrated_score: float


class ScoringStrategy(ABC):
    """Estrategia base para cálculo de puntuaciones en búsqueda semántica"""
    
    @abstractmethod
    def calculate_score(
        self,
        semantic_distance: float,
        query_terms: Set[str],
        result_terms: Set[str],
        result_length: int,
        query_length: int,
        diversity_penalty: float = 0.0,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calcula la puntuación final para un resultado de búsqueda"""
        pass


class AdvancedRelevanceStrategy(ScoringStrategy):
    """
    Estrategia avanzada de relevancia que implementa el sistema multifacético 
    descrito con normalización, transformación sigmoide, métricas alternativas 
    y calibración global/dinámica
    """
    
    def __init__(self, 
                 global_calibration_factor: float = 0.85,
                 lexical_boost_max: float = 0.15,
                 enable_dynamic_calibration: bool = True):
        """
        Inicializa la estrategia avanzada de relevancia
        
        Args:
            global_calibration_factor: Factor de calibración global para evitar sobreestimación
            lexical_boost_max: Máximo boost por coincidencias léxicas (hasta 15%)
            enable_dynamic_calibration: Habilitar calibración dinámica para búsquedas híbridas
        """
        self.global_calibration_factor = global_calibration_factor
        self.lexical_boost_max = lexical_boost_max
        self.enable_dynamic_calibration = enable_dynamic_calibration
        
        # Pesos para ponderación equilibrada según especificación
        self.primary_weight = 0.50      # Puntuación principal (sigmoide)
        self.alternative_1_weight = 0.30  # Primera métrica alternativa  
        self.alternative_2_weight = 0.20  # Segunda métrica alternativa
        
        # Cache para normalización de distancias
        self._distance_stats_cache = {}
        
        logger.info(f"Estrategia avanzada de relevancia inicializada - "
                   f"Calibración global: {global_calibration_factor}, "
                   f"Boost léxico máximo: {lexical_boost_max}")
    
    def calculate_score(
        self,
        semantic_distance: float,
        query_terms: Set[str],
        result_terms: Set[str],
        result_length: int,
        query_length: int,
        diversity_penalty: float = 0.0,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calcula la puntuación usando el proceso multifacético completo
        """
        if context is None:
            context = {}
            
        # 1. Normalización de distancias vectoriales
        normalized_distance = self._normalize_vector_distance(
            semantic_distance, 
            context.get('distance_stats', {})
        )
        
        # 2. Transformación no lineal (función sigmoide)
        primary_score = self._sigmoid_transformation(normalized_distance)
        
        # 3. Cálculo de métricas alternativas
        alt_metric_1 = self._calculate_alternative_metric_1(
            semantic_distance, query_terms, result_terms
        )
        alt_metric_2 = self._calculate_alternative_metric_2(
            semantic_distance, result_length, query_length
        )
        
        # 4. Ponderación equilibrada
        weighted_score = self._balanced_weighting(
            primary_score, alt_metric_1, alt_metric_2
        )
        
        # 5. Ajuste contextual (boost léxico)
        lexical_boost = self._calculate_lexical_boost(query_terms, result_terms)
        contextual_score = weighted_score * (1.0 + lexical_boost)
        
        # 6. Calibración global
        calibrated_score = self._apply_global_calibration(contextual_score)
        
        # 7. Calibración dinámica para búsquedas híbridas
        if self.enable_dynamic_calibration and context.get('search_type') == 'hybrid':
            final_score = self._apply_dynamic_calibration(
                calibrated_score, context
            )
        else:
            final_score = calibrated_score
        
        # 8. Factores de ajuste final
        final_score = self._apply_final_adjustments(
            final_score, diversity_penalty, context
        )
        
        # Crear métricas detalladas para análisis
        metrics = ScoringMetrics(
            semantic_score=1.0 - normalized_distance,
            term_overlap_score=len(query_terms.intersection(result_terms)) / len(query_terms) if query_terms else 0,
            length_penalty=self._calculate_length_factor(result_length, query_length),
            diversity_bonus=max(0, 0.2 - diversity_penalty),
            alternative_metric_1=alt_metric_1,
            alternative_metric_2=alt_metric_2,
            lexical_boost=lexical_boost,
            final_score=weighted_score,
            calibrated_score=final_score
        )
        
        # Log detallado para análisis
        logger.debug(f"Scoring breakdown - Primary: {primary_score:.3f}, "
                    f"Alt1: {alt_metric_1:.3f}, Alt2: {alt_metric_2:.3f}, "
                    f"Weighted: {weighted_score:.3f}, Lexical boost: {lexical_boost:.3f}, "
                    f"Final: {final_score:.3f}")
        
        return min(max(final_score, 0.0), 1.0)
    
    def _normalize_vector_distance(self, distance: float, distance_stats: Dict[str, float]) -> float:
        """
        Normaliza la distancia vectorial al rango [0, 1] usando estadísticas de la consulta
        """
        min_dist = distance_stats.get('min_distance', 0.0)
        max_dist = distance_stats.get('max_distance', 1.0)
        
        if max_dist <= min_dist:
            return 0.0
            
        # Normalizar al rango [0, 1]
        normalized = (distance - min_dist) / (max_dist - min_dist)
        
        # Invertir escala para que valores altos = mayor similitud
        return 1.0 - min(max(normalized, 0.0), 1.0)
    
    def _sigmoid_transformation(self, normalized_similarity: float) -> float:
        """
        Aplica transformación sigmoide para amplificar diferencias entre resultados
        """
        # Parámetros ajustados para crear contraste definido
        # k controla la pendiente, x0 es el punto medio
        k = 10.0  # Pendiente más pronunciada
        x0 = 0.5  # Punto medio
        
        # Función sigmoide: 1 / (1 + e^(-k(x - x0)))
        try:
            sigmoid_value = 1.0 / (1.0 + math.exp(-k * (normalized_similarity - x0)))
            return sigmoid_value
        except (OverflowError, ZeroDivisionError):
            # Fallback para casos extremos
            return 1.0 if normalized_similarity > x0 else 0.0
    
    def _calculate_alternative_metric_1(self, distance: float, query_terms: Set[str], result_terms: Set[str]) -> float:
        """
        Primera métrica alternativa: transformación exponencial con boost por términos
        """
        # Transformación exponencial de la distancia original
        exp_metric = math.exp(-2.0 * distance)  # e^(-2d)
        
        # Boost por superposición de términos
        if query_terms and result_terms:
            term_overlap_ratio = len(query_terms.intersection(result_terms)) / len(query_terms)
            term_boost = 1.0 + (term_overlap_ratio * 0.3)  # Hasta 30% de boost
            exp_metric *= term_boost
        
        return min(exp_metric, 1.0)
    
    def _calculate_alternative_metric_2(self, distance: float, result_length: int, query_length: int) -> float:
        """
        Segunda métrica alternativa: transformación logarítmica con factor de longitud
        """
        # Transformación logarítmica: -log(1 + distance)
        log_metric = -math.log(1.0 + distance) + math.log(2.0)  # Normalizar a [0,1] aprox
        log_metric = max(0.0, log_metric)
        
        # Factor de longitud óptima
        length_factor = self._calculate_length_factor(result_length, query_length)
        
        return min(log_metric * (1.0 + length_factor * 0.2), 1.0)
    
    def _calculate_length_factor(self, result_length: int, query_length: int) -> float:
        """
        Calcula factor de longitud óptima
        """
        if query_length == 0:
            return 0.0
            
        ratio = result_length / query_length
        
        # Función gaussiana centrada en ratio = 2.0 (longitud óptima)
        optimal_ratio = 2.0
        sigma = 1.5
        
        length_factor = math.exp(-0.5 * ((ratio - optimal_ratio) / sigma) ** 2)
        return length_factor
    
    def _balanced_weighting(self, primary: float, alt1: float, alt2: float) -> float:
        """
        Aplica ponderación equilibrada: 50% principal, 30% alt1, 20% alt2
        """
        weighted_score = (
            self.primary_weight * primary +
            self.alternative_1_weight * alt1 +
            self.alternative_2_weight * alt2
        )
        
        return weighted_score
    
    def _calculate_lexical_boost(self, query_terms: Set[str], result_terms: Set[str]) -> float:
        """
        Calcula boost léxico basado en coincidencias exactas de términos
        """
        if not query_terms:
            return 0.0
        
        # Proporción de términos de la consulta que aparecen en el resultado
        term_match_ratio = len(query_terms.intersection(result_terms)) / len(query_terms)
        
        # Aplicar boost moderado hasta el máximo configurado
        lexical_boost = term_match_ratio * self.lexical_boost_max
        
        return lexical_boost
    
    def _apply_global_calibration(self, score: float) -> float:
        """
        Aplica calibración global para evitar sobreestimación
        """
        # Factor de calibración que refleja que raramente hay correspondencia perfecta
        calibrated = score * self.global_calibration_factor
        
        # Función de compresión suave para mantener gradiente
        compressed = calibrated / (calibrated + (1.0 - calibrated) * 0.3)
        
        return compressed
    
    def _apply_dynamic_calibration(self, score: float, context: Dict[str, Any]) -> float:
        """
        Aplica calibración dinámica para búsquedas híbridas con parámetro alfa dinámico
        """
        # Obtener información del contexto
        query = context.get('query', '')
        has_proper_nouns = self._detect_proper_nouns(query)
        
        # Calcular alfa dinámico
        if has_proper_nouns:
            # Reducir peso semántico para favorecer coincidencias exactas
            alpha = 0.3
        else:
            # Balance normal entre semántico y léxico
            alpha = 0.6
        
        # Aplicar calibración basada en alfa
        semantic_weight = alpha
        lexical_weight = 1.0 - alpha
        
        # Ajustar puntuación según el balance semántico/léxico detectado
        calibration_factor = 0.8 + (semantic_weight * 0.2)  # Entre 0.8 y 1.0
        
        return score * calibration_factor
    
    def _detect_proper_nouns(self, query: str) -> bool:
        """
        Detección simple de nombres propios en la consulta
        """
        words = query.split()
        proper_noun_count = sum(1 for word in words if word and word[0].isupper())
        
        # Si más del 30% de palabras empiezan con mayúscula, probable nombres propios
        return (proper_noun_count / len(words)) > 0.3 if words else False
    
    def _apply_final_adjustments(self, score: float, diversity_penalty: float, context: Dict[str, Any]) -> float:
        """
        Aplica factores de ajuste final
        """
        adjusted_score = score
        
        # 1. Filtro de puntuación mínima
        min_confidence_threshold = context.get('min_confidence', 0.1)
        if adjusted_score < min_confidence_threshold:
            adjusted_score *= 0.5  # Penalizar resultados de muy baja confianza
        
        # 2. Boost por coincidencia en múltiples métodos
        multiple_method_match = context.get('found_by_multiple_methods', False)
        if multiple_method_match:
            adjusted_score *= 1.1  # 10% de boost por coincidencia múltiple
        
        # 3. Penalización por diversidad
        diversity_factor = max(0.0, 1.0 - diversity_penalty)
        adjusted_score *= diversity_factor
        
        # 4. Suavizado final para evitar scores perfectos artificiales
        if adjusted_score > 0.95:
            adjusted_score = 0.90 + (adjusted_score - 0.95) * 0.5
        
        return adjusted_score
    
    def update_global_calibration(self, new_factor: float) -> None:
        """
        Actualiza el factor de calibración global
        """
        self.global_calibration_factor = max(0.1, min(1.0, new_factor))
        logger.info(f"Factor de calibración global actualizado a: {self.global_calibration_factor}")
    
    def get_detailed_metrics(self, 
                           semantic_distance: float,
                           query_terms: Set[str],
                           result_terms: Set[str],
                           result_length: int,
                           query_length: int,
                           context: Optional[Dict[str, Any]] = None) -> ScoringMetrics:
        """
        Obtiene métricas detalladas del proceso de puntuación para análisis
        """
        # Re-calcular con logging detallado
        self.calculate_score(
            semantic_distance, query_terms, result_terms,
            result_length, query_length, 0.0, context
        )
        
        # Retornar métricas (implementación simplificada para ejemplo)
        return ScoringMetrics(
            semantic_score=1.0 - semantic_distance,
            term_overlap_score=len(query_terms.intersection(result_terms)) / len(query_terms) if query_terms else 0,
            length_penalty=self._calculate_length_factor(result_length, query_length),
            diversity_bonus=0.0,
            alternative_metric_1=self._calculate_alternative_metric_1(semantic_distance, query_terms, result_terms),
            alternative_metric_2=self._calculate_alternative_metric_2(semantic_distance, result_length, query_length),
            lexical_boost=self._calculate_lexical_boost(query_terms, result_terms),
            final_score=0.0,  # Se calcula en calculate_score
            calibrated_score=0.0  # Se calcula en calculate_score
        )


class BalancedScoringStrategy(ScoringStrategy):
    """Estrategia de puntuación balanceada que evita sobre-ajuste"""
    
    def __init__(self, diversification_factor: float = 0.2):
        """
        Inicializa la estrategia de puntuación balanceada
        
        Args:
            diversification_factor: Factor para promocionar diversidad en resultados
        """
        self.diversification_factor = diversification_factor
        self.w_sem, self.w_term, self.w_len, self.w_div = 0.6, 0.25, 0.1, 0.05
        self.score_weights = {
            'semantic_similarity': 0.60,   # Peso principal para similitud semántica
            'term_overlap': 0.25,          # Peso para coincidencias exactas de términos
            'length_penalty': 0.10,        # Peso para penalización por longitud
            'diversity_bonus': 0.05        # Peso para bonus por diversidad
        }
        logger.info(f"Estrategia de puntuación balanceada inicializada con pesos: {self.score_weights}")
    
    def calculate_score(
        self,
        semantic_score: float,
        term_score: float,
        result_length: int,
        query_length: int,
        diversity_penalty: float = 0.0
    ) -> float:
        # 1. Length score: 1 - |ratio - 1|
        ratio = result_length / max(query_length, 1)
        length_score = max(0.0, 1.0 - abs(ratio - 1.0))

        # 2. Diversity bonus dinámico
        diversity_bonus = max(0.0, self.diversification_factor - diversity_penalty)

        # 3. Combina TODO
        raw = (
            self.w_sem  * self._clamp(semantic_score) +
            self.w_term * self._clamp(term_score)     +
            self.w_len  * length_score               +
            self.w_div  * diversity_bonus
        )

        # 4. Calibración final: sigmoide para comprimir a [0,1]
        return self._smooth_sigmoid(raw)

    @staticmethod
    def _clamp(x: float) -> float:
        return min(max(x, 0.0), 1.0)

    @staticmethod
    def _smooth_sigmoid(x):
        # a=2, b=1 -> curva moderada, no saturará todo
        return 1.0 / (1.0 + np.exp(-2.0 * x + 1.0))

    def calculate_score2(
        self,
        semantic_distance: float,
        query_terms: Set[str],
        result_terms: Set[str],
        result_length: int,
        query_length: int,
        diversity_penalty: float = 0.0
    ) -> float:
        """
        Calcula puntuación balanceada evitando sobre-ajuste
        
        Args:
            semantic_distance: Distancia semántica entre query y resultado
            query_terms: Conjunto de términos de la consulta
            result_terms: Conjunto de términos del resultado
            result_length: Longitud del texto resultado
            query_length: Longitud del texto de consulta
            diversity_penalty: Penalización por falta de diversidad
            
        Returns:
            float: Puntuación final en rango [0, 1]
        """
        
        # 1. Puntuación semántica base (método único para evitar distorsión)
        semantic_score = self._calculate_semantic_score(semantic_distance)
        
        # 2. Puntuación por coincidencia de términos
        term_score = self._calculate_term_overlap_score(query_terms, result_terms)
        
        # 3. Penalización por longitud desproporcionada
        length_penalty = self._calculate_length_penalty(result_length, query_length)
        
        # 4. Bonus por diversidad
        diversity_bonus = max(0, self.diversification_factor - diversity_penalty)
        
        # Combinar puntuaciones de forma balanceada
        final_score = (
            semantic_score * self.score_weights['semantic_similarity'] +
            term_score * self.score_weights['term_overlap'] +
            length_penalty * self.score_weights['length_penalty'] +
            diversity_bonus * self.score_weights['diversity_bonus']
        )
        
        # Mantener en rango [0, 1]
        final_score = min(max(final_score, 0.0), 1.0)
        
        logger.debug(f"Scoring breakdown - Semantic: {semantic_score:.3f}, "
                    f"Term: {term_score:.3f}, Length: {length_penalty:.3f}, "
                    f"Diversity: {diversity_bonus:.3f}, Final: {final_score:.3f}")
        
        return final_score
    
    def _calculate_semantic_score(self, distance: float) -> float:
        """
        Calcula puntuación semántica usando transformación suave única
        
        Args:
            distance: Distancia semántica
            
        Returns:
            float: Puntuación semántica normalizada
        """
        # Usar transformación inversa suave en lugar de múltiples métodos
        # Esta función es más estable y evita sobre-ajuste
        return max(0.0, min(1.0, 1.0 - distance))
    
    def _calculate_term_overlap_score(self, query_terms: Set[str], result_terms: Set[str]) -> float:
        """
        Calcula puntuación por superposición de términos usando Jaccard similarity
        
        Args:
            query_terms: Términos de la consulta
            result_terms: Términos del resultado
            
        Returns:
            float: Puntuación por coincidencia de términos
        """
        if not query_terms:
            return 0.0
        
        intersection = len(query_terms.intersection(result_terms))
        union = len(query_terms.union(result_terms))
        
        # Usar Jaccard similarity para mejor balance
        jaccard_score = intersection / union if union > 0 else 0.0
        
        # Aplicar peso adicional a coincidencias exactas importantes
        exact_matches = intersection / len(query_terms) if query_terms else 0.0
        
        # Combinar Jaccard con exactitud de matches
        return 0.7 * jaccard_score + 0.3 * exact_matches
    
    def _calculate_length_penalty(self, result_length: int, query_length: int) -> float:
        """
        Calcula penalización por desproporción en longitud de texto
        
        Args:
            result_length: Longitud del resultado
            query_length: Longitud de la consulta
            
        Returns:
            float: Penalización por longitud (puede ser negativa)
        """
        if query_length == 0:
            return 0.0
            
        ratio = result_length / query_length
        
        # Penalizar textos muy largos (ratio > 5) o muy cortos (ratio < 0.2)
        if ratio > 5:
            # Penalización progresiva para textos muy largos
            return -0.2 * min((ratio - 5) / 10, 1.0)  # Cap máximo de penalización
        elif ratio < 0.2:
            # Penalización para textos muy cortos
            return -0.3 * (0.2 - ratio) / 0.2
        else:
            # Rango óptimo: ligero bonus
            return 0.1 * (1.0 - abs(ratio - 1.0))
    
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Actualiza los pesos de la estrategia de puntuación
        
        Args:
            new_weights: Nuevos pesos para los componentes de puntuación
        """
        # Validar que la suma sea aproximadamente 1.0
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"La suma de pesos ({total_weight}) no es 1.0, normalizando...")
            new_weights = {k: v / total_weight for k, v in new_weights.items()}
        
        self.score_weights.update(new_weights)
        logger.info(f"Pesos de puntuación actualizados: {self.score_weights}")


