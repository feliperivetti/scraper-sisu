import requests
import time
import models

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

def obter_lista_vagas(id_curso):
    url = f"https://sisu-api.sisu.mec.gov.br/api/v1/oferta/curso/{id_curso}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [v for k, v in data.items() if k != "search_rule"]
    except:
        return []

def obter_nota_corte(co_oferta):
    url = f"https://sisu-api.sisu.mec.gov.br/api/v1/oferta/{co_oferta}/modalidades"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        for mod in data.get("modalidades", []):
            if mod.get("no_concorrencia") == "Ampla concorrência":
                nota = mod.get("nu_nota_corte")
                return float(nota) if nota else None
    except:
        return None
    return None

def processar_tudo(id_curso, progress_callback):
    vagas_raw = obter_lista_vagas(id_curso)
    if not vagas_raw: return None
    
    resultados = []
    total = len(vagas_raw)
    for i, v in enumerate(vagas_raw):
        # Transforma o JSON bruto no dicionário que usamos
        vaga = {
            "co_oferta": v.get("co_oferta"),
            "universidade": v.get("sg_ies"),
            "cidade": v.get("no_municipio_campus"),
            "uf": v.get("sg_uf_campus"),
            "curso": v.get("no_curso")
        }
        vaga["nota_corte"] = obter_nota_corte(vaga["co_oferta"])
        resultados.append(vaga)
        progress_callback((i + 1) / total)
        time.sleep(0.3)

    # Ordena e manda o Model salvar
    resultados.sort(key=lambda x: x['nota_corte'] if x['nota_corte'] is not None else float('inf'))
    models.salvar_relatorios_estaticos(resultados, id_curso)
    csv_path = models.atualizar_historico_csv(resultados, id_curso)
    return csv_path