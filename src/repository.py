import json
import csv
import os
from datetime import datetime
from typing import List, Dict
from models import SisuVacancy

# Configuração dos caminhos baseados na raiz do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))

# Definição das subpastas para exportação (podem ser usadas no app.py)
MAPPINGS_DIR = os.path.join(ROOT_DATA_DIR, "mappings")
HISTORY_DIR = os.path.join(ROOT_DATA_DIR, "history")
REPORTS_DIR = os.path.join(ROOT_DATA_DIR, "reports")

class SisuRepository:
    def __init__(self):
        """Inicializa o repositório garantindo que a estrutura de pastas exista."""
        for folder in [MAPPINGS_DIR, HISTORY_DIR, REPORTS_DIR]:
            os.makedirs(folder, exist_ok=True)
            
        self.courses_file = os.path.join(MAPPINGS_DIR, "cursos.json")

    def load_courses_mapping(self) -> Dict[str, str]:
        """Carrega o de/para de nomes e IDs de cursos da pasta mappings."""
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
            print(f"Erro ao carregar mapeamento de cursos: {e}")
            return {}

    def save_daily_csv(self, vacancies: List[SisuVacancy], co_curso: str):
        """
        Gerencia o histórico incremental em CSV dentro da pasta history.
        Verifica se a coluna do dia existe e adiciona novos dados sem apagar os antigos.
        """
        file_path = os.path.join(HISTORY_DIR, f"historico_sisu_curso_{co_curso}.csv")
        today_col = f"nota_{datetime.now().strftime('%d_%m')}"
        
        history = {}
        headers = ["co_oferta", "curso", "universidade", "cidade", "uf"]
        
        # 1. Carrega dados existentes se o arquivo já existir
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                for row in reader:
                    history[row['co_oferta']] = row

        # 2. Adiciona a coluna do dia se for uma data nova
        if today_col not in headers:
            headers.append(today_col)

        # 3. Faz o merge das novas vagas com o histórico
        for v in vacancies:
            if v.co_oferta not in history:
                history[v.co_oferta] = {
                    "co_oferta": v.co_oferta,
                    "curso": v.no_curso,
                    "universidade": v.sg_ies,
                    "cidade": v.no_municipio_campus,
                    "uf": v.sg_uf_campus
                }
            # Adiciona a nota de corte na coluna do dia atual
            history[v.co_oferta][today_col] = v.nu_nota_corte if v.nu_nota_corte else "N/A"

        # 4. Salva o arquivo final atualizado
        with open(file_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            # Ordena por universidade para facilitar a leitura manual
            sorted_data = sorted(history.values(), key=lambda x: x['universidade'])
            writer.writerows(sorted_data)
        
        return file_path