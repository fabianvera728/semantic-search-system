import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

from .entities import SearchResult, SearchResults

logger = logging.getLogger(__name__)


@dataclass
class SearchQualityReport:
    """Reporte de calidad de búsqueda"""
    query: str
    total_results: int
    quality_score: float
    diversity_score: float
    relevance_score: float
    score_distribution_score: float
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Métricas de rendimiento del sistema"""
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    cache_hit_rate: float
    queries_per_second: float
    error_rate: float
    avg_quality_score: float
    total_queries: int
    timestamp: datetime = field(default_factory=datetime.now)


class SearchQualityAnalyzer:
    """Analizador de calidad de búsqueda semántica"""
    
    def __init__(self):
        """Inicializa el analizador de calidad"""
        self.quality_history: deque = deque(maxlen=1000)  # Historial limitado
        self.performance_window: deque = deque(maxlen=500)  # Ventana de rendimiento
        self.quality_thresholds = {
            'excellent': 0.85,
            'good': 0.70,
            'fair': 0.55,
            'poor': 0.40
        }
        logger.info("Analizador de calidad de búsqueda inicializado")
    
    def analyze_search_quality(
        self, 
        results: SearchResults, 
        query: str,
        execution_time_ms: float = 0.0
    ) -> SearchQualityReport:
        """
        Analiza la calidad de los resultados de búsqueda
        
        Args:
            results: Resultados de búsqueda
            query: Consulta original
            execution_time_ms: Tiempo de ejecución en milisegundos
            
        Returns:
            SearchQualityReport: Reporte detallado de calidad
        """
        
        if not results.results:
            return SearchQualityReport(
                query=query,
                total_results=0,
                quality_score=0.0,
                diversity_score=0.0,
                relevance_score=0.0,
                score_distribution_score=0.0,
                execution_time_ms=execution_time_ms,
                recommendations=["No se encontraron resultados para la consulta"]
            )
        
        # Calcular métricas individuales
        relevance_score = self._calculate_relevance_score(results.results)
        diversity_score = self._calculate_diversity_score(results.results)
        score_distribution = self._analyze_score_distribution(results.results)
        
        # Calcular puntuación de calidad general
        quality_score = self._calculate_overall_quality(
            relevance_score, diversity_score, score_distribution, len(results.results)
        )
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            quality_score, relevance_score, diversity_score, 
            score_distribution, results.results, query
        )
        
        # Crear reporte
        report = SearchQualityReport(
            query=query,
            total_results=len(results.results),
            quality_score=quality_score,
            diversity_score=diversity_score,
            relevance_score=relevance_score,
            score_distribution_score=score_distribution,
            execution_time_ms=execution_time_ms,
            recommendations=recommendations,
            metadata={
                'score_stats': self._get_score_statistics(results.results),
                'query_complexity': self._analyze_query_complexity(query),
                'result_length_stats': self._analyze_result_lengths(results.results)
            }
        )
        
        # Almacenar en historial
        self.quality_history.append(report)
        
        logger.debug(f"Análisis de calidad completado - Score: {quality_score:.3f}, "
                    f"Diversidad: {diversity_score:.3f}, Relevancia: {relevance_score:.3f}")
        
        return report
    
    def _calculate_relevance_score(self, results: List[SearchResult]) -> float:
        """Calcula puntuación de relevancia promedio"""
        
        if not results:
            return 0.0
        
        scores = [result.score for result in results]
        
        # Usar promedio ponderado que da más peso a los primeros resultados
        weights = [1.0 / (i + 1) for i in range(len(scores))]
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_diversity_score(self, results: List[SearchResult]) -> float:
        """Calcula diversidad usando distancia promedio entre resultados"""
        
        if len(results) < 2:
            return 1.0  # Un solo resultado es completamente diverso
        
        total_diversity = 0.0
        comparisons = 0
        
        # Calcular diversidad basada en diferencias de texto
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                text1_words = set(results[i].text.lower().split())
                text2_words = set(results[j].text.lower().split())
                
                # Calcular diversidad usando distancia Jaccard
                intersection = len(text1_words.intersection(text2_words))
                union = len(text1_words.union(text2_words))
                
                diversity = 1.0 - (intersection / union if union > 0 else 0)
                total_diversity += diversity
                comparisons += 1
        
        return total_diversity / comparisons if comparisons > 0 else 0.0
    
    def _analyze_score_distribution(self, results: List[SearchResult]) -> float:
        """Analiza la distribución de puntuaciones para detectar sobre-ajuste"""
        
        if len(results) < 2:
            return 1.0
        
        scores = [result.score for result in results]
        
        # Calcular estadísticas de distribución
        mean_score = statistics.mean(scores)
        std_score = statistics.stdev(scores) if len(scores) > 1 else 0.0
        
        # Evaluar distribución
        # Una buena distribución tiene varianza moderada y gradiente descendente
        
        # 1. Verificar gradiente descendente
        gradient_score = self._evaluate_score_gradient(scores)
        
        # 2. Verificar varianza apropiada
        variance_score = self._evaluate_score_variance(std_score, mean_score)
        
        # 3. Detectar clustering artificial de puntuaciones
        clustering_penalty = self._detect_score_clustering(scores)
        
        # Combinar métricas
        distribution_score = (
            gradient_score * 0.4 + 
            variance_score * 0.4 + 
            (1.0 - clustering_penalty) * 0.2
        )
        
        return max(0.0, min(1.0, distribution_score))
    
    def _evaluate_score_gradient(self, scores: List[float]) -> float:
        """Evalúa si las puntuaciones tienen un gradiente descendente natural"""
        
        if len(scores) < 3:
            return 1.0
        
        # Calcular diferencias consecutivas
        differences = [scores[i] - scores[i + 1] for i in range(len(scores) - 1)]
        
        # Evaluar si la mayoría de diferencias son positivas o cero (orden descendente)
        positive_diffs = sum(1 for diff in differences if diff >= 0)
        gradient_score = positive_diffs / len(differences)
        
        return gradient_score
    
    def _evaluate_score_variance(self, std_score: float, mean_score: float) -> float:
        """Evalúa si la varianza de puntuaciones es apropiada"""
        
        if mean_score == 0:
            return 0.0
        
        # Coeficiente de variación
        cv = std_score / mean_score
        
        # Una varianza moderada es deseable (CV entre 0.1 y 0.4)
        if 0.1 <= cv <= 0.4:
            return 1.0
        elif cv < 0.1:
            # Muy poca varianza puede indicar sobre-ajuste
            return 0.5
        else:
            # Demasiada varianza puede indicar inconsistencia
            return max(0.0, 1.0 - (cv - 0.4) / 0.6)
    
    def _detect_score_clustering(self, scores: List[float]) -> float:
        """Detecta clustering artificial de puntuaciones"""
        
        if len(scores) < 5:
            return 0.0
        
        # Contar puntuaciones muy similares (diferencia < 0.01)
        similar_pairs = 0
        total_pairs = 0
        
        for i in range(len(scores)):
            for j in range(i + 1, len(scores)):
                total_pairs += 1
                if abs(scores[i] - scores[j]) < 0.01:
                    similar_pairs += 1
        
        clustering_ratio = similar_pairs / total_pairs if total_pairs > 0 else 0.0
        
        # Penalizar si más del 30% de puntuaciones son muy similares
        return max(0.0, clustering_ratio - 0.3)
    
    def _calculate_overall_quality(
        self, 
        relevance: float, 
        diversity: float, 
        distribution: float, 
        result_count: int
    ) -> float:
        """Calcula puntuación de calidad general"""
        
        # Pesos para diferentes aspectos
        weights = {
            'relevance': 0.45,      # Más importante
            'diversity': 0.30,      # Importante para evitar redundancia
            'distribution': 0.20,   # Importante para detectar sobre-ajuste
            'completeness': 0.05    # Bonus por número apropiado de resultados
        }
        
        # Calcular puntuación de completitud
        completeness_score = min(1.0, result_count / 10.0)  # Máximo en 10 resultados
        
        # Combinar puntuaciones
        overall_quality = (
            relevance * weights['relevance'] +
            diversity * weights['diversity'] +
            distribution * weights['distribution'] +
            completeness_score * weights['completeness']
        )
        
        return max(0.0, min(1.0, overall_quality))
    
    def _generate_recommendations(
        self, 
        quality_score: float,
        relevance_score: float, 
        diversity_score: float,
        distribution_score: float,
        results: List[SearchResult],
        query: str
    ) -> List[str]:
        """Genera recomendaciones para mejorar la calidad de búsqueda"""
        
        recommendations = []
        
        # Recomendaciones basadas en calidad general
        if quality_score < self.quality_thresholds['poor']:
            recommendations.append("❌ Calidad muy baja - Revisar algoritmo de búsqueda")
        elif quality_score < self.quality_thresholds['fair']:
            recommendations.append("⚠️ Calidad baja - Considerar ajustar parámetros de búsqueda")
        elif quality_score < self.quality_thresholds['good']:
            recommendations.append("📊 Calidad moderada - Oportunidades de mejora identificadas")
        else:
            recommendations.append("✅ Excelente calidad de búsqueda")
        
        # Recomendaciones específicas por relevancia
        if relevance_score < 0.5:
            recommendations.append("🎯 Baja relevancia - Verificar modelo de embeddings o preprocesamiento")
        
        # Recomendaciones específicas por diversidad
        if diversity_score < 0.3:
            recommendations.append("🔄 Baja diversidad - Implementar diversificación MMR o clustering")
        
        # Recomendaciones específicas por distribución
        if distribution_score < 0.5:
            recommendations.append("📈 Distribución problemática - Revisar función de scoring para evitar sobre-ajuste")
        
        # Recomendaciones basadas en número de resultados
        if len(results) < 3:
            recommendations.append("📝 Pocos resultados - Considerar expandir consulta o reducir filtros")
        
        # Recomendaciones basadas en complejidad de consulta
        query_complexity = self._analyze_query_complexity(query)
        if query_complexity['word_count'] < 2:
            recommendations.append("🔍 Consulta muy corta - Resultados pueden ser muy generales")
        elif query_complexity['word_count'] > 10:
            recommendations.append("📏 Consulta muy larga - Considerar extraer términos clave")
        
        return recommendations
    
    def _get_score_statistics(self, results: List[SearchResult]) -> Dict[str, float]:
        """Obtiene estadísticas de las puntuaciones"""
        
        if not results:
            return {}
        
        scores = [result.score for result in results]
        
        return {
            'mean': statistics.mean(scores),
            'median': statistics.median(scores),
            'std': statistics.stdev(scores) if len(scores) > 1 else 0.0,
            'min': min(scores),
            'max': max(scores),
            'range': max(scores) - min(scores)
        }
    
    def _analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analiza la complejidad de la consulta"""
        
        words = query.strip().split()
        
        return {
            'word_count': len(words),
            'char_count': len(query),
            'avg_word_length': statistics.mean(len(word) for word in words) if words else 0,
            'has_special_chars': any(char in query for char in "\"'()[]{}"),
            'is_question': query.strip().endswith('?')
        }
    
    def _analyze_result_lengths(self, results: List[SearchResult]) -> Dict[str, float]:
        """Analiza las longitudes de los resultados"""
        
        if not results:
            return {}
        
        lengths = [len(result.text) for result in results]
        
        return {
            'mean_length': statistics.mean(lengths),
            'median_length': statistics.median(lengths),
            'std_length': statistics.stdev(lengths) if len(lengths) > 1 else 0.0,
            'min_length': min(lengths),
            'max_length': max(lengths)
        }
    
    def get_quality_trends(self, days: int = 7) -> Dict[str, Any]:
        """Obtiene tendencias de calidad en los últimos días"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_reports = [
            report for report in self.quality_history 
            if report.timestamp >= cutoff_date
        ]
        
        if not recent_reports:
            return {"message": "No hay datos suficientes para análisis de tendencias"}
        
        # Calcular tendencias
        quality_scores = [report.quality_score for report in recent_reports]
        diversity_scores = [report.diversity_score for report in recent_reports]
        relevance_scores = [report.relevance_score for report in recent_reports]
        
        return {
            'period_days': days,
            'total_queries': len(recent_reports),
            'quality_trend': {
                'mean': statistics.mean(quality_scores),
                'median': statistics.median(quality_scores),
                'std': statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0.0,
                'improvement_rate': self._calculate_improvement_rate(quality_scores)
            },
            'diversity_trend': {
                'mean': statistics.mean(diversity_scores),
                'improvement_rate': self._calculate_improvement_rate(diversity_scores)
            },
            'relevance_trend': {
                'mean': statistics.mean(relevance_scores),
                'improvement_rate': self._calculate_improvement_rate(relevance_scores)
            },
            'common_recommendations': self._get_common_recommendations(recent_reports)
        }
    
    def _calculate_improvement_rate(self, scores: List[float]) -> float:
        """Calcula tasa de mejora comparando primera y segunda mitad del período"""
        
        if len(scores) < 4:
            return 0.0
        
        mid_point = len(scores) // 2
        first_half_avg = statistics.mean(scores[:mid_point])
        second_half_avg = statistics.mean(scores[mid_point:])
        
        if first_half_avg == 0:
            return 0.0
        
        return ((second_half_avg - first_half_avg) / first_half_avg) * 100
    
    def _get_common_recommendations(self, reports: List[SearchQualityReport]) -> List[Tuple[str, int]]:
        """Obtiene recomendaciones más comunes en el período"""
        
        recommendation_counts = defaultdict(int)
        
        for report in reports:
            for recommendation in report.recommendations:
                recommendation_counts[recommendation] += 1
        
        # Retornar las 5 más comunes
        return sorted(
            recommendation_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]


class PerformanceMonitor:
    """Monitor de rendimiento del sistema de búsqueda"""
    
    def __init__(self, window_size: int = 100):
        """
        Inicializa el monitor de rendimiento
        
        Args:
            window_size: Tamaño de la ventana deslizante para métricas
        """
        self.window_size = window_size
        self.response_times: deque = deque(maxlen=window_size)
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_queries = 0
        self.error_count = 0
        self.quality_scores: deque = deque(maxlen=window_size)
        self.start_time = datetime.now()
        
        logger.info(f"Monitor de rendimiento inicializado con ventana de {window_size}")
    
    def record_query(
        self, 
        response_time_ms: float, 
        cache_hit: bool, 
        quality_score: float, 
        had_error: bool = False
    ) -> None:
        """Registra métricas de una consulta"""
        
        self.response_times.append(response_time_ms)
        self.quality_scores.append(quality_score)
        self.total_queries += 1
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        if had_error:
            self.error_count += 1
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Obtiene métricas actuales de rendimiento"""
        
        if not self.response_times:
            return PerformanceMetrics(
                avg_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                cache_hit_rate=0.0,
                queries_per_second=0.0,
                error_rate=0.0,
                avg_quality_score=0.0,
                total_queries=0
            )
        
        # Calcular métricas de tiempo de respuesta
        sorted_times = sorted(self.response_times)
        avg_response_time = statistics.mean(self.response_times)
        p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
        p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Calcular tasa de cache hit
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_cache_requests) if total_cache_requests > 0 else 0.0
        
        # Calcular queries por segundo
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        queries_per_second = self.total_queries / elapsed_time if elapsed_time > 0 else 0.0
        
        # Calcular tasa de error
        error_rate = (self.error_count / self.total_queries) if self.total_queries > 0 else 0.0
        
        # Calcular puntuación de calidad promedio
        avg_quality_score = statistics.mean(self.quality_scores) if self.quality_scores else 0.0
        
        return PerformanceMetrics(
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            cache_hit_rate=cache_hit_rate,
            queries_per_second=queries_per_second,
            error_rate=error_rate,
            avg_quality_score=avg_quality_score,
            total_queries=self.total_queries
        ) 