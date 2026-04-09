import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit

# --- COSTANTI FISICHE ---
C, H, K = 3e8, 6.626e-34, 1.38e-23
R_SUN, D_10PC = 6.957e8, 3.086e+17

# --- FUNZIONE FALLBACK PER IL COLORE (Se tempNcolor fallisce) ---
def get_star_color(temperature):
    """Restituisce un colore Hex approssimativo basato sulla temperatura (K)"""
    if temperature < 3500: return "#ff3300"  # Rosso (M)
    if temperature < 5000: return "#ff9933"  # Arancione (K)
    if temperature < 6000: return "#ffff66"  # Giallo (G - Sole)
    if temperature < 7500: return "#ffffff"  # Bianco (F)
    if temperature < 10000: return "#ccf2ff" # Bianco-Azzurro (A)
    return "#99ccff" # Blu (O/B)

# --- FUNZIONI CORE ---
def blackbody(lamda, T):
    return np.array(((2 * H * (C ** 2)) / (lamda ** 5)) / (np.exp((H * C) / (lamda * K * T)) - 1), dtype=float)

def wien_law(T):
    return 0.002897755 / T

# --- DATI FILTRI UBVRI ---
filters_data = {
    'U': {300:0.0, 310:0.068, 370:1.0, 420:0.0},
    'B': {360:0.0, 420:1.0, 560:0.0},
    'V': {470:0.0, 530:1.0, 700:0.0},
    'R': {550:0.0, 600:1.0, 900:0.0},
    'I': {700:0.0, 800:1.0, 920:0.0}
}

def get_filter_funcs():
    funcs = {}
    for f_name, data in filters_data.items():
        w_m = np.array(list(data.keys())) * 1e-9
        trans = np.array(list(data.values()))
        funcs[f_name] = interp1d(w_m, trans, kind='cubic', bounds_error=False, fill_value=0)
    return funcs

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Investigatore della Luce - Lab", layout="wide")
st.title("🔭 Laboratorio di Astrofisica: Spettri e Colori")

tab1, tab2, tab3 = st.tabs(["Confronto Stelle Note", "Fotometria UBVRI", "Analisi Dati Reali"])

# --- TAB 1: CONFRONTO ---
with tab1:
    st.header("Analisi Comparativa: Modello vs Stelle Note")
    known_stars = {'Proxima Centauri': 3300, 'Il Sole': 5800, 'Polaris': 7200, 'Alpha Andromedae': 13000, 'Bellatrix': 22000}
    
    col1, col2 = st.columns([1, 3])
    with col1:
        star_choice = st.radio("Seleziona una stella nota:", list(known_stars.keys()), index=1)
        t_ref = known_stars[star_choice]
        t_model = st.slider("Temperatura Modello (K)", 2000, 35000, 5000, step=100, key="slider_t1")
        
        color_ref = get_star_color(t_ref)
        color_model = get_star_color(t_model) # Il colore della linea cambia con lo slider!
        st.write(f"λ_max Modello: {wien_law(t_model)*1e9:.1f} nm")

    with col2:
        lams = np.linspace(100e-9, 2000e-9, 1000)
        y_ref, y_model = blackbody(lams, t_ref), blackbody(lams, t_model)
        y_max = 1.1 * max(np.max(y_ref), np.max(y_model))
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=lams*1e9, y=y_ref, name=star_choice, line=dict(color=color_ref, width=4)))
        fig1.add_trace(go.Scatter(x=lams*1e9, y=y_model, name="Modello", line=dict(color=color_model, width=2, dash='dot')))
        fig1.update_layout(xaxis_title="nm", yaxis_title="Intensità", yaxis=dict(range=[0, y_max]), template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)

# --- TAB 2: FOTOMETRIA E STELLA VISUALE ---
with tab2:
    st.header("Fotometria e Aspetto della Stella")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        t_phot = st.slider("Temperatura Stella (K)", 2000, 40000, 5800, step=500, key="slider_t2")
        lams_phot = np.linspace(300e-9, 1200e-9, 1000)
        bb_phot = blackbody(lams_phot, t_phot)
        
        # Calcolo Indice B-V
        filter_funcs = get_filter_funcs()
        integrate = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz
        mags = {}
        for f_name, f_func in filter_funcs.items():
            flux_val = integrate(bb_phot * f_func(lams_phot), lams_phot)
            calib = {'U': 21.68, 'B': 21.99, 'V': 22.54, 'R': 22.27, 'I': 22.73} # Calibrazione semplificata
            mags[f_name] = -2.5 * np.log10(flux_val) + calib[f_name] if flux_val > 0 else 0
        
        st.metric("Indice B-V", f"{mags['B'] - mags['V']:.2f}")
        current_color = get_star_color(t_phot)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=lams_phot*1e9, y=bb_phot, name="BB", line=dict(color='gray', dash='dash')))
        colors_map = {'U': 'violet', 'B': 'blue', 'V': 'green', 'R': 'red', 'I': 'darkred'}
        for f_name, f_func in filter_funcs.items():
            fig2.add_trace(go.Scatter(x=lams_phot*1e9, y=bb_phot*f_func(lams_phot), name=f_name, fill='tozeroy', line=dict(color=colors_map[f_name])))
        fig2.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        st.write("**Aspetto della Stella**")
        fig_star = go.Figure()
        # Effetto bagliore: il colore cambierà in base a t_phot
        fig_star.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=120, color=current_color, opacity=0.3)))
        fig_star.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=70, color=current_color, line=dict(width=2, color='white'))))
        fig_star.update_layout(showlegend=False, plot_bgcolor='black', paper_bgcolor='black',
                               xaxis=dict(visible=False, range=[-1,1]), yaxis=dict(visible=False, range=[-1,1]), height=300)
        st.plotly_chart(fig_star, use_container_width=True)
        st.caption(f"Colore a {t_phot} K")

# --- TAB 3: DATI REALI ---
with tab3:
    st.header("Analisi Dati Reali")
    try:
        spec_data = pd.read_csv('data/spec_data_use.csv')
        star_name = st.selectbox("Seleziona stella:", spec_data['Name'].unique())
        st.info("Qui è possibile implementare il fitting dei dati caricati dal CSV.")
    except:
        st.warning("Carica 'data/spec_data_use.csv' per visualizzare i dati reali.")
