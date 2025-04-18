from src.domain.entities.harvest_job import HarvestJob
from src.domain.services.harvester_service import HarvesterService


class ProcessHarvestJobUseCase:
    
    def __init__(self, harvester_service: HarvesterService):
        self.harvester_service = harvester_service
    
    async def execute(self, job_id: str) -> HarvestJob:
        return await self.harvester_service.process_harvest_job(job_id) 