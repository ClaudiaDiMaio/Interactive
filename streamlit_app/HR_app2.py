import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import tempNcolor as t2c 

st.set_page_config(page_title="Fitting della Sequenza Principale", layout="wide")

@st.cache_data
def load_data():
    try:
        hip = pd.read_csv('data/Hipparcos.csv')
        hip['hex'] = t2c.rgb2hex(t2c.bv2rgb(hip['B-V']))
        clusters = pd.read_csv('data/clusterdata.csv')
        
        c_info = pd.DataFrame({
            'Name': ['Pleiades', 'Hyades', 'M53', '47 Tuc'],
            'id': ['pleiades', 'hyades', 'm53', '47tuc'],
            'true_d': [136, 47, 18000, 4000],
            'minB': [1e-10, 1e-10, 1e-11, 1e-11],
            'maxB': [1e-2, 1e-2, 1e-3, 1e-3]
        }).set_index('Name')
        return hip, clusters, c_info
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return None, None, None

hip_df, cluster_df, cluster_info = load_data()

# --- SIDEBAR: I NUOVI COMANDI DI FITTING ---
st.sidebar.header("🕹️ Calibrazione Modello")
st.sidebar.write("Usa questi slider per adattare la linea azzurra:")

# 1. Spostamento verticale (Luminosità)
lum_offset = st.sidebar.slider("Sposta Su/Giù (Lum)", 0.1, 5.0, 1.0, step=0.1)
# 2. Spostamento orizzontale (Colore)
color_offset = st.sidebar.slider("Sposta Destra/Sinistra (Colore)", -0.5, 0.5, 0.0, step=0.05)

st.sidebar.markdown("---")
st.sidebar.header("📏 Trova la Distanza")
selected_name = st.sidebar.selectbox("Seleziona Ammasso:", list(cluster_info.index))
info = cluster_info.loc[selected_name]

log_dist = st.sidebar.slider("Distanza (log10 pc)", 1.0, 4.6, 2.0, step=0.01)
dist_pc = 10**log_dist

# --- LOGICA FISICA ---
# Definiamo la ZAMS base
zams_bv_base = np.array([-0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6])
zams_lum_base = 10**np.array([4.0, 3.0, 2.0, 1.2, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0])

# Applichiamo gli offset degli slider
current_zams_bv = zams_bv_base + color_offset
current_zams_lum = zams_lum_base * lum_offset

# --- GRAFICO 1 (HR) ---
fig_hr = go.Figure()
fig_hr.add_trace(go.Scattergl(x=hip_df['B-V'], y=hip_df['Lum'], mode='markers',
                            marker=dict(size=2, color='gray', opacity=0.2), name='Hipparcos'))
fig_hr.add_trace(go.Scatter(x=current_zams_bv, y=current_zams_lum, mode='lines+markers',
                          line=dict(color='#00FFFF', width=4), name='Modello ZAMS'))
fig_hr.update_layout(title="1. Calibrazione Modello", yaxis_type="log", template="plotly_dark",
                  xaxis=dict(range=[-0.5, 2.0]), yaxis=dict(range=[1e-3, 1e5]))

# --- GRAFICO 2 (CLUSTER) ---
this_cluster_data = cluster_df[cluster_df['Cluster'] == info['id']]
cluster_colors = t2c.rgb2hex(t2c.bv2rgb(this_cluster_data['B-V']))

fig_cl = go.Figure()
fig_cl.add_trace(go.Scattergl(x=this_cluster_data['B-V'], y=this_cluster_data['Brightness'], mode='markers',
                            marker=dict(size=5, color=cluster_colors, opacity=0.7), name=selected_name))

# Applichiamo la distanza al modello calibrato
zams_app = current_zams_lum / (4 * np.pi * (dist_pc**2))
fig_cl.add_trace(go.Scatter(x=current_zams_bv, y=zams_app, mode='lines',
                          line=dict(color='#00FFFF', width=4, dash='dot'), name='Fit Distanza'))

fig_cl.update_layout(title=f"2. Fitting: {selected_name}", yaxis_type="log", template="plotly_dark",
                   xaxis=dict(range=[-0.5, 2.0]), 
                   yaxis=dict(range=[np.log10(info['minB']), np.log10(info['maxB'])]))

# --- LAYOUT ---
st.title("🌌 Laboratorio: Main Sequence Fitting")
st.write("1. Regola **Colore** e **Lum** nel Grafico 1 per coprire le stelle Hipparcos.")
st.write("2. Regola la **Distanza** nel Grafico 2 per far coincidere la linea con l'ammasso.")

c1, c2 = st.columns(2)
c1.plotly_chart(fig_hr, use_container_width=True)
c2.plotly_chart(fig_cl, use_container_width=True)

st.metric("Distanza Stimata", f"{int(dist_pc)} pc", delta=f"{int(dist_pc - info['true_d'])} pc vs Reale")
if abs(dist_pc - info['true_d']) / info['true_d'] < 0.1:
    st.balloons()
