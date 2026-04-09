import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit

# --- COSTANTI FISICHE ---
C, H, K_B = 3e8, 6.626e-34, 1.38e-23
R_SUN, D_10PC = 6.957e8, 3.086e+17

# --- FUNZIONI CORE ---
def blackbody(lamda, T):
    """Calcola lo spettro di Planck"""
    return np.array(((2 * H * (C ** 2)) / (lamda ** 5)) / (np.exp((H * C) / (lamda * K_B * T)) - 1), dtype=float)

def wien_law(T):
    """Calcola la lunghezza d'onda di picco"""
    return 0.002897755 / T

def get_continuous_star_color(T):
    """Mappatura cromatica delle classi spettrali"""
    points = [(2000, [255, 100, 0]), (3500, [255, 160, 60]), (5000, [255, 210, 160]), 
              (6000, [255, 255, 240]), (7500, [220, 230, 255]), (9500, [180, 210, 255]), 
              (15000, [150, 190, 255]), (35000, [130, 170, 255])]
    temps, rgbs = [p[0] for p in points], np.array([p[1] for p in points])
    r = int(np.interp(T, temps, rgbs[:, 0]))
    g = int(np.interp(T, temps, rgbs[:, 1]))
    b = int(np.interp(T, temps, rgbs[:, 2]))
    return f'rgb({r},{g},{b})'

# --- DATI FILTRI UBVRI ---
U_raw = {300.0:0.0, 305.0:0.016, 310.0:0.068, 315.0:0.167, 320.0:0.287, 330.0:0.56, 340.0:0.772, 350.0:0.905, 360.0:0.981, 370.0:1.0, 380.0:0.916, 390.0:0.625, 400.0:0.238, 410.0:0.051, 420.0:0.0}
B_raw = {360.0:0.0, 370.0:0.03, 380.0:0.134, 390.0:0.567, 400.0:0.92, 410.0:0.978, 420.0:1.0, 430.0:0.978, 440.0:0.935, 450.0:0.853, 460.0:0.74, 480.0:0.536, 500.0:0.325, 520.0:0.15, 530.0:0.095, 540.0:0.043, 560.0:0.0}
V_raw = {470.0:0.0, 480.0:0.03, 490.0:0.163, 500.0:0.458, 510.0:0.78, 520.0:0.967, 530.0:1.0, 540.0:0.973, 550.0:0.898, 560.0:0.792, 580.0:0.574, 600.0:0.359, 620.0:0.197, 650.0:0.045, 700.0:0.0}
R_raw = {550.0:0.0, 560.0:0.23, 570.0:0.74, 580.0:0.91, 590.0:0.98, 600.0:1.0, 620.0:0.96, 640.0:0.9, 660.0:0.81, 680.0:0.72, 700.0:0.61, 750.0:0.35, 800.0:0.14, 900.0:0.0}
I_raw = {700.0:0.0, 720.0:0.232, 740.0:0.785, 760.0:0.965, 780.0:0.99, 800.0:1.0, 820.0:0.99, 840.0:0.95, 860.0:0.86, 880.0:0.56, 900.0:0.15, 920.0:0.0}

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
        star_choice = st.radio("Seleziona stella nota:", list(known_stars.keys()), index=1)
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

# --- TAB 2: FOTOMETRIA ---
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

# --- TAB 3: SPECTRAL FITTING (Sistemato secondo il tuo codice originale) ---
with tab3:
    st.header("Analisi Dati Reali (Fitting di Planck)")
    try:
        # Caricamento database
        spec_data = pd.read_csv('data/spec_data_use.csv')
        
        col_ctrl, col_plot = st.columns([1, 3])
        
        with col_ctrl:
            star_name = st.selectbox("Seleziona una stella dal catalogo:", spec_data['Name'].unique())
            show_fit = st.toggle("Mostra Fitting di Planck stimato", value=True)
            temp_model_vis = st.slider("Temperatura Modello Visivo (K)", 2800, 65000, 5800, step=100)
            
        # Estrazione dati (logica get_spectral_data)
        idx = spec_data[spec_data['Name'] == star_name].index[0]
        wl_real = np.array(spec_data['Wavelengths'][idx].split(':')).astype(float)
        flux_real = np.array(spec_data['Fluxes'][idx].split(':')).astype(float)
        
        # Logica EstTempAndRescale
        def model_func(lam, A, T): return A * blackbody(lam, T)
        
        # Stima iniziale per il fit
        lamb_max_idx = flux_real.argmax()
        t_init = 0.002897755 / wl_real[lamb_max_idx]
        a_init = flux_real.max() / blackbody(np.array([wl_real[lamb_max_idx]]), t_init)[0]
        
        # Fitting SciPy
        popt, _ = curve_fit(model_func, wl_real, flux_real, p0=(a_init, t_init))
        best_a, best_t = popt
        
        # Normalizzazione del flusso reale per il grafico
        flux_rescaled = flux_real / best_a
        
        with col_plot:
            fig3 = go.Figure()
            # Dati Reali
            fig3.add_trace(go.Scatter(x=wl_real*1e9, y=flux_rescaled, name="Dati Osservativi", line=dict(color='cyan', width=1.5)))
            
            # Modello Interattivo (Nero)
            y_model_vis = blackbody(wl_real, temp_model_vis)
            fig3.add_trace(go.Scatter(x=wl_real*1e9, y=y_model_vis, name="Modello Manuale", line=dict(color='white', dash='dash')))
            
            if show_fit:
                # Miglior Fit calcolato
                y_best = blackbody(wl_real, best_t)
                fig3.add_trace(go.Scatter(x=wl_real*1e9, y=y_best, name=f"Miglior Fit ({int(best_t)}K)", line=dict(color='orange', width=3)))
                st.success(f"Temperatura di miglior fit per {star_name}: **{int(best_t)} K**")

            fig3.update_layout(title=f"Spettro di {star_name}", xaxis_title="nm", yaxis_title="Intensità Normalizzata",
                               template="plotly_dark", plot_bgcolor='black', paper_bgcolor='black', height=500)
            st.plotly_chart(fig3, use_container_width=True)
            
    except FileNotFoundError:
        st.error("Errore: Assicurati di aver caricato il file 'data/spec_data_use.csv'.")
    except Exception as e:
        st.error(f"Si è verificato un errore: {e}")
