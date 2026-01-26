import sqlite3
import pandas as pd
import os
from typing import List, Dict, Any

# Standard path configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "sisu_data.db")

class SisuRepository:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.courses_file = os.path.join(BASE_DIR, "..", "data", "mappings", "cursos.json")

    def load_courses_mapping(self) -> Dict[str, str]:
        """Loads names and IDs for the Streamlit multiselect."""
        import json
        if not os.path.exists(self.courses_file): return {}
        with open(self.courses_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        mapping = {}
        for letter in raw:
            for item in raw[letter]:
                mapping[item.get("no_curso")] = str(item.get("co_curso"))
        return dict(sorted(mapping.items()))

    def load_full_mapping(self) -> Dict[str, Any]:
        """Loads raw JSON to retrieve specialist (fredao) IDs."""
        import json
        if not os.path.exists(self.courses_file): return {}
        with open(self.courses_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_history_dataframe(self, course_ids: List[str]) -> pd.DataFrame:
        """
        Fetches cutoff history from SQLite.
        Uses COALESCE to prevent empty 'curso' column causing pivot failures.
        """
        if not course_ids: return pd.DataFrame()
        
        placeholders = ','.join(['?'] * len(course_ids))
        # SQL logic: pick course_name from DB, if NULL use a placeholder
        query = f"""
            SELECT 
                TRIM(CAST(course_id AS TEXT)) as course_id,
                COALESCE(course_name, 'Curso ' || course_id) as curso, 
                university as universidade, 
                city as cidade, 
                uf, 
                date, 
                score, 
                source as fonte
            FROM cutoff_history 
            WHERE TRIM(CAST(course_id AS TEXT)) IN ({placeholders})
            ORDER BY date ASC
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                params = [str(cid).strip() for cid in course_ids]
                return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            print(f"❌ DB Query Error: {e}")
            return pd.DataFrame()