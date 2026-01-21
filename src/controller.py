import time
from typing import List, Callable
from models import SisuVacancy
from repository import SisuRepository

class SisuController:
    """
    Orchestrates the data flow between fetchers (Providers) 
    and persistence layers (Repository).
    """
    def __init__(self, provider, repository: SisuRepository):
        self.provider = provider
        self.repository = repository

    def process_all(self, course_id: str, progress_callback: Callable[[float], None]):
        """
        Main workflow: fetch data, transform into entities, and persist.
        """
        # 1. Fetch raw vacancy data from the provider
        raw_data = self.provider.get_lista_vagas(course_id)
        if not raw_data:
            return None
        
        vacancy_entities: List[SisuVacancy] = []
        total = len(raw_data)
        
        # 2. Process each entry to fetch scores and create Entities
        for i, item in enumerate(raw_data):
            # Fetch cut-off score via provider
            score = self.provider.get_nota_corte(item.get("co_oferta"))
            
            # Create Entity instance using Portuguese field names (as requested)
            vacancy = SisuVacancy(
                co_oferta=item.get("co_oferta"),
                sg_ies=item.get("sg_ies"),
                no_municipio_campus=item.get("no_municipio_campus"),
                sg_uf_campus=item.get("sg_uf_campus"),
                no_curso=item.get("no_curso"),
                nu_nota_corte=score
            )
            vacancy_entities.append(vacancy)
            
            # Update UI progress bar
            progress_callback((i + 1) / total)
            
            # Rate limiting to prevent API blocking
            time.sleep(0.3) 

        # 3. Sort results: lower scores first (Nones at the end)
        vacancy_entities.sort(key=lambda x: x.nu_nota_corte if x.nu_nota_corte is not None else float('inf'))
        
        # 4. Delegate persistence to the Repository (DAL)
        csv_path = self.repository.save_daily_csv(vacancy_entities, course_id)
        
        return csv_path