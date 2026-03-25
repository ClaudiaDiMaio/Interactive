import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import tempNcolor as t2c

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Evoluzione Stellare & Ammassi", layout="wide")

# --- FUNZIONI DI CARICAMENTO DATI ---
@st.cache_data
def load_data():
    try:
        # 1. Modelli Evolutivi (Isoctone)
        evol_df = pd.read_csv('data/interpolated_evolution.csv')
        evol_df['hex'] = t2c.rgb2hex(t2c.bv2rgb(evol_df['B-V']))
        
        # 2. Dati Ammassi
        cluster_df = pd.read_csv('data/clusterdata.csv')
        
        # 3. Metadati Ammassi (LongNames, Distanze, Metallicità)
        c_info = pd.DataFrame({
            'LongName': [
                'Pleiades (Solar Composition)', 
                'Hyades (Solar Composition)', 
                'M53 (Low in Metals)', 
                '47 Tuc (Low in Metals)'
            ],
            'ShortName': ['Pleiades', 'Hyades', 'M53', '47 Tuc'],
            'id': ['pleiades', 'hyades', 'm53', '47tuc'],
            'FeH': [0.0, 0.0, -1.86, -0.7],
            'minB': [1e-10, 1e-10, 1e-11, 1e-11],
            'maxB': [1e-2, 1e-2, 1e-3, 1e-3]
        }).set_index('LongName')
        
        return evol_df, cluster_df, c_info
    except Exception as e:
        st.error(f"Errore: Assicurati che i CSV siano nella cartella 'data/'. Dettaglio: {e}")
        return None, None, None

evol_df, cluster_df, cluster_info = load_data()

# --- HELPER: FORMATTAZIONE ETÀ ---
def format_age_text(age):
    if age < 1e6: return f"{age:.0f} anni"
    if age < 1e9: return f"{age/1e6:.1f} Milioni di anni"
    return f"{age/1e9:.2f} Miliardi di anni"

# --- SIDEBAR: CONTROLLI ---
st.sidebar.header("🔬 Parametri dell'Ammasso")

# 1. Selezione Cluster (LongName come nell'originale)
sel_long_name = st.sidebar.radio("Scegli Ammasso:", list(cluster_info.index))
info = cluster_info.loc[sel_long_name]

# 2. Slider Distanza (Logaritmico)
st.sidebar.markdown("---")
st.sidebar.subheader("📏 Calibrazione Distanza")
log_dist = st.sidebar.slider("Distanza Modello (log10 pc)", 1.0, 4.6, 2.0, step=0.01)
dist_pc = 10**log_dist

# 3. Slider Età (Seleziona tra le età disponibili nel file evol_data)
st.sidebar.markdown("---")
st.sidebar.subheader("⏳ Evoluzione Temporale")
available_ages = sorted(evol_df['Age'].unique())
age_idx = st.sidebar.select_slider(
    "Età del Modello:",
    options=range(len(available_ages)),
    value=0,
    format_func=lambda x: format_age_text(available_ages[x])
)
current_age = available_ages[age_idx]

# --- LOGICA DI FILTRAGGIO ---
# Filtriamo il modello evolutivo per Età e Metallicità dell'ammasso
model_data = evol_df[
    (evol_df['Age'] == current_age) & 
    (evol_df['FeH'] == info['FeH'])
]

# --- GRAFICO 1: HR DIAGRAM MODELLO ---
fig_theory = go.Figure()

# Linea evolutiva
fig_theory.add_trace(go.Scatter(
    x=model_data['B-V'], 
    y=model_data['Luminosity'],
    mode='lines+markers',
    line=dict(color='#00FFFF', width=3),
    marker=dict(size=4, color=model_data['hex']),
    name='Modello MIST'
))

fig_theory.update_layout(
    title=f"Modello Teorico (Età: {format_age_text(current_age)})",
    xaxis_title="Colore (B-V)", yaxis_title="Luminosità (L☉)",
    yaxis_type="log", template="plotly_dark", height=500,
    xaxis=dict(range=[-0.5, 2.0]),
    showlegend=False
)

# --- GRAFICO 2: CLUSTER FITTING ---
this_cluster_data = cluster_df[cluster_df['Cluster'] == info['id']]
# Calcolo brillantezza apparente del modello basata sulla distanza
zams_apparent = model_data['Luminosity'] / (4 * np.pi * (dist_pc**2))

fig_fit = go.Figure()

# Stelle dell'ammasso
fig_fit.add_trace(go.Scattergl(
    x=this_cluster_data['B-V'], 
    y=this_cluster_data['Brightness'],
    mode='markers',
    marker=dict(size=4, color='orange', opacity=0.5),
    name=info['ShortName']
))

# Modello proiettato
fig_fit.add_trace(go.Scatter(
    x=model_data['B-V'], 
    y=zams_apparent,
    mode='lines',
    line=dict(color='#00FFFF', width=3, dash='dot'),
    name='Modello Isoctona'
))

fig_fit.update_layout(
    title=f"Fitting: {sel_long_name}",
    xaxis_title="Colore (B-V)", yaxis_title="Brillantezza (L☉/pc²)",
    yaxis_type="log", template="plotly_dark", height=500,
    xaxis=dict(range=[-0.5, 2.0]),
    yaxis=dict(range=[np.log10(info['minB']), np.log10(info['maxB'])])
)

# --- DISPLAY ---
st.title("🕰️ Laboratorio: L'Orologio delle Stelle")
st.markdown(f"""
### Analisi di {info['ShortName']}
* **Metallicità assegnata [Fe/H]:** {info['FeH']}
* **Distanza calcolata:** {int(dist_pc)} parsec
""")

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(fig_theory, use_container_width=True)
with c2:
    st.plotly_chart(fig_fit, use_container_width=True)

st.divider()
st.info("💡 **Istruzioni:** Trova la combinazione corretta di **Età** (per la forma della curva) e **Distanza** (per l'altezza della curva) affinché il modello coincida con i dati.")
