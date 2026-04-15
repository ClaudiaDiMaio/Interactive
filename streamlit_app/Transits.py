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
    # Rumore di fondo (0.0 è la luminosità normale della stella)
    flux = np.random.normal(0, 0.08, len(time)) 
    
    # Aggiungi i transiti (i valori scendono sotto lo zero)
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
st.title("🔭 Laboratorio: Analisi Curve di Luce di Transito")
st.markdown("""
Questo laboratorio simula le osservazioni della missione Kepler della NASA. 
I grafici mostrano come il livello di luce cambia quando un pianeta transita davanti alla sua stella.
""")

col_left, col_right = st.columns([1.5, 1])

with col_left:
    st.header("1. Osservazione Curve di Luce")
    st.info("💡 **Istruzioni:** Usa il menu per cambiare pianeta. Passa il mouse sui puntini o seleziona un'area per zoomare e misurare la distanza tra due avvallamenti (il Periodo).")
    
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
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    st.plotly_chart(fig_lc, use_container_width=True)

    st.header("2. Terza Legge di Keplero")
    st.markdown("Trova il *Periodo* misurato sull'asse Y, e leggi la Distanza corrispondente sull'asse X.")
    
    periods_for_graph = np.linspace(0, 10, 100)
    distances_for_graph = [get_kepler_distance(p) for p in periods_for_graph]
    
    fig_kep = go.Figure()
    fig_kep.add_trace(go.Scatter(x=distances_for_graph, y=periods_for_graph, mode='lines', line=dict(color='orange', width=3)))
    fig_kep.update_layout(
        title="Terza Legge di Keplero",
        xaxis_title="Distance in Millions of Kilometers",
        yaxis_title="Period in (Earth) Days",
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    st.plotly_chart(fig_kep, use_container_width=True)

with col_right:
    st.header("3. Tabella Dati")
    # Aggiungiamo la 'r' prima delle virgolette per attivare la "raw string"
    st.markdown(r"""
    **Formule utili:**
    * **Raggio del Pianeta** $= 10 \times \sqrt{Z}$ 
    *(dove Z è il calo di luminosità espresso in numero positivo)*
    """)
    
    if 'student_data' not in st.session_state:
        df_empty = pd.DataFrame(
            "", 
            index=list(PLANET_DATA.keys()), 
            columns=["Period (Days)", "Orbital Dist.", "Drop of Z (%)", "Radius (Earth Radii)"]
        )
        st.session_state.student_data = df_empty

    edited_df = st.data_editor(st.session_state.student_data, use_container_width=True, height=350)
    
    st.header("4. Domande Finali")
    q1 = st.text_input("1. Quale/i pianeta/i hanno una dimensione simile alla Terra?")
    q2 = st.text_input("2. Quali pianeti hanno una dimensione simile a quella di Giove?")
    q3 = st.text_area("3. Descrivi la relazione tra il periodo dei pianeti e le loro distanze orbitali.")

    with st.expander("Mostra Soluzioni (Modalità Docente)"):
        st.write("Valori teorici attesi (approssimativi):")
        sol_df = pd.DataFrame(index=list(PLANET_DATA.keys()), columns=["Period (Days)", "Orbital Dist.", "Drop of Z (%)", "Radius (Earth Radii)"])
        for p, d in PLANET_DATA.items():
            sol_df.loc[p, "Period (Days)"] = d["period"]
            sol_df.loc[p, "Drop of Z (%)"] = d["depth"]
            sol_df.loc[p, "Orbital Dist."] = round(get_kepler_distance(d["period"]), 2)
            sol_df.loc[p, "Radius (Earth Radii)"] = round(10 * np.sqrt(d["depth"]), 1)
        st.dataframe(sol_df, use_container_width=True)
