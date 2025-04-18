import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Any, List

from src.domain.entities.harvested_data import HarvestedData, DataColumn
from src.domain.ports.harvester_port import HarvesterPort


class WebHarvesterAdapter(HarvesterPort):
    
    async def harvest(self, config: Dict[str, Any]) -> HarvestedData:
        """
        Cosecha datos de sitios web según la configuración proporcionada.
        
        Args:
            config: Configuración específica para la cosecha
                - urls: Lista de URLs a cosechar
                - selectors: Selectores CSS para extraer datos
            
        Returns:
            Los datos cosechados
            
        Raises:
            ValueError: Si la configuración es inválida o la cosecha falla
        """
        if "urls" not in config:
            raise ValueError("Las URLs son requeridas para la cosecha web")
        
        urls = config["urls"]
        selectors = config.get("selectors", {})
        
        rows = []
        
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, "html.parser")
                            
                            title = soup.title.text.strip() if soup.title else ""
                            
                            content = ""
                            if "content" in selectors:
                                content_elements = soup.select(selectors["content"])
                                content = "\n".join([el.text.strip() for el in content_elements])
                            else:
                                paragraphs = soup.find_all("p")
                                content = "\n".join([p.text.strip() for p in paragraphs])
                            
                            row_data = {
                                "url": url,
                                "title": title,
                                "content": content,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
                            for selector_name, selector_value in selectors.items():
                                if selector_name != "content":
                                    elements = soup.select(selector_value)
                                    if elements:
                                        row_data[selector_name] = elements[0].text.strip()
                            
                            rows.append(row_data)
                except Exception as e:
                    print(f"Error al cosechar {url}: {str(e)}")
        
        columns = []
        if rows:
            for key in rows[0].keys():
                columns.append(DataColumn(
                    name=key,
                    type="string"
                ))
        
        metadata = {
            "urls": urls,
            "selectors": selectors,
            "import_timestamp": datetime.utcnow().isoformat()
        }
        
        return HarvestedData(
            source_type="web",
            source_identifier=",".join(urls),
            rows=rows,
            columns=columns,
            metadata=metadata
        ) 