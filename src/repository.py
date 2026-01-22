import json
import csv
import os
from datetime import datetime
from typing import List, Dict
from models import SisuVacancy

# Path configuration based on project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))

# Subdirectory definitions for organization (exported for use in cron_sync/app.py)
MAPPINGS_DIR = os.path.join(ROOT_DATA_DIR, "mappings")
HISTORY_DIR = os.path.join(ROOT_DATA_DIR, "history")
REPORTS_DIR = os.path.join(ROOT_DATA_DIR, "reports")

class SisuRepository:
    def __init__(self):
        """Initializes the repository and ensures the folder structure exists."""
        for folder in [MAPPINGS_DIR, HISTORY_DIR, REPORTS_DIR]:
            os.makedirs(folder, exist_ok=True)
            
        self.courses_file = os.path.join(MAPPINGS_DIR, "cursos.json")

    def load_courses_mapping(self) -> Dict[str, str]:
        """Loads course names and IDs mapping from the mappings folder."""
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
            print(f"Error loading course mapping: {e}")
            return {}

    def save_txt_report(self, vacancies: List[SisuVacancy], course_id: str):
        """Generates a formatted TXT report for quick consultation in the reports folder."""
        file_path = os.path.join(REPORTS_DIR, f"report_course_{course_id}.txt")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"📊 SISU REPORT - COURSE ID {course_id}\n")
            f.write(f"Sync Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 65 + "\n")
            f.write(f"{'UNI':<10} | {'CITY':<30} | {'UF':<3} | {'SCORE'}\n")
            f.write("-" * 65 + "\n")
            
            for v in vacancies:
                score = f"{v.nu_nota_corte:.2f}" if v.nu_nota_corte else "N/A"
                f.write(f"{v.sg_ies:<10} | {v.no_municipio_campus[:30]:<30} | {v.sg_uf_campus:<3} | {score}\n")
        
        return file_path

    def save_daily_csv(self, vacancies: List[SisuVacancy], course_id: str):
        """
        Manages incremental historical data in CSV format within the history folder.
        Appends new daily columns without overwriting previous data.
        """
        file_path = os.path.join(HISTORY_DIR, f"historico_sisu_curso_{course_id}.csv")
        today_column = f"nota_{datetime.now().strftime('%d_%m')}"
        
        history = {}
        headers = ["co_oferta", "curso", "universidade", "cidade", "uf"]
        
        # 1. Load existing data if file exists
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                for row in reader:
                    history[row['co_oferta']] = row

        # 2. Add today's column if it's a new date
        if today_column not in headers:
            headers.append(today_column)

        # 3. Merge new vacancy data with history
        for v in vacancies:
            if v.co_oferta not in history:
                history[v.co_oferta] = {
                    "co_oferta": v.co_oferta,
                    "curso": v.no_curso,
                    "universidade": v.sg_ies,
                    "cidade": v.no_municipio_campus,
                    "uf": v.sg_uf_campus
                }
            # Add current cutoff score to today's column
            history[v.co_oferta][today_column] = v.nu_nota_corte if v.nu_nota_corte else "N/A"

        # 4. Save updated historical file
        with open(file_path, "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            # Sorted by university name for better manual readability
            sorted_data = sorted(history.values(), key=lambda x: x['universidade'])
            writer.writerows(sorted_data)
        
        return file_path