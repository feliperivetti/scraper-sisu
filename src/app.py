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
        df_check = pd.read_csv(csv_path, nrows=0)
        if coluna_hoje in df_check.columns:
            ja_atualizado = True

    st.sidebar.divider()
    
    if ja_atualizado:
        st.sidebar.success(f"✅ Dados de hoje ({datetime.now().strftime('%d/%m')}) já coletados.")
        recarregar = st.sidebar.checkbox("Forçar atualização manual?")
    else:
        recarregar = True

    if st.sidebar.button("🔄 Sincronizar com MEC", use_container_width=True):
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
        
        st.dataframe(df_view, use_container_width=True)

        # Gráfico Plotly
        if cols_nota:
            st.divider()
            st.subheader("📈 Evolução das 5 Menores Notas")
            
            # Seleciona top 5 menores (baseado no último dia)
            top_df = df_view.nsmallest(5, cols_nota[-1])
            df_plot = top_df.melt(id_vars=['universidade'], value_vars=cols_nota, var_name='Data', value_name='Nota')
            df_plot['Data'] = df_plot['Data'].str.replace('nota_', '').str.replace('_', '/')

            fig = px.line(df_plot, x='Data', y='Nota', color='universidade', markers=True)
            
            # Ajuste do Eixo Y para o intervalo 650-850 ou conforme os dados
            min_val = df_plot['Nota'].min()
            max_val = df_plot['Nota'].max()
            fig.update_layout(yaxis=dict(range=[min_val - 10, max_val + 10]))
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado local encontrado. Selecione um curso e clique em 'Sincronizar'.")

if __name__ == "__main__":
    main()