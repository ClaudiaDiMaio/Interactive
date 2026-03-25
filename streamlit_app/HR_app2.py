import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import tempNcolor as t2c 

st.set_page_config(page_title="Stellar Cluster Lab", layout="wide")

@st.cache_data
def load_data():
    hip = pd.read_csv('data/Hipparcos.csv')
    hip['hex'] = t2c.rgb2hex(t2c.bv2rgb(hip['B-V']))
    clusters = pd.read_csv('data/clusterdata.csv')
    
    # Metadata degli ammassi
    c_info = pd.DataFrame({
        'Name': ['Pleiades', 'Hyades', 'M53', '47 Tuc'],
        'id': ['pleiades', 'hyades', 'm53', '47tuc'],
        'true_d': [136, 47, 18000, 4000],
        'minB': [1e-10, 1e-10, 1e-11, 1e-11],
        'maxB': [1e-2, 1e-2, 1e-3, 1e-3]
    }).set_index('Name')
    return hip, clusters, c_info

hip_df, cluster_df, cluster_info = load_data()

# --- SIDEBAR ---
st.sidebar.header("🕹️ Controlli")
# DEFINIAMO 'selected_name' QUI
selected_name = st.sidebar.selectbox("Seleziona Ammasso:", list(cluster_info.index))
info = cluster_info.loc[selected_name]

log_dist = st.sidebar.slider("Distanza Modello (log10 pc)", 1.0, 4.6, 2.0, step=0.01)
dist_pc = 10**log_dist

# --- LOGICA FISICA ---
zams_bv = np.array([-0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6])
zams_lum = 10**np.array([4.0, 3.0, 2.0, 1.2, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0])

# Filtriamo i dati dell'ammasso scelto
this_cluster_data = cluster_df[cluster_df['Cluster'] == info['id']]

# DEFINIAMO 'cluster_colors' QUI
cluster_colors = t2c.rgb2hex(t2c.bv2rgb(this_cluster_data['B-V']))

# --- GRAFICO 1 (HR) ---
fig_hr = go.Figure()
fig_hr.add_trace(go.Scattergl(x=hip_df['B-V'], y=hip_df['Lum'], mode='markers',
                            marker=dict(size=2, color='gray', opacity=0.2), name='Hipparcos'))
fig_hr.add_trace(go.Scatter(x=zams_bv, y=zams_lum, mode='lines+markers',
                          line=dict(color='#00FFFF', width=4), name='Modello ZAMS'))
fig_hr.update_layout(title="1. Potenza Reale", yaxis_type="log", template="plotly_dark")

# --- GRAFICO 2 (CLUSTER) ---
fig_cl = go.Figure()
# Qui usiamo le variabili DEFINITE SOPRA: cluster_colors e selected_name
fig_cl.add_trace(go.Scattergl(
    x=this_cluster_data['B-V'], 
    y=this_cluster_data['Brightness'], 
    mode='markers',
    marker=dict(size=5, color=cluster_colors, opacity=0.7), 
    name=selected_name
))

# Curva modello alla distanza scelta
zams_app = zams_lum / (4 * np.pi * (dist_pc**2))
fig_cl.add_trace(go.Scatter(x=zams_bv, y=zams_app, mode='lines',
                          line=dict(color='#00FFFF', width=4, dash='dot'), name='Fit'))

fig_cl.update_layout(title=f"2. Fitting: {selected_name}", yaxis_type="log", template="plotly_dark",
                   yaxis=dict(range=[np.log10(info['minB']), np.log10(info['maxB'])]))

# --- LAYOUT ---
st.title("🌌 Fitting della Sequenza Principale")
c1, c2 = st.columns(2)
c1.plotly_chart(fig_hr, use_container_width=True)
c2.plotly_chart(fig_cl, use_container_width=True)

# Verifica risultato
st.write(f"### Distanza stimata: {int(dist_pc)} pc")
if abs(dist_pc - info['true_d']) / info['true_d'] < 0.1:
    st.balloons()
    st.success(f"Fitting corretto per {selected_name}!")
