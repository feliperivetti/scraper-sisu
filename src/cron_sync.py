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
            
            # The controller handles logic, we only pass the UI update callback
            controller.process_all(
                course_id, 
                lambda p: print(f"Progresso: {p*100:.1f}%", end="\r")
            )
            
            print(f"\n✅ Curso {course_id} finalizado com sucesso.")
            
            # Safety sleep to respect MEC's API limits and avoid IP flagging
            time.sleep(5) 
            
        except Exception as e:
            print(f"\n❌ Erro crítico ao sincronizar curso {course_id}: {e}")
            continue # Continue to the next course even if one fails

    print("-" * 50)
    print("🏁 Sincronização em lote concluída!")

if __name__ == "__main__":
    run_batch_sync()