import json
import csv
import os
from datetime import datetime
from typing import List, Dict
from models import SisuVacancy

# Localiza o caminho absoluto para a pasta 'data'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class SisuRepository:
    def __init__(self):
        self.courses_file = os.path.join(DATA_DIR, "cursos.json")

    def load_courses_mapping(self) -> Dict[str, str]:
        if not os.path.exists(self.courses_file):
            return {}
        try:
            with open(self.courses_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            mapping = {}
            for letter in raw_data:
                for item in raw_data[letter]:
                    mapping[item.get("no_curso")] = str(item.get("co_curso"))
            return dict(sorted(mapping.items()))
        except Exception as e:
            print(f"Error loading courses: {e}")
            return {}

    def save_daily_csv(self, vacancies: List[SisuVacancy], co_curso: str):
        # VOLTAMOS AO NOME ORIGINAL: historico_sisu_curso_...
        file_path = os.path.join(DATA_DIR, f"historico_sisu_curso_{co_curso}.csv")
        # VOLTAMOS AO PREFIXO ORIGINAL: nota_dd_mm
        today_col = f"nota_{datetime.now().strftime('%d_%m')}"
        
        history = {}
        # Cabeçalhos originais para manter compatibilidade
        headers = ["co_oferta", "curso", "universidade", "cidade", "uf"]
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                for row in reader:
                    history[row['co_oferta']] = row

        if today_col not in headers:
            headers.append(today_col)

        for v in vacancies:
            if v.co_oferta not in history:
                history[v.co_oferta] = {
                    "co_oferta": v.co_oferta,
                    "curso": v.no_curso,
                    "universidade": v.sg_ies,
                    "cidade": v.no_municipio_campus,
                    "uf": v.sg_uf_campus
                }
            # Atribui a nota atual à coluna do dia
            history[v.co_oferta][today_col] = v.nu_nota_corte if v.nu_nota_corte else "N/A"

        with open(file_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            sorted_data = sorted(history.values(), key=lambda x: x['universidade'])
            writer.writerows(sorted_data)
        
        return file_path