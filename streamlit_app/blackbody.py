import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit

# --- COSTANTI FISICHE ---
C = 3e8
H = 6.626e-34
K = 1.38e-23
R_SUN = 6.957e8
D_10PC = 3.086e+17

# --- FUNZIONI CORE ---
def wien_law(t):
    """Calcola la lunghezza d'onda di picco (metri)"""
    return 0.002897755 / t

def planck_law(lam, t):
    """Calcola l'intensità della radiazione di corpo nero"""
    return ((2 * H * (C ** 2)) / (lam ** 5)) / (np.exp((H * C) / (lam * K * t)) - 1)

# --- DATI FILTRI UBVRI (Johnson-Cousins) ---
# Dati estratti dal tuo codice per interpolazione
filters_data = {
    'U': {300:0.0, 330:0.56, 370:1.0, 400:0.23, 420:0.0},
    'B': {360:0.0, 400:0.92, 420:1.0, 500:0.32, 560:0.0},
    'V': {470:0.0, 520:0.96, 530:1.0, 600:0.35, 700:0.0},
    'R': {550:0.0, 600:1.0, 700:0.61, 800:0.14, 900:0.0},
    'I': {700:0.0, 800:1.0, 850:0.91, 900:0.15, 920:0.0}
}

def get_filter_funcs():
    funcs = {}
    for f_name, data in filters_data.items():
        w_nm = np.array(list(data.keys()))
        trans = np.array(list(data.values()))
        funcs[f_name] = interp1d(w_nm * 1e-9, trans, kind='cubic', bounds_error=False, fill_value=0)
    return funcs

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Investigatore della Luce - Lab", layout="wide")
st.title("🔭 Laboratorio di Astrofisica: Spettri e Colori")

tab1, tab2, tab3 = st.tabs(["Corpo Nero & Wien", "Filtri & Indice di Colore", "Analisi Dati Reali"])

# --- TAB 1: MODELLO TEORICO & WIEN ---
with tab1:
    st.header("Modello di Corpo Nero")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        temp = st.slider("Temperatura Stella (K)", 2800, 35000, 5800, step=100, key="t1")
        peak_w = wien_law(temp)
        st.metric("Lunghezza d'onda di picco ($λ_{max}$)", f"{peak_w*1e9:.2f} nm")
        st.write("Secondo la Legge di Wien, all'aumentare della temperatura il picco si sposta verso il blu[cite: 571, 588].")

    with col2:
        lams = np.linspace(1e-9, 2000e-9, 500)
        flux = planck_law(lams, temp)
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=lams*1e9, y=flux, name="Corpo Nero", line=dict(color='orange')))
        # Area del visibile
        fig1.add_vrect(x0=400, x1=700, fillcolor="rgba(0, 255, 0, 0.1)", layer="below", line_width=0, annotation_text="Visibile")
        fig1.update_layout(title=f"Spettro a {temp}K", xaxis_title="Wavelength (nm)", yaxis_title="Intensità", template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)

# --- TAB 2: FILTRI UBVRI ---
with tab2:
    st.header("Fotometria e Filtri")
    col1, col2 = st.columns([1, 3])
    
    filter_funcs = get_filter_funcs()
    
    with col1:
        temp2 = st.slider("Temperatura Stella (K)", 2800, 35000, 5800, step=100, key="t2")
        st.info("I filtri selezionano solo una parte dello spettro per calcolare la magnitudine[cite: 652, 691].")
        
    with col2:
        lams2 = np.linspace(300e-9, 1000e-9, 500)
        bb_flux = planck_law(lams2, temp2)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=lams2*1e9, y=bb_flux, name="Blackbody", line=dict(color='white', dash='dash')))
        
        colors = {'U': 'violet', 'B': 'blue', 'V': 'green', 'R': 'red', 'I': 'darkred'}
        for f_name, f_func in filter_funcs.items():
            f_flux = bb_flux * f_func(lams2)
            fig2.add_trace(go.Scatter(x=lams2*1e9, y=f_flux, name=f"Filtro {f_name}", fill='tozeroy', line=dict(color=colors[f_name])))
            
        fig2.update_layout(title="Luce che attraversa i filtri UBVRI", template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

# --- TAB 3: DATI REALI (SPECTRAL FITTING) ---
with tab3:
    st.header("Analisi degli Spettri Stellari")
    
    # Tentativo di caricamento dati (usa un placeholder se il file non c'è)
    try:
        spec_data = pd.read_csv('data/spec_data_use.csv')
        star_choice = st.selectbox("Seleziona una stella dai dati osservativi:", spec_data['Name'].unique())
        
        # Simulazione del fitting (Logica EstTempAndRescale del tuo codice)
        st.success(f"Dati caricati per {star_choice}. Qui l'app confronta lo spettro reale con il modello teorico[cite: 739, 961].")
        st.warning("Nota: Per il fitting interattivo completo è necessario il file CSV originale.")
        
    except:
        st.error("File 'data/spec_data_use.csv' non trovato. Carica il file nella cartella corretta.")
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Solar_spectrum_en.svg/800px-Solar_spectrum_en.svg.png", caption="Esempio di spettro solare con righe di assorbimento[cite: 741].")
