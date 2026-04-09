import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import interp1d

# --- COSTANTI FISICHE [cite: 395, 563] ---
C, H, K_B = 3e8, 6.626e-34, 1.38e-23
R_SUN, D_10PC = 6.957e8, 3.086e+17

# --- FUNZIONE PER COLORE CONTINUO (Basata sulle Classi Spettrali [cite: 756-779]) ---
def get_continuous_star_color(T):
    points = [
        (2000,  [255, 100, 0]),   # Rosso profondo
        (3500,  [255, 160, 60]),  # Classe M [cite: 777-778]
        (5000,  [255, 210, 160]), # Classe K [cite: 774-775]
        (6000,  [255, 255, 240]), # Classe G (Sole ~5770K) [cite: 101, 771-772]
        (7500,  [220, 230, 255]), # Classe F [cite: 768-769]
        (10000, [180, 210, 255]), # Classe A [cite: 765-766]
        (20000, [150, 190, 255]), # Classe B [cite: 762-763]
        (40000, [130, 170, 255])  # Classe O [cite: 759-760]
    ]
    temps = [p[0] for p in points]
    rgbs = np.array([p[1] for p in points])
    r = int(np.interp(T, temps, rgbs[:, 0]))
    g = int(np.interp(T, temps, rgbs[:, 1]))
    b = int(np.interp(T, temps, rgbs[:, 2]))
    return f'rgb({r},{g},{b})'

# --- FUNZIONI SCIENTIFICHE [cite: 561, 571] ---
def blackbody(lamda, T):
    """Funzione di Planck [cite: 561]"""
    return np.array(((2 * H * (C ** 2)) / (lamda ** 5)) / (np.exp((H * C) / (lamda * K_B * T)) - 1), dtype=float)

def wien_law(T):
    """Legge di Wien [cite: 571]"""
    return 0.002897755 / T

# --- DATI FILTRI UBVRI COMPLETI [cite: 664-683] ---
U_raw = {300:0.0, 310:0.068, 340:0.772, 370:1.0, 400:0.238, 420:0.0}
B_raw = {360:0.0, 390:0.567, 420:1.0, 500:0.325, 560:0.0}
V_raw = {470:0.0, 500:0.458, 530:1.0, 600:0.359, 700:0.0}
R_raw = {550:0.0, 600:1.0, 700:0.61, 800:0.14, 900:0.0}
I_raw = {700:0.0, 750:0.91, 800:1.0, 850:0.91, 920:0.0}

def get_filter_funcs():
    funcs = {}
    raw_data = {'U': U_raw, 'B': B_raw, 'V': V_raw, 'R': R_raw, 'I': I_raw}
    for f_name, data in raw_data.items():
        w_m = np.array(list(data.keys())) * 1e-9
        trans = np.array(list(data.values()))
        funcs[f_name] = interp1d(w_m, trans, kind='linear', bounds_error=False, fill_value=0)
    return funcs

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Investigatore della Luce", layout="wide")
st.title("🔭 Laboratorio di Astrofisica: Spettri e Colori")

tab1, tab2, tab3 = st.tabs(["Confronto Stelle Note", "Fotometria UBVRI", "Analisi Dati Reali"])

# --- TAB 1: CONFRONTO MODELLI ---
with tab1:
    st.header("Analisi Comparativa: Modello vs Stelle Note")
    known_stars = {'Proxima Centauri': 3300, 'Il Sole': 5800, 'Polaris': 7200, 'Alpha Andromedae': 13000, 'Bellatrix': 22000}
    col1, col2 = st.columns([1, 3])
    with col1:
        star_choice = st.radio("Seleziona stella reale:", list(known_stars.keys()), index=1)
        t_ref = known_stars[star_choice]
        t_model = st.slider("Temperatura Modello (K)", 2000, 40000, 5000, step=100, key="t1_s")
    with col2:
        lams = np.linspace(50e-9, 2500e-9, 1000)
        y_ref, y_model = blackbody(lams, t_ref), blackbody(lams, t_model)
        y_max = 1.1 * max(np.max(y_ref), np.max(y_model))
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=lams*1e9, y=y_ref, name=star_choice, line=dict(color=get_continuous_star_color(t_ref), width=4)))
        fig1.add_trace(go.Scatter(x=lams*1e9, y=y_model, name="Modello", line=dict(color='#ff00ff', width=2, dash='dot')))
        fig1.update_layout(xaxis_title="nm", yaxis_title="Intensità", yaxis=dict(range=[0, y_max]), template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black')
        st.plotly_chart(fig1, use_container_width=True)

# --- TAB 2: FOTOMETRIA E STELLA DINAMICA (SISTEMATO) ---
with tab2:
    st.header("Fotometria UBVRI e Aspetto della Stella")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        t_phot = st.slider("Temperatura Stella (K)", 2000, 40000, 5800, step=100, key="t2_s")
        lams_phot = np.linspace(250e-9, 1200e-9, 1000)
        bb_phot = blackbody(lams_phot, t_phot)
        filter_funcs = get_filter_funcs()
        integrate = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz
        mags = {}
        for f_name, f_func in filter_funcs.items():
            flux_val = integrate(bb_phot * f_func(lams_phot), lams_phot)
            calib = {'U': 21.68, 'B': 21.99, 'V': 22.54, 'R': 22.27, 'I': 22.73}
            mags[f_name] = -2.5 * np.log10(flux_val) + calib[f_name] if flux_val > 0 else 0
        if 'B' in mags and 'V' in mags:
            st.metric("Indice B-V", f"{mags['B'] - mags['V']:.2f}")
        current_color = get_continuous_star_color(t_phot)

    with col2:
        fig2 = go.Figure()
        # 1. Spettro Totale - Colore Grigio Chiaro per visibilità universale e sfondo Nero forzato
        fig2.add_trace(go.Scatter(
            x=lams_phot*1e9, 
            y=bb_phot, 
            name="Spettro Continuo", 
            line=dict(color='#D3D3D3', width=2) # Grigio chiaro (Silver)
        ))
        
        # 2. Contributi filtrati (Area colorata sotto la curva)
        colors_map = {'U': 'violet', 'B': 'blue', 'V': 'green', 'R': 'red', 'I': 'darkred'}
        for f_name, f_func in filter_funcs.items():
            f_flux = bb_phot * f_func(lams_phot)
            fig2.add_trace(go.Scatter(
                x=lams_phot*1e9, 
                y=f_flux, 
                name=f"Banda {f_name}", 
                fill='tozeroy', 
                line=dict(color=colors_map[f_name])
            ))
            
        fig2.update_layout(
            title="Spettro Completo vs Filtri UBVRI", 
            xaxis_title="nm", 
            template="plotly_dark", 
            plot_bgcolor='black', # Sfondo grafico nero
            paper_bgcolor='black', # Sfondo esterno nero
            height=450
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        st.write("**Aspetto Visivo**")
        fig_star = go.Figure()
        fig_star.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=140, color=current_color, opacity=0.3)))
        fig_star.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=80, color=current_color, line=dict(width=3, color='white'))))
        fig_star.update_layout(
            showlegend=False, plot_bgcolor='black', paper_bgcolor='black',
            xaxis=dict(visible=False, range=[-1,1]), yaxis=dict(visible=False, range=[-1,1]), 
            height=300, margin=dict(l=0,r=0,b=0,t=0)
        )
        st.plotly_chart(fig_star, use_container_width=True)
        st.caption(f"Colore a {t_phot} K")

# --- TAB 3: DATI REALI ---
with tab3:
    st.header("Analisi Dati Reali")
    try:
        spec_data = pd.read_csv('data/spec_data_use.csv')
        star_name = st.selectbox("Seleziona stella:", spec_data['Name'].unique())
        st.success(f"Dati caricati per {star_name}.")
    except:
        st.warning("Carica il file 'data/spec_data_use.csv' per visualizzare gli spettri osservativi.")
