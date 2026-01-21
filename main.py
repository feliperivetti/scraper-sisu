import requests
import time
import json
import csv
import os
from datetime import datetime

# Cabeçalhos para simular o navegador
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

def obter_lista_vagas(id_curso):
    """Fase 1: Obtém a lista de ofertas para o curso."""
    url = f"https://sisu-api.sisu.mec.gov.br/api/v1/oferta/curso/{id_curso}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        vagas = []
        for chave, valor in data.items():
            if chave == "search_rule": continue
            vagas.append({
                "co_oferta": valor.get("co_oferta"),
                "universidade": valor.get("sg_ies"),
                "cidade": valor.get("no_municipio_campus"),
                "uf": valor.get("sg_uf_campus"),
                "curso": valor.get("no_curso")
            })
        return vagas
    except Exception as e:
        print(f"Erro ao listar ofertas: {e}")
        return []

def obter_nota_corte(co_oferta):
    """Fase 2: Obtém a nota de corte (float) da Ampla Concorrência."""
    url = f"https://sisu-api.sisu.mec.gov.br/api/v1/oferta/{co_oferta}/modalidades"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        modalidades = data.get("modalidades", [])
        for mod in modalidades:
            if mod.get("no_concorrencia") == "Ampla concorrência":
                nota = mod.get("nu_nota_corte")
                return float(nota) if nota else None
        return None
    except Exception:
        return None

def atualizar_historico_csv(resultados, id_curso):
    """Nova função: Gerencia o CSV com colunas dinâmicas por data."""
    nome_csv = f"/historico_sisu_curso_{id_curso}.csv"
    coluna_hoje = f"nota_{datetime.now().strftime('%d_%m')}"
    
    dados_acumulados = {}
    colunas_header = ["co_oferta", "curso", "universidade", "cidade", "uf"]
    
    # 1. Tenta ler o CSV existente para preservar os dias anteriores
    if os.path.exists(nome_csv):
        with open(nome_csv, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f)
            colunas_header = leitor.fieldnames
            for linha in leitor:
                dados_acumulados[linha['co_oferta']] = linha

    # 2. Adiciona a coluna de hoje se ela for nova
    if coluna_hoje not in colunas_header:
        colunas_header.append(coluna_hoje)

    # 3. Atualiza os dados com as notas coletadas agora (usando co_oferta como chave)
    for r in resultados:
        id_vaga = r['co_oferta']
        if id_vaga not in dados_acumulados:
            dados_acumulados[id_vaga] = {k: r[k] for k in ["co_oferta", "curso", "universidade", "cidade", "uf"]}
        
        dados_acumulados[id_vaga][coluna_hoje] = r['nota_corte'] if r['nota_corte'] else "N/A"

    # 4. Escreve o arquivo final atualizado
    with open(nome_csv, mode='w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=colunas_header)
        escritor.writeheader()
        # Ordena por universidade para manter o arquivo organizado
        lista_final = sorted(dados_acumulados.values(), key=lambda x: x['universidade'])
        escritor.writerows(lista_final)
    
    return nome_csv

def salvar_relatorios_estaticos(resultados, id_curso):
    """Gerencia a criação do JSON e do TXT formatado."""
    nome_json = f"sisu_notas_curso_{id_curso}.json"
    nome_txt = f"sisu_notas_curso_{id_curso}.txt"

    # Salvar JSON
    with open(nome_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)

    # Salvar TXT
    with open(nome_txt, "w", encoding="utf-8") as f:
        f.write(f"NOTAS DE CORTE - CURSO ID {id_curso} | GERADO EM: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write("="*70 + "\n")
        f.write(f"{'IES':<10} | {'CIDADE':<25} | {'UF':<3} | {'NOTA'}\n")
        f.write("-" * 70 + "\n")
        for r in resultados:
            nota_str = f"{r['nota_corte']:.2f}" if r['nota_corte'] else "N/A"
            f_txt_linha = f"{r['universidade']:<10} | {r['cidade'][:25]:<25} | {r['uf']:<3} | {nota_str}\n"
            f.write(f_txt_linha)
            
    return nome_json, nome_txt

def main():
    # ID = "63" # Ciência da Computação
    ID = "44" # Psicologia
    resultados_finais = []

    print(f"--- Iniciando extração do curso {ID} ---")
    lista_vagas = obter_lista_vagas(ID)
    if not lista_vagas: return

    # Processamento de notas
    for i, vaga in enumerate(lista_vagas):
        if (i + 1) % 10 == 0: print(f"Progresso: {i+1}/{len(lista_vagas)} faculdades...")
        time.sleep(0.3) 
        vaga["nota_corte"] = obter_nota_corte(vaga["co_oferta"])
        resultados_finais.append(vaga)

    # Ordenação e salvamento
    resultados_finais.sort(key=lambda x: x['nota_corte'] if x['nota_corte'] is not None else float('inf'))
    
    # Chamada das funções de arquivo
    json_path, txt_path = salvar_relatorios_estaticos(resultados_finais, ID)
    csv_path = atualizar_historico_csv(resultados_finais, ID)

    print(f"\n" + "="*50)
    print(f"RELATÓRIOS ATUALIZADOS:\n- {json_path}\n- {txt_path}\n- {csv_path}")
    print("="*50)

if __name__ == "__main__":
    main()