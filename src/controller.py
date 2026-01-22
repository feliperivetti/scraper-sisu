import concurrent.futures
import time
from typing import List, Callable
from models import SisuVacancy
from repository import SisuRepository

class SisuController:
    """
    Orchestrates the data flow between fetchers (Providers) 
    and persistence layers (Repository) using multi-threading.
    """
    def __init__(self, provider, repository: SisuRepository):
        self.provider = provider
        self.repository = repository

    def process_all(self, course_id: str, progress_callback: Callable[[float], None]):
        """
        Main workflow: fetch data in parallel, transform into entities, and persist results.
        """
        # 1. Fetch raw vacancy data from the provider (using the new English method name)
        raw_data = self.provider.get_lista_vagas(course_id)
        if not raw_data:
            return None
        
        vacancy_entities: List[SisuVacancy] = []
        total = len(raw_data)

        # Inner function to process a single vacancy (to be executed in a thread)
        def fetch_vacancy_details(item):
            # Uses the English method name from the refactored provider
            score = self.provider.get_nota_corte(item.get("co_oferta"))
            
            return SisuVacancy(
                co_oferta=item.get("co_oferta"),
                sg_ies=item.get("sg_ies"),
                no_municipio_campus=item.get("no_municipio_campus"),
                sg_uf_campus=item.get("sg_uf_campus"),
                no_curso=item.get("no_curso"),
                nu_nota_corte=score
            )

        # 2. Use ThreadPoolExecutor to fetch scores in parallel
        # We use max_workers=10 to balance speed and prevent MEC API blocks
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Map the processing function to all items
            future_to_vacancy = {executor.submit(fetch_vacancy_details, item): item for item in raw_data}
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_vacancy)):
                try:
                    vacancy = future.result()
                    vacancy_entities.append(vacancy)
                    
                    # Update progress via callback as each thread finishes
                    progress_callback((i + 1) / total)
                except Exception as e:
                    print(f"Error processing a vacancy thread: {e}")

        # 3. Sort results: lower scores first (Nones at the end)
        vacancy_entities.sort(key=lambda x: x.nu_nota_corte if x.nu_nota_corte is not None else float('inf'))
        
        # 4. Delegate persistence to the Repository (DAL)
        # We save both the incremental CSV and the daily TXT report
        csv_path = self.repository.save_daily_csv(vacancy_entities, course_id)
        self.repository.save_txt_report(vacancy_entities, course_id)
        
        return csv_path