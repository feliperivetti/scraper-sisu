import time
from repository import SisuRepository
from providers.official_api import OfficialApiProvider
from controller import SisuController

def run_batch_sync():
    """
    Automates the synchronization of the top 17 SISU courses 
    to build a robust historical dataset.
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
    
    print(f"🚀 Iniciando sincronização em lote de {len(top_courses_ids)} cursos...")
    print(f"📅 Data/Hora: {time.strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 50)
    
    for course_id in top_courses_ids:
        try:
            print(f"⏳ Sincronizando curso ID: {course_id}...")
            
            # State variable to track 10% increments
            last_milestone = -1

            def progress_logger(p):
                """Callback to log progress at every 10% milestone."""
                nonlocal last_milestone
                # Convert 0.0-1.0 to 0-10 scale
                current_step = int(p * 10)
                
                # Only print if we moved to a new 10% bracket
                if current_step > last_milestone:
                    percentage = current_step * 10
                    print(f"  > Progresso curso {course_id}: {percentage}%", flush=True)
                    last_milestone = current_step

            # Execute processing with the discrete logger
            controller.process_all(course_id, progress_logger)
            
            print(f"✅ Curso {course_id} finalizado com sucesso.")
            
            # Safety sleep to respect MEC's API limits
            time.sleep(1.5) 
            
        except Exception as e:
            print(f"\n❌ Erro crítico ao sincronizar curso {course_id}: {e}")
            continue 

    print("-" * 50)
    print("🏁 Sincronização em lote concluída!")

if __name__ == "__main__":
    run_batch_sync()