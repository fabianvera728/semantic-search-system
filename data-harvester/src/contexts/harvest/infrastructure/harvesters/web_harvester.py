import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re


class WebHarvester:
    """Cosechador de datos desde páginas web mediante scraping."""
    
    async def harvest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cosecha datos desde una página web.
        
        Args:
            config: Configuración que debe incluir:
                - url: URL de la página web
                - selectors: Selectores CSS para extraer datos
                - headers: Headers HTTP opcionales
                - extract_type: Tipo de extracción (table, list, custom)
                
        Returns:
            Diccionario con los datos cosechados
        """
        url = config.get("url")
        selectors = config.get("selectors", {})
        headers = config.get("headers", {})
        extract_type = config.get("extract_type", "custom")
        
        if not url:
            raise ValueError("url is required")
        
        # Headers por defecto para evitar bloqueos
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        headers = {**default_headers, **headers}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    
                    if response.status >= 400:
                        raise Exception(f"Web request failed with status {response.status}")
                    
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    if extract_type == "table":
                        return await self._extract_table_data(soup, selectors, url)
                    elif extract_type == "list":
                        return await self._extract_list_data(soup, selectors, url)
                    else:
                        return await self._extract_custom_data(soup, selectors, url)
                        
        except Exception as e:
            raise Exception(f"Error harvesting from web {url}: {str(e)}")
    
    async def _extract_table_data(self, soup: BeautifulSoup, selectors: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Extrae datos de tablas HTML."""
        table_selector = selectors.get("table", "table")
        
        tables = soup.select(table_selector)
        if not tables:
            raise Exception("No tables found with the specified selector")
        
        # Usar la primera tabla encontrada
        table = tables[0]
        
        # Extraer headers
        headers = []
        header_rows = table.select("thead tr, tr:first-child")
        if header_rows:
            header_cells = header_rows[0].select("th, td")
            headers = [cell.get_text(strip=True) for cell in header_cells]
        
        # Extraer filas de datos
        data = []
        data_rows = table.select("tbody tr") if table.select("tbody") else table.select("tr")[1:]
        
        for row in data_rows:
            cells = row.select("td, th")
            if len(cells) == len(headers):
                row_data = {}
                for i, cell in enumerate(cells):
                    column_name = headers[i] if i < len(headers) else f"column_{i}"
                    row_data[column_name] = cell.get_text(strip=True)
                data.append(row_data)
        
        return {
            "data": data,
            "columns": headers,
            "row_count": len(data),
            "web_info": {
                "url": url,
                "extract_type": "table",
                "tables_found": len(tables)
            }
        }
    
    async def _extract_list_data(self, soup: BeautifulSoup, selectors: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Extrae datos de listas HTML."""
        list_selector = selectors.get("list", "ul li, ol li")
        
        items = soup.select(list_selector)
        if not items:
            raise Exception("No list items found with the specified selector")
        
        data = []
        for i, item in enumerate(items):
            data.append({
                "index": i + 1,
                "text": item.get_text(strip=True),
                "html": str(item)
            })
        
        return {
            "data": data,
            "columns": ["index", "text", "html"],
            "row_count": len(data),
            "web_info": {
                "url": url,
                "extract_type": "list",
                "items_found": len(items)
            }
        }
    
    async def _extract_custom_data(self, soup: BeautifulSoup, selectors: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Extrae datos usando selectores personalizados."""
        if not selectors:
            raise ValueError("selectors are required for custom extraction")
        
        data = []
        columns = list(selectors.keys())
        
        # Encontrar el número máximo de elementos para cualquier selector
        max_elements = 0
        selector_results = {}
        
        for field, selector in selectors.items():
            elements = soup.select(selector)
            selector_results[field] = elements
            max_elements = max(max_elements, len(elements))
        
        # Crear filas de datos
        for i in range(max_elements):
            row_data = {}
            for field, elements in selector_results.items():
                if i < len(elements):
                    row_data[field] = elements[i].get_text(strip=True)
                else:
                    row_data[field] = ""
            data.append(row_data)
        
        return {
            "data": data,
            "columns": columns,
            "row_count": len(data),
            "web_info": {
                "url": url,
                "extract_type": "custom",
                "selectors_used": list(selectors.keys())
            }
        } 