import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Laboratorio Transiti Esopianeti", layout="wide")

# --- DATI SIMULATI DEI PIANETI ---
PLANET_DATA = {
    "Kepler-1b": {"period": 2.47, "depth": 1.85},
    "Kepler-2b": {"period": 2.20, "depth": 2.35},
    "Kepler-3b": {"period": 4.88, "depth": 0.225},
    "Kepler-4b": {"period": 3.21, "depth": 0.16},
    "Kepler-5b": {"period": 3.55, "depth": 2.4},
    "Kepler-6b": {"period": 3.23, "depth": 2.25},
    "Kepler-7b": {"period": 4.88, "depth": 2.55},
    "Kepler-8b": {"period": 3.52, "depth": 2.3}
}

# --- FUNZIONI DI SUPPORTO ---
def generate_lightcurve(period, depth, duration=26):
    """Genera una curva di luce sintetica"""
    time = np.linspace(0, duration, 2000)
    # Rumore di fondo
    flux = np.random.normal(0, 0.08, len(time)) 
    
    # Aggiungi i transiti
    transit_duration = 0.15 
    for i, t in enumerate(time):
        if (t % period) < transit_duration or (t % period) > (period - transit_duration):
            flux[i] -= depth + np.random.normal(0, 0.05)
            
    return time, flux

def get_kepler_distance(period_days):
    """Calcola la distanza basata sulla 3a legge di Keplero"""
    period_years = period_days / 365.25
    distance_au = period_years ** (2/3)
    distance_km = distance_au * 149.6e6 
    return distance_km / 1e6 

# --- INTERFACCIA UTENTE ---
st.title("🔭 Strumento di Analisi: Transiti Esopianeti")
st.markdown("""
Questo simulatore replica i dati raccolti dalla missione Kepler della NASA. 
Utilizza i grafici sottostanti per raccogliere le misurazioni necessarie a completare la tua scheda cartacea.
""")

st.divider()

# --- 1. GRAFICO CURVA DI LUCE ---
st.header("1. Osservazione Curve di Luce")
st.info("💡 **Istruzioni:** Seleziona un pianeta. Usa il mouse per fare zoom sul grafico e misurare sia il **Periodo** (distanza in giorni tra due avvallamenti) sia il **Calo di Luminosità** (% sull'asse verticale).")

selected_planet = st.selectbox("Seleziona il pianeta da analizzare:", list(PLANET_DATA.keys()))

p_data = PLANET_DATA[selected_planet]
t, f = generate_lightcurve(p_data["period"], p_data["depth"])

fig_lc = go.Figure()

# Grafico con LINEA E PUNTINI
fig_lc.add_trace(go.Scattergl(
    x=t, 
    y=f, 
    mode='lines+markers', 
    line=dict(color='rgba(31, 119, 180, 0.4)', width=1), 
    marker=dict(color='#1f77b4', size=4, opacity=0.9)
))

fig_lc.update_layout(
    title=f"Curva di Luce: {selected_planet}",
    xaxis_title="Time in Days",
    yaxis_title="Change in Brightness (%)",
    height=450, # Leggermente più alto per vederlo meglio
    margin=dict(l=0, r=0, t=40, b=0)
)
st.plotly_chart(fig_lc, use_container_width=True)

st.divider()

# --- 2. GRAFICO TERZA LEGGE DI KEPLERO ---
st.header("2. Terza Legge di Keplero")
st.markdown("Utilizza il Periodo che hai misurato nel grafico precedente (asse Y di questo grafico) per trovare la **Distanza Orbitale** corrispondente (asse X). Passa il mouse sulla curva arancione per leggere i valori esatti.")

periods_for_graph = np.linspace(0, 10, 100)
distances_for_graph = [get_kepler_distance(p) for p in periods_for_graph]

fig_kep = go.Figure()
fig_kep.add_trace(go.Scatter(
    x=distances_for_graph, 
    y=periods_for_graph, 
    mode='lines', 
    line=dict(color='orange', width=4)
))
fig_kep.update_layout(
    title="Terza Legge di Keplero",
    xaxis_title="Distance in Millions of Kilometers",
    yaxis_title="Period in (Earth) Days",
    height=450,
    margin=dict(l=0, r=0, t=40, b=0)
)
st.plotly_chart(fig_kep, use_container_width=True)
