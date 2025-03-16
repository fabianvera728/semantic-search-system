import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Any, List

from src.domain.entities.harvested_data import HarvestedData, DataColumn
from src.domain.ports.harvester_port import HarvesterPort


class WebHarvesterAdapter(HarvesterPort):
    """
    Adaptador que implementa la cosecha de datos desde sitios web.
    
    Este adaptador soporta la cosecha de datos mediante web scraping.
    """
    
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
        # Validar configuración
        if "urls" not in config:
            raise ValueError("Las URLs son requeridas para la cosecha web")
        
        urls = config["urls"]
        selectors = config.get("selectors", {})
        
        # Cosechar datos
        rows = []
        
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, "html.parser")
                            
                            # Extraer datos según selectores
                            title = soup.title.text.strip() if soup.title else ""
                            
                            # Extraer contenido según selectores o usar valor por defecto
                            content = ""
                            if "content" in selectors:
                                content_elements = soup.select(selectors["content"])
                                content = "\n".join([el.text.strip() for el in content_elements])
                            else:
                                # Por defecto, extraer párrafos
                                paragraphs = soup.find_all("p")
                                content = "\n".join([p.text.strip() for p in paragraphs])
                            
                            # Crear datos de fila
                            row_data = {
                                "url": url,
                                "title": title,
                                "content": content,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
                            # Añadir selectores personalizados
                            for selector_name, selector_value in selectors.items():
                                if selector_name != "content":
                                    elements = soup.select(selector_value)
                                    if elements:
                                        row_data[selector_name] = elements[0].text.strip()
                            
                            # Añadir fila
                            rows.append(row_data)
                except Exception as e:
                    # Registrar error y continuar
                    print(f"Error al cosechar {url}: {str(e)}")
        
        # Crear columnas a partir de la primera fila
        columns = []
        if rows:
            for key in rows[0].keys():
                columns.append(DataColumn(
                    name=key,
                    type="string"  # Tipo por defecto
                ))
        
        # Crear metadatos
        metadata = {
            "urls": urls,
            "selectors": selectors,
            "import_timestamp": datetime.utcnow().isoformat()
        }
        
        # Crear y retornar datos cosechados
        return HarvestedData(
            source_type="web",
            source_identifier=",".join(urls),
            rows=rows,
            columns=columns,
            metadata=metadata
        ) 