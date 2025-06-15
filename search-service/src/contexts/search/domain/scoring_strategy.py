from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ScoringStrategy(ABC):
    """Estrategia base para cálculo de puntuaciones en búsqueda semántica"""
    
    @abstractmethod
    def calculate_score(
        self,
        #semantic_distance: float,
        query_terms: Set[str],
        result_terms: Set[str],
        result_length: int,
        query_length: int,
        diversity_penalty: float = 0.0
    ) -> float:
        """Calcula la puntuación final para un resultado de búsqueda"""
        pass


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


