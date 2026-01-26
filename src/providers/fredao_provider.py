import requests
import json
from requests.adapters import HTTPAdapter
from .base import SisuDataProvider
from typing import List, Dict, Any

class FredaoProvider(SisuDataProvider):
    def __init__(self):
        self.api_url = "https://professorfredao.app.br/_dash-update-component"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Referer": "https://professorfredao.app.br/meu-sisu",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)

    # Métodos obrigatórios da Classe Base
    def get_lista_vagas(self, course_id: str): return []
    def get_nota_corte(self, course_id: str): return None

    def get_full_history_data(self, fredao_course_name: str) -> List[Dict[str, Any]]:
        """Extrai o rowData (todas as faculdades e parciais) usando recursão DFS."""
        payload = {
            "output": "..e3e70682-c209-4cac-629f-6fbed82c07cd.loading...82e2e662-f728-b4fa-4248-5e3a0a5d2f34.children...82e2e662-f728-b4fa-4248-5e3a0a5d2f34.display..",
            "outputs": [
                {"id": "e3e70682-c209-4cac-629f-6fbed82c07cd", "property": "loading"},
                {"id": "82e2e662-f728-b4fa-4248-5e3a0a5d2f34", "property": "children"},
                {"id": "82e2e662-f728-b4fa-4248-5e3a0a5d2f34", "property": "display"}
            ],
            "inputs": [{"id": "e3e70682-c209-4cac-629f-6fbed82c07cd", "property": "n_clicks", "value": 1}],
            "changedPropIds": ["e3e70682-c209-4cac-629f-6fbed82c07cd.n_clicks"],
            "state": [
                {"id": "score_LC", "property": "value", "value": 700},
                {"id": "score_CH", "property": "value", "value": 700},
                {"id": "score_CN", "property": "value", "value": 700},
                {"id": "score_MT", "property": "value", "value": 700},
                {"id": "score_RED", "property": "value", "value": 700},
                {"id": "e6f4590b-9a16-4106-cf6a-659eb4862b21", "property": "value", "value": "2026_1"},
                {"id": "d4713d60-c8a7-0639-eb11-67b367a9c378", "property": "value", "value": fredao_course_name},
                {"id": "23a7711a-8133-2876-37eb-dcd9e87a1613", "property": "value", "value": "Ampla concorrência"},
                {"id": "f7b0b7d2-cda8-056c-3d15-eef738c1962e", "property": "value", "value": []},
                {"id": "1759edc3-72ae-2244-8b01-63c1cd9d2b7d", "property": "value", "value": "Decrescente"}
            ]
        }

        try:
            response = self.session.post(self.api_url, json=payload, timeout=20)
            response.raise_for_status()
            full_json = response.json()

            def find_key_recursive(obj, target_key):
                """Busca em profundidade na árvore de componentes do Dash."""
                if isinstance(obj, dict):
                    if target_key in obj: return obj[target_key]
                    for val in obj.values():
                        res = find_key_recursive(val, target_key)
                        if res: return res
                elif isinstance(obj, list):
                    for item in obj:
                        res = find_key_recursive(item, target_key)
                        if res: return res
                return None

            # O ponto de entrada é o nó de resposta do gráfico/tabela
            root = full_json.get("response", {}).get("82e2e662-f728-b4fa-4248-5e3a0a5d2f34", {})
            return find_key_recursive(root, "rowData") or []
        except Exception as e:
            print(f"❌ Erro na extração: {e}")
            return []