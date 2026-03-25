import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import tempNcolor as t2c  # Il tuo modulo locale per i colori

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Laboratorio Ammassi Stellari", layout="wide")

# --- FUNZIONE CARICAMENTO DATI ---
@st.cache_data
def load_data():
    try:
        # Carica Hipparcos (Sfondo)
        hip = pd.read_csv('data/Hipparcos.csv')
        hip['hex'] = t2c.rgb2hex(t2c.bv2rgb(hip['B-V']))
        
        # Carica Dati Ammassi
        clusters = pd.read_csv('data/clusterdata.csv')
        
        # Dizionario Metadati Ammassi (per scale e verifiche)
        c_info = {
            'Pleiades': {'id': 'pleiades', 'minB': 1e-10, 'maxB': 1e-2, 'true_d': 136},
            'Hyades': {'id': 'hyades', 'minB': 1e-10, 'maxB': 1e-2, 'true_d': 47},
            'M53': {'id': 'm53', 'minB': 1e-11, 'maxB': 1e-3, 'true_d': 18000},
            '47 Tuc': {'id': '47tuc', 'minB': 1e-11, 'maxB': 1e-3, 'true_d': 4000}
        }
        return hip, clusters, c_info
    except Exception as e:
        st.error(f"Errore: Assicurati che la cartella 'data' contenga i file CSV. Errore: {e}")
        return None, None, None

hip_df, cluster_df, cluster_info = load_data()

# --- LOGICA FISICA: SEQUENZA PRINCIPALE (ZAMS) ---
# Definiamo i punti della Sequenza Principale Teorica
zams_bv = np.array([-0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6])
zams_lum = 10**np.array([4.0, 3.0, 2.0, 1.2, 0.5, 0.0, -0.5, -1.0, -1.5, -2.0])

def calc_apparent_brightness(lum, dist):
    # b = L / (4 * pi * d^2)
    return lum / (4 * np.pi * (dist**2))

# --- INTERFACCIA SIDEBAR ---
st.sidebar.header("🔭 Comandi Laboratorio")
selected_name = st.sidebar.selectbox("Scegli Ammasso:", list(cluster_info.keys()))
info = cluster_info[selected_name]

st.sidebar.markdown("---")
st.sidebar.write("### 📏 Calibrazione Distanza")
# Slider logaritmico per coprire da 10 a 20.000 pc
dist_pc = st.sidebar.number_input("Distanza (pc)", min_value=1.0, max_value=30000.0, value=100.0, step=10.0)

# --- PREPARAZIONE GRAFICI ---
# 1. Grafico HR (Luminosità Reale)
fig_hr = go.Figure()
fig_hr.add_trace(go.Scattergl(
    x=hip_df['B-V'], y=hip_df['Lum'], mode='markers',
    marker=dict(size=2, color='gray', opacity=0.2), name='Stelle Hipparcos'
))
fig_hr.add_trace(go.Scatter(
    x=zams_bv, y=zams_lum, mode='lines+markers',
    line=dict(color='#00FFFF', width=4), name='Modello ZAMS'
))

fig_hr.update_layout(
    title="1. Diagramma H-R (Potenza Reale)",
    xaxis_title="Colore (B-V)", yaxis_title="Luminosità (L☉)",
    yaxis_type="log", template="plotly_dark", height=500,
    xaxis=dict(range=[-0.5, 2.0])
)

# 2. Grafico Cluster (Brillantezza Apparente)
this_cluster = cluster_df[cluster_df['Cluster'] == info['id']]
cluster_colors = t2c.rgb2hex(t2c.bv2rgb(this_cluster['B-V']))

fig_cl = go.Figure()
fig_cl.add_trace(go.Scattergl(
    x=this_cluster['B-V'], y=this_cluster['Brightness'], mode='markers',
    marker=dict(size=5, color=cluster_colors, opacity=0.8), name=selected_name
))

# Curva del modello scalata per la distanza scelta
zams_app = calc_apparent_brightness(zams_lum, dist_pc)
fig_cl.add_trace(go.Scatter(
    x=zams_bv, y=zams_app, mode='lines',
    line=dict(color='#00FFFF', width=4, dash='dot'), name=f'Modello a {dist_pc} pc'
))

fig_cl.update_layout(
    title=f"2. Fitting: {selected_name} (Apparenza)",
    xaxis_title="Colore (B-V)", yaxis_title="Brillantezza (L☉/pc²)",
    yaxis_type="log", template="plotly_dark", height=500,
    xaxis=dict(range=[-0.5, 2.0]),
    yaxis=dict(range=[np.log10(info['minB']), np.log10(info['maxB'])])
)

# --- DISPLAY ---
st.title("🌌 Laboratorio: La Scala delle Distanze")
st.write("Usa lo slider a sinistra per far coincidere il modello azzurro con i dati dell'ammasso.")

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(fig_hr, use_container_width=True)
with c2:
    st.plotly_chart(fig_cl, use_container_width=True)

# --- VERIFICA RISULTATO ---
st.divider()
true_d = info['true_d']
diff = abs(dist_pc - true_d) / true_d

if diff < 0.1:
    st.balloons()
    st.success(f"🎯 Eccellente! La distanza reale è {true_d} pc. Ottimo fitting!")
elif diff < 0.3:
    st.info(f"Sei vicino! La distanza reale è intorno a {true_d} pc. Prova a rifinire il valore.")
