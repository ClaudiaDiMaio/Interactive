import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import tempNcolor as t2c  # Assicurati che il file sia nella stessa cartella

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Fitting Ammassi Stellari", layout="wide")

# --- CARICAMENTO DATI ---
@st.cache_data
def load_all_data():
    try:
        # Dati Hipparcos
        hip_df = pd.read_csv('data/Hipparcos.csv')
        hip_df['hex'] = t2c.rgb2hex(t2c.bv2rgb(hip_df['B-V']))
        
        # Dati Cluster
        cluster_df = pd.read_csv('data/clusterdata.csv')
        
        # Informazioni Ammassi
        c_info = pd.DataFrame({
            'Name': ['Pleiades', 'Hyades', 'M53', '47 Tuc'],
            'id': ['pleiades', 'hyades', 'm53', '47tuc'],
            'Dist_Reale': [136, 47, 18000, 4000],
            'minB': [1e-10, 1e-10, 1e-11, 1e-11],
            'maxB': [1e-2, 1e-2, 1e-3, 1e-3]
        }).set_index('Name')
        
        return hip_df, cluster_df, c_info
    except Exception as e:
        st.error(f"Errore nel caricamento dati: {e}")
        return None, None, None

hip_df, cluster_df, cluster_info = load_all_data()

# --- LOGICA FISICA: SEQUENZA PRINCIPALE (ZAMS) ---
# Definiamo la Sequenza Principale Teorica (ZAMS) standard
zams_bv = np.array([-0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6])
zams_lum = 10**np.array([4.0, 3.0, 2.0, 1.2, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0])

def get_ms_apparent(lum, distance):
    # b = L / (4 * pi * d^2)
    return lum / (4 * np.pi * (distance**2))

# --- INTERFACCIA SIDEBAR ---
st.sidebar.header("🕹️ Controlli Fitting")

selected_cluster = st.sidebar.radio("Seleziona Ammasso:", list(cluster_info.index))
info = cluster_info.loc[selected_cluster]

st.sidebar.markdown("---")
st.sidebar.subheader("📏 Parametri del Modello")

# Slider per la distanza (Logaritmico)
# In Streamlit usiamo un numero che poi eleviamo alla potenza per simulare il logaritmo
log_dist = st.sidebar.slider("Distanza Modello (log10 pc)", 1.0, 4.6, 2.0, step=0.01)
dist_pc = 10**log_dist

st.sidebar.write(f"**Distanza calcolata:** {int(dist_pc)} pc")

# Offset Luminosità (Sostituisce il trascinamento manuale dei punti per ricalibrare il modello)
lum_offset = st.sidebar.slider("Aggiustamento Modello (Lum)", 0.5, 2.0, 1.0, step=0.1)
current_zams_lum = zams_lum * lum_offset

# --- PREPARAZIONE GRAFICI ---

# 1. Grafico HR (Luminosità Reale)
fig_hr = go.Figure()

# Sfondo Hipparcos
fig_hr.add_trace(go.Scattergl(
    x=hip_df['B-V'], y=hip_df['Lum'], mode='markers',
    marker=dict(size=2, color='gray', opacity=0.2), name='Hipparcos'
))

# Modello ZAMS
fig_hr.add_trace(go.Scatter(
    x=zams_bv, y=current_zams_lum, mode='lines+markers',
    line=dict(color='#00FFFF', width=4), name='Modello ZAMS'
))

fig_hr.update_layout(
    title="1. Modello Teorico (Diagramma H-R)",
    xaxis_title="Colore (B-V)", yaxis_title="Luminosità (L☉)",
    yaxis_type="log", template="plotly_dark", height=500,
    xaxis=dict(range=[-0.5, 2.0])
)

# 2. Grafico Cluster (Brillantezza Apparente)
this_cluster_data = cluster_df[cluster_df['Cluster'] == info['id']]
cluster_colors = t2c.rgb2hex(t2c.bv2rgb(this_cluster_data['B-V']))

fig_cl = go.Figure()

# Dati Ammasso
fig_cl.add_trace(go.Scattergl(
    x=this_cluster_data['B-V'], y=this_cluster_data['Brightness'], mode='markers',
    marker=dict(size=5, color=cluster_colors, opacity=0.7), name=selected_name
))

# Modello Proiettato alla distanza scelta
zams_app = get_ms_apparent(current_zams_lum, dist_pc)
fig_cl.add_trace(go.Scatter(
    x=zams_bv, y=zams_app, mode='lines',
    line=dict(color='#00FFFF', width=4, dash='dot'), name=f'Modello a {int(dist_pc)} pc'
))

fig_cl.update_layout(
    title=f"2. Fitting: {selected_cluster}",
    xaxis_title="Colore (B-V)", yaxis_title="Brillantezza (L☉/pc²)",
    yaxis_type="log", template="plotly_dark", height=500,
    xaxis=dict(range=[-0.5, 2.0]),
    yaxis=dict(range=[np.log10(info['minB']), np.log10(info['maxB'])])
)

# --- DISPLAY ---
st.title("🌌 Fitting della Sequenza Principale negli Ammassi")
st.markdown("""
Sposta lo slider della **Distanza** nella barra laterale finché la **linea azzurra punteggiata** non si sovrappone ai punti dell'ammasso stellare.
""")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_hr, use_container_width=True)
with col2:
    st.plotly_chart(fig_cl, use_container_width=True)

# --- AREA RISULTATI ---
st.divider()
st.subheader("🕵️‍♂️ Risultati dell'Analisi")
c1, c2, c3 = st.columns(3)

true_d = info['Dist_Reale']
err = abs(dist_pc - true_d) / true_d * 100

c1.metric("Distanza Stimata", f"{int(dist_pc)} pc")
c2.metric("Distanza Reale", f"{true_d} pc")
c3.metric("Errore", f"{err:.1f} %")

if err < 10:
    st.balloons()
    st.success("🎯 Ottimo lavoro! Hai trovato la distanza corretta dell'ammasso!")
