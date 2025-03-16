from typing import Dict, List, Optional
import copy

from src.domain.entities.harvest_job import HarvestJob
from src.domain.ports.harvester_repository_port import HarvesterRepositoryPort


class InMemoryHarvesterRepository(HarvesterRepositoryPort):
    """
    Adaptador que implementa el repositorio de trabajos de cosecha en memoria.
    
    Este adaptador es útil para pruebas y desarrollo, pero no es adecuado
    para producción ya que los datos se pierden al reiniciar la aplicación.
    """
    
    def __init__(self):
        """Inicializa el repositorio con un diccionario vacío."""
        self.jobs: Dict[str, HarvestJob] = {}
    
    async def save(self, job: HarvestJob) -> HarvestJob:
        """
        Guarda un trabajo de cosecha en el repositorio.
        
        Args:
            job: El trabajo de cosecha a guardar
            
        Returns:
            El trabajo guardado
        """
        # Crear una copia para evitar modificaciones externas
        job_copy = copy.deepcopy(job)
        self.jobs[job.job_id] = job_copy
        return job_copy
    
    async def find_by_id(self, job_id: str) -> Optional[HarvestJob]:
        """
        Busca un trabajo de cosecha por su ID.
        
        Args:
            job_id: ID del trabajo a buscar
            
        Returns:
            El trabajo encontrado o None si no existe
        """
        job = self.jobs.get(job_id)
        if job:
            # Retornar una copia para evitar modificaciones externas
            return copy.deepcopy(job)
        return None
    
    async def find_all(self) -> List[HarvestJob]:
        """
        Recupera todos los trabajos de cosecha.
        
        Returns:
            Lista de todos los trabajos de cosecha
        """
        # Retornar copias para evitar modificaciones externas
        return [copy.deepcopy(job) for job in self.jobs.values()]
    
    async def update(self, job: HarvestJob) -> HarvestJob:
        """
        Actualiza un trabajo de cosecha existente.
        
        Args:
            job: El trabajo con los datos actualizados
            
        Returns:
            El trabajo actualizado
            
        Raises:
            ValueError: Si el trabajo no existe
        """
        if job.job_id not in self.jobs:
            raise ValueError(f"Trabajo no encontrado: {job.job_id}")
        
        # Crear una copia para evitar modificaciones externas
        job_copy = copy.deepcopy(job)
        self.jobs[job.job_id] = job_copy
        return job_copy
    
    async def delete(self, job_id: str) -> None:
        """
        Elimina un trabajo de cosecha.
        
        Args:
            job_id: ID del trabajo a eliminar
            
        Raises:
            ValueError: Si el trabajo no existe
        """
        if job_id not in self.jobs:
            raise ValueError(f"Trabajo no encontrado: {job_id}")
        
        del self.jobs[job_id] 