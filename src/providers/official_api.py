import requests
from requests.adapters import HTTPAdapter
from .base import SisuDataProvider

class OfficialApiProvider(SisuDataProvider):
    def __init__(self):
        self.api_base = "https://sisu-api.sisu.mec.gov.br/api/v1/oferta"
        
        # 1. Initialize the session object
        self.session = requests.Session()
        
        # 2. Set default headers for all requests in this session
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        })

        # 3. Configure Connection Pooling (HTTPAdapter)
        # pool_connections: Number of connection pools to cache
        # pool_maxsize: Number of simultaneous connections to keep open
        # We set it to 10 to support our upcoming multi-threaded controller
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
        
        # Apply the adapter to both HTTP and HTTPS protocols
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_lista_vagas(self, course_id: str):
        """
        Fetches the list of available university vacancies for a specific course.
        """
        url = f"{self.api_base}/curso/{course_id}"
        try:
            # Use self.session to reuse the existing TCP connection
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Filter out 'search_rule' and return only vacancy data
            return [v for k, v in data.items() if k != "search_rule"]
        except Exception as e:
            print(f"Error in Official API (Vacancies): {e}")
            return []

    def get_nota_corte(self, offer_id: str):
        """
        Retrieves the cutoff score for the 'Ampla concorrência' modality.
        """
        url = f"{self.api_base}/{offer_id}/modalidades"
        try:
            # Reuses the same tunnel established in previous calls
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            # Navigate through modalities to find Wide Competition (Ampla concorrência)
            for mod in data.get("modalidades", []):
                if mod.get("no_concorrencia") == "Ampla concorrência":
                    score = mod.get("nu_nota_corte")
                    return float(score) if score else None
        except Exception:
            return None
        return None