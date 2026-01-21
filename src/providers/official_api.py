import requests
from .base import SisuDataProvider

class OfficialApiProvider(SisuDataProvider):
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }
        self.api_base = "https://sisu-api.sisu.mec.gov.br/api/v1/oferta"

    def get_lista_vagas(self, id_curso: str):
        url = f"{self.api_base}/curso/{id_curso}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Retorna apenas a lista de ofertas, ignorando o campo 'search_rule'
            return [v for k, v in data.items() if k != "search_rule"]
        except Exception as e:
            print(f"Erro na API Oficial (Vagas): {e}")
            return []

    def get_nota_corte(self, co_oferta: str):
        url = f"{self.api_base}/{co_oferta}/modalidades"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json()
            for mod in data.get("modalidades", []):
                if mod.get("no_concorrencia") == "Ampla concorrência":
                    nota = mod.get("nu_nota_corte")
                    return float(nota) if nota else None
        except Exception:
            return None
        return None