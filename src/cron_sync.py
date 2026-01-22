import time
import os
import csv
from datetime import datetime
from zoneinfo import ZoneInfo
from repository import SisuRepository, HISTORY_DIR
from providers.official_api import OfficialApiProvider
from controller import SisuController

# Define Brazil Timezone to ensure consistency across servers
BR_TZ = ZoneInfo("America/Sao_Paulo")

def run_batch_sync():
    """
    Automates the synchronization of the top 17 SISU courses.
    Includes a timezone-aware check to skip courses already updated today.
    """
    # Mapping of the most relevant Course IDs (co_curso)
    top_courses_ids = [
        "37", "44", "63", "1806",
        "1", "4636", "10", "20", 
        "22", "78", "2217", "30", 
        "38", "41", "42", "43", "21"
    ]
    
    # Initialize infrastructure layers
    repository = SisuRepository()
    provider = OfficialApiProvider()
    controller = SisuController(provider, repository)
    
    # Get current Brazil time for consistent date identification
    now_br = datetime.now(BR_TZ)
    today_column = f"nota_{now_br.strftime('%d_%m')}"
    
    print(f"🚀 Iniciando sincronização em lote de {len(top_courses_ids)} cursos...")
    print(f"📅 Data/Hora (BR): {now_br.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔍 Coluna do dia: {today_column}")
    print("-" * 50)
    
    for course_id in top_courses_ids:
        try:
            # 1. Pre-sync check: skip if data for today already exists in the CSV
            file_path = os.path.join(HISTORY_DIR, f"historico_sisu_curso_{course_id}.csv")
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader, [])
                    if today_column in header:
                        print(f"⏭️ Curso {course_id} já atualizado hoje. Pulando...")
                        continue

            print(f"⏳ Sincronizando curso ID: {course_id}...")
            
            # 2. Setup the discrete logger (prints every 10% milestone)
            last_milestone = -1

            def progress_logger(p):
                """Callback to log progress at every 10% bracket."""
                nonlocal last_milestone
                current_step = int(p * 10)
                
                if current_step > last_milestone:
                    percentage = current_step * 10
                    print(f"  > Progresso curso {course_id}: {percentage}%", flush=True)
                    last_milestone = current_step

            # 3. Execute high-speed parallel processing via Controller
            controller.process_all(course_id, progress_logger)
            
            print(f"✅ Curso {course_id} finalizado com sucesso.")
            
            # Short sleep between courses to allow the session pool to recycle
            time.sleep(1.5) 
            
        except Exception as e:
            print(f"\n❌ Erro crítico ao sincronizar curso {course_id}: {e}")
            continue 

    print("-" * 50)
    print("🏁 Sincronização em lote concluída!")

if __name__ == "__main__":
    run_batch_sync()