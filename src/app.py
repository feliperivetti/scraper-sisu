import streamlit as st
import pandas as pd
import plotly.express as px
from repository import SisuRepository
from providers.fredao_provider import FredaoProvider

# --- UI CONFIGURATION ---
st.set_page_config(page_title="SISU Analytics", layout="wide", page_icon="📊")

def get_unified_data(selected_ids, selected_names_map, repository, provider):
    """
    Hybrid data fetcher:
    1. Fetches priority data from the local SQLite (Top 17 courses).
    2. Fetches missing courses on-demand from the Specialist API.
    3. Normalizes strings and deduplicates entries prioritizing verified data.
    """
    # 1. Database retrieval
    df_db = repository.get_history_dataframe(selected_ids)
    
    if not df_db.empty:
        # Map IDs to names and normalize strings for consistent grouping
        df_db['curso'] = df_db['course_id'].map(selected_names_map)
        df_db['universidade'] = df_db['universidade'].str.upper().str.strip()
        df_db['cidade'] = df_db['cidade'].str.upper().str.strip()
    
    # Identify missing IDs not found in local DB
    found_ids = df_db['course_id'].unique().tolist() if not df_db.empty else []
    missing_ids = [str(cid).strip() for cid in selected_ids if str(cid).strip() not in found_ids]
    
    # 2. Live Fallback for on-demand courses
    live_results = []
    if missing_ids:
        raw_mapping = repository.load_full_mapping()
        for cid in missing_ids:
            specialist_id = None
            course_name = selected_names_map.get(cid, "Desconhecido")
            
            # Find the specialist_id (fredao_id) in the raw JSON mapping
            for letter in raw_mapping:
                for item in raw_mapping[letter]:
                    if str(item.get('co_curso')) == cid:
                        specialist_id = item.get('fredao_id')
                        break
            
            if specialist_id:
                with st.spinner(f"🛰️ Buscando dados ao vivo para {course_name}..."):
                    rows = provider.get_full_history_data(specialist_id)
                    if rows:
                        for r in rows:
                            # Map partial day keys to specific calendar dates
                            for i in range(1, 5):
                                day_key, date_str = f"PARCIAL_DIA{i}", f"{19+i}/01"
                                score = r.get(day_key)
                                if score:
                                    live_results.append({
                                        'curso': course_name.upper().strip(),
                                        'universidade': str(r.get('SIGLA')).upper().strip(),
                                        'cidade': str(r.get('MUNICIPIO_CAMPUS')).upper().strip(),
                                        'uf': str(r.get('SG_UF_CAMPUS')).upper().strip(),
                                        'date': date_str,
                                        'score': float(score),
                                        'fonte': 'LIVE_API',
                                        'course_id': cid
                                    })
    
    # 3. Data Integration and Cleaning
    df_live = pd.DataFrame(live_results)
    final_df = pd.concat([df_db, df_live], ignore_index=True) if not df_db.empty or not df_live.empty else pd.DataFrame()
    
    if not final_df.empty:
        # Force normalization to avoid duplicate rows in pivot table
        final_df['universidade'] = final_df['universidade'].str.upper().str.strip()
        final_df['cidade'] = final_df['cidade'].str.upper().str.strip()
        
        # Deduplicate prioritizing Live API to correct official SiSU bugs
        final_df = final_df.sort_values('fonte', ascending=False)
        final_df = final_df.drop_duplicates(
            subset=['course_id', 'universidade', 'cidade', 'date'], 
            keep='first'
        )
    return final_df

def main():
    # --- HEADER ---
    st.title("📊 Visualização de Dados do SISU")
    st.caption("Estratégia Híbrida: SQLite (Top 17) + API Fredão (Sob Demanda)")

    repo = SisuRepository()
    fredao = FredaoProvider()
    
    # --- SIDEBAR: COURSE SELECTION ---
    st.sidebar.header("🎯 Seleção de Cursos")
    mapping = repo.load_courses_mapping()
    reverse_mapping = {v: k for k, v in mapping.items()} 
    
    # User shows interest in Psychology
    selected_names = st.sidebar.multiselect(
        "Cursos para Monitorar", 
        options=list(mapping.keys()), 
        default=["PSICOLOGIA"] if "PSICOLOGIA" in mapping else None
    )
    selected_ids = [mapping[name] for name in selected_names]

    if not selected_ids:
        st.info("👋 Selecione um ou mais cursos na barra lateral para começar.")
        return

    # Data Retrieval
    df = get_unified_data(selected_ids, reverse_mapping, repo, fredao)

    if not df.empty:
        # Strict Date Filter (Jan 20 to Jan 23)
        valid_dates = ['20/01', '21/01', '22/01', '23/01']
        df = df[df['date'].isin(valid_dates)]

        # --- SIDEBAR: DEPENDENT FILTERS ---
        st.sidebar.divider()
        st.sidebar.header("🔍 Filtros de Localização")
        
        # 1. UF Filter
        ufs = st.sidebar.multiselect("Filtrar por UF", sorted(df['uf'].unique()))
        if ufs:
            df = df[df['uf'].isin(ufs)]

        # 2. University Filter (Dependent on UF filter)
        available_unis = sorted(df['universidade'].unique())
        selected_unis = st.sidebar.multiselect("Filtrar por Faculdade", options=available_unis)
        if selected_unis:
            df = df[df['universidade'].isin(selected_unis)]

        # --- VIEW 1: COMPARISON TABLE ---
        st.subheader("📋 Tabela Comparativa de Notas")
        df_table = df.pivot_table(
            index=['curso', 'universidade', 'cidade', 'uf'], 
            columns='date', 
            values='score'
        ).reset_index()
        st.dataframe(df_table.fillna("-"), use_container_width=True)

        # --- VIEW 2: EVOLUTION CHART ---
        st.divider()
        st.subheader("📈 Evolução Temporal")

        # Composite Legend to separate different campuses/courses
        df['Legenda'] = df['universidade'] + " (" + df['cidade'] + ") - " + df['curso']
        
        # Determine Top 5 based on the most recent score to avoid chart clutter
        latest_date = df['date'].max()
        top_entries = df[df['date'] == latest_date].nsmallest(5, 'score')['Legenda'].tolist()
        
        # Final dataset for line chart
        df_plot = df[df['Legenda'].isin(top_entries)].sort_values(['Legenda', 'date'])

        if not df_plot.empty:
            fig = px.line(
                df_plot, x='date', y='score', color='Legenda', 
                hover_data=['fonte'], markers=True,
                labels={"score": "Nota de Corte", "date": "Dia", "Legenda": "Opção"},
                template="plotly_dark"
            )
            
            # Use categorical X-axis to lock dates between 20/01 and 23/01
            fig.update_xaxes(type='category', categoryorder='array', categoryarray=valid_dates)
            
            # Focus Y-axis range
            y_min, y_max = df_plot['score'].min() - 10, df_plot['score'].max() + 10
            fig.update_layout(
                yaxis=dict(range=[y_min, y_max]),
                legend=dict(orientation="h", y=-0.2, xanchor="center", x=0.5, title=None),
                margin=dict(l=10, r=10, t=40, b=10)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ajuste os filtros para visualizar o gráfico de evolução.")
    else:
        st.error("Erro: Dados não encontrados para a seleção atual.")

if __name__ == "__main__":
    main()