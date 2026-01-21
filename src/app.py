import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# Importamos o HISTORY_DIR que definimos no Repository
from repository import SisuRepository, HISTORY_DIR
from providers.official_api import OfficialApiProvider
from controller import SisuController

st.set_page_config(page_title="SISU Analytica Pro", layout="wide", page_icon="📊")

def render_sidebar(repository: SisuRepository):
    st.sidebar.header("🎯 Configurações")
    
    # O repository já sabe que o cursos.json está em data/mappings/
    mapping = repository.load_courses_mapping()
    
    if mapping:
        names = list(mapping.keys())
        default_idx = names.index("PSICOLOGIA") if "PSICOLOGIA" in names else 0
        selected = st.sidebar.selectbox("Selecione o Curso", options=names, index=default_idx)
        course_id = mapping[selected]
    else:
        st.sidebar.warning("Mapeamento de cursos não encontrado em 'data/mappings/'.")
        course_id = st.sidebar.text_input("ID do Curso", "63")

    # ATUALIZAÇÃO: Agora aponta para a subpasta 'history'
    csv_path = os.path.join(HISTORY_DIR, f"historico_sisu_curso_{course_id}.csv")
    today_col = f"nota_{datetime.now().strftime('%d_%m')}"
    
    is_updated = False
    if os.path.exists(csv_path):
        # Verifica se a coluna de hoje já existe no CSV de histórico
        df_check = pd.read_csv(csv_path, nrows=0)
        if today_col in df_check.columns:
            is_updated = True

    st.sidebar.divider()
    
    # Botão de sincronização
    if st.sidebar.button("🔄 Sincronizar com MEC", use_container_width=True):
        if is_updated and not st.sidebar.checkbox("Forçar atualização?", value=False):
            st.sidebar.info("Dados já atualizados hoje.")
        else:
            provider = OfficialApiProvider()
            ctrl = SisuController(provider, repository)
            bar = st.progress(0)
            with st.spinner("Buscando dados no MEC..."):
                ctrl.process_all(course_id, lambda p: bar.progress(p))
            st.rerun()
            
    return course_id, csv_path

def main():
    st.title("📊 SISU Aggregator & Analytica")
    
    repository = SisuRepository()
    course_id, csv_path = render_sidebar(repository)

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        score_cols = [c for c in df.columns if c.startswith('nota_')]
        
        st.subheader("📋 Tabela de Notas de Corte")
        
        # Filtro de UF (Estado)
        if 'uf' in df.columns:
            ufs = st.multiselect("Filtrar por UF", sorted(df['uf'].unique()))
            df_view = df[df['uf'].isin(ufs)] if ufs else df
        else:
            df_view = df
        
        st.dataframe(df_view, use_container_width=True)

        # Gráfico de Evolução (Focado nas 5 menores notas)
        if score_cols:
            st.divider()
            st.subheader("📈 Evolução das 5 Menores Notas")
            
            # Pega as 5 menores faculdades baseadas na última nota coletada
            top_df = df_view.nsmallest(5, score_cols[-1]).copy()
            top_df['Campus'] = top_df['universidade'] + " (" + top_df['cidade'] + ")"
            
            # Transforma os dados para o formato longo (exigido pelo Plotly)
            df_plot = top_df.melt(
                id_vars=['Campus'], value_vars=score_cols, 
                var_name='Date', value_name='Score'
            )
            # Limpa a legenda da data (nota_21_01 -> 21/01)
            df_plot['Date'] = df_plot['Date'].str.replace('nota_', '').str.replace('_', '/')

            # Gráfico com legenda no rodapé para melhor visualização mobile
            fig = px.line(
                df_plot, x='Date', y='Score', color='Campus', markers=True,
                labels={"Score": "Nota", "Date": "Dia"},
                template="plotly_white"
            )
            
            fig.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5),
                margin=dict(l=10, r=10, t=40, b=10)
            )

            # Ajuste dinâmico do eixo Y para focar no intervalo das notas
            scores = pd.to_numeric(df_plot['Score'], errors='coerce').dropna()
            if not scores.empty:
                fig.update_layout(yaxis=dict(range=[scores.min() - 5, scores.max() + 5]))
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum histórico encontrado para este curso em 'data/history/'. Clique em 'Sincronizar'.")

if __name__ == "__main__":
    main()