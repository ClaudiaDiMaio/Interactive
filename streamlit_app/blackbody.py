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
def blackbody(lamda, T):
    """Calcola lo spettro di Planck (W/m^3)"""
    return np.array(((2 * H * (C ** 2)) / (lamda ** 5)) / (np.exp((H * C) / (lamda * K * T)) - 1), dtype=float)

def wien_law(T):
    """Calcola la lunghezza d'onda di picco in metri"""
    return 0.002897755 / T

# Funzione per mappare Raggio -> Luminosità (Sequenza Principale) dal tuo codice
def get_l_given_r(radius):
    coeffs = [-14.414732200764211, -13.259918928247322, 88.94347154444976, -24.088776726372608, 
              -87.71861646290176, 31.910048976800123, 30.045785739826723, -10.017454060166651, 
              -1.7461666512820873, 5.534581622863519, -0.06725347697088192]
    log_lum_poly = np.poly1d(coeffs)
    logR = np.log10(radius)
    return 10**log_lum_poly(logR)

# --- FOTOMETRIA UBVRI ---
filters_data = {
    'U': {300:0.0, 310:0.068, 340:0.772, 370:1.0, 400:0.238, 420:0.0},
    'B': {360:0.0, 390:0.567, 420:1.0, 500:0.325, 560:0.0},
    'V': {470:0.0, 500:0.458, 530:1.0, 600:0.359, 700:0.0},
    'R': {550:0.0, 600:1.0, 700:0.61, 800:0.14, 900:0.0},
    'I': {700:0.0, 750:0.91, 800:1.0, 850:0.91, 920:0.0}
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
st.title("🔭 Laboratorio di Astrofisica: Spettri, Filtri e Fitting")

tab1, tab2, tab3 = st.tabs(["Confronto Stelle Note", "Fotometria UBVRI", "Analisi Dati Reali"])

# --- TAB 1: CONFRONTO CON MODELLI NOTI (CORRETTO) ---
with tab1:
    st.header("Analisi Comparativa: Modello vs Stelle Note")
    st.write("Cerca di far coincidere la curva tratteggiata (Modello) con quella della stella reale.")
    
    known_stars = {
        'Proxima Centauri': 3300,
        'Il Sole': 5800,
        'Polaris': 7200,
        'Alpha Andromedae': 13000,
        'Eta Ursae Majoris': 16900,
        'Bellatrix': 22000
    }
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        star_choice = st.radio("Seleziona una stella nota:", list(known_stars.keys()), index=1)
        t_ref = known_stars[star_choice]
        
        # Slider per il Modello (fucsia nel tuo codice originale)
        t_model = st.slider("Temperatura Modello (K)", 2000, 35000, 5000, step=100)
        
        # Calcolo Lunghezza d'onda di picco secondo Wien
        pw_model = wien_law(t_model)
        st.metric("λ_max (Modello)", f"{pw_model*1e9:.2f} nm")
        
        # Ricaviamo il colore della stella reale usando il tuo modulo tempNcolor
        try:
            real_star_hex = tc.rgb2hex(tc.temp2rgb(t_ref))[0]
        except:
            real_star_hex = "#FFFF00" # Giallo di fallback se tc non è caricato

    with col2:
        # Range di lunghezze d'onda (da 1nm a 2000nm come nel tuo array originale)
        lams = np.linspace(1e-9, 2000e-9, 1000)
        y_ref = blackbody(lams, t_ref)
        y_model = blackbody(lams, t_model)
        
        # Calcolo dinamico dell'asse Y per vedere entrambi i picchi (logica cr nel tuo codice)
        y_max = 1.1 * max(np.max(y_ref), np.max(y_model))
        
        fig1 = go.Figure()
        
        # Traccia della Stella Reale (con colore fisico)
        fig1.add_trace(go.Scatter(
            x=lams * 1e9, 
            y=y_ref, 
            name=f"{star_choice} ({t_ref}K)", 
            line=dict(color=real_star_hex, width=4)
        ))
        
        # Traccia del Modello Interattivo (Fucsia come nel tuo bqplot)
        fig1.add_trace(go.Scatter(
            x=lams * 1e9, 
            y=y_model, 
            name="Modello Interattivo", 
            line=dict(color='#ff00ff', width=2, dash='dot')
        ))
        
        fig1.update_layout(
            title=f"Spettro: {star_choice} vs Modello",
            xaxis_title="Lunghezza d'onda (nm)",
            yaxis_title="Intensità (W/m³)",
            yaxis=dict(range=[0, y_max]),
            template="plotly_dark", # Sfondo scuro per far risaltare i colori delle stelle
            height=500
        )
        st.plotly_chart(fig1, use_container_width=True)

# --- TAB 2: FILTRI E INDICI DI COLORE (CON STELLA VISUALE) ---
with tab2:
    st.header("Fotometria e Aspetto della Stella")
    col1, col2, col3 = st.columns([1, 2, 1]) # Tre colonne per bilanciare i controlli, il grafico e la stella
    
    with col1:
        t_phot = st.slider("Temperatura Stella (K)", 2800, 35000, 5800, step=500, key="t_phot")
        st.write("---")
        st.write("**Indici di Colore:**")
        
        lams_phot = np.linspace(300e-9, 1000e-9, 1000)
        bb_phot = blackbody(lams_phot, t_phot)
        filter_funcs = get_filter_funcs()
        
        mags = {}
        integrate = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz

        for f_name, f_func in filter_funcs.items():
            flux_val = integrate(bb_phot * f_func(lams_phot), lams_phot)
            calib = {'U': 28.01-6.33, 'B': 27.30-5.31, 'V': 27.34-4.80, 'R': 26.87-4.60, 'I': 27.24-4.51}
            if flux_val > 0:
                mags[f_name] = -2.5 * np.log10(flux_val * (R_SUN/D_10PC)**2) - calib[f_name]
            else:
                mags[f_name] = np.nan
            
        if not np.isnan(mags['B']) and not np.isnan(mags['V']):
            st.metric("Indice B-V", f"{mags['B'] - mags['V']:.2f}")
        
        # Calcolo del colore per la stella visuale
        try:
            star_hex = tc.rgb2hex(tc.temp2rgb(t_phot))[0]
        except:
            star_hex = "#FFFFFF"

    with col2:
        # Grafico dei filtri UBVRI
        fig_filters = go.Figure()
        fig_filters.add_trace(go.Scatter(x=lams_phot*1e9, y=bb_phot, name="Corpo Nero", line=dict(color='orange', dash='dash')))
        
        colors = {'U': 'violet', 'B': 'blue', 'V': 'green', 'R': 'red', 'I': 'darkred'}
        for f_name, f_func in filter_funcs.items():
            f_flux = bb_phot * f_func(lams_phot)
            fig_filters.add_trace(go.Scatter(x=lams_phot*1e9, y=f_flux, name=f"Filtro {f_name}", fill='tozeroy', line=dict(color=colors[f_name])))
            
        fig_filters.update_layout(title="Luce filtrata (UBVRI)", template="plotly_dark", height=450, margin=dict(l=0,r=0,b=0,t=40))
        st.plotly_chart(fig_filters, use_container_width=True)

    with col3:
        # Visualizzazione della Stella (come nel tuo fig3)
        st.write("**Aspetto della Stella**")
        fig_star = go.Figure()
        
        # Aggiungiamo un effetto "glow" con due cerchi sovrapposti
        fig_star.add_trace(go.Scatter(
            x=[0], y=[0], mode='markers',
            marker=dict(size=120, color=star_hex, opacity=0.3) # Alone esterno
        ))
        fig_star.add_trace(go.Scatter(
            x=[0], y=[0], mode='markers',
            marker=dict(size=80, color=star_hex, line=dict(width=2, color='white')) # Nucleo stella
        ))
        
        fig_star.update_layout(
            showlegend=False, plot_bgcolor='black', paper_bgcolor='black',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 1]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 1]),
            height=300, margin=dict(l=0,r=0,b=0,t=0)
        )
        st.plotly_chart(fig_star, use_container_width=True)
        st.caption(f"Colore percepito a {t_phot}K")

# --- TAB 3: SPECTRAL FITTING (DATI REALI) ---
with tab3:
    st.header("Fitting di Spettri Osservativi")
    
    try:
        spec_data = pd.read_csv('data/spec_data_use.csv')
        star_name = st.selectbox("Seleziona una stella dal catalogo:", spec_data['Name'].unique())
        
        idx = spec_data[spec_data['Name'] == star_name].index[0]
        wl_real = np.array(spec_data['Wavelengths'][idx].split(':')).astype(float)
        flux_real = np.array(spec_data['Fluxes'][idx].split(':')).astype(float)
        
        show_fit = st.toggle("Mostra Fitting di Planck stimato")
        
        # Fitting (Logica EstTempAndRescale)
        def fit_func(lam, A, T):
            return A * blackbody(lam, T)

        # Stima iniziale
        lamb_max = wl_real[flux_real.argmax()]
        t_init = 0.002897755 / lamb_max
        a_init = flux_real.max() / blackbody(np.array([lamb_max]), t_init)[0]

        popt, _ = curve_fit(fit_func, wl_real, flux_real, p0=(a_init, t_init))
        best_a, best_t = popt
        
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=wl_real*1e9, y=flux_real / best_a, name="Dati Reali (Rescaled)", line=dict(color='cyan')))
        
        if show_fit:
            y_fit = blackbody(wl_real, best_t)
            fig3.add_trace(go.Scatter(x=wl_real*1e9, y=y_fit, name=f"Fit di Planck ({int(best_t)}K)", line=dict(color='orange', width=4)))
            st.success(f"Temperatura stimata per {star_name}: **{int(best_t)} K**")

        fig3.update_layout(xaxis_title="Lunghezza d'onda (nm)", yaxis_title="Intensità Normalizzata", template="plotly_dark")
        st.plotly_chart(fig3, use_container_width=True)
        
    except FileNotFoundError:
        st.error("Per questa Tab è necessario il file 'data/spec_data_use.csv'.")
    except Exception as e:
        st.error(f"Errore nel caricamento dati: {e}")
