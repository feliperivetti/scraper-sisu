import json
import csv
import os
from datetime import datetime

# Localiza o caminho absoluto para a pasta 'data' (sobe um nível saindo de /src)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))

# Garante que a pasta data exista fisicamente
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def carregar_cursos():
    """
    Lê o arquivo cursos.json estruturado de A a Z e 
    retorna um dicionário plano {Nome_do_Curso: ID}.
    """
    caminho_cursos = os.path.join(DATA_DIR, "cursos.json")
    
    if not os.path.exists(caminho_cursos):
        print(f"DEBUG: Arquivo não encontrado em {caminho_cursos}")
        return {}

    try:
        with open(caminho_cursos, "r", encoding="utf-8") as f:
            dados_brutos = json.load(f)
        
        cursos_mapeados = {}
        # Navega pelas chaves "A", "B", "C"... do seu JSON
        for letra in dados_brutos:
            # Garante que estamos lidando com a lista de cursos de cada letra
            lista_cursos = dados_brutos[letra]
            for curso in lista_cursos:
                nome = curso.get("no_curso")
                id_curso = str(curso.get("co_curso"))
                if nome and id_curso:
                    cursos_mapeados[nome] = id_curso
        
        # Retorna o dicionário ordenado alfabeticamente pelo nome do curso
        return dict(sorted(cursos_mapeados.items()))
    
    except Exception as e:
        print(f"Erro ao processar o arquivo de cursos: {e}")
        return {}

def salvar_relatorios_estaticos(resultados, id_curso):
    """Gera arquivos JSON e TXT individuais para a consulta atual."""
    nome_json = os.path.join(DATA_DIR, f"sisu_notas_curso_{id_curso}.json")
    nome_txt = os.path.join(DATA_DIR, f"sisu_notas_curso_{id_curso}.txt")

    # Salva JSON
    with open(nome_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=4, ensure_ascii=False)

    # Salva TXT formatado
    with open(nome_txt, "w", encoding="utf-8") as f:
        f.write(f"NOTAS DE CORTE - CURSO ID {id_curso} | {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write("="*75 + "\n")
        f.write(f"{'IES':<10} | {'CIDADE':<30} | {'UF':<3} | {'NOTA'}\n")
        f.write("-" * 75 + "\n")
        for r in resultados:
            nota_str = f"{r['nota_corte']:.2f}" if r['nota_corte'] else "N/A"
            f.write(f"{r['universidade']:<10} | {r['cidade'][:30]:<30} | {r['uf']:<3} | {nota_str}\n")
            
    return nome_json, nome_txt

def atualizar_historico_csv(resultados, id_curso):
    """Atualiza o CSV mestre adicionando uma nova coluna para o dia atual."""
    nome_csv = os.path.join(DATA_DIR, f"historico_sisu_curso_{id_curso}.csv")
    coluna_hoje = f"nota_{datetime.now().strftime('%d_%m')}"
    
    dados_acumulados = {}
    colunas_header = ["co_oferta", "curso", "universidade", "cidade", "uf"]
    
    # 1. Carrega dados anteriores se o arquivo já existir
    if os.path.exists(nome_csv):
        with open(nome_csv, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f)
            colunas_header = leitor.fieldnames
            for linha in leitor:
                dados_acumulados[linha['co_oferta']] = linha

    # 2. Adiciona a nova coluna de data ao cabeçalho (se não existir)
    if coluna_hoje not in colunas_header:
        colunas_header.append(coluna_hoje)

    # 3. Faz o merge dos dados novos com os antigos usando co_oferta como chave
    for r in resultados:
        id_vaga = r['co_oferta']
        if id_vaga not in dados_acumulados:
            dados_acumulados[id_vaga] = {
                "co_oferta": r['co_oferta'],
                "curso": r['curso'],
                "universidade": r['universidade'],
                "cidade": r['cidade'],
                "uf": r['uf']
            }
        
        # Atribui a nota na coluna do dia
        dados_acumulados[id_vaga][coluna_hoje] = r['nota_corte'] if r['nota_corte'] else "N/A"

    # 4. Grava o CSV atualizado
    with open(nome_csv, mode='w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=colunas_header)
        escritor.writeheader()
        # Ordena por universidade
        lista_final = sorted(dados_acumulados.values(), key=lambda x: x['universidade'])
        escritor.writerows(lista_final)
        
    return nome_csv