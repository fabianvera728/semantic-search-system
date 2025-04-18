from typing import Dict, List, Optional
import copy

from src.domain.entities.harvest_job import HarvestJob
from src.domain.ports.harvester_repository_port import HarvesterRepositoryPort


class InMemoryHarvesterRepository(HarvesterRepositoryPort):
    
    def __init__(self):
        self.jobs: Dict[str, HarvestJob] = {}
    
    async def save(self, job: HarvestJob) -> HarvestJob:
        job_copy = copy.deepcopy(job)
        self.jobs[job.job_id] = job_copy
        return job_copy
    
    async def find_by_id(self, job_id: str) -> Optional[HarvestJob]:
        job = self.jobs.get(job_id)
        if job:
            return copy.deepcopy(job)
        return None
    
    async def find_all(self) -> List[HarvestJob]:
        return [copy.deepcopy(job) for job in self.jobs.values()]
    
    async def update(self, job: HarvestJob) -> HarvestJob:
        if job.job_id not in self.jobs:
            raise ValueError(f"Trabajo no encontrado: {job.job_id}")
        
        job_copy = copy.deepcopy(job)
        self.jobs[job.job_id] = job_copy
        return job_copy
    
    async def delete(self, job_id: str) -> None:
        if job_id not in self.jobs:
            raise ValueError(f"Trabajo no encontrado: {job_id}")
        
        del self.jobs[job_id] 