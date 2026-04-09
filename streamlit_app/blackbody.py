import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import interp1d

# --- COSTANTI FISICHE ---
C, H, K_B = 3e8, 6.626e-34, 1.38e-23
R_SUN, D_10PC = 6.957e8, 3.086e+17

# --- FUNZIONE PER COLORE CONTINUO (Classi Spettrali) ---
def get_continuous_star_color(T):
    points = [
        (2000,  [255, 100, 0]),   # Rosso profondo
        (3500,  [255, 160, 60]),  # Classe M
        (5000,  [255, 210, 160]), # Classe K
        (6000,  [255, 255, 240]), # Classe G (Sole)
        (7500,  [220, 230, 255]), # Classe F
        (10000, [180, 210, 255]), # Classe A
        (20000, [150, 190, 255]), # Classe B
        (40000, [130, 170, 255])  # Classe O
    ]
    temps = [p[0] for p in points]
    rgbs = np.array([p[1] for p in points])
    r = int(np.interp(T, temps, rgbs[:, 0]))
    g = int(np.interp(T, temps, rgbs[:, 1]))
    b = int(np.interp(T, temps, rgbs[:, 2]))
    return f'rgb({r},{g},{b})'

# --- FUNZIONI SCIENTIFICHE ---
def blackbody(lamda, T):
    return np.array(((2 * H * (C ** 2)) / (lamda ** 5)) / (np.exp((H * C) / (lamda * K_B * T)) - 1), dtype=float)

def wien_law(T):
    return 0.002897755 / T

# --- DATI FILTRI UBVRI AD ALTA RISOLUZIONE (Dal tuo codice Jupyter) ---
U_raw = {300.0:0.000, 305.0:0.016, 310.0:0.068, 315.0:0.167, 320.0:0.287, 325.0:0.423, 330.0:0.560, 335.0:0.673, 340.0:0.772, 345.0:0.841, 350.0:0.905, 355.0:0.943, 360.0:0.981, 365.0:0.993, 370.0:1.000, 375.0:0.989, 380.0:0.916, 385.0:0.804, 390.0:0.625, 395.0:0.423, 400.0:0.238, 405.0:0.114, 410.0:0.051, 415.0:0.019, 420.0:0.000}
B_raw = {360.0:0.000, 370.0:0.030, 380.0:0.134, 390.0:0.567, 400.0:0.920, 410.0:0.978, 420.0:1.000, 430.0:0.978, 440.0:0.935, 450.0:0.853, 460.0:0.740, 470.0:0.640, 480.0:0.536, 490.0:0.424, 500.0:0.325, 510.0:0.235, 520.0:0.150, 530.0:0.095, 540.0:0.043, 550.0:0.009, 560.0:0.000}
V_raw = {470.0:0.000, 480.0:0.030, 490.0:0.163, 500.0:0.458, 510.0:0.780, 520.0:0.967, 530.0:1.000, 540.0:0.973, 550.0:0.898, 560.0:0.792, 570.0:0.684, 580.0:0.574, 590.0:0.461, 600.0:0.359, 610.0:0.270, 620.0:0.197, 630.0:0.135, 640.0:0.081, 650.0:0.045, 660.0:0.025, 670.0:0.017, 680.0:0.013, 690.0:0.009, 700.0:0.000}
R_raw = {550.0:0.00, 560.0:0.23, 570.0:0.74, 580.0:0.91, 590.0:0.98, 600.0:1.00, 610.0:0.98, 620.0:0.96, 630.0:0.93, 640.0:0.90, 650.0:0.86, 660.0:0.81, 670.0:0.78, 680.0:0.72, 690.0:0.67, 700.0:0.61, 710.0:0.56, 720.0:0.51, 730.0:0.46, 740.0:0.40, 750.0:0.35, 800.0:0.14, 850.0:0.03, 900.0:0.00}
I_raw = {700.0:0.000, 710.0:0.024, 720.0:0.232, 730.0:0.555, 740.0:0.785, 750.0:0.910, 760.0:0.965, 770.0:0.985, 780.0:0.990, 790.0:0.995, 800.0:1.000, 810.0:1.000, 820.0:0.990, 830.0:0.980, 840.0:0.950, 850.0:0.910, 860.0:0.860, 870.0:0.750, 880.0:0.560, 890.0:0.330, 900.0:0.150, 910.0:0.030, 920.0:0.000}

def get_filter_funcs():
    funcs = {}
    raw_data = {'U': U_raw, 'B': B_raw, 'V': V_raw, 'R': R_raw, 'I': I_raw}
    for f_name, data in raw_data.items():
        w_m = np.array(list(data.keys())) * 1e-9
        trans = np.array(list(data.values()))
        funcs[f_name] = interp1d(w_m, trans, kind='linear', bounds_error=False, fill_value=0)
    return funcs

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Laboratorio di Astronomia", layout="wide")
st.title("🔭 Investigatore della Luce: Spettri e Colori")

tab1, tab2, tab3 = st.tabs(["Confronto Stelle Note", "Fotometria UBVRI", "Analisi Dati Reali"])

# --- TAB 1 ---
with tab1:
    st.header("Modello vs Stelle Note")
    known_stars = {'Proxima Centauri': 3300, 'Il Sole': 5800, 'Polaris': 7200, 'Alpha Andromedae': 13000, 'Bellatrix': 22000}
    col1, col2 = st.columns([1, 3])
    with col1:
        star_choice = st.radio("Scegli stella nota:", list(known_stars.keys()), index=1)
        t_ref = known_stars[star_choice]
        t_model = st.slider("Temperatura Modello (K)", 2000, 40000, 5000, step=100, key="t1")
    with col2:
        lams = np.linspace(50e-9, 2500e-9, 1000)
        y_ref, y_model = blackbody(lams, t_ref), blackbody(lams, t_model)
        y_max = 1.1 * max(np.max(y_ref), np.max(y_model))
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=lams*1e9, y=y_ref, name=star_choice, line=dict(color=get_continuous_star_color(t_ref), width=4)))
        fig1.add_trace(go.Scatter(x=lams*1e9, y=y_model, name="Modello", line=dict(color='#ff00ff', width=2, dash='dot')))
        fig1.update_layout(xaxis_title="nm", yaxis_title="Intensità", yaxis=dict(range=[0, y_max]), template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black')
        st.plotly_chart(fig1, use_container_width=True)

# --- TAB 2 (SISTEMATO: FILTRI MORBIDI E SPETTRO VISIBILE) ---
with tab2:
    st.header("Fotometria UBVRI e Colore")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        t_phot = st.slider("Temperatura (K)", 2000, 40000, 5800, step=100, key="t2")
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
        # Spettro Totale in ARGENTO per essere visibile sempre
        fig2.add_trace(go.Scatter(x=lams_phot*1e9, y=bb_phot, name="Spettro Totale", line=dict(color='#D3D3D3', width=2.5)))
        colors_map = {'U': 'violet', 'B': 'blue', 'V': 'green', 'R': 'red', 'I': 'darkred'}
        for f_name, f_func in filter_funcs.items():
            f_flux = bb_phot * f_func(lams_phot)
            fig2.add_trace(go.Scatter(x=lams_phot*1e9, y=f_flux, name=f"Banda {f_name}", fill='tozeroy', line=dict(color=colors_map[f_name])))
        fig2.update_layout(title="Spettro e Filtri", xaxis_title="nm", template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black', height=450)
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        st.write("**Aspetto Stella**")
        fig_star = go.Figure()
        fig_star.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=140, color=current_color, opacity=0.3)))
        fig_star.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=80, color=current_color, line=dict(width=3, color='white'))))
        fig_star.update_layout(showlegend=False, plot_bgcolor='black', paper_bgcolor='black', xaxis=dict(visible=False), yaxis=dict(visible=False), height=300)
        st.plotly_chart(fig_star, use_container_width=True)

# --- TAB 3 ---
with tab3:
    st.header("Analisi Dati Reali")
    try:
        spec_data = pd.read_csv('data/spec_data_use.csv')
        star_name = st.selectbox("Seleziona stella:", spec_data['Name'].unique())
        st.success(f"Analisi per {star_name} attiva.")
    except:
        st.warning("Assicurati che 'data/spec_data_use.csv' sia presente.")
