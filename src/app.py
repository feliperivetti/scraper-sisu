import streamlit as st
import pandas as pd
import controller
import models
import os
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="SISU Analytica Pro", layout="wide", page_icon="📊")

def render_sidebar():
    st.sidebar.header("🎯 Configurações")
    
    # 1. Carregar lista de cursos do JSON
    dict_cursos = models.carregar_cursos()
    
    if dict_cursos:
        nomes_cursos = list(dict_cursos.keys())
        # Tenta selecionar "PSICOLOGIA" por padrão se existir
        default_idx = nomes_cursos.index("PSICOLOGIA") if "PSICOLOGIA" in nomes_cursos else 0
        
        nome_selecionado = st.sidebar.selectbox("Selecione o Curso", options=nomes_cursos, index=default_idx)
        id_curso = dict_cursos[nome_selecionado]
    else:
        st.sidebar.warning("Arquivo 'data/cursos.json' não encontrado.")
        id_curso = st.sidebar.text_input("Digite o ID do Curso manualmente", "63")

    # 2. Verificação de Dados do Dia
    csv_path = os.path.join(models.DATA_DIR, f"historico_sisu_curso_{id_curso}.csv")
    coluna_hoje = f"nota_{datetime.now().strftime('%d_%m')}"
    ja_atualizado = False
    
    if os.path.exists(csv_path):
        # Lê apenas o header para verificar se a coluna do dia já existe
        df_check = pd.read_csv(csv_path, nrows=0)
        if coluna_hoje in df_check.columns:
            ja_atualizado = True

    st.sidebar.divider()
    
    if ja_atualizado:
        st.sidebar.success(f"✅ Dados de hoje ({datetime.now().strftime('%d/%m')}) já coletados.")
        recarregar = st.sidebar.checkbox("Forçar atualização manual?")
    else:
        recarregar = True

    if st.sidebar.button("🔄 Sincronizar com MEC", width='stretch'):
        if ja_atualizado and not recarregar:
            st.sidebar.info("Os dados já estão atualizados.")
        else:
            bar = st.progress(0)
            with st.spinner("Buscando dados no MEC..."):
                controller.processar_tudo(id_curso, lambda p: bar.progress(p))
            st.rerun()
            
    return id_curso, csv_path

def main():
    st.title("📊 SISU Aggregator & Analytica")
    
    id_curso, csv_path = render_sidebar()

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        cols_nota = [c for c in df.columns if c.startswith('nota_')]
        
        st.subheader("📋 Tabela de Notas de Corte")
        
        # Filtro de UF
        ufs = st.multiselect("Filtrar por UF", sorted(df['uf'].unique()))
        df_view = df[df['uf'].isin(ufs)] if ufs else df
        
        # Exibição da tabela com destaque para as notas
        st.dataframe(df_view, width='stretch')

        # Gráfico Plotly Profissional
        if cols_nota:
            st.divider()
            st.subheader("📈 Evolução das 5 Menores Notas de Corte")
            st.caption("Nota: Identificadores combinam Instituição e Cidade para diferenciar campi.")

            # 1. Seleciona as 5 menores faculdades (baseado no último dia de nota)
            # Usamos .copy() para evitar o SettingWithCopyWarning ao criar a nova coluna
            top_df = df_view.nsmallest(5, cols_nota[-1]).copy()
            
            # 2. CORREÇÃO: Cria identificador único para evitar bug com IES iguais em cidades diferentes
            top_df['Campus'] = top_df['universidade'] + " (" + top_df['cidade'] + ")"
            
            # 3. Transforma os dados para o formato 'long' exigido pelo Plotly
            df_plot = top_df.melt(
                id_vars=['Campus'], 
                value_vars=cols_nota, 
                var_name='Data', 
                value_name='Nota'
            )
            
            # Formata a legenda da data para ficar mais limpa (nota_21_01 -> 21/01)
            df_plot['Data'] = df_plot['Data'].str.replace('nota_', '').str.replace('_', '/')

            # 4. Gera o gráfico de linha
            fig = px.line(
                df_plot, 
                x='Data', 
                y='Nota', 
                color='Campus', # Diferencia UEMG (Passos) de UEMG (Ituiutaba)
                markers=True,
                labels={"Nota": "Nota de Corte", "Data": "Dia da Consulta"},
                template="plotly_white"
            )
            
            # 5. AJUSTE DO EIXO Y: Foca no intervalo real (650 a 850) em vez de começar do zero
            notas_validas = df_plot['Nota'].dropna()
            if not notas_validas.empty:
                min_y = float(notas_validas.min()) - 5
                max_y = float(notas_validas.max()) + 5
                fig.update_layout(yaxis=dict(range=[min_y, max_y]))
            
            st.plotly_chart(fig, width='stretch')
    else:
        st.info("Nenhum dado local encontrado na pasta '/data'. Selecione um curso e clique em 'Sincronizar'.")

if __name__ == "__main__":
    main()