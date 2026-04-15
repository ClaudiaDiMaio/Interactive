import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Stellar Lab Debug", layout="wide")

# Funzione rapida per i colori (così non serve tempNcolor per il test)
def get_color_from_bv(bv):
    if bv < 0: return "#9bb0ff" # Blu
    if bv < 0.5: return "#ffffff" # Bianco
    if bv < 1.0: return "#ffff00" # Giallo
    return "#ff4500" # Rosso

# --- CARICAMENTO DATI SICURO ---
@st.cache_data
def load_stellar_data():
    # Controlliamo se la cartella data esiste
    if not os.path.exists('data/Hipparcos.csv'):
        st.error("❌ ERRORE: Non trovo il file 'data/Hipparcos.csv'. Controlla che la cartella 'data' sia su GitHub!")
        return None, None
    
    hip = pd.read_csv('data/Hipparcos.csv')
    clusters = pd.read_csv('data/clusterdata.csv')
    
    # Pulizia minima dei dati
    hip = hip.dropna(subset=['B-V', 'Lum'])
    hip['color'] = hip['B-V'].apply(get_color_from_bv)
    
    return hip, clusters

hip_df, cluster_df = load_stellar_data()

if hip_df is not None:
    # --- CONTROLLI NELLA SIDEBAR ---
    st.sidebar.header("🕹️ Comandi")
    
    # 1. Selezione Ammasso
    cluster_names = {"Pleiadi": "pleiades", "Iadi": "hyades", "M53": "m53", "47 Tuc": "47tuc"}
    sel_name = st.sidebar.selectbox("Scegli Ammasso:", list(cluster_names.keys()))
    sel_id = cluster_names[sel_name]
    
    # 2. Slider Distanza
    log_d = st.sidebar.slider("Distanza (log10)", 1.0, 4.5, 2.0, 0.01)
    d_pc = 10**log_d
    
    # 3. Offset Luminosità (Sostituisce il trascinamento punti)
    l_off = st.sidebar.slider("Aggiustamento Lum", 0.1, 5.0, 1.0, 0.1)

    # --- LOGICA FISICA ---
    # Sequenza Principale Teorica (ZAMS)
    z_bv = np.array([-0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6])
    z_lum = 10**np.array([4.0, 3.0, 2.0, 1.2, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0]) * l_off
    z_app = z_lum / (4 * np.pi * (d_pc**2))

    # --- GRAFICI ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("1. Modello Teorico")
        fig1 = go.Figure()
        fig1.add_trace(go.Scattergl(x=hip_df['B-V'], y=hip_df['Lum'], mode='markers',
                                  marker=dict(size=3, color='lightgray', opacity=0.4), name='Stelle'))
        fig1.add_trace(go.Scatter(x=z_bv, y=z_lum, mode='lines+markers',
                                line=dict(color='cyan', width=3), name='Modello'))
        fig1.update_layout(yaxis_type="log", template="plotly_dark", height=450, xaxis_title="B-V", yaxis_title="L")
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader(f"2. Fitting: {sel_name}")
        cl_data = cluster_df[cluster_df['Cluster'] == sel_id]
        fig2 = go.Figure()
        fig2.add_trace(go.Scattergl(x=cl_data['B-V'], y=cl_data['Brightness'], mode='markers',
                                  marker=dict(size=4, color='orange'), name='Ammasso'))
        fig2.add_trace(go.Scatter(x=z_bv, y=z_app, mode='lines',
                                line=dict(color='cyan', width=3, dash='dash'), name='Fit'))
        fig2.update_layout(yaxis_type="log", template="plotly_dark", height=450, xaxis_title="B-V", yaxis_title="b")
        st.plotly_chart(fig2, use_container_width=True)

    st.info(f"📏 Distanza calcolata: **{int(d_pc)} pc**")
